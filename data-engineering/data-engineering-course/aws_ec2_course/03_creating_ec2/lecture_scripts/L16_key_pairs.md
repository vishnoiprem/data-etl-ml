# L16 — Key Pairs

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 03
> **Duration target:** 8:00
> **Lecture ID:** L16

## Status

Authored.

## Prereqs

- L09 (the wizard) — Step 4 is "Key pair (login)".

## Key terms

- **Key pair** — a pair of RSA keys: a **public** key that AWS
  stores, and a **private** key that you download and keep on
  your laptop.
- **Public key** — the half of the pair AWS injects into the
  instance's `~/.ssh/authorized_keys` (Linux) or uses to decrypt
  the Windows admin password.
- **Private key** — the half you keep. **Never** upload it to a
  public place, paste it into chat, or commit it to git.
- **`ssh -i`** — the flag that tells SSH to use a specific
  identity file (the private key) instead of the default
  `~/.ssh/id_rsa`.
- **Key pair fingerprint** — the SHA-256 hash of the public key.
  AWS uses it to identify a key pair in the console / API.
- **Key pair type** — `rsa` (the default; 2048 or 4096 bits) or
  `ed25519` (newer, smaller, faster). Amazon Linux 2 accepts
  both; older AMIs may only accept `rsa`.

## Lecture

Step 4 of the wizard asks "How will you access the instance?" The
answer for a Linux instance is: **a key pair**.

The key pair is an RSA (or ED25519) public/private key pair. AWS
stores the public key; you download the private key (a `.pem`
file) and keep it on your laptop. When you launch a Linux
instance, AWS injects the public key into
`/home/ec2-user/.ssh/authorized_keys` (Amazon Linux 2) or
`/home/ubuntu/.ssh/authorized_keys` (Ubuntu). The `sshd` daemon
on the instance then accepts SSH logins from anyone who can
present the matching private key.

### Three ways to create a key pair

1. **In the wizard.** Click "Create new key pair" on Step 4. AWS
   generates the pair, stores the public key, and prompts you to
   download the private key. You **must** save it now — AWS
   doesn't keep a copy.
2. **In the EC2 console → Key Pairs.** Create the pair ahead of
   time. Same flow, but the key exists before you launch.
3. **In your terminal with ssh-keygen, then upload the public
   key.** `ssh-keygen -t rsa -b 4096 -f my-course-key` creates
   `my-course-key` (private) and `my-course-key.pub` (public).
   Upload the public key to AWS with "Import key pair" in the
   console, or with `aws ec2 import-key-pair`.

### File permissions matter

Once you've downloaded the private key, **fix its permissions**
before you try to SSH in. SSH refuses to use a key with open
permissions.

```bash
chmod 400 my-course-key.pem
ssh -i my-course-key.pem ec2-user@<public-dns-of-instance>
```

`chmod 400` means "read-only for the owner". SSH will reject
keys that are readable by other users on the system.

### The first SSH

A typical first connection looks like this:

```bash
$ chmod 400 my-course-key.pem
$ ssh -i my-course-key.pem ec2-user@ec2-1-2-3-4.compute-1.amazonaws.com
The authenticity of host 'ec2-1-2-3-4.compute-1.amazonaws.com (1.2.3.4)' can't be established.
ED25519 key fingerprint is SHA256:abc123...
This key you have never connected to this host before.
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

Type `yes`. SSH records the instance's host key in
`~/.ssh/known_hosts`. The next connection won't ask.

### What to do if you lose the private key

You **cannot** recover it. AWS does not keep a copy. The only
option is:

1. Create a new key pair in the console.
2. Stop the instance.
3. Replace the public key in
   `/home/ec2-user/.ssh/authorized_keys` (e.g. by attaching the
   root volume to another instance, editing the file, and
   re-attaching).
4. Start the instance.

For production, **back the private key up** to a secrets manager
or to an encrypted USB drive. Or better: don't use a
**per-instance** key pair at all. Use **SSM Session Manager**
(L14) — it doesn't need a key pair at all.

### Best practice: one key per person, not per instance

A common anti-pattern is creating a new key pair for every
instance ("I have 50 instances, I have 50 key pairs"). That makes
rotation impossible and is a security disaster.

The right pattern: **one key per person (or per service
account)**, and that key is granted access to every instance that
person needs. Rotation is then a matter of updating
`authorized_keys` on the instances.

For ephemeral workloads (spot, scale-out fleets), don't bother
with SSH at all — use **SSM Session Manager** or **EC2 Instance
Connect** (a browser-based SSH).

### How it shows up in boto3

```python
client.run_instances(
    ImageId=ami_id,
    InstanceType="t3.micro",
    KeyName="my-course-key",   # <-- this is the key pair NAME, not the file
    # ...
)
```

The `KeyName` argument is the **name** you gave the key pair in
AWS, not the path to the `.pem` file on your laptop. boto3
doesn't need the private key at all — it just tells AWS "use
this public key for the instance". The private key is what
**you** use to SSH in.

In `launch_instance.py` you pass `--key-name my-course-key`. The
script doesn't care about the private key.

### Key types: RSA vs ED25519

`aws ec2 create-key-pair --key-name my-key --key-type ed25519`
creates an ED25519 key pair. Amazon Linux 2 and Ubuntu 22.04+
accept ED25519 out of the box; older AMIs may need RSA.

ED25519 is preferred for new key pairs because:

- smaller keys (256 bits vs 2048+ for RSA);
- faster to generate;
- equally or more secure in practice.

### What this lecture intentionally doesn't cover

- **Windows instances.** Windows uses key pairs differently: AWS
  uses the public key to **encrypt** the initial Windows admin
  password, which you then decrypt with the private key. The
  flow is wizard-driven; see the AWS docs.
- **bastion hosts and SSH agent forwarding.** A common
  production pattern, but a section-3 deep-dive is overkill.
  The boto3 + moto demo uses a single, internet-reachable
  instance.

## Quiz prep

- What does AWS store, and what do you store? (AWS stores the
  public key; you store the private key on your laptop.)
- What does `chmod 400` do, and why is it required? (Sets the
  key to owner-read-only; SSH refuses to use keys with more
  permissive permissions.)
- What happens if you lose the private key? (You cannot recover
  it — you have to create a new key pair and replace the public
  key on the instance, which usually means stop, edit, start.)
- What does the `KeyName` argument in boto3 refer to? (The name
  of the key pair in AWS, not the path to the `.pem` file on
  your laptop.)

## Further reading

- AWS docs: *Amazon EC2 key pairs and Linux instances* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html>
- AWS docs: *Connect to your Linux instance using SSH* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AccessingInstancesLinux.html>
- `man ssh-keygen` — local docs.
