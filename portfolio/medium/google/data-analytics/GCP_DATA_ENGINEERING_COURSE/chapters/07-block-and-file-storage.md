# 2.2 — Block & File Storage

> **Section 2 · Storage & Databases · Lecture 2.2 · 8:00**

## 🎯 What you will learn

- What a **block device** is and why the operating system is the only thing that can read one
- Persistent Disk: types, IOPS/throughput coupling, and how to size a disk you do not have to babysit
- Local SSD: the throughput it really gives you, and the durability it costs you
- Filestore: NFS, performance tiers, and where it sits on the block/file spectrum
- The difference between block and file storage, explained from the syscall upward
- When object, block, or file storage is the right answer — a real decision matrix
- Why "just use a bigger disk" is a scaling strategy that eventually stops working
- The cost mechanics of provisioned IOPS versus throughput, and how to avoid the two big surprises
- How to apply the decision matrix to the course's own pipeline

---

## 🧠 Concept

### Three storage models, one axis of difference

The question "object, block, or file?" is really a question about **who is allowed to interpret the bytes**.

```text
OBJECT STORAGE          BLOCK STORAGE              FILE STORAGE
─────────────           ─────────────              ────────────
bytes + metadata        bytes + metadata           bytes + metadata
  in a namespace          on a device                in a tree
                                                       
access via HTTP/JSON    access via a block device   access via POSIX
no filesystem           needs a filesystem driver   has a filesystem
  (raw bytes)             mounted on it                (names, dirs)
                       
"read object o"         "read block 4096"           "open /data/x.csv"
```

The decisive point: **object storage hands you a stream of bytes and a key. Block storage hands you a device that the kernel exposes as a file of raw bytes. File storage hands you a filesystem.** An application that has `open()`, `read()`, `write()`, `seek()` can use file storage directly. It cannot use object storage without a library that emulates that interface. And block storage is *invisible* to the application until something formats it and mounts it.

### Block storage: Persistent Disk

A **Persistent Disk (PD)** is a network-attached block device. From inside the VM it looks exactly like `/dev/sdb`; the kernel sees a block device, you partition it or give it to `xfs`/`ext4`, and you mount it. The hypervisor does not know or care what is on it. This is the whole point of the abstraction: the disk survives the VM, and any POSIX application works with it unchanged.

Persistent Disk comes in four types. The differences are in how the underlying media is provisioned and, critically, in how **IOPS and throughput interact**:

| Type | Media | Max size | Max IOPS | Max throughput | IOPS/throughput coupling |
|---|---|---|---|---|---|
| `pd-standard` | HDD | 64 TB | 0.75 IOPS/GB | 0.12 MB/s/GB | **Fully coupled** — you get a fixed ratio |
| `pd-balanced` | SSD | 64 TB | 6 IOPS/GB | 0.28 MB/s/GB | **Fully coupled** |
| `pd-ssd` | SSD | 64 TB | 30 IOPS/GB | 1.2 MB/s/GB | **Fully coupled** |
| `pd-extreme` | SSD | 64 TB | 60 IOPS/GB | 2.4 MB/s/GB | **Fully coupled**, plus 1,000 IOPS baseline |
| `hyperdisk-balanced` | SSD | 64 TB | 100 IOPS/GB | 1.2 MB/s/GB | **Independently provisionable** |

The coupling is the thing that bites. On a coupled disk, when you request more IOPS you get proportionally more throughput, and vice versa — but you cannot ask for "10,000 IOPS at 50 MB/s" if that ratio is not on the disk's line. In practice the simplest approach works: **request the size, take the disk type's defaults, and add a separate provisioned-IOPS or provisioned-throughput disk if the defaults are not enough.** Adding a second disk of a different type (one for capacity, one for hot data) is a normal, well-supported pattern.

The important operational facts about Persistent Disk:

- **They are zonal.** A PD lives in one zone. If you want the disk to survive a zone outage, you use **Regional Persistent Disk**, which is a synchronously-replicated PD across two zones in a region. It costs roughly twice as much and has a write latency penalty, because every write must be acknowledged by both zones.
- **They support live migration.** A VM's disks can be moved to another host while the VM keeps running. This is what makes VM maintenance transparent.
- **Snapshots are incremental and asynchronous.** A snapshot is a crash-consistent point-in-time copy stored in Cloud Storage. It is not application-consistent unless the application flushes first. Snapshots of a PD are billed at the Cloud Storage rate for the data they hold.
- **They can be grown, but not shrunk.** Expanding a PD online is fine. Shrinking requires a new disk and a data migration.
- **You can attach the same PD to multiple VMs read-only.** That is how you get a shared database cluster's data files, or a golden image, onto several instances.

