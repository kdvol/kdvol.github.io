#!/usr/bin/env python3
"""헤더 정렬을 한 벌로 통일한다 — 어느 페이지에서 보든 같아야 한다.

KD 2026-08-15: "각 컴포넌트들의 크기/위치/정렬 상태가 삐뚤빼뚤하고 상당히
미관상 초보자 느낌인데, 정렬 확실히 해줘. 한 페이지에서만 바꾸는 게 아니라,
nav의 어떤 페이지에서 보더라도 동일하게 바뀌어야 함."

**무엇이 삐뚤어졌나**

헤더가 `display:flex; justify-content:center` 로 로고만 가운데 놓고, 검색과
구독은 `position:absolute; top:50%` 로 따로 떠 있었다. 그런데 헤더 패딩이
`26px 20px 18px` 로 위아래가 다르다. 절대위치 버튼은 **박스의 중심**에,
로고는 **패딩 안쪽 중심**에 앉으므로 둘이 4px 어긋난다. 눈에 띄는 그 어긋남이
초보자 느낌의 정체다.

가로도 마찬가지다. 검색은 `right:auto;left:10px`, 구독은 `right:14px` 로
양쪽 여백이 서로 달랐고, 본문 800px 칸과도 맞지 않았다.

**어떻게 고치나**

세 칸 그리드로 바꾼다. 한 축에 셋을 올려놓으면 세로 중심은 저절로 하나가 되고,
좌우 여백은 본문과 같은 `max(16px, 50% - 400px)` 을 쓴다.

  [검색]        [로고]        [구독하기]
   1fr           auto            1fr

칸을 `grid-column` 으로 못 박아 **마크업 순서와 무관**하게 만든다 —
순살차트는 구독이 먼저 오고 나머지는 검색이 먼저인데, 지금까지 그 차이가
그대로 화면에 나왔다.

사용:
  python3 scripts/fix_header_align.py --dry
  python3 scripts/fix_header_align.py
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MARK = "soonsal-header-v2"

# 본문 칸과 같은 좌우 여백. 헤더만 다른 여백을 쓰면 아래 내용과 어긋난다.
GUTTER = "max(16px, calc(50% - 400px))"

CSS = f"""<style id="{MARK}">
/* 헤더 — 한 축에 셋. 세로 중심이 하나여야 어긋나지 않는다 */
.site-header{{position:relative;display:grid;grid-template-columns:1fr auto 1fr;
align-items:center;column-gap:12px;padding:20px {GUTTER};
border-bottom:1px solid #222;background:#111}}
/* 칸과 **행**을 함께 못 박는다. 칸만 정하면 마크업 순서를 거스를 때
   그리드가 다음 줄로 내려보낸다 — 순살차트는 구독이 먼저 와서 검색이
   한 줄 아래(29px)로 떨어졌다. */
.site-header>.search-btn-header{{grid-area:1/1;justify-self:start}}
.site-header>.logo-link{{grid-area:1/2;justify-self:center}}
.site-header>.sub-btn-header{{grid-area:1/3;justify-self:end}}
.site-header>.logo-link{{display:flex;align-items:center;gap:10px;
text-decoration:none;color:#fff}}
.logo-text{{font-size:22px;font-weight:800;letter-spacing:-.5px;line-height:1.1}}

/* 구독 — 이 사이트의 유일한 전환점. 좁은 화면에서도 남는다 */
.sub-btn-header{{position:static;transform:none;display:inline-flex;
align-items:center;background:#E55A00;color:#fff;padding:9px 18px;
border-radius:999px;font-size:13px;font-weight:800;line-height:1;
text-decoration:none;white-space:nowrap;transition:background .18s ease}}
.sub-btn-header:hover{{background:#CC4F00}}

.search-btn-header{{position:static;transform:none;display:flex;
align-items:center;justify-content:center;width:36px;height:36px;
border-radius:999px;color:#8a857c;text-decoration:none;
transition:color .18s ease,background .18s ease}}
.search-btn-header:hover{{color:#fff;background:#1e1e1e}}

@media(max-width:560px){{
  .site-header{{padding:14px 12px;column-gap:8px}}
  .site-header .logo-text{{font-size:18px}}
  .site-header .logo-link img,.site-header .logo-icon{{height:26px}}
  .sub-btn-header{{padding:7px 13px;font-size:11.5px;letter-spacing:-.3px}}
  .search-btn-header{{width:32px;height:32px}}
}}
</style>"""

# 걷어낼 옛 규칙들. 남겨 두면 특정도 싸움이 나서 페이지마다 결과가 갈린다.
KILL = [
    re.compile(r'\.site-header\s*\{[^}]*\}'),
    re.compile(r'\.site-header:has\([^)]*\)[^{]*\{[^}]*\}'),
    re.compile(r'\.sub-btn-header\s*(?::hover)?\s*\{[^}]*\}'),
    re.compile(r'\.search-btn-header\s*(?::hover)?\s*\{[^}]*\}'),
]
# 빈 껍데기만 남은 미디어 쿼리
EMPTY_MEDIA = re.compile(r'@media[^{]*\{\s*\}')
OLD_STYLE = re.compile(rf'<style id="{MARK}">.*?</style>\s*', re.S)


# 인라인 style/onmouseover 는 스타일시트를 무조건 이긴다. 뉴스레터·카드뉴스
# 목록의 구독 버튼이 그래서 혼자 옛 색(#C24A00)에 옛 위치였다. 손으로 쓴
# 페이지에 남은 잔재라 여기서 걷어낸다 — 헤더 요소에 한해서만.
INLINE = re.compile(
    r'(<a[^>]*class="(?:sub-btn-header|search-btn-header|logo-link)"[^>]*?)'
    r'\s(?:style|onmouseover|onmouseout)="[^"]*"')


def strip_inline(html: str) -> str:
    prev = None
    while prev != html:
        prev = html
        html = INLINE.sub(r"\1", html)
    return html


def fix(src: str) -> str | None:
    if "sub-btn-header" not in src:
        return None
    out = strip_inline(src)
    out = OLD_STYLE.sub("", out)          # 다시 돌려도 쌓이지 않게
    for r in KILL:
        out = r.sub("", out)
    for _ in range(3):                    # 중첩 미디어까지 정리
        out = EMPTY_MEDIA.sub("", out)
    if "</head>" not in out:
        return None
    out = out.replace("</head>", CSS + "</head>", 1)
    return out if out != src else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    n = 0
    for p in sorted(ROOT.rglob("*.html")):
        if any(x in p.parts for x in (".git", "node_modules", ".claude")):
            continue
        s = p.read_text(encoding="utf-8", errors="ignore")
        new = fix(s)
        if new is None:
            continue
        if not a.dry:
            p.write_text(new, encoding="utf-8")
        n += 1
    print(f"  헤더 {n}개 페이지 정렬 통일" + ("  (dry)" if a.dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
