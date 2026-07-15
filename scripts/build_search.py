#!/usr/bin/env python3
"""클라이언트 사이드 검색 — /search/ 페이지 + 컴팩트 색인.

정적 사이트(백엔드 없음)이므로 검색은 브라우저에서 처리한다. story_atoms.json을
작은 색인(제목·URL·날짜·주제·엔티티)으로 줄여 /search/index.json 으로 내보내고,
/search/index.html 이 바닐라 JS로 입력 즉시 필터링한다. 스토리·주제·엔티티를
가로질러 검색. generate_seo.py 가 atomize 이후 호출.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://soonsal.com"
OUT = ROOT / "search"


def clean_title(t):
    return re.sub(r"^[^\w<>&\"']{1,4}\s+", "", t).strip()


PAGE = """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>검색 — 순살브리핑</title>
<meta name="description" content="순살브리핑 전체 브리핑을 주제·기업·인물·키워드로 검색.">
<link rel="canonical" href="__BASE__/search/"><meta name="robots" content="index, follow">
<meta property="og:title" content="검색 — 순살브리핑"><meta property="og:type" content="website">
<meta property="og:locale" content="ko_KR">
__FONTS__
<style>
__HEADER_CSS__
*{margin:0;padding:0;box-sizing:border-box}
body{background:#111;color:#eee;font-family:'DM Sans','Apple SD Gothic Neo',sans-serif;-webkit-text-size-adjust:100%}
.wrap{max-width:760px;margin:0 auto;padding:24px 16px 60px}
a{color:#eee;text-decoration:none}
.home{color:#F07040;font-size:.88rem;display:inline-block;margin-bottom:14px}
h1{font-size:1.4rem;margin-bottom:10px;letter-spacing:-.02em}
#q{width:100%;background:#1a1a1a;border:1px solid #2c2c2c;border-radius:10px;padding:13px 15px;
  color:#eee;font-size:1rem;outline:none}
#q:focus{border-color:#F07040}
.hint{color:#666;font-size:.82rem;margin:10px 0 4px}
.chips{display:flex;gap:7px;flex-wrap:wrap;margin:12px 0}
.chip{border:1px solid #2c2c2c;border-radius:16px;padding:5px 12px;font-size:.82rem;cursor:pointer;color:#bbb}
.chip:hover{border-color:#F07040;color:#F07040}
.chip.go{border-color:#3a2a22;background:#1b1512;color:#F07040;font-weight:600;text-decoration:none}
.count{color:#666;font-size:.8rem;margin:16px 0 4px}
.item{border-bottom:1px solid #1c1c1c}
.item-row{display:flex;gap:11px;align-items:baseline;padding:11px 2px}
.dt{color:#666;font-size:.76rem;font-variant-numeric:tabular-nums;white-space:nowrap;flex:0 0 auto;padding-top:2px}
.ti{font-size:.95rem;line-height:1.4;flex:1;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.item-row:hover .ti{color:#F07040}
.tags{margin:-4px 0 8px 46px;display:flex;gap:5px;flex-wrap:wrap}
.mtag{font-size:.68rem;color:#8b93a0;background:#181b20;border-radius:4px;padding:1px 7px}
mark{background:#F0704033;color:#F07040;padding:0 1px;border-radius:2px}
@media(min-width:640px){.wrap{padding:32px 20px 60px}.ti{font-size:1rem}}
</style></head><body>
__HEADER__<div class="wrap">
<a class="crumb" href="/topics/" id="ssback">← 뒤로</a>
<script>(function(){var b=document.getElementById('ssback');
if(document.referrer.indexOf(location.origin)===0&&history.length>1){
b.addEventListener('click',function(e){e.preventDefault();history.back();});}})();</script>
<h1>검색</h1>
<input id="q" type="search" placeholder="주제·기업·인물·키워드 (예: 엔비디아, 커버드콜, 파월)" autofocus autocomplete="off">
<div class="hint">브리핑 <span id="total">0</span>건을 제목·주제·등장 대상으로 검색합니다.</div>
<div class="chips" id="suggest"></div>
<div class="chips" id="quick"></div>
<div class="count" id="count"></div>
<div id="results"></div>
<script>
let IDX=[];
const $=s=>document.querySelector(s);
fetch('/search/index.json').then(r=>r.json()).then(d=>{IDX=d;$('#total').textContent=d.length;
  const st=new URLSearchParams(location.search).get('q');if(st){$('#q').value=st;run(st);}});
const SUG=__SUG__;                 // 🔥 지금 뜨는 (빌드 시 주입, 매일 갱신)
const QUICK=__QUICK__;             // 주제+엔티티 바로가기 사전 (타이프어헤드)
$('#suggest').innerHTML=SUG.map(s=>`<span class="chip" onclick="pick('${s}')">${s}</span>`).join('');
function pick(s){$('#q').value=s;run(s);$('#q').focus();}
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function hl(s,q){if(!q)return esc(s);const i=s.toLowerCase().indexOf(q.toLowerCase());
  if(i<0)return esc(s);return esc(s.slice(0,i))+'<mark>'+esc(s.slice(i,i+q.length))+'</mark>'+esc(s.slice(i+q.length));}
let timer;
$('#q').addEventListener('input',e=>{clearTimeout(timer);timer=setTimeout(()=>run(e.target.value),120);});
function run(q){q=(q||'').trim();history.replaceState(0,'',q?'?q='+encodeURIComponent(q):location.pathname);
  if(!q){$('#results').innerHTML='';$('#count').textContent='';$('#quick').innerHTML='';return;}
  const ql=q.toLowerCase();
  // 타이프어헤드: 주제·엔티티 페이지 바로가기 (치는 즉시)
  const qk=QUICK.filter(x=>x.n.toLowerCase().includes(ql)||(x.a||'').toLowerCase().includes(ql)).slice(0,6);
  $('#quick').innerHTML=qk.map(x=>`<a class="chip go" href="${x.u}">${x.e||''} ${esc(x.n)} ›</a>`).join('');
  const hits=IDX.map(it=>{
    let sc=0;const t=it.t.toLowerCase();
    if(t.includes(ql))sc+=3;
    if((it.k||'').toLowerCase().includes(ql))sc+=1;
    return sc>0?[sc,it]:null;}).filter(Boolean)
    .sort((a,b)=>b[0]-a[0]||(a[1].d<b[1].d?1:-1)).slice(0,120);
  $('#count').textContent=hits.length?`${hits.length}건`+(hits.length>=120?'+':''):'결과 없음';
  $('#results').innerHTML=hits.map(([,it])=>
    `<div class="item"><a class="item-row" href="${it.u}"><span class="dt">${it.d.slice(5).replace('-','.')}</span>`+
    `<span class="ti">${hl(it.t,q)}</span></a>`+
    (it.g&&it.g.length?`<div class="tags">${it.g.map(g=>`<span class="mtag">${esc(g)}</span>`).join('')}</div>`:'')+
    `</div>`).join('');
}
</script></div></body></html>"""


def build(atoms=None):
    if atoms is None:
        import atomize
        atoms = atomize.build()
    import atomize
    tax = atomize.load_tax()
    ent = atomize.load_entities()
    tname = {t["slug"]: t["name"] for t in tax["topics"]}
    ename = {e["slug"]: e["name"] for e in ent["entities"]}
    OUT.mkdir(exist_ok=True)

    idx = []
    for a in atoms:
        topics = [tname[s] for s in a["topics"] if s in tname]
        ents = [ename[s] for s in a["entities"] if s in ename]
        title = clean_title(a["title"])
        # k = 검색 대상 키워드(제목+주제+엔티티+영어표현), g = 화면 표시 태그
        keywords = " ".join([title] + topics + ents
                            + [e["en"] for e in a["english"]])
        idx.append({"t": title, "u": a["url"], "d": a["date"],
                    "g": topics[:3], "k": keywords})
    (OUT / "index.json").write_text(json.dumps(idx, ensure_ascii=False,
                                    separators=(",", ":")), encoding="utf-8")
    # 🔥 지금 뜨는(추천 칩) — 하드코딩 대신 트렌딩으로 매일 갱신
    trend = atomize.trending_entities(atoms)
    sug = [ename[s] for s in trend if s in ename][:10]

    # 바로가기 사전(타이프어헤드): 주제 + 엔티티 → 각 페이지. a=검색 별칭(패턴 내 영문 등)
    quick = []
    for t in tax["topics"]:
        quick.append({"n": t["name"], "u": f"/topics/{t['slug']}.html",
                      "e": t.get("emoji", ""), "a": t["slug"]})
    types = ent.get("types", {})
    for e in ent["entities"]:
        alias = " ".join(w for w in e["pattern"].replace("\\b", "").split("|")
                         if w.isascii())[:60]
        quick.append({"n": e["name"], "u": f"/wiki/{e['slug']}.html",
                      "e": types.get(e["type"], {}).get("emoji", ""), "a": alias})

    import build_nav
    html = (PAGE.replace("__BASE__", BASE)
            .replace("__FONTS__", build_nav.FONT_LINK)
            .replace("__HEADER_CSS__", build_nav.HEADER_CSS)
            .replace("__HEADER__", build_nav.header_html(None))
            .replace("__SUG__", json.dumps(sug, ensure_ascii=False))
            .replace("__QUICK__", json.dumps(quick, ensure_ascii=False, separators=(",", ":"))))
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"🔍 search: 색인 {len(idx)}건 + /search/ 페이지")
    return idx


if __name__ == "__main__":
    build()