The performance ceiling people hit most often: **network egress from the VM is capped**, and a PD's throughput is ultimately limited by how fast data can move over the VM's virtual NIC. A PD with 1,200 MB/s of throughput cannot help if the VM is limited to 1,000 Mbps (~125 MB/s) of egress.

### Local SSD

**Local SSD** is a non-persistent, high-performance block device attached directly to the VM's host. It is *not* network-attached, which is why it is faster than a Persistent Disk of any type: no virtualisation overhead, no network hop, and it is NVMe.

The two facts that define Local SSD:

1. **The data does not survive VM migration, instance recreation, or host failure.** It is a cache, not a disk. Anything on Local SSD must be reconstructible from elsewhere, and your application must tolerate its loss.
2. **You pay by attaching it.** Local SSD is billed per GB attached to a running VM, whether you write to it or not. Unlike a Persistent Disk, you pay for the whole capacity for the VM's lifetime.

Local SSD's throughput: on most machine types, up to ~375 MB/s per attached Local SSD, and you can attach several. The real benefit over a PD is **lower latency and higher IOPS at low queue depths**, plus a per-GB cost that is often *lower* than an equivalent PD for scratch workloads.

The canonical use: a Spark shuffle disk, a local Redis-like cache, a Dataflow streaming worker temp space, or a build cache. The rule is: **Local SSD for data you can rebuild; Persistent Disk for data you cannot.**

### Filestore

**Filestore** is a managed **NFS** file service. It provides a POSIX filesystem over the network, backed by durable storage, with capacity that scales independently of any single VM.

```text
Compute VM  ──┐
Compute VM  ──┼── NFS mount (10.0.0.0/8) ──► Filestore service
Compute VM  ──┘
```

Filestore's distinguishing properties:

- **Shared POSIX namespace.** Multiple VMs mount the same filesystem and see the same files. This is the "shared filesystem" that object storage cannot provide and that block storage provides only clumsily (by attaching the same disk to several VMs read-write, which is a bad idea).
- **Standard NFS semantics.** `mount -t nfs ...`, and everything that works on a Linux NFS mount works.
- **Three tiers**: `BASIC` (zonal, HDD, 1 TB–63 TB), `ZONAL` (zonal, SSD, up to 63 TB, higher IOPS), and `REGIONAL` (regional, replicated across zones, 10–100 TB, HA).
- **Performance is driven by the network path.** Filestore's maximum throughput depends on the machine type and the VPC network bandwidth. A `n2-standard-16` can pull far more than a `e2-micro`. This is the number people forget: a Filestore instance in the same VPC with a small VM is network-limited.
- **Tiered storage** (Premium tier) separates hot and cold capacity: `hot_tier` for frequent access, `cold_tier` for the rest, with a cold-tier read surcharge and a 30-day minimum.
- **Backups** are scheduled snapshots with a configurable retention period.

Filestore's role in a data platform is narrow and important: **shared mutable working space for a cluster of VMs** — a Spark/YARN or Hadoop cluster's intermediate data, a shared configuration directory, a shared model artefact store that several services mount read-only.

### Block versus file, from the syscall upward

This is the distinction to internalise, because it determines what a workload can do.

A **block device** exposes a linear array of sectors. The filesystem on top decides what a "file" is. Two consequences:

- **The kernel does the I/O, so the kernel chooses the semantics.** `open()`, `read()`, `write()`, `seek()`, `fsync()`, `mmap()` all work. So do POSIX locks, `rename()` atomicity, and `mmap`.
- **Sharing a block device read-write between two VMs is a data-corruption hazard.** Two kernels each run their own page cache, each with its own view of what is on disk. The filesystem's coherence assumptions break: a write in VM A may sit in A's page cache while VM B reads stale data. NFS solves this by putting the lock and cache-coherence protocol in the *server*, which is exactly why file storage shares safely and block storage does not.

A **file service** (NFS, or a modern distributed filesystem) owns the namespace and the coherence protocol. Clients mount it and see a consistent tree. That is the mechanism that makes "many VMs, one working directory" safe.

So the decision matrix at the storage-type level is:

| Property | Object | Block (PD) | File (Filestore) |
|---|---|---|---|
| Namespace | flat key/value | none (raw sectors) | POSIX tree |
| Shared between VMs | yes, via API | only read-only safely | yes, read-write |
| Random access | whole object | byte-level | byte-level |
| Partial update | no (rewrite whole) | yes | yes |
| Latency | ms to hours (by class) | sub-ms | ~ms |
| Scale | effectively infinite | 64 TB per disk | 100 TB per instance |
| Cost | lowest | medium | highest |
| Best at | durable blobs, data lake | OS + local DB | shared mutable working set |

