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

# 주제별은 탭에서 뺐다. 검색과 하는 일이 같은데(찾기) 탭 한 칸을 차지했고,
# /search/ 안에 이미 주제 입구가 18개 있다. 돋보기 하나로 합친다.
CORE_ITEMS = [("/newsletters/", "뉴스레터"), ("/chart/", "순살차트"),
              ("/talk/", "순살톡")]
DESKTOP_ITEMS = [("/school/", "스쿨"), ("/collab/", "협업 문의")]
MENU_ITEMS = [("/topics/", "주제별"), ("/saved/", "내가 모은 글"), ("/cardnews/", "카드뉴스"),
              ("/youtube/", "YouTube")]
MORE_ITEMS = MENU_ITEMS + DESKTOP_ITEMS
BIZ = {"/collab/"}

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
    if section in {"chart", "morning"}:
        return "/chart/"
    if section in {"topics", "wiki", "search"}:
        return "/topics/"
    return {
        "saved": "/saved/",
        "cardnews": "/cardnews/",
        "youtube": "/youtube/",
        "school": "/school/",
        "advertise": "/collab/",
        "collab": "/collab/",
        "talk": "/talk/",
    }.get(section)


# ── 생성 페이지(주제별·검색·엔티티)용 공용 헤더 — 본 사이트와 동일 스타일 ──
SEARCH_CSS = """
/* 헤더 — 한 축에 셋. 세로 중심이 하나여야 어긋나지 않는다 */
.site-header{position:relative;display:grid;grid-template-columns:1fr auto 1fr;
align-items:center;column-gap:12px;padding:20px max(16px, calc(50% - 400px));
border-bottom:1px solid #222;background:#111}
/* 칸을 못 박아 마크업 순서와 무관하게 만든다 */
.site-header>.search-btn-header{grid-area:1/1;justify-self:start}
.site-header>.logo-link{grid-area:1/2;justify-self:center}
.site-header>.sub-btn-header{grid-area:1/3;justify-self:end}
.site-header>.logo-link{display:flex;align-items:center;gap:10px;
text-decoration:none;color:#fff}
.logo-text{font-size:22px;font-weight:800;letter-spacing:-.5px;line-height:1.1}

/* 구독 — 이 사이트의 유일한 전환점. 좁은 화면에서도 남는다 */
.sub-btn-header{position:static;transform:none;display:inline-flex;
align-items:center;background:#E55A00;color:#fff;padding:9px 18px;
border-radius:999px;font-size:13px;font-weight:800;line-height:1;
text-decoration:none;white-space:nowrap;transition:background .18s ease}
.sub-btn-header:hover{background:#CC4F00}

.search-btn-header{position:static;transform:none;display:flex;
align-items:center;justify-content:center;width:36px;height:36px;
border-radius:999px;color:#8a857c;text-decoration:none;
transition:color .18s ease,background .18s ease}
.search-btn-header:hover{color:#fff;background:#1e1e1e}

@media(max-width:560px){
  .site-header{padding:14px 12px;column-gap:8px}
  .site-header .logo-text{font-size:18px}
  .site-header .logo-link img,.site-header .logo-icon{height:26px}
  .sub-btn-header{padding:7px 13px;font-size:11.5px;letter-spacing:-.3px}
  .search-btn-header{width:32px;height:32px}
}





/* 구독하기가 있는 페이지에서는 그 왼쪽으로 비켜 앉는다 */


"""
SEARCH_STYLE_RE = re.compile(r'<style id="soonsal-search-v1">.*?</style>', re.S)

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
  /* 칸 수는 항목 수를 따라간다 — 정의 뒤에서 CORE_ITEMS로 채운다 */
  .nav{display:grid;grid-template-columns:repeat(%%NAVCOLS%%,minmax(0,1fr));width:100%}
  .nav>a,.nav-more>summary{justify-content:center;padding:11px 2px;font-size:11.5px;
  letter-spacing:-.4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .nav-more{position:static;min-width:0}
  .nav-menu{left:10px;right:10px;top:100%;grid-template-columns:repeat(2,minmax(0,1fr));min-width:0;padding:8px}
  .nav-menu a{text-align:center;padding:11px 6px}
  .nav-menu a.biz{border-top:0;margin-top:0;padding-top:11px}
}
@media(max-width:360px){
  .nav>a,.nav-more>summary{font-size:10.5px;letter-spacing:-.5px;padding:11px 1px}
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
  /* 코어 4개 + 더보기 = 5칸. 예전 CSS가 4칸이라 다섯 번째가 다음 줄로 넘어갔다.
     이 블록은 페이지마다 나중에 주입되므로 안에 박힌 옛 규칙을 덮는다. */
  .nav{display:grid;grid-template-columns:repeat(%%NAVCOLS%%,minmax(0,1fr));width:100%}
  .nav>a,.nav-more>summary{justify-content:center;padding:11px 2px;font-size:11.5px;
    letter-spacing:-.4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
}
@media(max-width:360px){
  .nav>a,.nav-more>summary{font-size:10.5px;letter-spacing:-.5px;padding:11px 1px}
}
/* ── 눌러보고 싶게 ──────────────────────────────────────
   탭은 '지금 어디' 말고는 아무것도 알려주지 않는다. 더보기는 특히 그렇다 —
   안에 뭐가 있는지 모르면 누를 이유가 없다. 세 가지를 바꾼다:
   (1) 밑줄이 자라며 눌리는 느낌, (2) 화살표가 열림에 반응, (3) 메뉴 안에
   아이콘을 붙여 목록이 아니라 '갈 곳'으로 보이게. */
.nav>a,.nav-more>summary{position:relative;transition:color .18s}
.nav>a:after,.nav-more>summary:after{content:"";position:absolute;left:50%;right:50%;
bottom:-1px;height:2px;background:#F07040;border-radius:2px;
transition:left .22s cubic-bezier(.4,0,.2,1),right .22s cubic-bezier(.4,0,.2,1)}
.nav>a:hover:after,.nav-more>summary:hover:after{left:18%;right:18%}
.nav>a.active:after,.nav-more.active>summary:after{left:0;right:0}

.nav-more>summary span[aria-hidden]{display:inline-block;transition:transform .22s ease;
margin-left:2px}
.nav-more[open]>summary span[aria-hidden]{transform:rotate(180deg)}
.nav-more[open]>summary{color:#F07040}

.nav-menu{animation:navdrop .18s cubic-bezier(.2,.8,.2,1)}
@keyframes navdrop{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
.nav-menu a{transition:background .15s,color .15s,padding-left .15s}
.nav-menu a:before{margin-right:7px;opacity:.9}
.nav-menu a[href="/cardnews/"]:before{content:"🎴"}
.nav-menu a[href="/youtube/"]:before{content:"▶"}
.nav-menu a[href="/school/"]:before{content:"🎓"}
.nav-menu a[href="/collab/"]:before{content:"✉"}
.nav-menu a[href="/talk/"]:before{content:"💬"}

/* 더보기 안에 뭐가 있는지 한 줄로 알려준다 — 열기 전에 궁금해지는 건 이 지점이다 */
.nav-more>summary:before{content:"";position:absolute;top:9px;right:6px;width:5px;height:5px;
border-radius:50%;background:#F07040;opacity:0;transition:opacity .2s}
.nav-more:not([open])>summary:hover:before{opacity:.85}
@media(max-width:560px){
  .nav-menu a{text-align:left;padding-left:14px}
  .nav-more>summary:before{right:3px;top:7px}
}
"""

# 칸 수를 고정값으로 두면 항목이 줄었을 때(주제별을 뺐다) 빈 칸이 남아
# nav가 왼쪽으로 쏠린다. 코어 항목 + 더보기 개수로 채운다.
def _fill_cols(css):
    return css.replace("%%NAVCOLS%%", str(len(CORE_ITEMS) + 1))

NAV_CSS = _fill_cols(NAV_CSS)
NAV_ENHANCEMENT_CSS = _fill_cols(NAV_ENHANCEMENT_CSS)


# ── 섹션 머리 ────────────────────────────────────────────────
# 섹션마다 제목 구성이 달랐다. 킥커가 있는 곳과 없는 곳이 섞였고,
# 말투도 "여기 모입니다"(합쇼체)와 "바로 봄"(음슴체)이 같이 있었다.
# 제목은 nav 라벨을 그대로 쓴다 — /saved/ 는 nav 가 "내가 모은 글"인데
# 페이지만 "내가 모은 스토리"였다.
#
# 두 종류를 구분한다:
#   아카이브·도구 — 킥커 + 짧은 이름 + 한 줄
#   랜딩(스쿨·유튜브·협업) — 킥커에 섹션명, 제목은 문장형
# 설명은 전부 음슴체로 맞춘다. 본문이 음슴체인데 섹션 설명만 합쇼체면
# 같은 사이트로 안 읽힌다.
SECTION_HEAD = {
    "/chart/":      ("날짜별 시장 정리", "순살차트", "날짜를 고르고, 궁금한 주제부터 바로 봄"),
    "/talk/":       ("독자들이 남긴 한 줄", "순살톡", "브리핑을 읽다 남긴 한마디가 회차 상관없이 여기 모임"),
    "/saved/":      ("이 브라우저에만 저장됨", "내가 모은 글", "반응을 남기거나 한마디를 쓴 스토리가 여기 쌓임"),
    "/search/":     ("전체에서 찾기", "검색", "제목·주제·등장 대상으로 브리핑을 찾음"),
    "/topics/":     ("주제로 모아보기", "주제별", "스토리를 주제·기업·인물로 묶어 둠"),
    "/newsletters/":("매일 아침 배달", "뉴스레터", "밤새 시장에서 일어난 일을 아침에 한 번에 봄"),
    "/cardnews/":   ("인스타에 올라간 것", "카드뉴스", "한 장씩 넘겨 보는 순살, 여기 다 모아 둠"),
}

SECTION_CSS = """
.sec-head{margin:0 0 26px}
.sec-kicker{display:flex;align-items:center;gap:9px;margin:0 0 12px;color:#F59B75;
font-size:11px;font-weight:800;letter-spacing:.08em}
.sec-kicker::before{content:"";width:22px;height:2px;background:#F07040;border-radius:2px;flex:0 0 auto}
.sec-head h1{margin:0;font-size:1.62rem;font-weight:800;letter-spacing:-.03em;
line-height:1.25;color:#fff;word-break:keep-all}
.sec-head .deck{margin:10px 0 0;color:#8b8578;font-size:.92rem;line-height:1.65;word-break:keep-all}
@media(max-width:560px){.sec-head h1{font-size:1.42rem}}
"""


def section_head(path: str, deck: str | None = None, extra: str = "") -> str:
    """섹션 머리를 한 모양으로 낸다. 없는 경로면 빈 문자열."""
    item = SECTION_HEAD.get(path)
    if not item:
        return ""
    kicker, title, default_deck = item
    text = deck or default_deck
    return (f'<div class="sec-head"><div class="sec-kicker">{kicker}</div>'
            f'<h1>{title}{extra}</h1><p class="deck">{text}</p></div>')


HEADER_CSS = """

.logo-link{display:flex;align-items:center;gap:10px;text-decoration:none;color:#fff}
/* 로고 마크 크기는 여기 한 곳에서만 정한다. 26px는 파비콘처럼 묻히고
   36px는 22px 워드마크를 눌러 헤더가 위로 무거워진다. 32px가 그 사이다. */
.logo-link img,.logo-icon{height:32px;width:auto}
.logo-text{font-size:22px;font-weight:800;letter-spacing:-0.5px;font-family:'DM Sans','Apple SD Gothic Neo',sans-serif}



.crumb{color:#F07040;font-size:.88rem;display:inline-block;margin-bottom:14px;text-decoration:none}
""" + SEARCH_CSS + NAV_CSS + SECTION_CSS

# 아이콘 선언이 아예 없어서 브라우저가 관례로 /favicon.ico 만 집어갔다.
# SVG 를 선언해야 또렷하게 나오고, 그 안에서 다크모드 전환도 된다.
ICON_LINKS = ('<link rel="icon" href="/favicon.svg" type="image/svg+xml"/>'
              '<link rel="icon" href="/favicon.ico" sizes="any"/>'
              '<link rel="apple-touch-icon" href="/apple-touch-icon.png"/>')

FONT_LINK = ('<link rel="preconnect" href="https://fonts.googleapis.com"/>'
             '<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;800&display=swap" rel="stylesheet"/>')


SUB_BTN = ('<a href="https://subscribe.soonsal.com/subscribe" target="_blank" '
           'rel="noopener" class="sub-btn-header">구독하기</a>')

SEARCH_BTN = (
    '<a href="/search/" class="search-btn-header" aria-label="검색">'
    '<svg viewBox="0 0 24 24" width="19" height="19" fill="none" '
    'stroke="currentColor" stroke-width="2.1" stroke-linecap="round" aria-hidden="true">'
    '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.6-3.6"/></svg></a>')

# 홈·뉴스레터는 자기 헤더를 갖고 있다(생성 페이지가 아니다). 여는 태그 바로
# 뒤에 버튼을 넣는다. position:absolute라 헤더에 position이 있어야 한다.
HEADER_OPEN_RE = re.compile(r'<(div|header)([^>]*)class="site-header"([^>]*)>')


NAV_COLS_RE = re.compile(
    r'(\.nav\{display:grid;grid-template-columns:repeat\()\d+(,minmax\(0,1fr\)\);width:100%\})')


def _fix_nav_cols(html: str) -> str:
    return NAV_COLS_RE.sub(rf'\g<1>{len(CORE_ITEMS) + 1}\g<2>', html)


LOGO_SIZE = 32
# favicon.svg는 라운드 사각 타일에 여백이 든 앱 아이콘이라 헤더에 넣으면
# 같은 px에서도 마크가 작아 보인다. 헤더에는 여백 없는 순수 마크를 쓴다.
# soonsal-logo.png는 검은 마크(밝은 배경용)다. 헤더는 #111이라 거기 넣으면
# 로고가 통째로 묻힌다. 헤더에는 흰 마크를 쓴다.
LOGO_SRC = "/assets/soonsal-logo-white.png"
LOGO_SRC_RE = re.compile(
    r'(<img\s+src=")(?:/favicon\.svg|/assets/soonsal-logo\.png|data:image/[^"]+)'
    r'("[^>]*\bclass="logo-icon"|"[^>]*>(?=<span class="logo-text"))')
# 손으로 만든 헤더에 박힌 값은 여기서 다시 맞춘다. 그러지 않으면
# 페이지마다 로고가 다른 크기로 보인다 — 실제로 26px와 36px가 섞여 있었다.
# width:auto가 붙은 규칙만 건드린다. 카드뉴스 본문 안의 .logo-icon은
# 22px 정사각(width도 고정)이고 헤더 로고가 아니다.
LOGO_H_RE = re.compile(
    r'(\.logo-(?:link img|icon)[^{}]*{[^}]*?height:\s*)\d+(px)(?=[^}]*width:\s*auto)'
    r'|(\.logo-(?:link img|icon)[^{}]*{[^}]*?width:\s*auto[^}]*?height:\s*)\d+(px)', re.I)


ICON_RE = re.compile(r'<link[^>]+rel="(?:icon|apple-touch-icon)"[^>]*>')


def _with_icons(html: str) -> str:
    """탭 아이콘을 선언한다.

    선언이 없으면 브라우저가 관례로 /favicon.ico 만 집어간다. SVG 를 선언해야
    또렷하게 나오고, 그 SVG 안의 media query 로 다크모드 전환도 된다.
    """
    if "</head>" not in html:
        return html
    stripped = ICON_RE.sub("", html)
    i = stripped.index("</head>")
    return stripped[:i] + ICON_LINKS + stripped[i:]


def _fix_logo_src(html: str) -> str:
    return LOGO_SRC_RE.sub(rf'\g<1>{LOGO_SRC}\g<2>', html)


def _fix_logo_size(html: str) -> str:
    return LOGO_H_RE.sub(
        lambda m: f"{m.group(1) or m.group(3)}{LOGO_SIZE}{m.group(2) or m.group(4)}",
        html)


TICKER_FILE = Path(__file__).resolve().parent / "_ticker.html"
TICKER_RE = re.compile(r'<div id="soonsal-live-ticker".*?</script>', re.S)


# 이 두 페이지는 생성 스크립트가 따로 없고 손으로 쓴 HTML이다. 그래서
# 섹션 머리가 <div> 킥커 하나뿐이었고 h1 도 설명도 없었다. nav 후처리를
# 매번 거치므로 여기서 표준 머리로 바꿔 둔다.
LEGACY_KICKER_RE = re.compile(
    r'<div style="font-size:11px;\s*font-weight:700;\s*color:#F07040;[^"]*"[^>]*>'
    r'\s*[^<]*?</div>', re.S)


def _with_section_head(html: str, path: str) -> str:
    head = section_head(path)
    if not head:
        return html
    new = html
    if 'class="sec-head"' not in new:
        new, count = LEGACY_KICKER_RE.subn(lambda _: head, new, count=1)
        if not count:
            return html
    # 손으로 쓴 페이지에는 섹션 머리 CSS가 없다. 마크업만 넣으면 h1 이
    # 브라우저 기본값(32px)으로 뜬다 — 스타일도 같이 넣는다.
    if ".sec-kicker{" not in new and "</head>" in new:
        new = new.replace("</head>", f'<style id="soonsal-sec-head">{SECTION_CSS}</style>\n</head>', 1)
    return new


def _with_ticker(html: str) -> str:
    """상단 시황 띠를 헤더 있는 모든 페이지에 보장한다."""
    if not TICKER_FILE.exists() or "<body" not in html:
        return html
    block = TICKER_FILE.read_text(encoding="utf-8")
    # 자리를 차지하는 sticky 라서 DOM 위치가 곧 화면 위치다. 예전에 문서
    # 끝에 붙은 페이지들이 있었는데(fixed 일 땐 안 보이던 문제다) 띠가
    # 페이지 맨 아래에 깔렸다. 있던 걸 걷어내고 <body> 직후로 다시 놓는다.
    html = TICKER_RE.sub("", html, count=1)
    i = html.index("<body")
    j = html.index(">", i) + 1
    return html[:j] + "\n" + block + html[j:]


def _with_subscribe(html: str) -> str:
    """구독하기 버튼을 헤더에 보장한다. 페이지마다 자리가 달라지면 안 된다."""
    if 'class="sub-btn-header"' in html:
        return html
    m = HEADER_OPEN_RE.search(html)
    if not m:
        return html
    # 여는 태그 바로 뒤에 넣는다(절대 위치라 순서는 화면에 영향 없다)
    return html[:m.end()] + SUB_BTN + html[m.end():]


def _with_search(html: str) -> str:
    # 스타일은 마크업과 늘 같이 간다. 한쪽만 들어가면 로고 옆에 덩그러니 붙는다.
    style = f'<style id="soonsal-search-v1">\n{SEARCH_CSS.strip()}\n</style>'
    if SEARCH_STYLE_RE.search(html):
        html = SEARCH_STYLE_RE.sub(style, html, count=1)
    elif "search-btn-header{position:absolute" not in html.replace("\n", "") \
            and "</head>" in html:
        html = html.replace("</head>", style + "\n</head>", 1)
    if 'class="search-btn-header"' in html:
        return html
    m = HEADER_OPEN_RE.search(html)
    if not m:
        return html
    tag = m.group(0)
    if 'position:relative' not in tag:
        tag = tag[:-1] + ' style="position:relative">' if 'style="' not in tag \
              else tag.replace('style="', 'style="position:relative;', 1)
    return html[:m.start()] + tag + SEARCH_BTN + html[m.end():]


def header_html(active="/topics/"):
    """로고 + 구독하기 + nav 탭(본 사이트 헤더와 동일 구성)."""
    return (
        '<header class="site-header">' + SEARCH_BTN +
        '<a class="logo-link" href="/">'
        f'<img src="{LOGO_SRC}" alt="" onerror="this.style.display=\'none\'">'
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
            only = _with_ticker(t)
            if only != t:
                p.write_text(only, encoding="utf-8")
                n += 1
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
        new = _with_search(new)
        new = _with_subscribe(new)
        new = _with_ticker(new)
        new = _fix_nav_cols(new)
        new = _fix_logo_size(new)
        new = _fix_logo_src(new)
        new = _with_icons(new)
        own = "/" + p.relative_to(ROOT).parts[0] + "/"
        new = _with_section_head(new, own)
        if new != t:
            p.write_text(new, encoding="utf-8")
            n += 1
    print(f"🧭 nav 동기화: {n}개 페이지")
    return n


if __name__ == "__main__":
    main()
