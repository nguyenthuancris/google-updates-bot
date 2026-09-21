# -*- coding: utf-8 -*-
"""Danh sách các nguồn RSS/Atom theo dõi tin Google Ads, SEO và các sản phẩm liên quan."""

FEEDS = [
    # --- Nguồn chính thức về SEO / Google Search ---
    {
        "name": "Google Search Central Blog",
        "url": "https://developers.google.com/search/blog/feed.xml",
        "category": "SEO chính thức",
    },
    {
        "name": "Google Search Status Dashboard",
        "url": "https://status.search.google.com/en/feed.atom",
        "category": "SEO chính thức",
    },

    # --- Nguồn chính thức về Google Ads ---
    {
        "name": "Google Ads & Commerce Blog",
        "url": "https://blog.google/products/ads-commerce/rss/",
        "category": "Google Ads chính thức",
    },
    {
        "name": "Google Ads Developer Blog",
        "url": "http://feeds.feedburner.com/GoogleAdsDeveloperBlog",
        "category": "Google Ads chính thức",
    },
    {
        "name": "Google Marketing Platform Blog",
        "url": "https://blog.google/products/marketingplatform/rss/",
        "category": "Google Ads / GA4 chính thức",
    },

    # Đã tắt các nguồn tin ngành (Search Engine Land, Search Engine Roundtable,
    # Search Engine Journal, PPC Land) theo yêu cầu -> chỉ giữ tin CHÍNH THỨC từ Google,
    # để bớt tin vụn vặt / bài phân tích của bên thứ ba, chỉ còn thông báo quan trọng.
]

# Từ khóa để lọc bớt các bài không liên quan tới Google Ads/SEO/GA4/Merchant Center/GBP
# (chỉ áp dụng cho các feed tổng hợp có nhiều chủ đề như Search Engine Land / SEJ / PPC Land)
KEYWORDS = [
    "google ads", "google search", "seo", "search console", "search engine",
    "google analytics", "ga4", "merchant center", "google shopping",
    "google business profile", "gbp", "google my business",
    "performance max", "smart bidding", "demand gen", "google discover",
    "core update", "spam update", "ranking", "algorithm", "sitelink",
    "structured data", "schema", "crawl", "indexing", "google ai overview",
    "ai mode", "ai max", "quality score", "keyword", "ppc", "sem",
    "display & video 360", "dv360", "search ads 360", "campaign manager",
    "google marketing platform", "adwords",
]

# Các feed chính thức không cần lọc từ khóa (mọi bài đều liên quan)
NO_FILTER_FEEDS = {
    "Google Search Central Blog",
    "Google Search Status Dashboard",
    "Google Ads & Commerce Blog",
    "Google Ads Developer Blog",
    "Google Marketing Platform Blog",
}
