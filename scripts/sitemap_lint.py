#!/usr/bin/env python3
"""사이트맵이 「색인해 달라」와 「색인하지 마라」를 동시에 보내지 않는지 본다.

2026-08-17, Search Console 이 「NOINDEX 태그에 의해 제외됨」 문제가 안 풀렸다고
메일을 보냈다. 찾아 보니 사이트맵이 `/advertise/` 를 가리키는데 그 페이지는
**리다이렉트 껍데기**였다. 문의 페이지가 `/collab/` 로 옮겨졌는데
`generate_seo.py` 의 `INDEXES` 목록만 안 고친 것이다.

  사이트맵: 이 주소를 색인해 주세요
  그 페이지: <meta name="robots" content="noindex">

둘이 부딪히면 구글은 색인을 안 하고 **문제로 기록한다.** 그리고 그 상태로
몇 달이 지나도 아무도 모른다 — 주소가 바뀐 건 사람이 기억해야 하는 일이었다.

세 가지를 본다.
  ① 사이트맵에 있는데 noindex 인 페이지
  ② 사이트맵에 있는데 파일이 없는 주소 (404)
  ③ 사이트맵에 있는데 다른 데로 튕기는 페이지 (meta refresh)

사용:
  python3 scripts/sitemap_lint.py        # 어긋난 데가 있으면 종료코드 1
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "sitemap.xml"


def page_for(loc: str) -> Path | None:
    p = loc.lstrip("/")
    for c in (ROOT / p, ROOT / p / "index.html", ROOT / p.rstrip("/") / "index.html"):
        if c.is_file():
            return c
    return None


def main() -> int:
    if not SITEMAP.is_file():
        print("  사이트맵이 없다 — generate_seo.py 를 먼저 돌린다")
        return 1
    sm = SITEMAP.read_text(encoding="utf-8")
    locs = re.findall(r"<loc>https?://soonsal\.com(/[^<]*)</loc>", sm)

    noindex, missing, redirect = [], [], []
    for loc in locs:
        f = page_for(loc)
        if f is None:
            missing.append(loc)
            continue
        head = f.read_text(encoding="utf-8", errors="ignore")[:4000]
        if re.search(r'name="robots"[^>]*noindex', head):
            noindex.append(loc)
        elif re.search(r'http-equiv="refresh"', head):
            redirect.append(loc)

    print(f"═ 사이트맵 {len(locs)}개")
    rows = [("색인하지 말라면서 사이트맵에 넣은 것", noindex),
            ("사이트맵에 있는데 파일이 없는 것", missing),
            ("사이트맵에 있는데 다른 데로 튕기는 것", redirect)]
    broken = 0
    for label, items in rows:
        if items:
            broken += len(items)
            print(f"  ⛔ {label} {len(items)}개")
            for x in items[:8]:
                print(f"     {x}")
        else:
            print(f"  ✅ {label} — 없음")
    if broken:
        print("\n  주소를 옮겼으면 generate_seo.py 의 INDEXES 도 같이 고친다")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
