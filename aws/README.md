# aws/ — AWS CLI bundle + small AWS projects

> **The AWS CLI v2 install bundle plus the small
> AWS-specific projects that aren't big enough to live
> at the top level.** Most of the AWS work in this
> portfolio is in the `data-engineering/` and
> `realtime-stock-pipeline/` directories; this `aws/`
> directory is the small odds-and-ends bucket.

The `install` script and the `dist/` tree are the
unmodified AWS CLI v2 install bundle (downloaded
from the AWS website). The `ecs-data-ingestion/`
subdirectory is a CRA scaffold used as a placeholder
workload for ECS / Fargate testing.

---

## What's in this directory

| Path | What it is |
|------|------------|
| `install` | The AWS CLI v2 install script (unmodified from the AWS distribution) |
| `dist/` | The AWS CLI v2 distribution tree (unmodified) |
| `THIRD_PARTY_LICENSES` | The third-party license bundle for the AWS CLI v2 |
| `ecs-data-ingestion/` | A CRA-scaffold React app used as a placeholder workload for ECS / Fargate testing |

The `install` script and `dist/` are version-pinned
bundles; they're not modified by this repo. Run
`./install` to get the AWS CLI on your machine, then
ignore them.

---

## How to install the AWS CLI from this bundle

```bash
cd aws/
sudo ./install
# -> installs to /usr/local/bin/aws
aws --version
# -> aws-cli/2.x.x ...
```

If you don't have `sudo`:

```bash
./install -i ~/.local/aws-cli -b ~/.local/bin
# make sure ~/.local/bin is on $PATH
aws --version
```

To update an existing install:

```bash
sudo ./install --update
```

To remove the install:

```bash
sudo rm -rf /usr/local/aws-cli
sudo rm /usr/local/bin/aws
sudo rm /usr/local/bin/aws_completer
```

The CLI itself is documented at
[docs.aws.amazon.com/cli](https://docs.aws.amazon.com/cli/).

---

## The `ecs-data-ingestion/` subproject

A Create-React-App scaffold used as the demo
workload for the AWS ECS workshop. See
[`ecs-data-ingestion/README.md`](ecs-data-ingestion/README.md)
for the details.

The point of the subproject: a known-good container
image (`nginx` serving the CRA `build/` output on
port 80) that you can point at an ALB and verify
the full ECS / Fargate / CodePipeline flow works
end-to-end. No real data ingestion happens here
despite the name.

---

## What this is NOT

- **Not a real data-ingestion platform.** The
  `ecs-data-ingestion/` directory name is the AWS
  workshop's, not ours. The real data-ingestion
  patterns live in
  [`../data-engineering/keystone-iceberg-ops/`](../data-engineering/keystone-iceberg-ops/)
  (Flink on ECS, Iceberg tables) and
  [`../realtime-stock-pipeline/`](../realtime-stock-pipeline/)
  (Kafka → Flink → TimescaleDB → Grafana).
- **Not a maintained fork of the AWS CLI.** The
  `dist/` tree is the unmodified bundle from
  aws.amazon.com. Update it by re-downloading the
  official installer; don't patch it in place.
- **Not a Terraform or CDK reference.** There are
  no IaC files here. The ECS / Fargate /
  CodePipeline reference is in the
  [AWS ECS workshop](https://ecsworkshop.com/), not
  this repo.

---

## Related directories

- [`../data-engineering/keystone-iceberg-ops/`](../data-engineering/keystone-iceberg-ops/) —
  the production-shaped Flink-on-ECS data
  ingestion build.
- [`../realtime-stock-pipeline/`](../realtime-stock-pipeline/) —
  the full real-time data pipeline
  (Kafka → Flink → TimescaleDB → Grafana).
- [`ecs-data-ingestion/`](ecs-data-ingestion/) —
  the CRA scaffold used as the ECS workshop's
  demo workload.
- [The official AWS CLI v2 docs](https://docs.aws.amazon.com/cli/)
  for the full CLI reference (the `install` script
  in this directory is just the install path; the
  docs are the long-form reference).
