# Amazon ECS Data Ingestion — demo app (CRA scaffold)

> **The minimum-viable React app for the AWS "Getting
> Started with Amazon ECS" workshop.** A Create-React-App
> scaffold configured to serve on port 80 (matching the
> workshop's ALB → ECS → container → port 80 flow).

This directory is a **scaffold**. It's the React app that
the AWS ECS workshop deploys into a Fargate cluster as
the demo workload. The interesting work is the
surrounding Terraform / ECS task definition / ALB
configuration; that lives in the
[official AWS workshop](https://ecsworkshop.com/), not
here.

The reason this is in the repo: it's a known-good
container that builds, runs on port 80, and can be
pointed at by an ALB without any code changes. Useful
as a placeholder workload when you want to test an ECS
cluster / pipeline without writing a real app.

---

## What's in this directory

A standard Create React App project:

| Path | What it is |
|------|------------|
| `package.json` | CRA dependencies, `react-scripts` start/build/test/eject |
| `public/` | The static HTML shell + the favicon |
| `src/` | The React app source |
| `node_modules/` | (gitignored) the dependency tree |

The app itself is the default CRA "rotating React logo"
demo. The point is the *build artifact* (a production
bundle that can be served by `nginx` on port 80 inside
a container), not the React code.

---

## How to run it

### Local (the standard CRA flow)

```bash
cd aws/ecs-data-ingestion
npm install
sudo npm start          # port 80 (sudo needed on macOS / Linux)
# or
PORT=3000 npm start     # port 3000 (no sudo)
```

Open `http://localhost` (or `:3000`).

### Production build (the ECS-relevant flow)

```bash
npm run build
# -> ./build/  (static files; ready for nginx)
```

The `build/` directory is what you `COPY` into a
container image. The Dockerfile pattern is:

```dockerfile
FROM nginx:alpine
COPY build/ /usr/share/nginx/html
EXPOSE 80
```

That image is the workload you push to ECR and run as
an ECS Fargate task.

---

## How it fits into the ECS workshop

The full flow (from the workshop, not this repo):

```
   ALB (port 80)
     │
     ▼
   ECS Fargate service (desired_count=2)
     │
     ▼
   Task definition (this app's nginx image, port 80)
     │
     ▼
   ECR (private repo: ecsworkshop-container)
     │
     ▼
   CodePipeline (source → build → deploy to ECS)
```

This directory contributes the **container** (the
`nginx + build/` image). Everything else (Terraform,
task definition, service, pipeline) lives in the
workshop's own repo.

---

## What this is NOT

- **Not a real data-ingestion app.** Despite the
  directory name, this is the *demo React app* from
  the AWS ECS workshop. There is no data ingestion
  here. For real data-ingestion patterns on ECS, see
  [`../../data-engineering/keystone-iceberg-ops/`](../../data-engineering/keystone-iceberg-ops/)
  (Flink on ECS, Iceberg tables) and
  [`../../realtime-stock-pipeline/`](../../realtime-stock-pipeline/)
  (Kafka producer, Flink job, TimescaleDB).
- **Not a production-grade React app.** It's a CRA
  scaffold with the default demo. No routing, no
  state management, no testing infrastructure. Use it
  as a placeholder, not as a starting point.
- **Not the ECS / Fargate configuration.** The
  task definition, IAM roles, ALB target group, and
  CodePipeline all live in the
  [AWS ECS workshop](https://ecsworkshop.com/) repo.
  This directory is just the container payload.

---

## The 3 things this directory teaches

1. **A known-good container image is a useful test
   artifact.** When you want to verify an ECS
   pipeline, ALB, or service mesh works end-to-end,
   you don't need a real app — you need *a* app that
   builds and serves HTTP. This directory is that.
2. **Port 80 in a container ≠ port 80 on the host.**
   The `sudo npm start` in the CRA scripts exists to
   bind to port 80 locally; in a container the
   `nginx:alpine` image just `EXPOSE 80` and the
   ALB does the rest.
3. **The build artifact is the contract.** For
   ECS, what matters is "did `npm run build` produce
   static files I can serve?" Everything else is
   packaging.

---

## Related directories

- [`../../data-engineering/keystone-iceberg-ops/`](../../data-engineering/keystone-iceberg-ops/) —
  the production-shaped Flink-on-ECS build (real
  data ingestion, not a CRA scaffold).
- [`../../realtime-stock-pipeline/`](../../realtime-stock-pipeline/) —
  the full real-time data pipeline (Kafka producer
  → Flink → TimescaleDB → Grafana).
- [`../`](../) — the parent `aws/` directory
  (small AWS-specific projects and workshops).
- The [official AWS ECS workshop](https://ecsworkshop.com/)
  for the full ECS / Fargate / CodePipeline
  reference architecture.
