#!/usr/bin/env python3
"""뉴스레터 목록에 그날 스토리 제목을 작게 덧댄다.

지금은 회차마다 제목 하나뿐이라, 목록에서 무슨 얘기가 있었는지 알 수 없다.
그렇다고 스토리 다섯 개를 같은 크기로 늘어놓으면 목록을 훑는 사람에게
글 폭탄이 된다 (KD 2026-08-15: "text bomb으로 느껴지면 안 되니, 폰트와
디자인을 좀 덜 드러내는 방식으로").

그래서 **덜 드러내는 층**으로 붙인다.
  · 11px · 흐린 회색 · 가운뎃점으로 이어 한 줄
  · 회차 제목보다 작고 연하게 — 훑을 땐 안 보이고 볼 땐 보인다
  · 다섯 개까지만, 넘으면 「+n」
  · 각 제목이 그 스토리 앵커로 바로 간다

재료는 이미 있다 — search/index.json 에 스토리 1,022건이 앵커와 함께 있다.

사용:
  python3 scripts/build_newsletter_nav.py
  python3 scripts/build_newsletter_nav.py --dry
"""

import argparse
import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "newsletters" / "index.html"
STORIES = ROOT / "search" / "index.json"

MAX = 5

CSS = """
<style id="soonsal-issue-stories">
/* 회차 아래 스토리 — 훑을 땐 안 보이고, 보려 하면 보이는 층.
   부모가 grid 라 그냥 넣으면 제목마다 카드가 하나씩 생긴다(=글 폭탄).
   한 칸을 통째로 차지하고, 안쪽 링크는 그리드에서 빼 글줄로 흐르게 한다. */
.issue-stories{grid-column:1/-1;margin:2px 0 0;padding:0;
font-size:11px;line-height:1.75;color:#6b665e;letter-spacing:-.1px;
word-break:keep-all;background:none;border:0}
.issue-stories a{display:inline!important;background:none!important;border:0!important;
padding:0!important;margin:0!important;box-shadow:none!important;
color:inherit;text-decoration:none;font-size:inherit;font-weight:400}
.issue-stories a:hover{color:#F07040}
.issue-stories .sep{opacity:.4;margin:0 5px}
.issue-stories .more{opacity:.55}
@media(max-width:560px){.issue-stories{font-size:10.5px;line-height:1.7}}
</style>
"""


def stories_by_issue() -> dict[str, list[dict]]:
    if not STORIES.is_file():
        return {}
    out = defaultdict(list)
    for s in json.loads(STORIES.read_text(encoding="utf-8")):
        m = re.search(r"/newsletters/(\d{4})/(\d{4})\.html#(\S+)", s.get("u", ""))
        if m:
            out[f"{m.group(1)}/{m.group(2)}"].append(s)
    # 본문 순서(story-1, story-2 …)로 되돌린다
    for k in out:
        out[k].sort(key=lambda s: int(re.search(r"story-(\d+)", s["u"]).group(1))
                    if re.search(r"story-(\d+)", s["u"]) else 99)
    return out


def block(rows: list[dict]) -> str:
    if not rows:
        return ""
    parts = []
    for s in rows[:MAX]:
        parts.append(f'<a href="{html.escape(s["u"])}">{html.escape(s["t"])}</a>')
    more = len(rows) - MAX
    body = '<span class="sep">·</span>'.join(parts)
    if more > 0:
        body += f'<span class="sep">·</span><span class="more">+{more}</span>'
    return f'<div class="issue-stories">{body}</div>'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    if not INDEX.is_file():
        print("  newsletters/index.html 이 없다")
        return 1
    by = stories_by_issue()
    if not by:
        print("  search/index.json 이 없다 — build_search 먼저")
        return 1

    src = INDEX.read_text(encoding="utf-8")
    # 이미 붙어 있으면 통째로 걷어내고 다시 붙인다(회차가 늘어나므로)
    src = re.sub(r'<div class="issue-stories">.*?</div>', "", src, flags=re.S)
    src = re.sub(r'<style id="soonsal-issue-stories">.*?</style>\s*', "", src, flags=re.S)

    added = 0

    def fill(m: re.Match) -> str:
        nonlocal added
        inner, close = m.group(1), m.group(2)
        link = re.search(r'href="/newsletters/(\d{4})/(\d{4})\.html"', inner)
        if not link:
            return inner + close
        rows = by.get(f"{link.group(1)}/{link.group(2)}")
        if not rows:
            return inner + close
        added += 1
        return inner + block(rows) + close

    # today-grid 안쪽에 붙인다. 바깥(.today 밖)에 붙이면 카드 여백을 벗어난다.
    out = re.sub(r'(<div class="today-grid".*?)(</div>)',
                 lambda m: fill(m), src, flags=re.S)
    if "soonsal-issue-stories" not in out and "</head>" in out:
        out = out.replace("</head>", CSS + "</head>", 1)

    print(f"  회차 {added}개에 스토리 줄 추가")
    if a.dry:
        print("  (dry) 쓰지 않음")
        return 0
    INDEX.write_text(out, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
