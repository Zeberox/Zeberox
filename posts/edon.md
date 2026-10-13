---
title: Edon
date: 2026-10-07
category: Haxagon
summary: Dump a Node.js process's memory through /proc/<PID>/mem to recover a flag that was deleted from disk.
featured: true
---

## Flag

`haxagon{01060650ec87d4957ffc7fadcd7cc1b12496d2e5}`

## 1. Source code analysis

Looking at `Challenge/build/main.js` (or `src/main.ts`), the program runs in four steps:

- **Read file:** reads the flag from `../Flags/flag1` into the in-memory variable `flag`.
- **Overwrite:** overwrites `flag1` with the lyrics of a well-known rickroll song.
- **Delete file (`unlink`):** removes `flag1` entirely from the filesystem.
- **Hang the process:** falls into an infinite loop:

```javascript
while (1) {
  await delay(10000);
  console.log("slept 10s");
}
```

**The logic flaw:** the on-disk file is gone, but the Node.js process never exits. The `flag` string is still sitting intact in that process's heap (RAM).

## 2. Why the flag can be read from /proc

On Linux, the kernel exposes the virtual `/proc` filesystem, which holds state information about the system and the running processes.

### /proc/<PID>/maps

This file contains the process's virtual memory map:

- Lists every virtual address range the process holds, e.g. `00400000-0040b000`.
- Shows the permissions of each range: `r` (read), `w` (write), `x` (execute), `p` (private).
- Node.js's V8 engine stores string variables (like `flag`) on the heap, and those regions are always marked `rw`.

### /proc/<PID>/mem

This is a binary file that maps 1:1 onto the process's entire virtual memory space:

- Open it as root (or the same user), then `seek` to the address ranges taken from `maps` to read the binary data straight out of RAM.

### Exploit script

```javascript
// 1. Read the memory map of process PID 7
const maps = fs.readFileSync("/proc/7/maps", "utf8").trim().split("\n");
const mem = fs.openSync("/proc/7/mem", "r");

for (const line of maps) {
    const parts = line.split(/\s+/);
    // 2. Keep only regions with "rw" permission (where JS variables / the heap live)
    if (parts[1] && parts[1].includes("rw")) {
        const [start, end] = parts[0].split("-").map(x => parseInt(x, 16));
        const len = end - start;
        const buf = Buffer.alloc(len);
        try {
            // 3. Read the binary data from address start -> end in RAM
            fs.readSync(mem, buf, 0, len, start);

            // 4. Turn the bytes into a string and scan for the flag format with a regex
            const str = buf.toString("latin1");
            const matches = str.match(/[A-Za-z0-9_\-]{0,20}\{[^}\n\r\t ]+\}/g);
            if (matches) {
                console.log([...new Set(matches)].join("\n"));
            }
        } catch (e) {}
    }
}
```

## 3. Solution steps

1. Recon: the `Challenge/Flags` directory is empty; the source `src/main.ts` holds an infinite loop.
2. Find the PID of the background process with `ps aux | grep node`; the process `node /root/Challenge/build/main.js` is running with PID = 7.
3. Dump the process RAM: the minimal environment has no `gdb` or `strings`, so use the available `node` runtime itself to read `/proc/7/maps` and `/proc/7/mem`.
4. The regex matches the right string format and returns the flag.

## 4. Takeaways

- Deleting a file (`unlink` / `rm`) only removes the filesystem link; data already loaded into a process's memory lives on until the process exits or the garbage collector overwrites it.
- On Linux, a privileged user can read any process's data through `/proc/<PID>/mem`.
- Memory dumping is a foundational DFIR technique for extracting encryption keys, tokens, or sensitive data that was never written to disk.
