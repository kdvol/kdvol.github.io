#!/usr/bin/env python3
"""/talk/ — 스토리 막론 전체 코멘트 한 화면.

스토리별 코멘트는 필요하지만, 그것만 있으면 대화가 파편화된다. 1007개 스토리에
흩어진 한 줄들은 아무도 못 본다. 여기 다 모아 두면 무슨 글에 달렸든 한자리에서
읽고 답할 수 있다.

  - 최근에 움직인 스레드부터. 답글만 새로 달려도 그 스레드가 위로 올라온다
  - 15초마다 새로고침 없이 갱신. 내가 쓰는 중이면 건너뛴다(입력 중 화면이
    갈아엎히면 쓰던 걸 잃는다)
  - 답글·좋아요는 원본 스토리로 가지 않고 여기서 바로

코멘트 작성 UI는 soonsal.js가 이미 갖고 있다. 여기서는 목록과 답글만 다루고
프로필·익명 번호는 같은 localStorage를 그대로 쓴다.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATOMS = ROOT / "content/story_atoms.json"
OUT = ROOT / "talk"

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#111;color:#eee;
font-family:'DM Sans',-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;
-webkit-font-smoothing:antialiased}
.wrap{max-width:620px;margin:0 auto;padding:22px 16px 80px}
h1{font-size:1.5rem;font-weight:800;margin:0 0 4px;letter-spacing:-.02em;color:#f2efe8}
.sub{color:#8b8578;font-size:.87rem;margin:0 0 20px;line-height:1.6}
.sub a{color:#E55A00;text-decoration:none;font-weight:600}
.live{display:inline-flex;align-items:center;gap:5px;font-size:.72rem;color:#8b8578;
background:#161616;border:1px solid #262626;border-radius:20px;padding:3px 10px;margin-left:6px}
.live b{width:6px;height:6px;border-radius:50%;background:#4ea87a;display:inline-block}
.th{background:#141414;border:1px solid #222;border-radius:14px;padding:14px 15px;margin-bottom:11px}
.src{font-size:.72rem;color:#7a756c;margin-bottom:9px;display:flex;gap:6px;align-items:baseline}
.src a{color:#8b8578;text-decoration:none;border-bottom:1px solid #2a2a2a;
overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.src a:hover{color:#E55A00;border-bottom-color:#E55A00}
.src .dt{flex:0 0 auto;color:#5f5a52}
.c{font-size:.93rem;line-height:1.65;padding:7px 0}
.c.rep{padding-left:13px;border-left:2px solid #262626;margin-left:2px}
.c .k{font-weight:700;color:#f0ede6;margin-right:5px}
.c .g{font-size:.66rem;color:#8b8578;background:#1e1e1e;border-radius:4px;padding:1px 5px;margin-right:4px}
/* 순살 팀 글은 팀 글이라고 밝힌다 — 독자 글과 섞이면 안 된다 */
.c.op{background:#191512;border-left:2px solid #E55A00;padding-left:11px;
margin-left:-2px;border-radius:0 8px 8px 0}
.c .ob{font-size:.62rem;font-weight:700;color:#fff;background:#E55A00;border-radius:4px;
padding:1px 6px;margin-right:5px;vertical-align:1px}
.c .t{color:#5f5a52;font-size:.7rem;margin-left:5px}
.act{display:inline-flex;gap:11px;margin-left:7px}
.act button{background:none;border:none;padding:2px 0;font-size:.75rem;color:#7a756c;
cursor:pointer;font-family:inherit}
.act button:hover{color:#E55A00}
.act .like.on{color:#E55A00;font-weight:700}
.rf{margin-top:10px;display:none}
.rf.on{display:block}
.rf textarea{width:100%;border:1px solid #2a2a2a;border-radius:10px;padding:11px 12px;
font-size:16px;font-family:inherit;resize:none;background:#1a1a1a;color:#eee;line-height:1.5}
.rf textarea:focus{outline:none;border-color:#F07040}
.rf .row{display:flex;align-items:center;gap:8px;margin-top:7px}
.rf .who{flex:1;font-size:.78rem;color:#8b8578;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rf button.go{background:#E55A00;color:#fff;border:none;border-radius:9px;padding:9px 17px;
font-size:.82rem;font-weight:700;cursor:pointer;font-family:inherit}
.rf button.go:disabled{background:#242424;color:#5f5a52}
.rf button.x{background:none;border:none;color:#7a756c;font-size:.75rem;cursor:pointer;font-family:inherit}
.empty{color:#7a756c;text-align:center;padding:52px 16px;line-height:1.7}
.empty b{display:block;color:#f0ede6;font-size:1.12rem;margin-bottom:9px;letter-spacing:-.02em}
.empty .ecta{display:inline-block;margin-top:18px;background:#E55A00;color:#fff;
text-decoration:none;font-weight:700;font-size:.87rem;border-radius:10px;padding:12px 20px}
.empty .ecta:hover{background:#F07040}
.new{background:#191512;border-color:#4a2d1c}
"""

