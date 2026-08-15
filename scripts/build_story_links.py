#!/usr/bin/env python3
"""뉴스레터 스토리 끝에 「이 이야기에 나온 것 / 같은 흐름」을 붙인다.

재료는 이미 다 있다 — 엔티티 152개, 위키 142장, 스토리 색인 1,022건.
없는 건 연결뿐이다. 0814 한 편에만 엔티티가 24개 나오는데 위키를 가리키는
링크는 1개였다.

**본문 안에 인라인으로 깔지 않는다** (KD 2026-08-15: 가독성 유지).
24개를 문단에 박으면 읽을 수가 없고, 뉴스레터는 이메일 원본이라 링크가
많으면 스팸 판정 위험도 오른다. 나무위키는 찾아보러 온 사람의 구조고
뉴스레터는 읽으러 온 사람이 본다.

그래서 **스토리를 다 읽은 자리**에 두 줄로 단다.
  이 이야기에 나온 것 →  메타 · 저커버그 · 오픈AI      (최대 5개, 등장 순)
  같은 흐름 →  8/12 「AI 크레딧이 완전 뒤바뀐 거 봤어?」  (최대 2개)

「같은 흐름」이 실은 더 중요하다. 엔티티 페이지보다 **다른 회차로 보내는 것**이
체류를 늘린다. 그게 연재처럼 읽히게 만드는 장치이기도 하다.

사용:
  python3 scripts/build_story_links.py --issue 0814
  python3 scripts/build_story_links.py --all --dry
"""

import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTITIES = ROOT / "scripts" / "entities.json"
STORIES = ROOT / "search" / "index.json"

MAX_ENT = 5
MAX_REL = 2

CSS = """
<style id="soonsal-story-links">
/* 스토리 끝 — 다 읽은 사람만 본다. 본문 흐름을 끊지 않는다 */
.story-links{margin:14px 0 0;padding:11px 0 0;border-top:1px solid #ece8e0;
font-size:11.5px;line-height:1.8;color:#9a958a;word-break:keep-all}
.story-links .k{color:#b5b0a4;margin-right:5px}
.story-links a{color:#8a857c;text-decoration:none;border-bottom:1px solid #e6e1d8}
.story-links a:hover{color:#C24A00;border-bottom-color:#C24A00}
.story-links .sep{opacity:.4;margin:0 4px}
.story-links .row + .row{margin-top:3px}
</style>
"""


def entities() -> list[dict]:
    if not ENTITIES.is_file():
        return []
    d = json.loads(ENTITIES.read_text(encoding="utf-8"))
    return d.get("entities", d) if isinstance(d, dict) else d


def stories() -> list[dict]:
    return json.loads(STORIES.read_text(encoding="utf-8")) if STORIES.is_file() else []


def wiki_exists(slug: str) -> bool:
    return (ROOT / "wiki" / f"{slug}.html").is_file()


def found_in(text: str, ents: list[dict]) -> list[tuple[int, dict]]:
    """본문에 나온 엔티티를 등장 순으로. 위키 페이지가 있는 것만.

    이름으로 부분일치를 하면 오탐이 난다 — `금지`에서 `금`(gold)이 잡혔다.
    entities.json 의 pattern 이 그 문제를 이미 풀어 뒀다(`금값|금 선물|온스당`).
    """
    hits = []
    for e in ents:
        if not wiki_exists(e["slug"]):
            continue
        pat = e.get("pattern") or re.escape(e.get("name") or "")
        if not pat:
            continue
        try:
            m = re.search(pat, text)
        except re.error:
            continue
        if m:
            hits.append((m.start(), e))
    hits.sort(key=lambda x: x[0])
    return hits[:MAX_ENT]


def related(title: str, issue: str, all_stories: list[dict]) -> list[dict]:
    """같은 흐름 — 제목이 겹치는 지난 스토리. 같은 회차는 뺀다."""
    def bg(t):
        t = "".join(c for c in t if c.isalnum())
        return {t[i:i + 2] for i in range(len(t) - 1)}
    want = bg(title)
    if not want:
        return []
    scored = []
    for s in all_stories:
        if issue in s.get("u", ""):
            continue
        have = bg(s.get("t", ""))
        if not have:
            continue
        score = len(want & have) / min(len(want), len(have))
        if score >= 0.30:
            scored.append((score, s))
    scored.sort(key=lambda x: (-x[0], x[1].get("d", "")))
    return [s for _, s in scored[:MAX_REL]]


def block(ents: list[tuple[int, dict]], rel: list[dict]) -> str:
    rows = []
    if ents:
        links = '<span class="sep">·</span>'.join(
            f'<a href="/wiki/{e["slug"]}.html">{html.escape(e.get("name",""))}</a>'
            for _, e in ents)
        rows.append(f'<div class="row"><span class="k">이 이야기에 나온 것</span>{links}</div>')
    if rel:
        links = '<span class="sep">·</span>'.join(
            f'<a href="{html.escape(s["u"])}">{html.escape(s.get("d","")[5:])} '
            f'{html.escape(s.get("t",""))[:26]}</a>' for s in rel)
        rows.append(f'<div class="row"><span class="k">같은 흐름</span>{links}</div>')
    return f'<div class="story-links">{"".join(rows)}</div>' if rows else ""


def process(page: Path, ents: list[dict], all_stories: list[dict], dry: bool) -> int:
    src = page.read_text(encoding="utf-8", errors="ignore")
    src = re.sub(r'<div class="story-links">.*?</div>\s*</div>',
                 "</div>", src, flags=re.S)
    src = re.sub(r'<style id="soonsal-story-links">.*?</style>\s*', "", src, flags=re.S)
    issue = f"/{page.parent.name}/{page.stem}."
    mine = [s for s in all_stories if issue in s.get("u", "")]
    if not mine:
        return 0

    added = 0
    out = src
    for s in mine:
        anchor = re.search(r"#(story-\d+)", s.get("u", ""))
        if not anchor:
            continue
        # 그 스토리 블록의 면책 문구 바로 앞에 끼운다 — 본문이 끝나는 자리다
        pat = re.compile(
            r'(id="' + anchor.group(1) + r'".*?)'
            r'(<p style="font-size:11px[^>]*>매수매도 추천 아님[^<]*</p>)', re.S)
        m = pat.search(out)
        if not m:
            continue
        body = re.sub(r"<[^>]+>", " ", m.group(1))
        blk = block(found_in(body, ents), related(s.get("t", ""), issue, all_stories))
        if not blk:
            continue
        out = out[:m.start(2)] + blk + out[m.start(2):]
        added += 1

    if added and "soonsal-story-links" not in out and "</head>" in out:
        out = out.replace("</head>", CSS + "</head>", 1)
    if added and not dry:
        page.write_text(out, encoding="utf-8")
    return added


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue", help="MMDD")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    ents, all_stories = entities(), stories()
    if not ents or not all_stories:
        print("  엔티티나 스토리 색인이 없다")
        return 1

    pages = []
    if a.issue:
        pages = [ROOT / "newsletters" / "2026" / f"{a.issue}.html"]
    elif a.all:
        pages = sorted((ROOT / "newsletters" / "2026").glob("[0-9][0-9][0-9][0-9].html"))
    else:
        print("  --issue MMDD 또는 --all")
        return 1

    total = 0
    for p in pages:
        if not p.is_file():
            continue
        n = process(p, ents, all_stories, a.dry)
        if n:
            print(f"  {p.name}  스토리 {n}개")
            total += n
    print(f"\n  {total}개 스토리에 링크 줄 추가" + ("  (dry)" if a.dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
