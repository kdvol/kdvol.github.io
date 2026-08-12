#!/usr/bin/env python3
"""내비게이션 자동 동기화 — 모든 공개 페이지의 nav를 한 정의로 통일(자가치유).

nav가 페이지마다 하드코딩돼 있어 최신 페이지만 새 탭을 갖던 문제 → 매 빌드마다
generate_seo가 이 함수를 호출해 전 페이지 nav를 정규형으로 덮어쓴다. deploy.py가
아카이브 인덱스를 재생성하며 옛 nav를 써도 그 직후 여기서 교정된다.

위키는 공개 탭에서 제외(어드민이 entities.json으로 관리). 엔티티 탐색은 주제별 안에서.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CORE_ITEMS = [("/newsletters/", "브리핑"), ("/morning/", "아침 메모"), ("/topics/", "주제별")]
MORE_ITEMS = [("/cardnews/", "카드뉴스"), ("/youtube/", "YouTube"),
              ("/school/", "스쿨"), ("/advertise/", "광고 문의")]
BIZ = {"/advertise/"}

NAV_RE = re.compile(r'<(?:div|nav)\s+class="nav"(?:\s[^>]*)?>.*?</(?:div|nav)>', re.S)
NAV_STYLE_RE = re.compile(r'<style id="soonsal-nav-v2">.*?</style>', re.S)


def _nav(active):
    def cls(h):
        c = (["active"] if h == active else []) + (["biz"] if h in BIZ else [])
        return f' class="{" ".join(c)}"' if c else ""
    core = "".join(f'<a href="{h}"{cls(h)}>{l}</a>' for h, l in CORE_ITEMS)
    more_active = active in {href for href, _label in MORE_ITEMS}
    more_cls = ' class="nav-more active"' if more_active else ' class="nav-more"'
    more = "".join(f'<a href="{h}"{cls(h)}>{l}</a>' for h, l in MORE_ITEMS)
    return (
        '<nav class="nav" aria-label="주요 메뉴">' + core
        + f'<details{more_cls}><summary>더보기 <span aria-hidden="true">⌄</span></summary>'
        + f'<section class="nav-menu" aria-label="추가 메뉴">{more}</section></details></nav>'
    )


def _active_for(path: Path):
    rel = path.relative_to(ROOT)
    if rel == Path("index.html"):
        return None  # 로고가 홈 상태를 충분히 설명함
    section = rel.parts[0]
    if section == "newsletters":
        return "/newsletters/"
    if section == "morning":
        return "/morning/"
    if section in {"topics", "wiki", "search"}:
        return "/topics/"
    return {
        "cardnews": "/cardnews/",
        "youtube": "/youtube/",
        "school": "/school/",
        "advertise": "/advertise/",
    }.get(section)


# ── 생성 페이지(주제별·검색·엔티티)용 공용 헤더 — 본 사이트와 동일 스타일 ──
NAV_CSS = """
.nav{position:relative;display:flex;justify-content:center;align-items:stretch;overflow:visible;border-bottom:1px solid #222;background:#151515;z-index:100}
.nav>a,.nav-more>summary{display:flex;align-items:center;padding:12px 18px;font-size:13px;font-weight:700;color:#777;white-space:nowrap;text-decoration:none;border:0;border-bottom:2px solid transparent;cursor:pointer;list-style:none;transition:color .2s,border-color .2s,background .2s}
.nav-more>summary::-webkit-details-marker{display:none}
.nav>a:hover,.nav-more>summary:hover{color:#ccc}
.nav>a.active,.nav-more.active>summary{color:#F07040;border-bottom-color:#F07040}
.nav-more{position:relative;flex-shrink:0}
.nav-more[open]>summary{color:#fff;background:#202020}
.nav-menu{position:absolute;top:100%;right:0;z-index:1001;display:grid;min-width:190px;padding:8px;background:#1b1b1b;border:1px solid #333;border-radius:0 0 8px 8px;box-shadow:0 12px 26px rgba(0,0,0,.28)}
.nav-menu a{display:block;padding:10px 12px;border-radius:5px;color:#aaa;text-decoration:none;font-size:13px;font-weight:700;white-space:nowrap}
.nav-menu a:hover,.nav-menu a.active{color:#fff;background:#282828}
.nav-menu a.active{color:#F07040}
.nav-menu a.biz{color:#777;border-top:1px solid #303030;margin-top:4px;padding-top:12px}
@media(max-width:560px){
  .nav{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));width:100%}
  .nav>a,.nav-more>summary{justify-content:center;padding:11px 3px;font-size:12px;letter-spacing:-.2px}
  .nav-more{position:static;min-width:0}
  .nav-menu{left:10px;right:10px;top:100%;grid-template-columns:repeat(2,minmax(0,1fr));min-width:0;padding:8px}
  .nav-menu a{text-align:center;padding:11px 6px}
  .nav-menu a.biz{border-top:0;margin-top:0;padding-top:11px}
}
"""

HEADER_CSS = """
.site-header{padding:26px 20px 18px;border-bottom:1px solid #222;display:flex;justify-content:center;position:relative;background:#111}
.logo-link{display:flex;align-items:center;gap:10px;text-decoration:none;color:#fff}
.logo-link img{height:26px;width:auto}
.logo-text{font-size:22px;font-weight:800;letter-spacing:-0.5px;font-family:'DM Sans','Apple SD Gothic Neo',sans-serif}
.sub-btn-header{position:absolute;right:max(16px,calc(50% - 400px));top:50%;transform:translateY(-50%);
background:#E55A00;color:#fff;padding:8px 18px;border-radius:6px;font-size:13px;font-weight:700;text-decoration:none;white-space:nowrap}
@media(max-width:560px){.sub-btn-header{display:none}}
.crumb{color:#F07040;font-size:.88rem;display:inline-block;margin-bottom:14px;text-decoration:none}
""" + NAV_CSS

FONT_LINK = ('<link rel="preconnect" href="https://fonts.googleapis.com"/>'
             '<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;800&display=swap" rel="stylesheet"/>')


def header_html(active="/topics/"):
    """로고 + 구독하기 + nav 탭(본 사이트 헤더와 동일 구성)."""
    return (
        '<header class="site-header"><a class="logo-link" href="/">'
        '<img src="/favicon.svg" alt="" onerror="this.style.display=\'none\'">'
        '<span class="logo-text">순살브리핑 Soonsal</span></a>'
        '<a href="https://subscribe.soonsal.com/subscribe" target="_blank" rel="noopener" '
        'class="sub-btn-header">구독하기</a></header>'
        + _nav(active))


def main():
    n = 0
    style = f'<style id="soonsal-nav-v2">\n{NAV_CSS.strip()}\n</style>'
    for p in sorted(ROOT.rglob("*.html")):
        if not p.is_file():
            continue
        t = p.read_text(encoding="utf-8")
        if not NAV_RE.search(t):
            continue
        new = NAV_RE.sub(_nav(_active_for(p)), t, count=1)
        if NAV_STYLE_RE.search(new):
            new = NAV_STYLE_RE.sub(style, new, count=1)
        elif "</head>" in new:
            new = new.replace("</head>", style + "\n</head>", 1)
        if new != t:
            p.write_text(new, encoding="utf-8")
            n += 1
    print(f"🧭 nav 동기화: {n}개 페이지")
    return n


if __name__ == "__main__":
    main()