### "Which storage to use when"

This is the table worth memorising, because it is the one you will be asked to produce in a design review.

| If the workload… | Use | Why |
|---|---|---|
| Writes immutable blobs and reads them later | **Object (GCS)** | Durability, scale, per-object lifecycle classes, cheap |
| Needs a filesystem for an OS or a local database | **Block (PD)** | The database needs POSIX semantics and random writes |
| Needs scratch space that can be lost | **Local SSD** | Lowest latency; losing it is fine if it is rebuildable |
| Several VMs must read and write the same working set | **File (Filestore)** | Server-side locking and cache coherence |
| Runs a relational OLTP database | **Block (PD)** + Cloud SQL's own storage | Cloud SQL manages the disk for you |
| Runs a distributed analytics cluster's shuffle | **File (Filestore)** or **Local SSD** | Shared namespace across workers |
| Needs the world's largest table | **Bigtable / Spanner** | Neither object nor block storage scales that way |
| Serves a mobile client with offline sync | **Firestore** | Sync is a product feature, not a storage feature |

The three-question test that gets you the right answer quickly:

1. **Is the data immutable once written?** If yes → object storage. If no → block or file.
2. **Does more than one machine need to write it at the same time?** If yes → file storage (or a database). If no → block storage.
3. **Can it be thrown away and rebuilt?** If yes → Local SSD. If no → Persistent Disk or Filestore.

Note what falls out of question 3 for data engineering specifically: **the landing zone (raw immutable data) is object storage; the scratch space (intermediate shuffle, staging) is file or Local SSD; the curated output is object storage or the warehouse.** The pipeline in `project/core/pipeline_logic.py` maps exactly onto this: raw events land in GCS, and the intermediate aggregation happens in memory or on a Dataproc node's disks.

### Cost mechanics

The cost of block and file storage has a shape that surprises people, because both are billed on **provisioned** capacity with a **performance floor**:

- **Persistent Disk**: per GB-month for the provisioned size, plus a per-IOPS-month charge for provisioned IOPS above the default. Capacity is billed whether you use it or not.
- **Local SSD**: per GB-month for the **attached** capacity, and it must be attached to a **running** VM. Stop the VM and the Local SSD charge stops, and the data is gone.
- **Filestore**: per GB-month for provisioned capacity, per TB of tiered cold capacity at a lower rate, per-hour for some tiers, plus **egress** for data leaving the Filestore service to the internet (a cold-tier read also carries a surcharge).

Two specific cost traps:

1. **Over-provisioning for performance.** People request 10 TB of `pd-ssd` to get 300,000 IOPS when they needed 10,000. They are paying for 300× the capacity they use. The fix is `hyperdisk-balanced` (independent IOPS and throughput) or a separate small provisioned-IOPS disk for the hot data.
2. **Filestore egress.** Data written to Filestore and read out to the internet is billed at internet egress rates. A Filestore instance is a working space, not an archive.

---

## 🛠️ Hands-On

### 1. See the block/filesystem boundary from inside a VM

Create a VM with a Persistent Disk and look at what the kernel sees.

```text
gcloud compute instances create pd-demo \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --boot-disk-size=20GB \
    --create-disk=size=100GB,type=pd-balanced,name=data-disk \
    --image-family=ubuntu-2404-lts-amd64 \
    --image-project=ubuntu-os-cloud
```

Attach and format the extra disk:

```text
gcloud compute instances disk-attach pd-demo \
    --zone=us-central1-a \
    --disk-name=data-disk \
    --device-name=data

gcloud compute ssh pd-demo --zone=us-central1-a --command="lsblk"
```

```text
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
sda      8:0    0   20G  0 disk
└─sda1 8:1    0   20G  0 part /boot
sdb      8:16   0  100G  0 disk
```

`sdb` is a block device with no filesystem on it. There are no files in it — there are sectors. This is the entire point: **the block device is below the filesystem, and the kernel is what turns sectors into files.**

```text
gcloud compute ssh pd-demo --zone=us-central1-a --command="sudo mkfs.ext4 -F /dev/sdb && sudo mkdir -p /mnt/data && sudo mount /dev/sdb /mnt/data && df -h /mnt/data"
```

Now attach a Local SSD alongside it and compare. Local SSD appears as a **non-persistent** device (`/dev/nvme0n1` on most machine types) with `TYPE disk`, and critically, its identity is tied to the VM instance — the device name changes when the VM moves hosts.

```text
gcloud compute instances create ssd-demo \
    --zone=us-central1-a \
    --machine-type=n2-standard-8 \
    --local-ssd=interface=nvme \
    --image-family=ubuntu-2404-lts-amd64 \
    --image-project=ubuntu-os-cloud
```

