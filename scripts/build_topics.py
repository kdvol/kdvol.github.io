#!/usr/bin/env python3
"""주제별 태그 페이지 생성 — /topics/ 허브 + /topics/{slug}.html.

뉴스레터 제목 + soonsal-keywords 메타를 주제 사전(TAXONOMY)과 매칭해
주제별 아카이브 페이지를 만든다. 매 실행마다 전체 재생성(멱등).
generate_seo.py가 호출하므로 새 뉴스레터 발행 시 자동 갱신된다.
"""
import re
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape
import json

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://soonsal.com"
OUT = ROOT / "topics"

# (slug, 표시명, 이모지, 매칭 패턴)
TAXONOMY = [
    ("crypto", "크립토", "🔐", r"크립토|비트코인|이더리움|BTC|ETH|코인|스테이블|리플|솔라나|바이낸스|코인베이스|디파이|DeFi|NFT|DAO|토큰"),
    ("ai", "AI", "🤖", r"\bAI\b|인공지능|오픈AI|OpenAI|챗GPT|ChatGPT|Anthropic|앤스로픽|클로드|LLM|젠슨\s?황|생성형"),
    ("semiconductor", "반도체", "🔩", r"반도체|삼성전자|하이닉스|TSMC|인텔|파운드리|HBM|엔비디아|Nvidia|NVIDIA"),
    ("fed-rates", "연준·금리", "🏛️", r"연준|Fed|FOMC|파월|금리\s?인상|금리\s?인하|기준금리|국채\s?금리|양적"),
    ("fx", "환율·달러", "💱", r"환율|원/달러|원화|달러|엔화|위안화|DXY"),
    ("china", "중국", "🇨🇳", r"중국|알리바바|텐센트|BYD|샤오미|홍콩|항셍|시진핑"),
    ("japan", "일본", "🇯🇵", r"일본|닛케이|도요타|엔저|BOJ|일본은행"),
    ("deals", "딜·M&A", "🤝", r"인수|합병|M&A|바이아웃|사모펀드|PEF|매각|인수전"),
    ("ipo", "IPO·상장", "🔔", r"IPO|상장(?!폐지)|공모가|공모주|나스닥\s?데뷔"),
    ("trump-politics", "트럼프·정책", "🏳️", r"트럼프|백악관|관세|대선|의회|규제|행정명령|SEC"),
    ("energy", "에너지·원자재", "🛢️", r"유가|OPEC|원유|WTI|천연가스|에너지|정유|금값|골드|구리"),
    ("tesla-ev", "테슬라·전기차", "🚗", r"테슬라|머스크|전기차|\bEV\b|자율주행|로보택시"),
    ("bigtech", "빅테크", "📱", r"애플|구글|아마존|메타|마이크로소프트|\bMS\b|알파벳|넷플릭스"),
    ("korea-market", "국내 증시", "📈", r"코스피|코스닥|한국은행|국민연금|밸류업|공매도"),
    ("etf-funds", "ETF·펀드", "🧺", r"ETF|펀드|자산운용|인덱스|블랙록|뱅가드"),
    ("banks-wallst", "월가·은행", "🏦", r"은행|JP모건|골드만|모건스탠리|씨티|웰스파고|월가|헤지펀드|버크셔|버핏"),
]

