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

CORE_ITEMS = [("/newsletters/", "브리핑"), ("/morning/", "모닝순살"),
              ("/talk/", "순살톡"), ("/topics/", "주제별")]
DESKTOP_ITEMS = [("/school/", "스쿨"), ("/advertise/", "광고 문의")]
MENU_ITEMS = [("/cardnews/", "카드뉴스"), ("/youtube/", "YouTube")]
MORE_ITEMS = MENU_ITEMS + DESKTOP_ITEMS
BIZ = {"/advertise/"}

NAV_RE = re.compile(r'<(?:div|nav)\s+class="nav"(?:\s[^>]*)?>.*?</(?:div|nav)>', re.S)
NAV_STYLE_RE = re.compile(r'<style id="soonsal-nav-v2">.*?</style>', re.S)
NAV_ENHANCEMENT_RE = re.compile(r'<style id="soonsal-nav-visibility-v3">.*?</style>', re.S)
NAV_CSS_PRESENT_RE = re.compile(r'\.nav-more\s*>\s*summary')


def _nav(active):
    def cls(h, *extra):
        c = list(extra) + (["active"] if h == active else []) + (["biz"] if h in BIZ else [])
        return f' class="{" ".join(c)}"' if c else ""
    core = "".join(f'<a href="{h}"{cls(h)}>{l}</a>' for h, l in CORE_ITEMS)
    desktop = "".join(f'<a href="{h}"{cls(h, "nav-desktop-link")}>{l}</a>'
                      for h, l in DESKTOP_ITEMS)
    menu_hrefs = {href for href, _label in MENU_ITEMS}
    desktop_hrefs = {href for href, _label in DESKTOP_ITEMS}
    more_classes = ["nav-more"]
    if active in menu_hrefs:
        more_classes.append("active")
    if active in desktop_hrefs:
        more_classes.append("mobile-active")
    more_cls = f' class="{" ".join(more_classes)}"'
    more = "".join(
        f'<a href="{h}"{cls(h, "nav-mobile-only") if h in desktop_hrefs else cls(h)}>{l}</a>'
        for h, l in MORE_ITEMS)
    return (
        '<nav class="nav" aria-label="주요 메뉴">' + core + desktop
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
        "talk": "/talk/",
    }.get(section)


# ── 생성 페이지(주제별·검색·엔티티)용 공용 헤더 — 본 사이트와 동일 스타일 ──
NAV_CSS = """
.nav{position:relative;display:flex;justify-content:center;align-items:stretch;overflow:visible;border-bottom:1px solid #222;background:#151515;z-index:100}
.nav>a,.nav-more>summary{display:flex;align-items:center;padding:12px 18px;font-size:13px;font-weight:700;color:#777;white-space:nowrap;text-decoration:none;border:0;border-bottom:2px solid transparent;cursor:pointer;list-style:none;transition:color .2s,border-color .2s,background .2s}
.nav-more>summary::-webkit-details-marker{display:none}
.nav>a:hover,.nav-more>summary:hover{color:#ccc}
.nav>a.active,.nav-more.active>summary{color:#F07040;border-bottom-color:#F07040}
/* 데스크톱/모바일 갈래. 이 두 규칙이 없어서 스쿨·광고 문의가 바와 더보기에
   이중으로 렌더됐고, 가로 스크롤 위치에 따라 보이는 항목이 달라졌다. */
.nav-mobile-only{display:none}
.nav-more{position:relative;flex-shrink:0}
.nav-more[open]>summary{color:#fff;background:#202020}
.nav-menu{position:absolute;top:100%;right:0;z-index:1001;display:grid;min-width:190px;padding:8px;background:#1b1b1b;border:1px solid #333;border-radius:0 0 8px 8px;box-shadow:0 12px 26px rgba(0,0,0,.28)}
.nav-menu a{display:block;padding:10px 12px;border-radius:5px;color:#aaa;text-decoration:none;font-size:13px;font-weight:700;white-space:nowrap}
.nav-menu a:hover,.nav-menu a.active{color:#fff;background:#282828}
.nav-menu a.active{color:#F07040}
.nav-menu a.biz{color:#777;border-top:1px solid #303030;margin-top:4px;padding-top:12px}
@media(max-width:560px){
.nav>a.nav-desktop-link{display:none}
.nav-menu a.nav-mobile-only{display:block}
  .nav{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));width:100%}
  .nav>a,.nav-more>summary{justify-content:center;padding:11px 3px;font-size:12px;letter-spacing:-.2px}
  .nav-more{position:static;min-width:0}
  .nav-menu{left:10px;right:10px;top:100%;grid-template-columns:repeat(2,minmax(0,1fr));min-width:0;padding:8px}
  .nav-menu a{text-align:center;padding:11px 6px}
  .nav-menu a.biz{border-top:0;margin-top:0;padding-top:11px}
}
"""

NAV_ENHANCEMENT_CSS = """
.nav-menu a.nav-mobile-only{display:none}
.nav>a.nav-desktop-link.biz{color:#F07040}
.nav>a.nav-desktop-link.biz:hover{color:#ff8a52}
.nav-menu a.biz{color:#F07040}
@media(max-width:560px){
  .nav>a.nav-desktop-link{display:none}
  .nav-menu a.nav-mobile-only{display:block}
  .nav-more.mobile-active>summary{color:#F07040;border-bottom-color:#F07040}
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
    enhancement = (f'<style id="soonsal-nav-visibility-v3">\n'
                   f'{NAV_ENHANCEMENT_CSS.strip()}\n</style>')
    for p in sorted(ROOT.rglob("*.html")):
        if not p.is_file():
            continue
        t = p.read_text(encoding="utf-8")
        if not NAV_RE.search(t):
            continue
        new = NAV_RE.sub(_nav(_active_for(p)), t, count=1)
        if NAV_STYLE_RE.search(new):
            new = NAV_STYLE_RE.sub(style, new, count=1)
        elif not NAV_CSS_PRESENT_RE.search(new) and "</head>" in new:
            new = new.replace("</head>", style + "\n</head>", 1)
        if NAV_ENHANCEMENT_RE.search(new):
            new = NAV_ENHANCEMENT_RE.sub(enhancement, new, count=1)
        elif "</head>" in new:
            new = new.replace("</head>", enhancement + "\n</head>", 1)
        if new != t:
            p.write_text(new, encoding="utf-8")
            n += 1
    print(f"🧭 nav 동기화: {n}개 페이지")
    return n


if __name__ == "__main__":
    main()
