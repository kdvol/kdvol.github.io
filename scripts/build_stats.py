#!/usr/bin/env python3
"""운영자용 반응 통계 페이지 (/stats/).

스토리별 👍🤔🔥 집계를 한 화면에 보여준다. 데이터는 Supabase(무료 티어)에서
브라우저가 직접 읽는다 — 서버 불필요. 미설정 시엔 설정 안내를 표시.
스토리 제목·날짜·링크는 빌드 시점에 story_atoms.json에서 심는다.

noindex(검색 노출 X). sitemap에도 넣지 않음.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://soonsal.com"
OUT = ROOT / "stats"
ATOMS = ROOT / "content" / "story_atoms.json"

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#111;color:#eee;font-family:'DM Sans','Apple SD Gothic Neo','Malgun Gothic',sans-serif;
-webkit-text-size-adjust:100%}
.wrap{max-width:820px;margin:0 auto;padding:30px 16px 70px}
a{color:#eee;text-decoration:none}
h1{font-size:1.5rem;letter-spacing:-.02em;margin-bottom:6px}
.sub{color:#888;font-size:.88rem;margin-bottom:22px}
.setup{background:#161616;border:1px solid #2a2320;border-radius:12px;padding:20px 22px;line-height:1.75}
.setup h2{font-size:1rem;color:#F07040;margin-bottom:10px}
.setup ol{margin:0 0 0 18px;color:#bbb;font-size:.9rem}
.setup code{background:#0d0d0d;border:1px solid #262626;border-radius:5px;padding:1px 6px;
font-family:'JetBrains Mono',monospace;font-size:.82rem;color:#F0a070}
pre{background:#0d0d0d;border:1px solid #222;border-radius:8px;padding:14px;overflow-x:auto;
font-size:.78rem;line-height:1.6;color:#bbb;margin:10px 0}
.sum{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}
.kpi{background:#161616;border:1px solid #232323;border-radius:10px;padding:12px 16px;min-width:104px}
.kpi .v{font-size:1.5rem;font-weight:800;color:#F07040;line-height:1.2}
.kpi .l{font-size:.75rem;color:#888;margin-top:2px}
.row{display:flex;gap:12px;align-items:baseline;padding:12px 4px;border-bottom:1px solid #1c1c1c}
.dt{color:#666;font-size:.76rem;white-space:nowrap;font-variant-numeric:tabular-nums;padding-top:2px}
.ti{flex:1;font-size:.94rem;line-height:1.45}
.row:hover .ti{color:#F07040}
.cnt{display:flex;gap:9px;white-space:nowrap;font-size:.85rem;color:#aaa;font-variant-numeric:tabular-nums}
.cnt span.z{color:#3a3a3a}
.empty{color:#777;font-size:.9rem;padding:22px 4px}
"""


def build(atoms=None):
    if atoms is None:
        atoms = json.loads(ATOMS.read_text(encoding="utf-8")) if ATOMS.exists() else []
    OUT.mkdir(exist_ok=True)
    # 최근 60일치만 심는다(파일 크기 관리)
    recent = sorted(atoms, key=lambda a: a.get("date", ""), reverse=True)[:400]
    smap = {a["id"]: {"t": re.sub(r"^[^\w<>&\"']{1,4}\s+", "", a["title"]).strip(),
                      "d": a["date"], "u": a["url"]} for a in recent}

    setup_sql = """-- 기존 Supabase 프로젝트에 그대로 추가해도 안전(soonsal_ 접두어)
create table if not exists soonsal_reactions (
  story text not null, emoji text not null,
  count int not null default 0,
  primary key (story, emoji)
);
alter table soonsal_reactions enable row level security;
create policy "read" on soonsal_reactions for select using (true);

create or replace function soonsal_react(p_story text, p_emoji text, p_delta int)
returns void language plpgsql security definer as $$
begin
  insert into soonsal_reactions(story, emoji, count)
  values (p_story, p_emoji, greatest(p_delta, 0))
  on conflict (story, emoji)
  do update set count = greatest(soonsal_reactions.count + p_delta, 0);
end; $$;"""

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex,nofollow">
<title>반응 통계 — 순살브리핑</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;800&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet"/>
<script src="/ss-config.js"></script>
<style>{CSS}</style></head><body><div class="wrap">
<h1>반응 통계</h1>
<p class="sub">독자들이 어떤 스토리에 반응했는지 — 운영자용 화면 (검색 노출 안 됨)</p>
<div id="app"><div class="empty">불러오는 중…</div></div>
</div>
<script>
var SMAP = {json.dumps(smap, ensure_ascii=False)};
var EMO = ['👍','🤔','🔥'];
var CFG = (window.SS_CFG||{{}}).supabase;
var app = document.getElementById('app');