DATED = re.compile(r"^(\d{2})(\d{2})")

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#111;color:#eee;font-family:'DM Sans','Apple SD Gothic Neo',sans-serif;min-height:100vh}
.wrap{max-width:800px;margin:0 auto;padding:32px 20px}
a{color:#eee;text-decoration:none}
h1{font-size:1.5rem;margin-bottom:6px}
.sub{color:#888;font-size:.9rem;margin-bottom:24px}
.home{color:#F07040;font-size:.9rem;display:inline-block;margin-bottom:18px}
.tags{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}
.tag{border:1px solid #333;border-radius:20px;padding:7px 16px;font-size:.92rem;transition:.15s}
.tag:hover{border-color:#F07040;color:#F07040}
.tag b{color:#F07040;font-weight:600;margin-left:6px}
.item{display:flex;gap:14px;padding:13px 4px;border-bottom:1px solid #222;align-items:baseline}
.item:hover .t{color:#F07040}
.d{color:#777;font-size:.85rem;white-space:nowrap;font-variant-numeric:tabular-nums}
.t{font-size:.97rem;line-height:1.5;transition:.15s}
.badge{font-size:.75rem;color:#f5a623;border:1px solid #3a3220;border-radius:4px;padding:1px 6px;margin-left:8px;white-space:nowrap}
"""


def head(title, desc, canonical, ld=None):
    ldtag = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ""
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title><meta name="description" content="{escape(desc)}">
<link rel="canonical" href="{canonical}"><meta name="robots" content="index, follow">
<meta property="og:type" content="website"><meta property="og:site_name" content="순살브리핑 Soonsal">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(desc)}">
<meta property="og:url" content="{canonical}"><meta property="og:locale" content="ko_KR">
{ldtag}<style>{CSS}</style></head><body><div class="wrap">
<a class="home" href="/">← 순살 홈</a>"""

FOOT = "</div></body></html>"


def collect_posts():
    posts = []
    for p in sorted((ROOT / "newsletters" / "2026").glob("*.html"), reverse=True):
        if p.name == "index.html":
            continue
        raw = p.read_text(encoding="utf-8", errors="replace")[:4000]
        tm = re.search(r"<title>([^<]+)</title>", raw)
        title = tm.group(1).strip() if tm else p.stem
        km = re.search(r'name="soonsal-keywords" content="([^"]*)"', raw)
        haystack = title + " " + (km.group(1) if km else "")
        dm = DATED.match(p.stem)
        d = date(2026, int(dm.group(1)), int(dm.group(2))) if dm else None
        posts.append({
            "url": f"/newsletters/2026/{p.name}",
            "title": re.sub(r"^[^\w<>&\"']{1,4}\s+", "", title).split(" — ")[0],
            "date": d,
            "crypto": "-crypto" in p.stem,
            "haystack": haystack,
        })
    posts.sort(key=lambda x: (x["date"] or date.min), reverse=True)
    return posts


def main():
    posts = collect_posts()
    OUT.mkdir(exist_ok=True)
    today = date.today().isoformat()

    topics = []
    for slug, name, emoji, pattern in TAXONOMY:
        rx = re.compile(pattern)
        matched = [p for p in posts if rx.search(p["haystack"])]
        if len(matched) < 3:
            continue
        topics.append((slug, name, emoji, matched))

        canonical = f"{BASE}/topics/{slug}.html"
        ld = {"@context": "https://schema.org", "@type": "CollectionPage",
              "name": f"{name} 관련 브리핑 모음", "url": canonical, "inLanguage": "ko",
              "isPartOf": {"@type": "WebSite", "name": "순살브리핑", "url": f"{BASE}/"},
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "url": f"{BASE}{p['url']}",
                   "name": p["title"]} for i, p in enumerate(matched[:30])]}}
        items = "".join(
            f'<a class="item" href="{p["url"]}"><span class="d">{p["date"].isoformat() if p["date"] else ""}</span>'
            f'<span class="t">{escape(p["title"])}'
            + ('<span class="badge">크립토</span>' if p["crypto"] else "")
            + "</span></a>"
            for p in matched)
        html = (head(f"{name} 관련 브리핑 {len(matched)}건 — 순살브리핑",
                     f"{name} 주제를 다룬 순살브리핑 아카이브 {len(matched)}건. 최신순 정리.",
                     canonical, ld)
                + f'<h1>{emoji} {name}</h1><p class="sub">이 주제를 다룬 브리핑 {len(matched)}건 · {today} 기준 · '
                  f'<a href="/topics/" style="color:#F07040">전체 주제 보기</a></p>'
                + items + FOOT)
        (OUT / f"{slug}.html").write_text(html, encoding="utf-8")

    # 허브 페이지
    canonical = f"{BASE}/topics/"
    ld = {"@context": "https://schema.org", "@type": "CollectionPage",
          "name": "주제별 브리핑 아카이브", "url": canonical, "inLanguage": "ko"}
    tags = "".join(
        f'<a class="tag" href="/topics/{slug}.html">{emoji} {name}<b>{len(matched)}</b></a>'
        for slug, name, emoji, matched in sorted(topics, key=lambda t: -len(t[3])))
    html = (head("주제별 브리핑 — 순살브리핑", "크립토·AI·반도체·연준 등 주제별로 모아 보는 순살브리핑 아카이브.",
                 canonical, ld)
            + f'<h1>주제별 브리핑</h1><p class="sub">뉴스레터 {len(posts)}건을 {len(topics)}개 주제로 · {today} 기준</p>'
            + f'<div class="tags">{tags}</div>' + FOOT)
    (OUT / "index.html").write_text(html, encoding="utf-8")

    print(f"🏷️  topics: {len(topics)}개 주제 페이지 (+허브), 소스 {len(posts)}건")


if __name__ == "__main__":
    main()
