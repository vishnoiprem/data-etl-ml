# L04 — VMs, Hosts, and Hypervisors

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 02
> **Duration target:** 10:00
> **Lecture ID:** L04

## Status

Authored.

## Prereqs

- L01–L03 (course intro).

## Key terms

- **Virtual machine (VM)** — a software emulation of a physical
  computer. From the perspective of the operating system and the
  applications running inside it, a VM looks like dedicated hardware:
  it has virtual CPUs, virtual memory, a virtual disk, and a virtual
  network interface. The fact that it is sharing the underlying
  physical machine with other VMs is invisible unless you go looking
  for it.
- **Hypervisor** — the program that creates and runs VMs. It sits
  between the physical hardware and the guest operating systems,
  carving the physical CPU, memory, disk, and network into slices
  that look like independent machines to each guest.
- **Type-1 (bare-metal) hypervisor** — runs directly on the physical
  hardware with no host OS underneath. Examples: VMware ESXi, Microsoft
  Hyper-V (in server mode), Xen (the historical AWS hypervisor), and
  AWS Nitro (the current one). Type-1 is what you find in production
  data centers because it has direct access to the hardware and very
  little overhead.
- **Type-2 (hosted) hypervisor** — runs as an application on top of a
  conventional host operating system. Examples: VirtualBox, VMware
  Workstation, Parallels. Type-2 is what you run on a laptop to spin
  up a Linux VM on top of macOS or Windows. Convenient, but slower
  and not what cloud providers use.
- **Host** — the physical server in an AWS data center that runs your
  EC2 instance. You will never see it, but every EC2 VM is running
  on a host (or, increasingly, on bare-metal hardware with the Nitro
  card doing the virtualization).
- **AWS Nitro System** — the combination of custom hardware (Nitro
  cards for networking, storage, and security) and a lightweight
  hypervisor that AWS built to replace Xen. Nitro offloads
  virtualization work that used to happen in software to dedicated
  hardware, which gives EC2 more CPU for your workloads and better
  networking performance.

## Lecture

To understand EC2 you have to understand three layers stacked on top
of each other: the **physical hardware** (the actual server in a
data center rack), the **hypervisor** (the software that carves that
server into pieces), and the **virtual machines** (the pieces). Most
of your life as a developer happens at the top layer. Most of the
engineering work that goes into making EC2 fast and cheap happens
at the bottom two.

A **virtual machine** is just a software emulation of a computer.
You install an operating system into it the same way you would on a
bare-metal box, you give it disk, RAM, and a CPU, and applications
inside it cannot tell the difference. The only thing that is fake is
the hardware itself — the disk is a file, the network card is a
software interface, and the CPU cycles are scheduled by a program
running underneath.

That program is the **hypervisor**. The hypervisor is the boss. It
owns the physical hardware, and it decides which VM gets which slice
of CPU, how much RAM each VM can use, where each VM's disk reads and
writes actually go, and which virtual network interface maps to
which physical NIC. The hypervisor is what makes "many VMs on one
server" possible, and the design of the hypervisor is what
determines how much performance overhead the VMs pay for the
privilege of running there.

There are two flavors of hypervisor, and the difference matters.

**Type-1 (bare-metal) hypervisors** run directly on the physical
hardware. There is no host operating system underneath — the
hypervisor *is* the operating system, in a sense. It is small, it
has direct access to the CPU, memory, and I/O devices, and it is
what production cloud and enterprise virtualization use. VMware ESXi,
Citrix XenServer, and the historical AWS hypervisor (also Xen) are
all type-1. Performance is close to bare metal because nothing is
sitting in between.

**Type-2 (hosted) hypervisors** run as an application on top of a
conventional operating system. VirtualBox, VMware Workstation, and
Parallels are all type-2. They are convenient — you can run them on
your laptop with no special setup — but they are slower because
every VM I/O has to traverse the host OS.

AWS has used three generations of hypervisor over the years. **Xen**
was the first, and Xen is a type-1 bare-metal hypervisor. Xen
worked fine, but it forced every I/O operation through the
hypervisor, which meant the hypervisor CPU was busy doing
virtualization work even when your VM was not doing anything
interesting. **Nitro** is the current generation, introduced
starting in 2017. Nitro splits the work: the hypervisor is now
extremely small (it just schedules vCPUs), and a set of dedicated
hardware cards handle networking, EBS storage, encryption, and
security. The practical effect is that more of the physical CPU is
available to your VM, network throughput is higher, and EBS disk
I/O does not bottleneck on the hypervisor.

You will never see a Xen or Nitro hypervisor in the EC2 console,
and that is the point. AWS hides the host entirely — you do not get
to know which physical server your instance is on, you do not get
to know which other tenants share that host (though AWS does enforce
isolation), and you do not get to install a different hypervisor
yourself. The trade is that you get a clean, predictable, software-
defined machine you can launch in 30 seconds and throw away in 30
more.

## Hands-on

Theory lecture — no code, no console. But while you watch this one,
do this:

1. Open the EC2 console and go to **Instances**. Note the
   "Instance type" column (e.g., `t3.micro`) and the "Private IP"
   and "Public IP" columns. You are looking at the *virtual* view:
   vCPUs, virtual NIC, virtual disk.
2. Realize there is no "Host" column, no "Hypervisor" column, and
   no way to ask AWS which physical server your instance is on.
   That is the abstraction in action.

In L06 we will look at the next layer up — the geographic
abstraction of regions and Availability Zones.

## Quiz prep

- What is the difference between a type-1 and type-2 hypervisor?
  Which one does AWS use, and why?
- What is the Nitro System? What work does it offload from the
  hypervisor to dedicated hardware?
- Why can you not see the physical host in the EC2 console?
- What is the layering from physical hardware up to your application
  on EC2 (hardware -> hypervisor -> VM -> OS -> app)?

## Further reading

- AWS docs: [Amazon EC2 — Under the hood](https://docs.aws.amazon.com/ec2/)
- AWS: [The AWS Nitro System](https://aws.amazon.com/ec2/nitro/)
- Wikipedia: [Hypervisor](https://en.wikipedia.org/wiki/Hypervisor)