#!/usr/bin/env python3
"""라이선싱 가능한 스토리 목록을 한 장으로 굽는다 (한국투자신탁운용용).

고객사가 「무엇을 고를 수 있는지」를 물었을 때, 목록을 메일에 붙이면 그날로 낡는다.
매일 발행되는데 목록만 멈춰 있으면 고르는 쪽이 옛 재고를 보게 된다.
그래서 URL 하나로 넘기고, 발행기가 돌 때마다 이 스크립트가 목록을 다시 만든다.

  입력  content/story_atoms.json  (gitignore — 로컬에만 있다)
        scripts/entities.json     (기업·인물·자산 사전, 제목 옆 태그로 쓴다)
  출력  partners/kim/index.html

추천 10선은 CURATED 에 손으로 박아둔다. 자동 선별로는 「이 고객의 플랫폼에
무엇이 맞는가」가 안 나온다 — 그건 사람이 고르는 자리다.
"""

import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATOMS = ROOT / "content/story_atoms.json"
ENTS = ROOT / "scripts/entities.json"
OUT = ROOT / "partners/kim-catalog/index.html"
# ※ partners/KIM/ 은 기존 제안서 자리다. macOS 는 대소문자를 구분하지 않아
#   partners/kim/ 으로 쓰면 그 제안서를 통째로 덮어쓴다. 폴더 이름을 겹치지 않게 둔다.

SINCE = "2026-05-01"        # 목록에 담을 최소 발행일
DEADLINE = "2026년 9월 17일"  # 이 날까지 갱신한다고 고객에게 약속한 날

# 한국투자신탁운용 ACE 플랫폼 브리프 기준 추천 10선.
# (일상 투자자~전문 투자자 · ETF/펀드/금 · 상품 이해와 비교 · 제3자 시선)
CURATED = [
    ("0728-2", "ETF 구조",     "단일종목 레버리지가 24년 만에 돌아온 이유. 상품 구조를 파는 앱이라면 첫 장에 깔 이야기"),
    ("0727-5", "자산배분",     "채권이 방패 역할을 못 하게 된 국면. 60/40을 다시 묻는 독자에게 붙는다"),
    ("0708-1", "패시브 자금",   "지수 편입 하나로 돈이 어떻게 움직이는지. 인덱스를 처음 이해하는 사람에게 좋은 입구"),
    ("0709-3", "지수 집중도",   "한 종목이 지수를 끌고 가는 상태의 위험. 분산을 설명할 때 쓰기 좋다"),
    ("0814-5", "연금",         "퇴직연금 제도가 바뀌는 방향. 연금 상품을 담는 플랫폼에 맞는 주제"),
    ("0716-1", "국내 레버리지", "코스피 변동성을 키운 빚투 구조. 국내 투자자 체감이 가장 큰 이야기"),
    ("0804-1", "변동성 가격",   "하루 반토막 확률에 값이 매겨지는 방식. 위험을 숫자로 보는 감각을 준다"),
    ("0805-4", "글로벌 자금",   "돈이 어느 나라로 흘러가는지. 해외 상품 비교 화면과 맞물린다"),
    ("0811-3", "현금 비중",     "버크셔의 현금이 줄어든 의미. 타이밍을 묻는 독자에게 답이 되는 편"),
    ("0803-1", "투자자 행태",   "급등한 날 개인이 오히려 던진 기록. 체험 기능과 붙이면 설득력이 생긴다"),
]


def load_entities():
    d = json.loads(ENTS.read_text(encoding="utf-8"))
    out = []
    for e in d.get("entities", []):
        try:
            out.append((re.compile(e["pattern"]), e["name"], e.get("type", "")))
        except re.error:
            continue
    return out


def tag(atom, ents):
    """제목 옆에 붙일 기업·자산 이름. 본문 앞부분에서만 찾는다 — 뒤로 갈수록 곁가지다."""
    text = atom["title"] + " " + atom["body"][:600]
    hits, seen = [], set()
    for pat, name, typ in ents:
        if name in seen:
            continue
        if pat.search(text):
            hits.append(name)
            seen.add(name)
        if len(hits) >= 3:
            break
    return hits