JS = r"""
var API = (window.SS_CFG && window.SS_CFG.worker) || '';
var app = document.getElementById('app');
var seen = {}, first = true, liked = {};
try { liked = JSON.parse(localStorage.getItem('ss_liked') || '{}'); } catch (e) {}

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
  });
}
function ago(ts) {
  var s = Math.max(0, Math.floor(Date.now() / 1000) - ts);
  if (s < 60) return '방금';
  if (s < 3600) return Math.floor(s / 60) + '분';
  if (s < 86400) return Math.floor(s / 3600) + '시간';
  return Math.floor(s / 86400) + '일';
}
function vid() {
  try {
    var v = localStorage.getItem('ss_vid');
    if (!v || !/^[a-z0-9-]{8,32}$/.test(v)) {
      v = (Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2)).slice(0, 16);
      localStorage.setItem('ss_vid', v);
    }
    return v;
  } catch (e) { return null; }
}
function prof() {
  try { return JSON.parse(localStorage.getItem('ss_prof') || 'null') || {}; } catch (e) { return {}; }
}

// 스토리 제목 — 없는 회차면 경로만 보여준다
function label(story) {
  var m = SMAP[story];
  return m ? m.t : story;
}
function href(story) {
  var m = SMAP[story];
  return m ? m.u : '#';
}

function render(items) {
  if (!items.length) {
    app.innerHTML = '<div class="empty"><b>여기가 첫 줄이 될 자리예요</b>' +
      '브리핑을 읽다 남긴 한마디가 회차 상관없이 여기 모입니다.<br>' +
      '읽고 든 생각, 아는 이야기, 질문 — 무엇이든 좋아요.' +
      '<a class="ecta" href="/">오늘 브리핑 읽으러 가기 →</a></div>';
    return;
  }
  // 스레드로 묶는다 — 서버가 이미 (최신 스레드, root, id) 순으로 준다
  var order = [], roots = {};
  items.forEach(function (c) {
    if (!roots[c.root_id]) { roots[c.root_id] = []; order.push(c.root_id); }
    roots[c.root_id].push(c);
  });

  var html = order.map(function (rid) {
    var list = roots[rid], head = list[0];
    var isNew = !first && !seen[head.id];
    return '<div class="th' + (isNew ? ' new' : '') + '" data-r="' + rid + '">' +
      '<div class="src"><a href="' + href(head.story) + '">' + esc(label(head.story)) + '</a>' +
      '<span class="dt">' + ago(head.ts) + '</span></div>' +
      list.map(function (c) { return one(c, c.parent_id); }).join('') +
      '<div class="rf" data-r="' + rid + '">' +
        '<textarea rows="2" maxlength="140" placeholder="답글 남기기"></textarea>' +
        '<div class="row"><span class="who"></span>' +
          '<button type="button" class="x">취소</button>' +
          '<button type="button" class="go" disabled>남기기</button></div>' +
      '</div></div>';
  }).join('');
  app.innerHTML = html;
  items.forEach(function (c) { seen[c.id] = 1; });
  first = false;
  wire();
}

function one(c, isRep) {
  var tag = [c.tag, c.co].filter(Boolean).join(' · ');
  return '<div class="c' + (isRep ? ' rep' : '') + (c.op ? ' op' : '') +
    '" data-i="' + c.id + '">' +
    '<span class="k">' + esc(c.nick) + '</span>' +
    (c.op ? '<span class="ob">순살 팀</span>' : '') +
    (tag ? '<span class="g">' + esc(tag) + '</span>' : '') +
    esc(c.body) +
    '<span class="act">' +
      '<button type="button" class="like' + (liked[c.id] ? ' on' : '') + '" data-i="' + c.id + '">' +
        '♥ ' + (c.likes || '') + '</button>' +
      (isRep ? '' : '<button type="button" class="rep" data-i="' + c.id +
                    '" data-k="' + esc(c.nick) + '" data-s="' + esc(c.story) + '">답글</button>') +
    '</span><span class="t">' + ago(c.ts) + '</span></div>';
}

function wire() {
  app.querySelectorAll('.like').forEach(function (b) {
    b.addEventListener('click', function () {
      var id = parseInt(b.getAttribute('data-i'), 10), v = vid();
      if (!API || !v) return;
      b.disabled = true;
      fetch(API.replace(/[/]$/, '') + '/like', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ id: id, v: v }),
      }).then(function (r) { return r.json(); }).then(function (res) {
        b.disabled = false;
        if (!res || !res.ok) return;
        if (res.on) liked[id] = 1; else delete liked[id];
        try { localStorage.setItem('ss_liked', JSON.stringify(liked)); } catch (e) {}
        b.className = 'like' + (res.on ? ' on' : '');
        b.textContent = '♥ ' + (res.n || '');
      }).catch(function () { b.disabled = false; });
    });
  });

  app.querySelectorAll('.rep').forEach(function (b) {
    b.addEventListener('click', function () {
      var th = b.closest('.th'), rf = th.querySelector('.rf');
      var ta = rf.querySelector('textarea'), go = rf.querySelector('.go');
      rf.className = 'rf on';
      rf._pid = parseInt(b.getAttribute('data-i'), 10);
      rf._story = b.getAttribute('data-s');
      var tag = '@' + b.getAttribute('data-k') + ' ';
      if (ta.value.indexOf('@') !== 0) ta.value = tag + ta.value;
      rf.querySelector('.who').textContent = (prof().n || '') + ' (으)로 답글';
      go.disabled = !ta.value.trim();
      ta.focus();
    });
  });

  app.querySelectorAll('.rf').forEach(function (rf) {
    var ta = rf.querySelector('textarea'), go = rf.querySelector('.go');
    ta.addEventListener('input', function () { go.disabled = !ta.value.trim(); });
    ta.addEventListener('focus', function () { typing = true; });
    ta.addEventListener('blur', function () { typing = false; });
    rf.querySelector('.x').addEventListener('click', function () {
      rf.className = 'rf'; ta.value = ''; typing = false;
    });
    go.addEventListener('click', function () { submit(rf, ta, go); });
  });
}

function submit(rf, ta, go) {
  var body = ta.value.trim(), v = vid(), p = prof();
  if (!body || !API || !v) return;
  go.disabled = true;
  fetch(API.replace(/[/]$/, '') + '/comment', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      story: rf._story, v: v, nick: p.n || '독자', body: body,
      tag: p.i || '', co: p.sc ? (p.c || '') : '', parent: rf._pid || 0,
    }),
  }).then(function (r) { return r.json(); }).then(function (res) {
    go.disabled = false;
    if (res && res.error) { alert('남기지 못했어요'); return; }
    ta.value = ''; rf.className = 'rf'; typing = false;
    load();                                   // 바로 반영
  }).catch(function () { go.disabled = false; });
}

var typing = false;
function load() {
  if (!API) { app.innerHTML = '<div class="empty">집계 저장소가 연결되지 않았습니다.</div>'; return; }
  // 모바일에서 요청이 멈추면 화면이 '불러오는 중…'에 갇힌다 — 12초에 끊는다
  var ctl = typeof AbortController !== 'undefined' ? new AbortController() : null;
  var timer = setTimeout(function () { if (ctl) ctl.abort(); }, 12000);
  fetch(API.replace(/[/]$/, '') + '/recent?n=60', { signal: ctl ? ctl.signal : undefined })
    .then(function (r) { clearTimeout(timer); return r.json(); })
    .then(function (d) {
      if (d && d.off) {
        app.innerHTML = '<div class="empty"><b>코멘트를 잠시 닫았어요</b>곧 다시 열립니다.</div>';
        return;
      }
      render((d && d.items) || []);
    })
    .catch(function () {
      clearTimeout(timer);
      // 이미 뭔가 보여주고 있으면 건드리지 않는다 — 갱신 실패로 화면을 비우면 손해다
      if (first) app.innerHTML = '<div class="empty"><b>불러오지 못했어요</b>' +
        '연결을 확인하고 새로고침해 주세요.</div>';
    });
}

load();
// 쓰는 중에 갈아엎으면 쓰던 걸 잃는다 — 입력 중이면 건너뛴다
setInterval(function () { if (!typing && !document.hidden) load(); }, 15000);
document.addEventListener('visibilitychange', function () { if (!document.hidden) load(); });
"""


