#!/usr/bin/env python3
"""인사말 마지막 줄 — 오늘 다룬 기업의 과거 아카이브로 잇는 한 줄을 만든다.

요일 로테이션(월=웹, 화=인스타…)은 그날 내용과 무관해서 광고처럼 읽힌다.
대신 리드 스토리의 대표 엔티티를 잡아 "이 회사 얘기 처음 아님 → N건" 으로
건다. 순살만 걸 수 있는 링크이고, 그 페이지에 텔레그램·인스타 버튼이 이미
붙어 있어서 채널 분배는 웹사이트가 대신한다.

사용:
  python3 scripts/archive_line.py 2026-08-11              # 후보 제시 + 1순위 줄 생성
  python3 scripts/archive_line.py newsletters/2026/0811.html
  python3 scripts/archive_line.py 2026-08-11 nvidia       # 인사말 헤드라인에 맞춰 직접 지정

인사말 헤드라인이 가리키는 스토리와 다른 후보가 1순위로 뽑힐 수 있다.
(0811: 헤드라인은 엔비디아인데 아카이브는 오픈AI가 더 두꺼움)
그래서 후보를 같이 뿌리고, 어긋나면 슬러그를 직접 넘긴다.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATOMS = ROOT / "content" / "story_atoms.json"
ENTS = ROOT / "scripts" / "entities.json"
BASE = "https://soonsal.com"

# 회사·인물만 쓴다. 원유·금·국채 같은 자산은 "원유 얘기, 오늘이 처음 아님"처럼
# 어색해지고, 규제기관은 아카이브가 두꺼워도 읽을 이유가 없다.
OK_TYPES = {"company", "person"}


def _date_of(arg: str) -> str:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", arg):
        return arg
    m = re.search(r"/(\d{4})/(\d{2})(\d{2})", arg)
    if not m:
        raise SystemExit(f"날짜를 못 읽음: {arg}")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def build(date: str, want: str | None = None):
    atoms = json.loads(ATOMS.read_text(encoding="utf-8"))
    ents = json.loads(ENTS.read_text(encoding="utf-8"))["entities"]
    names = {e["slug"]: e["name"] for e in ents}
    kinds = {e["slug"]: e.get("type") for e in ents}

    total = Counter()
    for s in atoms:
        for e in s.get("entities", []):
            total[e] += 1

    today = [s for s in atoms if s.get("date") == date]
    if not today:
        return None

    seen = {e for s in today for e in s.get("entities", [])}
    cands = sorted((e for e in seen if kinds.get(e) in OK_TYPES and total[e] >= 5),
                   key=lambda e: -total[e])
    if not cands:
        return None

    pick = want if want in seen else cands[0]
    if want and want not in seen:
        print(f"⚠️  {want}는 이 회차에 안 나옴 — 1순위로 대체")

    def line(slug):
        ko, n = names.get(slug, slug), total[slug]
        url = f"{BASE}/wiki/{slug}.html"
        return {"entity": slug, "ko": ko, "count": n, "url": url,
                "html": f'<span style="margin-top:9px;">{ko} 얘기, 오늘이 처음 아님 '
                        f'&#8594; <a href="{url}">순살이 다룬 {ko} {n}건</a></span>'}

    r = line(pick)
    r["candidates"] = [(names.get(c, c), c, total[c]) for c in cands[:4]]
    return r


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    r = build(_date_of(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else None)
    if not r:
        print("걸 만한 엔티티 없음 — 이 줄은 넣지 않는다")
        sys.exit(1)
    print("후보:", " · ".join(f"{ko}({s}) {n}건" for ko, s, n in r["candidates"]))
    print(f"선택: {r['ko']} ({r['entity']}) · 아카이브 {r['count']}건")
    print(f"URL   : {r['url']}")
    print("\n── 인사말에 붙여넣기 ──")
    print(r["html"])
