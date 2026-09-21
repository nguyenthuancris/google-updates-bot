# Bot Telegram – Cập nhật Google Ads & SEO

Bot tự động theo dõi các nguồn tin **CHÍNH THỨC** từ Google về **Google Ads**,
**Google Search/SEO**, **Google Analytics (GA4)**, **Google Marketing Platform**...
rồi gửi thông báo vào nhóm/kênh Telegram của bạn, chạy **miễn phí** trên GitHub
Actions, tự động mỗi **30 phút**.

## Nguồn tin đang theo dõi

Chỉ theo dõi các nguồn **chính thức từ Google** (đã tắt các trang tin ngành như
Search Engine Land, PPC Land... để tránh tin vụn vặt, chỉ giữ lại thông báo quan trọng):
- Google Search Central Blog
- Google Search Status Dashboard (core update, spam update, sự cố)
- Google Ads & Commerce Blog
- Google Ads Developer Blog
- Google Marketing Platform Blog (GA4, DV360, CM360...)

> Muốn bật lại các nguồn tin ngành (Search Engine Land, PPC Land...) thì thêm lại
> vào danh sách `FEEDS` trong file `feeds.py`.

Tin nhắn được **tự động dịch sang tiếng Việt** (tiêu đề + tóm tắt), kèm link đọc
bài gốc tiếng Anh đầy đủ.

---

## Cài đặt (khoảng 10 phút, không cần biết code)

### Bước 1: Tạo Telegram Bot

1. Mở Telegram, tìm **@BotFather**, nhắn `/newbot`.
2. Đặt tên bot (ví dụ: `TL Google Updates Bot`) và username (phải kết thúc bằng `bot`, ví dụ `tl_google_updates_bot`).
3. BotFather sẽ trả về một **token** dạng `123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`. **Lưu lại token này.**

### Bước 2: Lấy Chat ID

**Nếu gửi vào nhóm Telegram:**
1. Tạo nhóm (hoặc dùng nhóm có sẵn), thêm bot vừa tạo vào nhóm.
2. Gửi 1 tin nhắn bất kỳ vào nhóm.
3. Mở trình duyệt, truy cập:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   (thay `<TOKEN>` bằng token ở bước 1)
4. Tìm số `"chat":{"id":-1001234567890...}` — đó là **Chat ID** (nhóm thường có số âm).

**Nếu gửi vào kênh (channel):**
1. Tạo kênh, thêm bot làm **quản trị viên (admin)** của kênh.
2. Đăng 1 bài bất kỳ trong kênh.
3. Truy cập link `getUpdates` như trên để lấy `chat_id` (dạng `-100...`).
   Hoặc dùng luôn username kênh dạng `@ten_kenh` nếu kênh công khai.

### Bước 3: Tạo repo GitHub và tải code lên

1. Tạo tài khoản GitHub (nếu chưa có) tại https://github.com
2. Tạo repository mới (Private hoặc Public đều được).
3. Tải toàn bộ các file trong thư mục này lên repo đó (kéo-thả trên giao diện web GitHub, hoặc dùng `git push`).

### Bước 4: Khai báo Secrets (token & chat id) cho GitHub Actions

1. Vào repo trên GitHub → **Settings** → **Secrets and variables** → **Actions**.
2. Bấm **New repository secret**, tạo lần lượt 2 secret:
   - `TELEGRAM_BOT_TOKEN` = token lấy ở Bước 1
   - `TELEGRAM_CHAT_ID` = chat id lấy ở Bước 2
3. Vào tab **Actions** của repo, bật Actions nếu GitHub hỏi.

### Bước 5: Chạy thử

1. Vào tab **Actions** → chọn workflow **"Gửi tin cập nhật Google Ads/SEO về Telegram"**.
2. Bấm **Run workflow** để chạy thử ngay (không cần đợi lịch).
3. Kiểm tra Telegram — bot sẽ gửi vài tin mới nhất từ mỗi nguồn (lần đầu chạy chỉ lấy 3 bài/nguồn để tránh spam).
4. Từ sau đó, bot tự chạy đều đặn mỗi **30 phút** và chỉ gửi bài **mới**, không gửi trùng.

> **Lưu ý về chi phí:** với lịch 30 phút/lần, nên để repo ở chế độ **Public**
> để chạy hoàn toàn miễn phí, không giới hạn. Nếu để **Private**, GitHub chỉ
> tặng 2.000 phút chạy/tháng — chạy 30 phút/lần có thể sát hoặc vượt mức này.
> Muốn an toàn với repo Private thì nới lịch ra 1-2 tiếng/lần (sửa dòng
> `cron` trong `.github/workflows/check-updates.yml`).

---

## Cấu trúc file

```
bot.py                          # Script chính
feeds.py                        # Danh sách nguồn RSS + từ khóa lọc
requirements.txt                # Thư viện Python cần cài
seen_ids.json                   # Bot tự lưu danh sách bài đã gửi (đừng sửa tay)
test_local.py                   # Kiểm thử logic (không cần mạng)
.github/workflows/check-updates.yml   # Lịch chạy tự động trên GitHub Actions
```

## Tuỳ chỉnh thêm

- **Đổi tần suất gửi:** sửa dòng `cron: "*/30 * * * *"` trong file
  `.github/workflows/check-updates.yml`. Ví dụ mỗi 1 tiếng: `"0 * * * *"`.
- **Thêm/bớt nguồn:** sửa danh sách `FEEDS` trong `feeds.py`. Muốn bật lại các nguồn
  tin ngành (Search Engine Land, PPC Land...) thì thêm lại vào danh sách này, và nhớ
  thêm tên nguồn đó vào `NO_FILTER_FEEDS` nếu muốn không lọc từ khóa.
- **Đổi từ khóa lọc** (cho các nguồn tin ngành, nếu bật lại): sửa danh sách `KEYWORDS` trong `feeds.py`.
- **Dịch sang tiếng Việt:** bot đã tự động dịch tiêu đề + tóm tắt sang tiếng Việt (dùng
  MyMemory Translate, dự phòng Google Translate, đều miễn phí không cần API key) —
  không cần làm gì thêm.

## Xử lý sự cố

- **Không thấy tin nào được gửi:** vào tab Actions, xem log của lần chạy gần nhất, tìm dòng `[Lỗi]` để biết nguồn nào bị lỗi.
- **Bot không gửi được tin, báo lỗi Telegram 401/403:** kiểm tra lại token, và đảm bảo bot đã được thêm vào nhóm/kênh với quyền gửi tin.
- **Muốn gửi lại toàn bộ tin cũ:** xoá nội dung `seen_ids.json` về `{"seen_ids": [], "updated_at": null}` rồi chạy lại (lưu ý sẽ gửi tối đa 3 bài/nguồn do giới hạn "lần đầu chạy").