def build(atoms=None):
    if atoms is None:
        atoms = json.loads(ATOMS.read_text(encoding="utf-8")) if ATOMS.exists() else []
    OUT.mkdir(exist_ok=True)

    recent = sorted(atoms, key=lambda a: a.get("date", ""), reverse=True)[:600]
    smap = {a["id"]: {"t": re.sub(r"^[^\w<>&\"']{1,4}\s+", "", a["title"]).strip()[:44],
                      "u": a["url"]} for a in recent}

    try:
        import build_nav
        nav = "<style>" + build_nav.HEADER_CSS + "</style>" + build_nav.header_html("/talk/")
    except Exception:
        nav = ""

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>순살톡 — 독자들이 남긴 말</title>
<meta name="description" content="순살브리핑 독자들이 스토리마다 남긴 한 줄을 한자리에. 순살톡."/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;800&display=swap" rel="stylesheet"/>
<script src="/ss-config.js"></script>
<style>{CSS}</style></head><body>
{nav}
<div class="wrap">
<h1>순살톡</h1>
<p class="sub">브리핑을 읽다 남긴 한 줄이 여기 다 모입니다.
<span class="live"><b></b>실시간</span><br>
<a href="/">오늘 브리핑 보러 가기 →</a></p>
<div id="app"><div class="empty">불러오는 중…</div></div>
</div>
<script src="/soonsal.js" defer></script>
<script>
var SMAP = {json.dumps(smap, ensure_ascii=False)};
{JS}
</script>
</body></html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"💬 talk: /talk/ 전체 코멘트 ({len(smap)}개 스토리 제목)")


if __name__ == "__main__":
    build()
