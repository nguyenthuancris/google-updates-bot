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

from feeds import FEEDS, KEYWORDS, NO_FILTER_FEEDS

STATE_FILE = Path(__file__).parent / "seen_ids.json"
MAX_ITEMS_PER_FEED_FIRST_RUN = 3
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


def format_message(feed_name: str, category: str, entry) -> str:
    title = html.escape(entry.get("title", "(không có tiêu đề)"))
    link = entry.get("link", "")
    published = entry.get("published", "") or entry.get("updated", "")

    summary = entry.get("summary", "") or ""
    import re
    summary_text = re.sub("<[^<]+?>", "", summary).strip()
    summary_text = html.unescape(summary_text)
    if len(summary_text) > 300:
        summary_text = summary_text[:300].rsplit(" ", 1)[0] + "..."
    summary_text = html.escape(summary_text)

    lines = [
        f"🔔 <b>{title}</b>",
        f"📌 Nguồn: {html.escape(feed_name)} ({html.escape(category)})",
    ]
    if published:
        lines.append(f"🕒 {html.escape(published)}")
    if summary_text:
        lines.append("")
        lines.append(summary_text)
    if link:
        lines.append("")
        lines.append(f'<a href="{html.escape(link)}">Đọc bài gốc →</a>')

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
        candidates = []
        for entry in entries:
            eid = entry_id(name, entry)
            if eid in seen_ids:
                continue
            if not is_relevant(name, entry):
                continue
            candidates.append((eid, entry))

        if is_first_run:
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
                    time.sleep(1.2)
                else:
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
