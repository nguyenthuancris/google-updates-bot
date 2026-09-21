# -*- coding: utf-8 -*-
"""
Bot Telegram tự động gom tin cập nhật Google Ads, SEO, GA4, Merchant Center,
Google Business Profile... từ nhiều nguồn RSS/Atom và gửi vào một nhóm/kênh Telegram.

Cách chạy:
    python bot.py                 # gửi tin thật (cần biến môi trường TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    python bot.py --dry-run       # chỉ in ra màn hình, không gửi và không lưu trạng thái

Thiết kế để chạy định kỳ (vd: GitHub Actions mỗi 6 tiếng). Bot tự nhớ những bài
đã gửi (lưu trong seen_ids.json) để không gửi trùng lần sau.
"""

import argparse
import html
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests
from deep_translator import GoogleTranslator

from feeds import FEEDS, KEYWORDS, NO_FILTER_FEEDS

STATE_FILE = Path(__file__).parent / "seen_ids.json"
MAX_ITEMS_PER_FEED_FIRST_RUN = 3  # lần chạy đầu tiên, chỉ lấy vài bài mới nhất mỗi nguồn (tránh spam)
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
REQUEST_TIMEOUT = 20


def load_seen_ids() -> set:
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return set(data.get("seen_ids", []))
        except (json.JSONDecodeError, OSError):
            return set()
    return set()