Measure the difference with `fio` (an honest measurement, not a marketing number):

```text
gcloud compute ssh ssd-demo --zone=us-central1-a --command="sudo apt-get install -y fio && sudo fio --name=seqwrite --filename=/mnt/fiotest --size=2G --bs=1M --rw=write --direct=1 --iodepth=16 --group_reporting"
```

Compare against the same test on the Persistent Disk and against Local SSD. The Persistent Disk result is network-bound and has higher latency; Local SSD is roughly an order of magnitude faster on both throughput and IOPS at low queue depth.

### 2. Create a Filestore instance

```text
gcloud filestore instances create fs-demo \
    --project=YOUR_PROJECT_ID \
    --location=us-central1 \
    --tier=zonal \
    --file-share=name=shared,capacity=2048,storage-type=ssd \
    --network=projects/YOUR_PROJECT_ID/global/networks/default
```

Mount it from a VM:

```text
gcloud compute instances create fs-client \
    --zone=us-central1-a \
    --machine-type=n2-standard-4 \
    --subnet=default \
    --image-family=ubuntu-2404-lts-amd64 \
    --image-project=ubuntu-os-cloud

gcloud compute ssh fs-client --zone=us-central1-a --command="sudo apt-get install -y nfs-common && sudo mkdir -p /mnt/share && sudo mount -t nfs -o vers=4.1 fs-demo:/shared /mnt/share && df -h /mnt/share"
```

Now the shared-namespace property, which is the whole reason to pick file storage:

```text
gcloud compute ssh fs-client --zone=us-central1-a --command="echo hello-from-client-1 > /mnt/share/probe.txt && cat /mnt/share/probe.txt"
```

Then from a *second* VM in the same VPC, read the same file. It is there — because Filestore owns the namespace and the coherence protocol, not any individual VM. With a Persistent Disk, this shared read-write scenario is precisely what you must not attempt.

```text
gcloud compute ssh fs-client-2 --zone=us-central1-b --command="cat /mnt/share/probe.txt"
```

### 3. Size a Persistent Disk from a workload, not a guess

The rule: measure your actual IOPS and throughput requirement, then map it to the disk type's line.

```text
# On a running workload, look at what the block layer is actually doing.
gcloud compute ssh pd-demo --zone=us-central1-a --command="cat /proc/diskstats | grep sdb"
```

Or use the Cloud Monitoring API:

```text
gcloud monitoring time-series list \
    --filter='metric.type="compute.googleapis.com/instance/disk/read_ops_count" AND resource.labels.instance_id="INSTANCE_ID"' \
    --format="table(points[0].value.int64Value)"
```

The sizing formula:

```text
required_IOPS     = read_ops_per_sec + write_ops_per_sec
required_MBps     = read_bytes_per_sec + write_bytes_per_sec  (in MB)

pd-standard:  IOPS = 0.75 × GB,  throughput = 0.12 MB/s × GB
pd-balanced:  IOPS = 6    × GB,  throughput = 0.28 MB/s × GB
pd-ssd:       IOPS = 30   × GB,  throughput = 1.2  MB/s × GB

GB_needed_for_IOPS     = required_IOPS / IOPS_per_GB
GB_needed_for_throughput = required_MBps / MBps_per_GB
GB_to_provision        = max(GB_needed_for_IOPS, GB_needed_for_throughput)
```

Worked example: a PostgreSQL instance needing 6,000 IOPS and 200 MB/s.

```text
pd-balanced:  GB for IOPS      = 6000 / 6      = 1000 GB
              GB for throughput = 200 / 0.28   =  715 GB
              provision        = max(1000, 715) = 1000 GB   →  6000 IOPS, 280 MB/s

pd-ssd:       GB for IOPS      = 6000 / 30     =  200 GB
              GB for throughput = 200 / 1.2    =  167 GB
              provision        = max(200, 167) =  200 GB   →  6000 IOPS, 240 MB/s
```

Note that `pd-ssd` needs one fifth the capacity for the same IOPS. On 6 TB of data that is the difference between ~$300/month and ~$1,150/month of disk. This is the single most common block-storage cost mistake.

### 4. Encode the decision matrix as code

The matrix in this chapter is worth having in executable form, because the review question always arrives as "and which one for *this*?"

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Workload:
    """A workload's storage requirements, in the terms of the matrix.

    Attributes:
        name: A human-readable name.
        immutable: Whether the data is written once and never changed.
        concurrent_writers: How many machines write to it at the same time.
        rebuildable: Whether the data can be thrown away and reconstructed.
        needs_posix: Whether the workload needs open/read/write/seek semantics.
        expected_gb: The expected capacity in GB.
    """

    name: str
    immutable: bool
    concurrent_writers: int
    rebuildable: bool
    needs_posix: bool
    expected_gb: float


