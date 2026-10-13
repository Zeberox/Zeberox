# =====================================================================
#  SITE CONFIGURATION  —  edit this file to make the site yours.
#  Tohle je jediný soubor, který musíš upravit, aby byl web tvůj.
#  (Příspěvky se píšou jako .md soubory ve složce posts/.)
# =====================================================================

CONFIG = {
    # --- Identity / Identita ------------------------------------------
    "name": "Zeberox",
    "handle": "zeberox",
    # Full <title> of the home page. Leave "" to fall back to "name | handle".
    "homeTitle": "Van Minh Nguyen | Zeberox",
    "tagline": "learn, write",

    # --- Deployment / Nasazení ----------------------------------------
    # Leave both EMPTY to let GitHub Actions figure them out automatically.
    # Override only for a CUSTOM DOMAIN: base="/", siteUrl="https://example.com"
    "base": "",
    "siteUrl": "",

    # --- Languages / Jazyky -------------------------------------------
    "defaultLang": "en",
    "langs": ["en", "vi"],

    # --- Navigation / Navigace ----------------------------------------
    "sections": ["home", "about", "writeups", "certs"],
    "featuredCount": 3,

    # --- Links / Odkazy (leave "" to hide a link/button) --------------
    "links": {
        "email": "mailto:zeberox@proton.me",
        "github": "https://github.com/Zeberox",
        "cv": "",                   # e.g. "cv.pdf" (put the file in static/)
        "pgp": "",                  # e.g. "pgp.txt" (put the file in static/)
    },

    # --- Social preview image (optional) ------------------------------
    "ogImage": "",                  # e.g. "img/og.png" (inside static/)

    # --- Categories / Kategorie (name -> CSS colour var) --------------
    # Any category not listed here still gets a stable automatic colour.
    "categories": {
        "Haxagon": "--t-cert",
        "HTB": "--t-ctf",
    },

    # --- Certifications / Certifikace ---------------------------------
    # Drop badge images into static/img/ and point "badge" at them.
    "certs": [
        {
            "name": "HTB CJCA",
            "issuer": "Hack The Box",
            "issuer_url": "https://academy.hackthebox.com/app/exams/7#key-differentiators",
            "status": "In preparation",
            "url": "",
            "badge": "img/cjca.png",
            "note": "",
        },
    ],

    # --- Translatable text / Překládané texty -------------------------
    # 'en' is baked into the HTML; 'vi' is swapped in by JavaScript when the
    # visitor flips the language switch. Post bodies are shown exactly as you
    # wrote them (the switch only changes the interface + these texts).
    "i18n": {
        "en": {
            "home": "Home", "about": "About me", "writeups": "Writeups",
            "certs": "Certifications", "featured": "Featured", "topics": "Topics",
            "newest": "Newest", "latest": "Latest writeups", "viewAll": "View all",
            "readMore": "Read more", "search": "Search writeups…", "all": "All",
            "noResults": "No writeups match this filter.",
            "back": "Back to writeups", "links": "Links",
            "published": "Published", "contents": "Contents",
            "copy": "Copy", "copied": "Copied!",
            "roles": "Red teamer",
            "bio": "I am an IT student at SSSI Tábor, Czech Republic. I am 18 years "
                   "old and got into cybersecurity at 17. I play CTFs, solve lab "
                   "machines and write about what I learn.",
            "aboutBody": "Nothing.",
            "certsNote": "Currently preparing for the HTB CJCA (Certified Junior "
                         "Cybersecurity Analyst) exam. This page will be updated once "
                         "the certification is earned.",
        },
        "vi": {
            "home": "Trang chủ", "about": "Giới thiệu", "writeups": "Writeups",
            "certs": "Chứng chỉ", "featured": "Nổi bật", "topics": "Chủ đề",
            "newest": "Mới nhất", "latest": "Bài mới nhất", "viewAll": "Xem tất cả",
            "readMore": "Đọc tiếp", "search": "Tìm writeup…", "all": "Tất cả",
            "noResults": "Không có writeup nào khớp bộ lọc.",
            "back": "Quay lại danh sách", "links": "Liên kết",
            "published": "Đăng", "contents": "Mục lục",
            "copy": "Sao chép", "copied": "Đã sao chép!",
            "roles": "Red teamer",
            "bio": "Mình là sinh viên IT của trường SSSI Tábor, Cộng hòa Séc. Năm nay "
                   "mình 18 tuổi và bắt đầu quan tâm đến an ninh mạng từ năm 17 tuổi. "
                   "Mình chơi CTF, giải lab và viết lại những gì học được.",
            "aboutBody": "Không có gì.",
            "certsNote": "Hiện đang chuẩn bị cho kỳ thi HTB CJCA (Certified Junior "
                         "Cybersecurity Analyst). Mục này sẽ được cập nhật khi có "
                         "chứng chỉ.",
        },
    },
}
