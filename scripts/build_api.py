#!/usr/bin/env python3
"""챗에서 web_fetch로 바로 쓰는 공개 엔드포인트 (/api/entities.json).

뉴스레터 본문은 claude.ai 프로젝트 챗에서 쓰는데, 거기선 이 리포의 스크립트를 못
돌린다. 인사말 아카이브 줄("엔비디아 얘기, 오늘이 처음 아님 → 순살이 다룬 엔비디아
102건")을 챗이 매번 자동으로 만들려면 건수와 URL을 조회할 데가 있어야 한다.

챗은 오늘 리드 스토리의 회사 이름을 이미 안다(방금 본인이 썼으니까). 그래서 필요한 건
"이름 → 건수·URL·완성된 HTML" 한 방향 조회뿐이고, 그건 정적 JSON 하나로 충분하다.
Worker도 DB도 필요 없다.

항목마다 완성 HTML을 넣으면 40KB가 넘어 챗이 매번 읽기 무겁다. 그래서 템플릿 한 줄 +
[이름, 별칭, 건수, 슬러그] 압축 배열로 5KB 아래로 줄였다.

응답 형태:
  {
    "generated": "2026-08-11",
    "usage": "...",
    "template": "<span ...>{name} 얘기, 오늘이 처음 아님 &#8594; <a href=\\"{url}\\">순살이 다룬 {name} {count}건</a></span>",
    "url_form": "https://soonsal.com/wiki/{slug}.html",
    "example": "엔비디아를 골랐을 때의 완성 결과",
    "entities": [["엔비디아", ["Nvidia","NVIDIA"], 102, "nvidia"], ...]
  }
"""
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATOMS = ROOT / "content" / "story_atoms.json"
ENTS = ROOT / "scripts" / "entities.json"
OUT = ROOT / "api"
BASE = "https://soonsal.com"

# archive_line.py와 같은 기준 — 자산·기관은 "원유 얘기, 오늘이 처음 아님"이 되어 안 쓴다
OK_TYPES = {"company", "person"}
MIN_STORIES = 5

TEMPLATE = ('<span style="margin-top:9px;">{name} 얘기, 오늘이 처음 아님 '
            '&#8594; <a href="{url}">순살이 다룬 {name} {count}건</a></span>')
URL_FORM = f"{BASE}/wiki/{{slug}}.html"

USAGE = (
    "순살브리핑 인사말 아카이브 줄용. entities는 [이름, 별칭목록, 건수, 슬러그] 배열이다. "
    "① 오늘 인사말 헤드라인이 가리키는 회사/인물을 이름 또는 별칭에서 찾는다 "
    "(아카이브가 가장 두꺼운 항목이 아니라 헤드라인이 가리키는 쪽). "
    "② url_form의 {slug}를 채워 URL을 만든다. "
    "③ template의 {name} {url} {count}를 채워 인사말 CTA 마지막에 그대로 붙인다. "
    "목록에 없으면 줄을 넣지 않는다 — 건수를 추정하거나 지어내지 말 것."
)


def _aliases(pattern: str) -> list:
    """정규식 패턴에서 사람이 읽을 별칭만 추린다(\\b, 룩비하인드 등 제거)."""
    out = []
    for p in pattern.split("|"):
        p = re.sub(r"\(\?<![^)]*\)|\\b|\\s\?|\(\?:|\)|\?", "", p).strip()
        if p and re.fullmatch(r"[\w가-힣 .&-]+", p) and p not in out:
            out.append(p)
    return out[:6]


def build(atoms=None):
    if atoms is None:
        atoms = json.loads(ATOMS.read_text(encoding="utf-8"))
    ents = json.loads(ENTS.read_text(encoding="utf-8"))["entities"]

    total = Counter()
    for s in atoms:
        for e in s.get("entities", []):
            total[e] += 1

    rows = []
    for e in ents:
        slug, n = e["slug"], total.get(e["slug"], 0)
        if e.get("type") not in OK_TYPES or n < MIN_STORIES:
            continue
        ko = e["name"]
        url = f"{BASE}/wiki/{slug}.html"
        alias = [a for a in _aliases(e.get("pattern", "")) if a != ko]
        rows.append([ko, alias, n, slug])
    rows.sort(key=lambda r: -r[2])

    today = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    OUT.mkdir(exist_ok=True)
    ex = next((r for r in rows if r[3] == "nvidia"), rows[0])
    payload = {
        "generated": today,
        "usage": USAGE,
        "template": TEMPLATE,
        "url_form": URL_FORM,
        "fields": ["name", "aliases", "count", "slug"],
        "example": TEMPLATE.format(name=ex[0], count=ex[2],
                                   url=URL_FORM.format(slug=ex[3])),
        "count": len(rows),
        "entities": rows,
    }
    (OUT / "entities.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    kb = (OUT / "entities.json").stat().st_size / 1024
    print(f"🔌 api: /api/entities.json 엔티티 {len(rows)}개 ({kb:.0f}KB) — 챗 web_fetch용")
    return len(rows)


if __name__ == "__main__":
    build()