def recommend(workload: Workload) -> tuple[str, str]:
    """Recommend a storage type and a reason.

    The decision order is deliberate. Immutability is checked first because
    it is the strongest signal: immutable data belongs in object storage
    regardless of everything else. Shared write access is checked second
    because it is the only thing that requires server-side coherence.
    Posix semantics are checked third, because they rule out object
    storage. Rebuildability is checked last, because it only decides
    between block and local SSD.

    Args:
        workload: The workload description.

    Returns:
        A (storage_type, reason) tuple.
    """
    if workload.immutable and not workload.needs_posix:
        return (
            "object",
            "immutable data with no POSIX requirement — object storage gives "
            "durability, lifecycle classes and effectively unlimited scale",
        )

    if workload.concurrent_writers > 1:
        return (
            "file",
            "more than one writer needs the same working set — a file service "
            "provides server-side locking and cache coherence; a shared "
            "read-write block device corrupts data",
        )

    if workload.needs_posix:
        if workload.rebuildable:
            return (
                "local-ssd",
                "POSIX semantics needed but the data is rebuildable — Local SSD "
                "gives the lowest latency; losing it is acceptable",
            )
        return (
            "block",
            "POSIX semantics needed and the data is not rebuildable — a "
            "Persistent Disk provides a durable block device",
        )

    if workload.rebuildable:
        return (
            "local-ssd",
            "no POSIX requirement and rebuildable — keep it in memory or on "
            "Local SSD rather than paying for durable storage",
        )

    return (
        "object",
        "no POSIX requirement and durable — object storage",
    )


if __name__ == "__main__":
    workloads = [
        Workload("raw landing zone", True, 1, False, False, 50_000),
        Workload("postgres data dir", False, 1, False, True, 500),
        Workload("spark shuffle", False, 8, True, True, 5_000),
        Workload("shared model artefacts", False, 4, False, True, 200),
        Workload("scratch cache", False, 1, True, False, 100),
    ]
    for item in workloads:
        kind, reason = recommend(item)
        print(f"{item.name:<26} → {kind:<10} {reason}")
```

Expected output:

```text
raw landing zone         → object     immutable data with no POSIX requirement — object storage gives durability, lifecycle classes and effectively unlimited scale
postgres data dir        → block      POSIX semantics needed and the data is not rebuildable — a Persistent Disk provides a durable block device
spark shuffle            → file       more than one writer needs the same working set — a file service provides server-side locking and cache coherence; a shared read-write block device corrupts data
shared model artefacts   → file       more than one writer needs the same working set — a file service provides server-side locking and cache coherence; a shared read-write block device corrupts data
scratch cache            → local-ssd  no POSIX requirement and rebuildable — keep it in memory or on Local SSD rather than paying for durable storage
```

### 5. Price block, file, and local against each other

Use the course's `cost_model` where it models the service, and the published rates where it does not.

```python
import sys

sys.path.insert(0, "project/core")

from cost_model import estimate

# Published us-central1 list rates for the comparison.
PD_STANDARD_PER_GB_MONTH = 0.04
PD_SSD_PER_GB_MONTH = 0.17
PD_BALANCED_PER_GB_MONTH = 0.10
PD_EXTREME_PER_GB_MONTH = 0.125
LOCAL_SSD_PER_GB_MONTH = 0.08
FILESTORE_PER_GB_MONTH = 0.35

#: A 2 TB disk that needs 6,000 IOPS.
GB = 2048
REQUIRED_IOPS = 6000


def pd_gb_for_iops(disk_type: str, io: int) -> float:
    """Return the GB of a coupled disk needed to deliver the requested IOPS.

    Args:
        disk_type: The disk type name.
        io: The required IOPS.

    Returns:
        The GB to provision.
    """
    ratios = {
        "pd-standard": 0.75,
        "pd-balanced": 6.0,
        "pd-ssd": 30.0,
        "pd-extreme": 60.0,
    }
    return io / ratios[disk_type]


def price_disk(disk_type: str, io: int, price: float) -> dict[str, float]:
    """Price a Persistent Disk sized for a required IOPS level.

    Args:
        disk_type: The disk type name.
        io: The required IOPS.
        price: The price per GB-month.

    Returns:
        A dict of sizing and cost figures.
    """
    needed = pd_gb_for_iops(disk_type, io)
    gb = max(needed, 10.0)
    return {
        "disk_type": disk_type,
        "provisioned_gb": round(gb),
        "monthly_cost": round(gb * price, 2),
        "relative_to_ssd": round((gb * price) / (needed * PD_SSD_PER_GB_MONTH), 2),
    }