def save_seen_ids(seen_ids: set) -> None:
    # Giới hạn kích thước file: chỉ giữ 3000 id gần nhất để tránh phình to mãi
    ids_list = list(seen_ids)
    if len(ids_list) > 3000:
        ids_list = ids_list[-3000:]
    STATE_FILE.write_text(
        json.dumps({"seen_ids": ids_list, "updated_at": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def entry_id(feed_name: str, entry) -> str:
    raw = entry.get("id") or entry.get("link") or entry.get("title", "")
    return f"{feed_name}::{raw}"


def is_relevant(feed_name: str, entry) -> bool:
    if feed_name in NO_FILTER_FEEDS:
        return True
    text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
    return any(kw in text for kw in KEYWORDS)


def fetch_feed(url: str):
    try:
        resp = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TLCommunicationUpdatesBot/1.0)"},
        )
        resp.raise_for_status()
        return feedparser.parse(resp.content)
    except requests.RequestException as exc:
        print(f"  [Lỗi] Không tải được feed {url}: {exc}", file=sys.stderr)
        return None


_TRANSLATOR = GoogleTranslator(source="auto", target="vi")
TRANSLATE_RETRY_WAITS = (4, 8, 16)  # giây, tăng dần khi bị chặn do gọi quá nhanh
TRANSLATE_THROTTLE_SECONDS = 1.0  # nghỉ giữa các lần gọi để tránh vượt giới hạn ~5 request/giây


def translate_vi(text: str) -> str:
    """Dịch text sang tiếng Việt. Tự thử lại nếu bị giới hạn tốc độ (rate limit).
    Nếu vẫn lỗi sau khi thử lại (mất mạng, bị chặn hẳn...), trả lại text gốc."""
    if not text:
        return text

    last_exc = None
    for attempt, wait_seconds in enumerate((0, *TRANSLATE_RETRY_WAITS)):
        if wait_seconds:
            print(f"  [Dịch] Bị giới hạn tốc độ, đợi {wait_seconds}s rồi thử lại (lần {attempt})...")
            time.sleep(wait_seconds)
        try:
            translated = _TRANSLATOR.translate(text)
            time.sleep(TRANSLATE_THROTTLE_SECONDS)  # nghỉ để không gọi API quá dồn dập
            return translated or text
        except Exception as exc:  # pragma: no cover - lỗi mạng/API không nên làm sập bot
            last_exc = exc

    print(f"  [Lỗi dịch] Bỏ qua dịch, dùng bản gốc. Lỗi cuối: {last_exc}", file=sys.stderr)
    return text


_TRANSLATE_DELIMITER = "\n\n@@@\n\n"  # chuỗi phân tách để gộp 2 đoạn text vào 1 lần gọi dịch


def translate_title_and_summary(title: str, summary: str) -> tuple:
    """Dịch tiêu đề + tóm tắt trong CÙNG 1 lần gọi API (giảm số lượng request, tránh rate limit).
    Nếu không tách lại được kết quả (do bản dịch đổi cấu trúc), fallback về dịch riêng từng phần."""
    if not summary:
        return translate_vi(title), ""

    combined = f"{title}{_TRANSLATE_DELIMITER}{summary}"
    translated = translate_vi(combined)
    parts = translated.split(_TRANSLATE_DELIMITER.strip())
    if len(parts) != 2:
        # Bản dịch làm hỏng dấu phân tách -> dịch riêng từng phần (chậm hơn nhưng chắc chắn đúng)
        return translate_vi(title), translate_vi(summary)
    return parts[0].strip(), parts[1].strip()


def format_message(feed_name: str, category: str, entry) -> str:
    raw_title = entry.get("title", "(không có tiêu đề)")
    link = entry.get("link", "")
    published = entry.get("published", "") or entry.get("updated", "")

    summary = entry.get("summary", "") or ""
    # loại bỏ thẻ html thô trong summary, giữ ngắn gọn
    import re
    summary_text = re.sub("<[^<]+?>", "", summary).strip()
    summary_text = html.unescape(summary_text)
    if len(summary_text) > 500:
        summary_text = summary_text[:500].rsplit(" ", 1)[0] + "..."

    # Dịch tiêu đề + tóm tắt sang tiếng Việt trong 1 lần gọi (giữ link gốc để đọc bản tiếng Anh đầy đủ)
    title_vi, summary_vi = translate_title_and_summary(raw_title, summary_text)
    title_vi = html.escape(title_vi)
    summary_vi = html.escape(summary_vi) if summary_vi else ""

    lines = [
        f"🔔 <b>{title_vi}</b>",
        f"📌 Nguồn: {html.escape(feed_name)} ({html.escape(category)})",
    ]
    if published:
        lines.append(f"🕒 {html.escape(published)}")
    if summary_vi:
        lines.append("")
        lines.append(summary_vi)
    if link:
        lines.append("")
        lines.append(f'<a href="{html.escape(link)}">Đọc bài gốc (tiếng Anh) →</a>')

    return "\n".join(lines)


def send_telegram_message(token: str, chat_id: str, text: str) -> bool:
    resp = requests.post(
        TELEGRAM_API.format(token=token),
        data={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code != 200:
        print(f"  [Lỗi Telegram] {resp.status_code}: {resp.text}", file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Bot gửi tin cập nhật Google Ads/SEO về Telegram")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ in ra màn hình, không gửi Telegram và không lưu trạng thái")
    args = parser.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not args.dry_run and (not token or not chat_id):
        print("Thiếu biến môi trường TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID.", file=sys.stderr)
        sys.exit(1)

    seen_ids = load_seen_ids()
    is_first_run = len(seen_ids) == 0
    new_seen_ids = set(seen_ids)

    total_sent = 0
    total_new_found = 0

    for feed in FEEDS:
        name, url, category = feed["name"], feed["url"], feed["category"]
        print(f"Đang kiểm tra: {name} ...")
        parsed = fetch_feed(url)
        if parsed is None or not parsed.entries:
            print(f"  -> Không có dữ liệu hoặc lỗi feed.")
            continue

        entries = parsed.entries
        # Sắp xếp theo thời gian nếu có, mới nhất trước; feed vốn đã theo thứ tự này thường
        candidates = []
        for entry in entries:
            eid = entry_id(name, entry)
            if eid in seen_ids:
                continue
            if not is_relevant(name, entry):
                continue
            candidates.append((eid, entry))

        if is_first_run:
            # Lần đầu chạy: không spam toàn bộ lịch sử, chỉ lấy vài bài mới nhất mỗi nguồn
            candidates = candidates[:MAX_ITEMS_PER_FEED_FIRST_RUN]

        total_new_found += len(candidates)

        for eid, entry in candidates:
            message = format_message(name, category, entry)
            if args.dry_run:
                print("----- DRY RUN: sẽ gửi tin sau -----")
                print(message)
                print("------------------------------------")
            else:
                ok = send_telegram_message(token, chat_id, message)
                if ok:
                    total_sent += 1
                    time.sleep(1.2)  # tránh bị Telegram giới hạn tốc độ (rate limit)
                else:
                    # nếu gửi lỗi, không đánh dấu là đã gửi để thử lại lần sau
                    continue
            new_seen_ids.add(eid)

    print(f"\nTổng số bài mới tìm thấy: {total_new_found}")
    if args.dry_run:
        print("Chế độ dry-run: không lưu trạng thái, không gửi tin thật.")
    else:
        print(f"Đã gửi thành công: {total_sent}")
        save_seen_ids(new_seen_ids)
        print(f"Đã lưu trạng thái vào {STATE_FILE.name}")


if __name__ == "__main__":
    main()
