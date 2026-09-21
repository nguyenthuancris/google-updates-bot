# -*- coding: utf-8 -*-
"""Kiểm thử logic của bot bằng dữ liệu RSS giả lập (không cần mạng)."""

import feedparser

from bot import format_message, entry_id, is_relevant

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Sample Feed</title>
  <item>
    <title>Google Ads rolls out new AI Max feature</title>
    <link>https://example.com/google-ads-ai-max</link>
    <description><![CDATA[<p>Google Ads is testing a new <b>AI Max</b> feature for Search campaigns that improves bidding.</p>]]></description>
    <pubDate>Fri, 18 Sep 2026 14:43:42 +0000</pubDate>
    <guid>https://example.com/google-ads-ai-max</guid>
  </item>
  <item>
    <title>Unrelated recipe: How to bake bread</title>
    <link>https://example.com/bake-bread</link>
    <description><![CDATA[<p>A recipe for bread with no relation to marketing.</p>]]></description>
    <pubDate>Fri, 18 Sep 2026 10:00:00 +0000</pubDate>
    <guid>https://example.com/bake-bread</guid>
  </item>
</channel>
</rss>"""

def main():
    parsed = feedparser.parse(SAMPLE_RSS)
    assert len(parsed.entries) == 2, "Phải có 2 bài trong feed mẫu"

    ads_entry = parsed.entries[0]
    bread_entry = parsed.entries[1]

    # Test is_relevant với feed cần lọc từ khóa (không nằm trong NO_FILTER_FEEDS)
    assert is_relevant("Search Engine Land", ads_entry), "Bài về Google Ads AI Max phải được coi là liên quan"
    assert not is_relevant("Search Engine Land", bread_entry), "Bài về bánh mì phải bị lọc bỏ"

    # Test entry_id ổn định
    eid1 = entry_id("Search Engine Land", ads_entry)
    eid2 = entry_id("Search Engine Land", ads_entry)
    assert eid1 == eid2, "entry_id phải ổn định cho cùng 1 bài"
    print("entry_id:", eid1)

    # Test format_message không lỗi và chứa các phần quan trọng
    msg = format_message("Search Engine Land", "Tin ngành", ads_entry)
    assert "Google Ads rolls out new AI Max feature" in msg
    assert "https://example.com/google-ads-ai-max" in msg
    assert "Search Engine Land" in msg
    print("\n----- Tin nhắn mẫu sẽ gửi lên Telegram -----")
    print(msg)
    print("---------------------------------------------")

    # Test feed chính thức không lọc từ khóa
    assert is_relevant("Google Search Central Blog", bread_entry), "Feed chính thức không được lọc từ khóa"

    print("\n✅ Tất cả kiểm thử đều PASS")


if __name__ == "__main__":
    main()