if __name__ == "__main__":
    print(f"Requirement: {REQUIRED_IOPS} IOPS, 2 TB of data\n")
    for name, price in (
        ("pd-standard", PD_STANDARD_PER_GB_MONTH),
        ("pd-balanced", PD_BALANCED_PER_GB_MONTH),
        ("pd-ssd", PD_SSD_PER_GB_MONTH),
        ("pd-extreme", PD_EXTREME_PER_GB_MONTH),
    ):
        row = price_disk(name, REQUIRED_IOPS, price)
        print(
            f"{row['disk_type']:<12} {row['provisioned_gb']:>7} GB  "
            f"${row['monthly_cost']:>9.2f}/mo  "
            f"({row['relative_to_ssd']:.2f}x pd-ssd at equal size)"
        )

    print()
    filestore = GB * FILESTORE_PER_GB_MONTH
    local = GB * LOCAL_SSD_PER_GB_MONTH
    compute = estimate(
        "compute-engine", vcpu_hours=730, gb_months=GB
    ).total
    print(f"filestore 2 TB (zonal, ssd tier): ${filestore:.2f}/mo")
    print(f"local ssd 2 TB (attached):        ${local:.2f}/mo")
    print(f"compute engine + 2 TB pd:         ${compute:.2f}/mo")
```

The relative-cost column is the lesson: **for the same IOPS requirement, `pd-standard` costs many times what `pd-ssd` costs, because it needs proportionally more capacity.** Sizing a disk by IOPS rather than by capacity is a real and common mistake, and it is a cost decision disguised as a performance decision.

---

## 🛠️ Common Errors and Fixes

### 1. `PD` creation fails with an invalid size/IOPS combination

```text
ERROR: (gcloud.compute.disks.create) HTTPError: 400: Invalid value for field 'resource.sizeGb': 100. The maximum size for disk type 'pd-standard' is 65536 GB.
```

Or, when you ask for provisioned IOPS on a coupled disk:

```text
ERROR: (gcloud.compute.disks.create) HTTPError: 400: The property 'provisionedIops' is not allowed for disk type 'pd-balanced'. Use 'provisionedIops' only with disk types that support it.
```

The fix is to choose the disk type first and derive the size from the requirement, using the ratios from the sizing formula above. If you need independent IOPS and throughput, use `hyperdisk-balanced`:

```text
gcloud compute disks create data-disk \
    --zone=us-central1-a \
    --size=2048GB \
    --type=hyperdisk-balanced \
    --provisioned-iops=6000 \
    --provisioned-throughput=200
