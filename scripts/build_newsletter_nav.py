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
/* 회차 아래 스토리 — 목록으로 읽히게 한 줄에 하나씩.
   가운뎃점으로 이어 붙이면 줄바꿈이 아무 데서나 일어나 덩어리로 보인다.
   부모가 grid 라 한 칸을 통째로 차지하고, 안쪽은 직접 흐름을 만든다. */
.issue-stories{grid-column:1/-1;margin:7px 0 1px;padding:0;background:none;border:0}
.issue-stories li{list-style:none;margin:0;padding:1px 0 1px 11px;position:relative;
font-size:11.5px;line-height:1.55;color:#6b665e;letter-spacing:-.1px;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.issue-stories li::before{content:"";position:absolute;left:2px;top:9px;
width:3px;height:3px;border-radius:50%;background:currentColor;opacity:.35}
.issue-stories a{display:inline!important;background:none!important;border:0!important;
padding:0!important;margin:0!important;box-shadow:none!important;
color:inherit;text-decoration:none;font-size:inherit;font-weight:400}
.issue-stories a:hover{color:#F07040}
.issue-stories .more{opacity:.5;padding-left:11px;font-size:11px;color:#6b665e}
@media(max-width:560px){.issue-stories li{font-size:11px}}
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
    """한 줄에 하나씩. 가운뎃점으로 이어 붙이면 덩어리로 읽힌다.

    KD 2026-08-15: "줄별로 잘 정돈되게 보여줘. 그냥 나열하지 말고."
    가운뎃점 방식은 줄바꿈이 아무 데서나 일어나 문단처럼 보였다.
    """
    if not rows:
        return ""
    items = "".join(
        f'<li><a href="{html.escape(s["u"])}">{html.escape(s["t"])}</a></li>'
        for s in rows[:MAX])
    more = len(rows) - MAX
    tail = f'<li class="more">외 {more}편</li>' if more > 0 else ""
    return f'<ul class="issue-stories">{items}{tail}</ul>'


def issues_in_page(src: str) -> list[str]:
    """목록 페이지에 실린 회차를 **최신부터** 돌려준다.

    페이지가 최신순이라 나온 순서를 그대로 쓴다. 중복은 첫 번째만 남긴다.
    """
    out, seen = [], set()
    for y, m in re.findall(r'href="/newsletters/(\d{4})/(\d{4})\.html"', src):
        k = f"{y}/{m}"
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out



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
    src = re.sub(r'<ul class="issue-stories">.*?</ul>', "", src, flags=re.S)
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

    # ── 안 붙은 회차를 **말한다** (KD 2026-08-19) ────────────────────
    #   *"만들고 누락되는 규칙 없도록 철저히 기존 시스템과 연결"*
    #
    #   8/19 목록에 그날 스토리가 안 붙어 있었다. 빌더는 정상 종료했다 —
    #   색인에 그 회차가 아직 없으면 `if not rows: return` 으로 **조용히
    #   건너뛰기** 때문이다. 붙은 개수만 세니 안 붙은 건 안 보였다.
    #
    #   순서 문제라서 더 나쁘다. `build_search` 가 색인을 새로 쓰기 전에
    #   이 빌더가 돌면 **늘 최신 회차만 빠진다** — 그리고 그게 제일 중요한
    #   회차다. 그래서 최신 회차가 빠지면 **실패로 끝낸다.**
    missing = [d for d in issues_in_page(src) if not by.get(d)]
    print(f"  회차 {added}개에 스토리 줄 추가")
    if missing:
        print(f"  ⚠️ 스토리를 못 찾은 회차 {len(missing)}개: {', '.join(missing[:5])}"
              + (" …" if len(missing) > 5 else ""))
    newest = (issues_in_page(src) or [None])[0]
    if newest and newest in set(missing):
        print(f"  ⛔ 최신 회차 {newest} 에 스토리가 안 붙는다 — 색인이 아직 그 회차를 모른다.\n"
              f"     python3 scripts/build_search.py 를 먼저 돌린 뒤 다시 부른다")
        return 2
    if a.dry:
        print("  (dry) 쓰지 않음")
        return 0
    INDEX.write_text(out, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
