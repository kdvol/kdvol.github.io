#!/usr/bin/env python3
"""콘텐츠 페이지에 SEO/AEO 메타 일괄 주입 (idempotent).

뉴스레터·잉글리시·카드뉴스·스페셜 페이지의 </head> 직전에
canonical + description + OG/트위터 + NewsArticle JSON-LD를 삽입한다.
이미 canonical이 있는 파일은 건너뛰므로 반복 실행에 안전하다.
generate_seo.py가 호출 → deploy.py/워크플로 커밋 직전에 자동 반영.
"""
import html as htmlmod
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://soonsal.com"

# (디렉터리, 언어, 스키마 타입)
SECTIONS = [
    ("newsletters/2026", "ko", "NewsArticle"),
    ("english/2026", "en", "NewsArticle"),
    ("financial-english", "en", "Article"),
    ("financial-english/2026", "en", "Article"),
    ("cardnews/2026", "ko", "Article"),
    ("special", "ko", "Article"),
    ("zzal/2026", "ko", "Article"),
]

DATED = re.compile(r"^(\d{2})(\d{2})")
EMOJI_PREFIX = re.compile(r"^[^\w<>&\"']{1,4}\s+")  # 🐟 등 선두 이모지 제거


def page_date(p):
    m = DATED.match(p.stem)
    if m:
        year = int(p.parent.name) if p.parent.name.isdigit() else date.today().year
        try:
            return date(year, int(m.group(1)), int(m.group(2)))
        except ValueError:
            pass
    return date.fromtimestamp(p.stat().st_mtime)


def find_og_image(p):
    """같은 이름의 카드뉴스 PNG 폴더가 있으면 첫 장을 썸네일로."""
    candidates = [p.parent / f"{p.stem}_png",
                  ROOT / "cardnews" / "2026" / f"{p.stem}_png"]
    for c in candidates:
        img = c / "card_01.png"
        if img.exists():
            return f"{BASE}/{img.relative_to(ROOT).as_posix()}"
    return None


def build_block(p, lang, schema_type):
    raw = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<title>([^<]+)</title>", raw)
    title = (m.group(1).strip() if m else p.stem)
    clean = EMOJI_PREFIX.sub("", title)
    d = page_date(p)
    rel = p.relative_to(ROOT).as_posix()
    url = f"{BASE}/{rel}"
    img = find_og_image(p)

    if lang == "ko":
        desc = (f"{clean.split(' — ')[0]} — {d.year}년 {d.month}월 {d.day}일 순살브리핑. "
                "글로벌 금융·경제·크립토 뉴스를 뼈만 발라낸 데일리 브리핑.")
    else:
        desc = f"{clean.split(' — ')[0]} — Soonsal daily briefing, {d.isoformat()}."

    kw = re.search(r'name="soonsal-keywords" content="([^"]*)"', raw)
    keywords = [k for k in (kw.group(1).split(",") if kw else []) if k]

    ld = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "headline": clean[:110],
        "datePublished": f"{d.isoformat()}T09:00:00+09:00",
        "dateModified": f"{d.isoformat()}T09:00:00+09:00",
        "inLanguage": lang,
        "mainEntityOfPage": url,
        "author": {"@type": "Organization", "name": "순살브리핑", "url": f"{BASE}/"},
        "publisher": {"@type": "Organization", "name": "순살브리핑",
                      "logo": {"@type": "ImageObject",
                               "url": f"{BASE}/apple-touch-icon.png"}},
    }
    if keywords:
        ld["keywords"] = ", ".join(keywords)
    if img:
        ld["image"] = [img]

    t = htmlmod.escape(title, quote=True)
    de = htmlmod.escape(desc, quote=True)
    lines = [
        f'<link rel="canonical" href="{url}"/>',
        f'<meta name="description" content="{de}"/>',
        f'<meta property="og:type" content="article"/>',
        f'<meta property="og:site_name" content="순살브리핑 Soonsal"/>',
        f'<meta property="og:title" content="{t}"/>',
        f'<meta property="og:description" content="{de}"/>',
        f'<meta property="og:url" content="{url}"/>',
        f'<meta property="og:locale" content="{"ko_KR" if lang == "ko" else "en_US"}"/>',
    ]
    if img:
        lines += [f'<meta property="og:image" content="{img}"/>',
                  '<meta name="twitter:card" content="summary_large_image"/>']
    else:
        lines += ['<meta name="twitter:card" content="summary"/>']
    lines += [f'<meta name="twitter:title" content="{t}"/>',
              f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>']
    return raw, "\n" + "\n".join(lines) + "\n"


def enrich_file(p, lang, schema_type):
    raw = p.read_text(encoding="utf-8", errors="replace")
    if 'rel="canonical"' in raw:
        return False
    raw, block = build_block(p, lang, schema_type)
    if "</head>" in raw:
        out = raw.replace("</head>", block + "</head>", 1)
    elif "</title>" in raw:
        out = raw.replace("</title>", "</title>" + block, 1)
    else:
        return False
    p.write_text(out, encoding="utf-8")
    return True


def main():
    done = skipped = 0
    for sec, lang, typ in SECTIONS:
        d = ROOT / sec
        if not d.exists():
            continue
        for p in sorted(d.glob("*.html")):
            if p.name == "index.html":
                continue
            if enrich_file(p, lang, typ):
                done += 1
            else:
                skipped += 1
    print(f"📰 article enrich: {done} injected, {skipped} skipped(already done)")
    return done


if __name__ == "__main__":
    main()