def main():
    if not ATOMS.exists():
        print("  ⚠️ story_atoms.json 없음 — 목록 생성 건너뜀")
        return
    atoms = [a for a in json.loads(ATOMS.read_text(encoding="utf-8"))
             if not a.get("crypto") and a["date"] >= SINCE]
    atoms.sort(key=lambda a: (a["date"], a.get("n", 0)), reverse=True)
    ents = load_entities()
    by_id = {a["id"]: a for a in atoms}

    def card(a, extra=""):
        names = tag(a, ents)
        chips = "".join(f'<span class="ent">{html.escape(n)}</span>' for n in names)
        label = html.escape(re.sub(r"&amp;", "&", a.get("label", "")))
        return (
            f'<a class="row" href="https://soonsal.com{a["url"]}" target="_blank" rel="noopener" '
            f'data-t="{html.escape((a["title"] + " " + " ".join(names) + " " + label).lower())}">'
            f'<div class="meta"><span class="date">{a["date"][5:].replace("-", ".")}</span>'
            f'<span class="lab">{label}</span></div>'
            f'<div class="ttl">{html.escape(a["title"])}</div>'
            f'<div class="ents">{chips}</div>'
            f'{extra}</a>'
        )

    picks = []
    for sid, theme, why in CURATED:
        a = by_id.get(sid)
        if not a:
            print(f"  ⚠️ 추천 항목 누락: {sid}")
            continue
        picks.append(card(a, f'<div class="why"><b>{html.escape(theme)}</b> · {html.escape(why)}</div>'))

    rows = [card(a) for a in atoms]

    doc = f"""<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>순살 콘텐츠 라이선싱 목록 — 한국투자신탁운용</title>
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>
:root{{--bg:#0a0a0a;--surface:#141414;--surface2:#1b1b1b;--border:#2a2a2a;--text:#e8e8e8;--dim:#8a8a8a;--accent:#F38C61}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:'Pretendard',sans-serif;line-height:1.7;word-break:keep-all}}
.wrap{{max-width:960px;margin:0 auto;padding:56px 22px 90px}}
h1{{font-size:32px;font-weight:800;letter-spacing:-1.2px;line-height:1.3}}
.sub{{color:var(--dim);margin-top:10px;font-size:16px}}
.note{{background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--accent);
  border-radius:0 12px 12px 0;padding:18px 22px;margin:26px 0;font-size:15.5px;line-height:1.75}}
.note b{{color:var(--accent)}}
h2{{font-size:21px;font-weight:800;margin:44px 0 6px;letter-spacing:-0.6px}}
h2 .cnt{{font-size:14px;color:var(--dim);font-weight:500;margin-left:8px}}
.h2sub{{color:var(--dim);font-size:14.5px;margin-bottom:16px}}
.row{{display:block;background:var(--surface);border:1px solid var(--border);border-radius:12px;
  padding:15px 18px;margin-bottom:9px;text-decoration:none;color:inherit;transition:border-color .15s}}
.row:hover{{border-color:var(--accent)}}
.meta{{display:flex;gap:9px;align-items:center;font-size:12.5px;color:var(--dim);margin-bottom:5px}}
.lab{{background:var(--surface2);padding:1px 8px;border-radius:5px;letter-spacing:.3px}}
.ttl{{font-size:17px;font-weight:700;letter-spacing:-0.4px;line-height:1.45}}
.ents{{margin-top:7px;display:flex;flex-wrap:wrap;gap:6px}}
.ent{{font-size:12.5px;color:var(--accent);border:1px solid rgba(243,140,97,.4);
  border-radius:20px;padding:1px 10px}}
.why{{margin-top:10px;padding-top:10px;border-top:1px dashed var(--border);font-size:14.5px;color:var(--dim)}}
.why b{{color:var(--text)}}
.pick .row{{border-color:rgba(243,140,97,.45);background:linear-gradient(160deg,rgba(243,140,97,.07),var(--surface))}}
#q{{width:100%;padding:13px 16px;background:var(--surface);border:1px solid var(--border);
  border-radius:10px;color:var(--text);font-size:15px;font-family:inherit;outline:none;margin-bottom:14px}}
#q:focus{{border-color:var(--accent)}}
.foot{{margin-top:46px;padding-top:22px;border-top:1px solid var(--border);color:var(--dim);font-size:14px}}
.foot b{{color:var(--text)}}
@media(max-width:600px){{h1{{font-size:25px}} .wrap{{padding:38px 16px 70px}}}}
</style></head><body><div class="wrap">

<h1>순살 콘텐츠 라이선싱 목록</h1>
<div class="sub">한국투자신탁운용 · 초기 심층 콘텐츠 10건 선정용</div>

<div class="note">
아래는 순살이 최근 발행한 스토리입니다. 이 중에서 골라주시면 <b>플랫폼 규격에 맞춰
다듬어 공급</b>해 드립니다. 지금 보시는 것과 비슷한 형태이며, 담고 싶은 앵글이 있으시면
그 방향을 반영해 작성합니다.<br><br>
목록은 <b>{DEADLINE}까지 매일 갱신</b>됩니다. 여기에 없는 주제도 요청하실 수 있습니다 —
원하시는 방향을 알려주시면 그에 맞춰 새로 기획합니다.
</div>

<h2>순살 추천 10선<span class="cnt">ACE 플랫폼 기준</span></h2>
<div class="h2sub">일상 투자자와 전문 투자자가 함께 쓰는 자산관리 앱, 상품을 비교·이해·탐색하는 흐름을 전제로 골랐습니다.</div>
<div class="pick">
{chr(10).join(picks)}
</div>

<h2>전체 목록<span class="cnt">{len(rows)}편</span></h2>
<div class="h2sub">{SINCE[:4]}년 {int(SINCE[5:7])}월 이후 발행분 · 제목을 누르면 원문으로 이동합니다</div>
<input id="q" type="search" placeholder="기업명·주제로 검색 (예: 엔비디아, ETF, 연금)" autocomplete="off">
<div id="list">
{chr(10).join(rows)}
</div>

<div class="foot">
<b>순살</b> · 신기동 대표이사 · team@soonsal.com · 010-9919-1712<br>
마지막 갱신 {date.today().strftime('%Y년 %m월 %d일')}
</div>

</div>
<script>
var q=document.getElementById('q'), rows=[].slice.call(document.querySelectorAll('#list .row'));
q.addEventListener('input',function(){{
  var v=q.value.trim().toLowerCase();
  rows.forEach(function(r){{ r.style.display = !v || r.dataset.t.indexOf(v)>-1 ? '' : 'none'; }});
}});
</script>
</body></html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(doc, encoding="utf-8")
    print(f"  ✅ 라이선싱 목록: 전체 {len(rows)}편 · 추천 {len(picks)}편 → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
