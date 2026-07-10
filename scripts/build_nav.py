#!/usr/bin/env python3
"""내비게이션 자동 동기화 — 모든 인덱스 페이지의 nav를 한 정의로 통일(자가치유).

nav가 페이지마다 하드코딩돼 있어 최신 페이지만 새 탭을 갖던 문제 → 매 빌드마다
generate_seo가 이 함수를 호출해 전 페이지 nav를 정규형으로 덮어쓴다. deploy.py가
아카이브 인덱스를 재생성하며 옛 nav를 써도 그 직후 여기서 교정된다.

위키는 공개 탭에서 제외(어드민이 entities.json으로 관리). 엔티티 탐색은 주제별 안에서.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 검색=주제별 내 접근, English=숨김. 커뮤니티 탭 제거(텔레그램은 플로팅 버튼 직결).
ITEMS = [("/", "최신"), ("/newsletters/", "뉴스레터"), ("/topics/", "주제별"),
         ("/cardnews/", "카드뉴스"), ("/school/", "스쿨"), ("/youtube/", "YouTube")]

# nav CSS 교정(자가치유). safe center = 데스크톱은 가운데, 넘치면 좌측정렬(첫 탭 안 잘림).
CSS_FIXES = [
    ("display:flex; justify-content:center; gap:0;",
     "display:flex; justify-content:safe center; gap:0;"),
    ("display:flex; justify-content:flex-start; gap:0;",
     "display:flex; justify-content:safe center; gap:0;"),
    ("padding:12px 24px; font-size:13px; font-weight:700; color:#777;",
     "padding:12px 17px; font-size:13px; font-weight:700; color:#777; white-space:nowrap;"),
]

PAGES = {"index.html": "/", "newsletters/index.html": "/newsletters/",
         "cardnews/index.html": "/cardnews/", "english/index.html": "/english/",
         "school/index.html": "/school/", "youtube/index.html": "/youtube/"}

NAV_RE = re.compile(r'<div class="nav">.*?</div>', re.S)


def _nav(active):
    links = "".join(
        f'<a href="{h}"{" class=\"active\"" if h == active else ""}>{l}</a>'
        for h, l in ITEMS)
    return f'<div class="nav">{links}</div>'


# ── 생성 페이지(주제별·검색·엔티티)용 공용 헤더 — 본 사이트와 동일 스타일 ──
HEADER_CSS = """
.site-header{padding:26px 20px 18px;border-bottom:1px solid #222;display:flex;justify-content:center;position:relative;background:#111}
.logo-link{display:flex;align-items:center;gap:10px;text-decoration:none;color:#fff}
.logo-link img{height:26px;width:auto}
.logo-text{font-size:22px;font-weight:800;letter-spacing:-0.5px;font-family:'DM Sans','Apple SD Gothic Neo',sans-serif}
.sub-btn-header{position:absolute;right:max(16px,calc(50% - 400px));top:50%;transform:translateY(-50%);
background:#E55A00;color:#fff;padding:8px 18px;border-radius:6px;font-size:13px;font-weight:700;text-decoration:none;white-space:nowrap}
@media(max-width:560px){.sub-btn-header{display:none}}
.nav{display:flex;justify-content:safe center;gap:0;border-bottom:1px solid #222;background:#151515;
flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch}
.nav a{padding:12px 17px;font-size:13px;font-weight:700;color:#777;white-space:nowrap;text-decoration:none;
border-bottom:2px solid transparent;transition:color .2s,border-color .2s;flex-shrink:0}
.nav a:hover{color:#ccc}
.nav a.active{color:#F07040;border-bottom-color:#F07040}
.crumb{color:#F07040;font-size:.88rem;display:inline-block;margin-bottom:14px;text-decoration:none}
"""

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
    for rel, active in PAGES.items():
        p = ROOT / rel
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        new = NAV_RE.sub(_nav(active), t, count=1)
        for a, b in CSS_FIXES:
            new = new.replace(a, b)
        if new != t:
            p.write_text(new, encoding="utf-8")
            n += 1
    print(f"🧭 nav 동기화: {n}개 페이지")
    return n


if __name__ == "__main__":
    main()