```

### 2. `mkfs.ext4` on a disk that already has a filesystem

```text
mkfs.ext4: /dev/sdb: mounted device? /dev/sdb is mounted.
```

Formatting a mounted device destroys data. The safe sequence is to identify the device first, check `lsblk` and `mount`, unmount, then format:

```text
lsblk -f /dev/sdb
sudo umount /dev/sdb
sudo mkfs.ext4 -F /dev/sdb
```

The deeper lesson: **never format a device by a guessed name.** `/dev/sdb` on one instance is a different disk on the next. Use the disk's serial or the device name you explicitly attached with `--device-name`, and always `lsblk -f` before writing.

### 3. Local SSD data disappears after a VM restart

```text
# After 'gcloud compute instances stop' then 'start':
lsblk
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
sda      8:0    0   20G  0 disk
└─sda1 8:1    0   20G  0 part /boot
```

The Local SSD device is simply absent. This is expected behaviour, not a fault: **Local SSD is scratch storage and its contents are lost on stop, start, or host failure.** If you find yourself surprised by this, the design is wrong — anything you put on Local SSD must be reconstructible from Cloud Storage, GCS, or a database.

The fix for code that depends on it: make the local directory a cache with a rebuild path, and make the application tolerate a cold cache at startup. If you need durability with Local-SSD-like performance, use a `pd-extreme` disk or `hyperdisk-balanced` instead.

### 4. Filestore mount fails with a timeout or `access denied`

```text
mount.nfs: access denied by server while mounting 10.0.0.5:/shared on /mnt/share
```

Two common causes:

- **The Filestore service network rule does not allow your client.** The default rule allows traffic only from within the Filestore's VPC network. If the client is in a different VPC or peered network, the mount hangs and then times out.
- **NFSv4.1 is not enabled on the instance.** Filestore defaults to NFSv3 in some configurations; NFSv4.1 must be explicitly requested.

Check and fix:

```text
gcloud filestore instances describe fs-demo --location=us-central1 --format="value(fileShares[0].enabledProtocols)"
gcloud filestore instances update fs-demo --location=us-central1 --file-share=name=shared,protocols=NFSV4_1
```

Then confirm the VPC network and the routing:

```text
gcloud filestore instances describe fs-demo --location=us-central1 --format="value(networks)"
gcloud compute ssh fs-client --zone=us-central1-a --command="sudo ping -c 3 FILESTORE_IP && sudo mount -t nfs -o vers=4.1 FILESTORE_IP:/shared /mnt/share"
```

### 5. `No space left on device` on a Persistent Disk, but `df` shows free space

```text
df: /mnt/data: No space left on device
```

On an ext4 filesystem, ~5% is reserved for root by default, and the filesystem's total is smaller than the block device's advertised size because of metadata. But the usual real cause is **inodes**: you have run out of inodes, not bytes.

```text
gcloud compute ssh pd-demo --zone=us-central1-a --command="df -i /mnt/data"
```

```text
Filesystem     Inodes  IUsed  IFree IUse% Mounted on
/dev/sdb      655360  655360     0  100% /mnt/data
```

A pipeline that writes millions of tiny files exhausts inodes long before it exhausts bytes. The fix is either fewer, larger files (which is also faster) or a filesystem with dynamic inode allocation (XFS) instead of ext4:

```text
sudo mkfs.xfs /dev/sdb && sudo mount /dev/sdb /mnt/data
```

This is a genuinely important lesson for data engineering: **object storage has no inodes and no files-per-directory limit, and that is one of the reasons it scales to what a POSIX filesystem cannot.**

### 6. Disk write performance far below the disk's advertised throughput

```text
# fio reports 180 MB/s on a pd-ssd that advertises 1,200 MB/s.
```

The cause is almost always the **network path**, not the disk. A Persistent Disk is network-attached; the VM's virtual NIC caps the achievable throughput. A `n1-standard-1` VM has far less egress bandwidth than the disk behind it.

```text
gcloud compute instances describe pd-demo --zone=us-central1-a --format="value(networkInterfaces[0].accessConfigs[0].natIP)"
gcloud compute instances describe pd-demo --zone=us-central1-a --format="value(machineType)"
```

Also check that the test used `--direct=1`. A buffered write measures the page cache, not the device, and will report absurd numbers for a network disk.

The fix is to size the VM's machine type to the disk's throughput — a `pd-ssd` behind a `n1-standard-1` is money wasted. And if you genuinely need more than the NIC allows, use Local SSD (which bypasses the network) or `hyperdisk-balanced` with a machine type that can actually saturate it.

---

## 💡 Production Notes

- **Never store data only on Local SSD.** It is a cache with a very short lifetime. The design rule is that Local SSD holds *derivable* state, and the rebuild path is exercised in staging, not discovered during an incident.
- **Size Persistent Disk by IOPS requirement, then read the capacity off the disk type's ratio.** `pd-standard` at 0.75 IOPS/GB means 6,000 IOPS costs 8 TB of capacity. Always check the ratio before provisioning; it is the most expensive disk mistake available.
- **Use `hyperdisk-balanced` when IOPS and throughput requirements diverge.** Coupled disks force one ratio; hyperdisk lets you buy 6,000 IOPS and 200 MB/s on 2 TB rather than 8 TB.
- **Regional Persistent Disk when the disk must survive a zone outage — and only then.** It costs roughly double and adds write latency because every write is acknowledged by two zones. For a stateless web VM, a zonal PD plus a stateless architecture is cheaper and better.
- **Reach for Filestore only when you genuinely need a shared read-write namespace.** The most common misuse is mounting Filestore for a single VM, where a Persistent Disk is cheaper, faster, and simpler. The second most common is using Filestore as an archive, where its egress and per-GB pricing make object storage dramatically cheaper.
- **Filestore performance is a function of the client machine type.** Measure the VM's network bandwidth before blaming the Filestore instance. A `n2-standard-16` and an `e2-medium` see very different Filestore throughput.
- **Watch Filestore egress in the bill.** Data leaving a Filestore instance to the internet is billed at internet egress rates. Filestore is a working space, not a landing zone.
- **Snapshots are crash-consistent, not application-consistent.** Quiesce the database (`pg_ctl stop` or `ALTER SYSTEM` checkpoint + flush) before taking a snapshot you intend to restore. An unclean snapshot of a WAL-mode database can need manual recovery on restore.

---

## 🔑 Key Takeaways

- Three storage models, one axis: **who interprets the bytes**. Object storage gives a key and a byte stream; block storage gives a raw sector array the kernel must format; file storage gives a POSIX tree with server-side coherence.
- Block storage is invisible to the application until it is formatted and mounted. Every POSIX program works on it unchanged. That is why databases and operating systems live on it.
- Persistent Disk types are **coupled**: IOPS and throughput move together along a fixed ratio. Size by IOPS requirement and read the capacity off the ratio, or use `hyperdisk-balanced` to decouple them.
- Local SSD is fast, non-persistent, and billed by attachment. It is a cache. Data on it must be rebuildable.
- Filestore is NFS with a managed, durable, elastic backend. Its reason to exist is **shared read-write access across many VMs** with correct locking — the one thing block storage cannot safely provide.
- Never share a read-write block device between VMs. Two kernels, two page caches, no coherence: data corruption.
- The decision reduces to three questions: is the data immutable? do multiple machines write it? can it be rebuilt?
- For a data platform specifically: raw immutable data → object storage; cluster scratch → file storage or Local SSD; curated output → object storage or the warehouse.
- Cost surprise lives in over-provisioning for performance, not in the byte price. `pd-standard` sized for IOPS can cost several times `pd-ssd` for the identical workload.

---

## 📚 Practice Exercises

1. **Extend the recommender.** Add a `block` recommendation path to the `recommend()` function for workloads that need POSIX semantics and are not rebuildable, and add an `object` path for immutable workloads that also need POSIX. Add at least six more `Workload` cases, including "PostgreSQL data directory", "Kafka broker log directory", "Firestore export target", and "Spark shuffle on Dataproc". Place the module in `project/core/` and add a test to `project/tests/`.
2. **Prove the shared-namespace claim.** Write the two shell sequences that demonstrate (a) two VMs seeing the same Filestore file, and (b) the *same* scenario with a Persistent Disk, showing why the second is not safe. Explain in prose what breaks at the page-cache layer in case (b), referring to `fsync()`, `rename()` and directory-entry coherence.
3. **Compute the disk-type break-even.** Using `pd_gb_for_iops()` and the price table in the Hands-On, find the IOPS level at which `pd-balanced` becomes cheaper than `pd-ssd` for a workload with a fixed 4 TB of data. Then repeat for 20 TB. Explain why the crossover moves, and what that says about whether you should size by capacity or by IOPS.
4. **Model the Local SSD cost of a Dataproc cluster.** A Dataproc cluster has 8 workers, each with one 375 GB Local SSD attached for shuffle. The cluster runs 6 hours a day. Compute the monthly Local SSD cost and compare it with an equivalent Filestore shared filesystem at 3 TB, tiered `zonal`/`ssd`. Use `estimate("compute-engine", vcpu_hours=..., gb_months=...)` for the compute side and the published Filestore rate for the file side. Then argue which is cheaper and under what cluster lifetime the answer flips.
5. **Use the course catalogue to check regional storage availability.** From `project/core/service_catalog.py`, print the region availability matrix for `["cloud-storage", "compute-engine"]` and explain, in terms of the Filestore and Persistent Disk model, why `cloud-storage` being available in all 12 regions while `datastore` is `restricted` in `southamerica-east1` is a storage-and-database decision rather than a random gap.
6. **Write the sizing function properly.** Implement `size_persistent_disk(required_iops, required_mbps, data_gb, disk_type)` returning the provisioned GB and the resulting IOPS and throughput, and assert that the provisioned disk satisfies both requirements. Then write `recommend_disk_type(...)` that picks the cheapest disk type meeting both requirements for a given data volume. Test it against the worked example in the Hands-On (6,000 IOPS, 200 MB/s) and confirm it selects `pd-ssd` at 200 GB.
7. **Draft the storage plan for the course pipeline.** The course pipeline ingests 4,800 events, writes a summary CSV, and writes a rejects CSV. For each of the three outputs, specify the storage type, the size, the lifecycle, and the IAM role the pipeline service account needs. Use the bucket names from `platform_sim.build_demo_project()` (`raw-events`) and the summary CSV header `region,event_count,revenue_eur` from `pipeline_logic.SUMMARY_HEADER`.

---

## 📖 Further Reading

- [Persistent Disk documentation](https://cloud.google.com/compute/docs/disks) — types, IOPS ratios, and performance
- [Persistent Disk performance guide](https://cloud.google.com/compute/docs/disks/performance) — the latency and throughput ceilings, and how to measure them
- [Local SSD documentation](https://cloud.google.com/compute/docs/disks/local-ssd) — the non-persistence contract and the performance envelope
- [Filestore documentation](https://cloud.google.com/filestore/docs) — tiers, protocols, and the client requirements
- [Filestore performance and scalability](https://cloud.google.com/filestore/docs/performance) — how client machine type caps throughput
- [Storage pricing](https://cloud.google.com/storage/pricing) — the full rate card for object storage, disks, and Filestore
- [Cloud SQL storage configuration](https://cloud.google.com/sql/docs/mysql/configure-storage) — how the managed database sizes its own disks
