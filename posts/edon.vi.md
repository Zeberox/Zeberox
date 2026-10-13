---
title: Edon
summary: Dump bộ nhớ tiến trình Node.js qua /proc/<PID>/mem để khôi phục flag đã bị xóa khỏi đĩa.
---

## Flag

`haxagon{01060650ec87d4957ffc7fadcd7cc1b12496d2e5}`

## 1. Phân tích mã nguồn

Khi kiểm tra thư mục `Challenge/build/main.js` (hoặc `src/main.ts`), logic hoạt động của chương trình diễn ra theo 4 bước:

- **Đọc file:** đọc cờ từ file `../Flags/flag1` vào biến bộ nhớ `flag`.
- **Ghi đè (overwrite):** ghi đè file `flag1` bằng lời bài hát Rickroll.
- **Xóa file (`unlink`):** xóa hoàn toàn file `flag1` khỏi hệ thống tệp.
- **Treo tiến trình:** rơi vào vòng lặp vô tận:

```javascript
while (1) {
  await delay(10000);
  console.log("slept 10s");
}
```

**Lỗ hổng logic:** file trên ổ đĩa đã biến mất, nhưng tiến trình Node.js không hề thoát. Giá trị chuỗi `flag` vẫn nằm nguyên vẹn trong Heap (RAM) của tiến trình đó.

## 2. Vì sao đọc được flag từ /proc

Trên Linux, kernel cung cấp hệ thống tệp ảo `/proc` để quản lý thông tin trạng thái của hệ thống và các tiến trình đang chạy.

### /proc/<PID>/maps

File này chứa bản đồ bộ nhớ ảo của tiến trình:

- Liệt kê tất cả các dải địa chỉ ảo mà tiến trình đang chiếm giữ, ví dụ `00400000-0040b000`.
- Cho biết quyền truy cập của từng dải: `r` (read), `w` (write), `x` (execute), `p` (private).
- V8 Engine của Node.js lưu các biến chuỗi (như biến `flag`) trên Heap, các dải nhớ này luôn có cờ `rw`.

### /proc/<PID>/mem

Đây là file nhị phân ánh xạ trực tiếp 1:1 toàn bộ không gian bộ nhớ ảo của tiến trình:

- Mở file này với quyền root (hoặc cùng user), rồi `seek` tới đúng dải địa chỉ lấy từ `maps` để đọc dữ liệu nhị phân trực tiếp trong RAM.

### Script khai thác

```javascript
// 1. Đọc bản đồ bộ nhớ của tiến trình PID 7
const maps = fs.readFileSync("/proc/7/maps", "utf8").trim().split("\n");
const mem = fs.openSync("/proc/7/mem", "r");

for (const line of maps) {
    const parts = line.split(/\s+/);
    // 2. Chỉ lọc những vùng nhớ có quyền "rw" (nơi chứa biến/Heap của JS)
    if (parts[1] && parts[1].includes("rw")) {
        const [start, end] = parts[0].split("-").map(x => parseInt(x, 16));
        const len = end - start;
        const buf = Buffer.alloc(len);
        try {
            // 3. Đọc dữ liệu nhị phân từ dải địa chỉ start -> end trong RAM
            fs.readSync(mem, buf, 0, len, start);

            // 4. Chuyển byte thành chuỗi và quét theo định dạng flag bằng regex
            const str = buf.toString("latin1");
            const matches = str.match(/[A-Za-z0-9_\-]{0,20}\{[^}\n\r\t ]+\}/g);
            if (matches) {
                console.log([...new Set(matches)].join("\n"));
            }
        } catch (e) {}
    }
}
```

## 3. Các bước giải

1. Trinh sát: thư mục `Challenge/Flags` trống, mã nguồn `src/main.ts` giữ vòng lặp vô tận.
2. Xác định PID của tiến trình chạy ngầm bằng `ps aux | grep node`, tìm ra tiến trình `node /root/Challenge/build/main.js` đang chạy với PID = 7.
3. Dump bộ nhớ RAM của tiến trình: môi trường tối giản không có `gdb` hay `strings`, nên dùng ngay runtime `node` có sẵn để đọc `/proc/7/maps` và `/proc/7/mem`.
4. Regex bắt đúng định dạng chuỗi và trả về flag.

## 4. Takeaways

- Xóa file (`unlink`/`rm`) chỉ hủy liên kết trên filesystem; dữ liệu đã nạp vào bộ nhớ tiến trình vẫn tồn tại cho đến khi tiến trình kết thúc hoặc bị garbage collector ghi đè.
- Trên Linux, người dùng có đặc quyền có thể đọc dữ liệu của bất kỳ tiến trình nào qua `/proc/<PID>/mem`.
- Memory dumping là kỹ thuật nền tảng trong DFIR để trích xuất khóa mã hóa, token hoặc dữ liệu nhạy cảm chưa kịp ghi xuống đĩa.
