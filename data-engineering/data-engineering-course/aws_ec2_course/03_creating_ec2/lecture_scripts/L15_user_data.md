# L15 — User Data Scripts

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 03
> **Duration target:** 10:00
> **Lecture ID:** L15

## Status

Authored.

## Prereqs

- L14 (Advanced Settings) — user data lives on the "Advanced
  details" tab.

## Key terms

- **User data** — a shell or cloud-init script that runs once, as
  `root`, the first time the instance boots.
- **cloud-init** — the de-facto standard multi-distro
  first-boot configuration tool. Reads a YAML document
  (`#cloud-config`) or a shell script (`#!/bin/bash`) from the
  instance metadata.
- **Instance metadata** — a fixed HTTP endpoint
  (`http://169.254.169.254/latest/`) on every EC2 instance that
  exposes the instance id, AZ, IAM credentials, user data, and so
  on.
- **MIME multi-part user data** — cloud-init supports a single
  blob that contains multiple "parts" (e.g. a shell script + a
  cloud-config + a "boot script" using the `upstart` job format).
- **Idempotent** — a script that you can run multiple times and
  get the same end state. The most important property of a
  user-data script that runs on every boot.

## Lecture

User data is the most useful — and most dangerous — piece of "free"
configuration you get when you launch an EC2 instance. It runs **once
on first boot**, as `root`, with the network up. That makes it the
right place to:

- install packages (`yum install -y nginx`);
- pull the latest code (`git clone https://github.com/myorg/app.git`);
- write a config file;
- register the instance with a service registry (Consul, ECS, etc.);
- tag the instance with a "ready" sentinel.

It is **not** the right place for secrets (use Parameter Store or
Secrets Manager), long-running processes (use systemd units, not
user data), or things that need to run on every boot (use
`@reboot` cron or a systemd `WantedBy=multi-user.target`).

### The two flavours

The EC2 launch wizard (and boto3's `UserData` parameter) accept a
**single text string** of up to 16 KB. The most common ways to use
that text string are:

1. **A bash shell script.** Start with `#!/bin/bash`. The
   cloud-init agent on the instance will run it with `bash`.
2. **A cloud-config document.** Start with `#cloud-config`. This
   is YAML and gives you structured directives
   (`packages:`, `runcmd:`, `write_files:`, `users:`, etc.).
3. **MIME multi-part.** A `MIME-Version: 1.0` blob with multiple
   parts. Useful when you want cloud-config + a shell script +
   a bootcmd.

For the boto3 demo we use the first form: a plain bash script.

### What cloud-init does

On a fresh Amazon Linux 2 or Ubuntu instance, the
`cloud-init` service starts at boot and:

1. Reads the user data from the instance metadata.
2. Detects the format (`#cloud-config` vs `#!/bin/bash` vs
   `MIME-Version: 1.0`).
3. Runs the directives in order, as `root`, before the network
   is fully up (for some directives) or after (for `runcmd`).

You can watch it run by SSHing in and `tail -f
/var/log/cloud-init-output.log`.

### An example: a "ready" web server

```bash
#!/bin/bash
yum update -y
amazon-linux-extras install -y nginx1
systemctl enable nginx
systemctl start nginx
echo "Hello from $(hostname)" > /usr/share/nginx/html/index.html
```

This is **idempotent** only partly — `yum update -y` is fine to
re-run, but `systemctl enable` is also fine. The `echo >` line is
the dangerous one: it overwrites the index file every time the
script runs. On a re-run the file is the same; on a re-launch from
a new instance it's the same; that's idempotent enough for us.

### A more disciplined example

```bash
#!/bin/bash
set -euo pipefail

# 1. Update packages
yum update -y

# 2. Install nginx if not already present
if ! command -v nginx >/dev/null 2>&1; then
  amazon-linux-extras install -y nginx1
fi

# 3. Ensure nginx is enabled and started
systemctl enable nginx
systemctl is-active --quiet nginx || systemctl start nginx

# 4. Write a marker file (idempotent: same content every time)
cat > /var/lib/cloud/instances/ready <<'EOF'
ready
EOF
```

The discipline: `set -euo pipefail` so any failing line aborts;
guards around state-changing operations; the marker file as a
visible "I have finished" sentinel.

### Common gotchas

1. **User data runs once per instance, not once per launch.**
   The cloud-init service runs at first boot of the AMI. If you
   stop and start the instance, user data does **not** re-run
   (unless the AMI is set up for it). If you terminate and
   launch a new instance, **that** new instance runs user data.
2. **The 16 KB limit.** A 16 KB shell script is enough to do a
   lot, but not enough to bundle a 50 MB application. For big
   artifacts, user data should `curl` from S3 and run that.
3. **`#!/bin/bash` matters.** If you don't start with a
   shebang, cloud-init may interpret the script as a
   `#cloud-config` document and silently do nothing.
4. **Secrets in user data are visible to anyone with
   `describe-instance-attribute`.** Don't put passwords or API
   keys in user data. Use Parameter Store or Secrets Manager.
5. **User data runs as `root`.** If your script is bad, it can
   wreck the instance before you've even finished SSHing in.
6. **The instance might not have network at the moment the
   script runs.** Adding `set -e` and `set -o pipefail` makes
   failures visible, not silent.

### How to use it from boto3

```python
response = client.run_instances(
    ImageId=ami_id,
    InstanceType="t3.micro",
    UserData="#!/bin/bash\nyum update -y\n",
    # ... other args
)
```

boto3 will base64-encode the string for you. The Cloud-init agent
on the instance decodes it back.

The `launch_instance.py` script in L18 takes a
`--user-data-file` argument and reads the file's contents into
`UserData`. The script does **not** interpret the file; whatever
you put in the file is what the instance runs.

### Debugging tips

- `tail -f /var/log/cloud-init-output.log` — shows the full
  output of the user-data script.
- `cloud-init query userdata` — shows what cloud-init thought the
  user data was.
- `systemctl status cloud-init` — checks the cloud-init service.
- Re-running manually: `sudo cloud-init single --name
  cc_scripts_user -f /var/lib/cloud/.../user-data.txt`.

### When NOT to use user data

- **Long-running processes.** Use systemd units, not user data
  with `&` and `disown`.
- **Application config that changes often.** Bake it into an AMI
  and re-deploy the AMI.
- **Secrets.** Use Parameter Store / Secrets Manager.
- **Big artifacts.** curl them from S3.

## Quiz prep

- Does user data run on every boot, or only on first boot? (Only
  on first boot of a fresh instance. Stop/start does not re-run
  user data; terminate + launch does.)
- What's the maximum size of the user-data blob? (16 KB.)
- Name two reasons not to put a secret in user data. (It's
  visible to anyone with `describe-instance-attribute`; the AMI
  is in plaintext; an unencrypted snapshot of the root volume
  would expose it.)
- What's the safe practice if your user data does network
  operations? (Use `set -euo pipefail` and treat failures as
  failures — don't silently swallow them.)

## Further reading

- AWS docs: *Run commands on your Linux instance at launch* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html>
- cloud-init docs: <https://cloudinit.readthedocs.io/>
- AWS docs: *Retrieve instance metadata* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html>