function setup() {{
  app.innerHTML = '<div class="setup"><h2>아직 집계 저장소가 연결되지 않았습니다</h2>' +
    '<p style="color:#bbb;font-size:.9rem;margin-bottom:12px">지금은 반응이 각자 브라우저에만 남습니다. ' +
    '아래 3단계(3분, 무료·카드 불필요)를 마치면 전체 집계가 이 화면에 쌓입니다.</p>' +
    '<ol><li><b>supabase.com</b> 무료 프로젝트 생성</li>' +
    '<li>SQL Editor에 아래를 붙여넣고 실행</li>' +
    '<li>Project Settings → API에서 <code>URL</code>과 <code>anon public</code> 키를 복사해 ' +
    '<code>/ss-config.js</code>에 넣기</li></ol>' +
    '<pre>{setup_sql.replace(chr(10), chr(92) + "n").replace("'", chr(92) + "'")}</pre>' +
    '<pre>// ss-config.js\\nwindow.SS_CFG = {{ supabase: {{ url: "https://xxxx.supabase.co", key: "eyJ..." }} }};</pre>' +
    '</div>';
}}

function render(rows) {{
  var by = {{}};
  rows.forEach(function (r) {{ (by[r.story] = by[r.story] || {{}})[r.emoji] = r.count; }});
  var keys = Object.keys(by).sort(function (a, b) {{
    var sa = 0, sb = 0;
    EMO.forEach(function (e) {{ sa += by[a][e] || 0; sb += by[b][e] || 0; }});
    return sb - sa;
  }});
  if (!keys.length) {{ app.innerHTML = '<div class="empty">아직 반응이 없습니다.</div>'; return; }}
  var tot = 0, st = 0;
  keys.forEach(function (k) {{ EMO.forEach(function (e) {{ tot += by[k][e] || 0; }}); st++; }});
  var h = '<div class="sum">' +
    '<div class="kpi"><div class="v">' + tot + '</div><div class="l">전체 반응</div></div>' +
    '<div class="kpi"><div class="v">' + st + '</div><div class="l">반응받은 스토리</div></div></div>';
  keys.forEach(function (k) {{
    var m = SMAP[k] || {{ t: k, d: '', u: '#' }};
    h += '<a class="row" href="' + m.u + '"><span class="dt">' + (m.d || '').slice(5) + '</span>' +
      '<span class="ti">' + m.t + '</span><span class="cnt">' +
      EMO.map(function (e) {{
        var n = by[k][e] || 0;
        return '<span class="' + (n ? '' : 'z') + '">' + e + ' ' + n + '</span>';
      }}).join('') + '</span></a>';
  }});
  app.innerHTML = h;
}}

if (!CFG) {{ setup(); }}
else {{
  fetch(CFG.url + '/rest/v1/' + (CFG.table || 'soonsal_reactions') + '?select=story,emoji,count', {{ headers: {{ apikey: CFG.key }} }})
    .then(function (r) {{ return r.json(); }})
    .then(render)
    .catch(function () {{ app.innerHTML = '<div class="empty">집계를 불러오지 못했습니다.</div>'; }});
}}
</script>
</body></html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print("📊 stats: /stats/ 반응 통계(운영자용)")
    return 1


if __name__ == "__main__":
    build()
