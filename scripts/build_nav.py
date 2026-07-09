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

# 검색=주제별 내 접근, 커뮤니티=플로팅 버튼(build_fab)으로 이동, English=숨김.
# 남는 건 실제 콘텐츠 탭만 — 모바일 간결성 우선.
ITEMS = [("/", "최신"), ("/newsletters/", "뉴스레터"), ("/topics/", "주제별"),
         ("/cardnews/", "카드뉴스"), ("/school/", "스쿨"), ("/youtube/", "YouTube")]

# nav CSS 모바일 교정(자가치유) — 시그니처가 유니크해 안전하게 치환.
CSS_FIXES = [
    ("display:flex; justify-content:center; gap:0;",
     "display:flex; justify-content:flex-start; gap:0;"),   # 첫 탭 잘림 방지(좌측 정렬)
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
