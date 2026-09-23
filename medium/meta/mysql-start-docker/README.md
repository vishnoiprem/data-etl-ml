# MySQL Docker Setup

Local MySQL container for the **meta_interview** project.

## Configuration

| Setting      | Value            |
|--------------|------------------|
| Image        | `mysql:latest`  |
| Database     | `meta_interview`|
| User         | `meta_interview`|
| Password     | `meta_interview`|
| Root password| `meta_interview`|
| Host port    | `3306`           |

## Folder layout

```
mysql-start-docker/
├── Dockerfile              # Standalone image build
├── docker-compose.yml      # Recommended way to run
├── .env                    # Environment variables (not for image build)
├── .dockerignore           # Files excluded from image build context
├── init/
│   └── 01-init.sql         # Auto-runs on first start (empty volume)
└── README.md
```

## Quick start (docker compose — recommended)

```bash
cd mysql-start-docker
docker compose up -d
docker compose logs -f mysql   # watch startup
```

Stop & remove:

```bash
docker compose down            # keep data volume
docker compose down -v         # also delete data volume
```

## Quick start (plain Docker)

```bash
docker build -t mysql-meta-interview .
docker run -d --name mysql-meta-interview \
  -p 3306:3306 \
  -v mysql_data:/var/lib/mysql \
  -v "$(pwd)/init:/docker-entrypoint-initdb.d:ro" \
  mysql-meta-interview
```

## Connect

From CLI:

```bash
docker exec -it mysql-meta-interview mysql -umeta_interview -pmeta_interview meta_interview
```

From a host app / DBeaver / TablePlus:

```
host:     localhost
port:     3306
user:     meta_interview
password: meta_interview
database: meta_interview
```

Connection URL:

```
mysql+pymysql://meta_interview:meta_interview@localhost:3306/meta_interview
```

## Initialization scripts

Anything in `./init/*.sql` runs **only on first start**, when the data
volume is empty. To re-run them, delete the volume:

```bash
docker compose down -v
docker compose up -d
```

## Useful commands

```bash
# Shell into container
docker exec -it mysql-meta-interview bash

# Inspect data volume
docker volume inspect mysql-start-docker_mysql_data

# Backup
docker exec mysql-meta-interview sh -c 'mysqldump -umeta_interview -pmeta_interview meta_interview' > backup.sql

# Restore
cat backup.sql | docker exec -i mysql-meta-interview sh -c 'mysql -umeta_interview -pmeta_interview meta_interview'
```
