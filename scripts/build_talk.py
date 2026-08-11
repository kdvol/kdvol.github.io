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
body{margin:0;background:#faf8f3;color:#2b2b2b;
font-family:'DM Sans',-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;
-webkit-font-smoothing:antialiased}
.wrap{max-width:620px;margin:0 auto;padding:22px 16px 80px}
h1{font-size:1.5rem;font-weight:800;margin:0 0 4px;letter-spacing:-.02em}
.sub{color:#8a8578;font-size:.87rem;margin:0 0 20px;line-height:1.6}
.sub a{color:#E55A00;text-decoration:none;font-weight:600}
.live{display:inline-flex;align-items:center;gap:5px;font-size:.72rem;color:#8a8578;
background:#fff;border:1px solid #e6e1d5;border-radius:20px;padding:3px 10px;margin-left:6px}
.live b{width:6px;height:6px;border-radius:50%;background:#4ea87a;display:inline-block}
.th{background:#fff;border:1px solid #ece8de;border-radius:14px;padding:14px 15px;margin-bottom:11px}
.src{font-size:.72rem;color:#a8a294;margin-bottom:9px;display:flex;gap:6px;align-items:baseline}
.src a{color:#8a8578;text-decoration:none;border-bottom:1px solid #e6e1d5;
overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.src a:hover{color:#E55A00;border-bottom-color:#E55A00}
.src .dt{flex:0 0 auto;color:#c0bcb2}
.c{font-size:.93rem;line-height:1.65;padding:7px 0}
.c.rep{padding-left:13px;border-left:2px solid #f0ece2;margin-left:2px}
.c .k{font-weight:700;color:#2b2b2b;margin-right:5px}
.c .g{font-size:.66rem;color:#8a8578;background:#f4f1e9;border-radius:4px;padding:1px 5px;margin-right:4px}
.c .t{color:#c0bcb2;font-size:.7rem;margin-left:5px}
.act{display:inline-flex;gap:11px;margin-left:7px}
.act button{background:none;border:none;padding:2px 0;font-size:.75rem;color:#a8a294;
cursor:pointer;font-family:inherit}
.act button:hover{color:#E55A00}
.act .like.on{color:#E55A00;font-weight:700}
.rf{margin-top:10px;display:none}
.rf.on{display:block}
.rf textarea{width:100%;border:1px solid #e2ded4;border-radius:10px;padding:11px 12px;
font-size:16px;font-family:inherit;resize:none;background:#fff;line-height:1.5}
.rf textarea:focus{outline:none;border-color:#F07040}
.rf .row{display:flex;align-items:center;gap:8px;margin-top:7px}
.rf .who{flex:1;font-size:.78rem;color:#8a8578;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rf button.go{background:#E55A00;color:#fff;border:none;border-radius:9px;padding:9px 17px;
font-size:.82rem;font-weight:700;cursor:pointer;font-family:inherit}
.rf button.go:disabled{background:#e8e4da;color:#b0aca2}
.rf button.x{background:none;border:none;color:#a8a294;font-size:.75rem;cursor:pointer;font-family:inherit}
.empty{color:#a8a294;text-align:center;padding:52px 16px;line-height:1.7}
.empty b{display:block;color:#6b6659;font-size:1rem;margin-bottom:6px}
.new{background:#fdf0e9;border-color:#f6d9c8}
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
    app.innerHTML = '<div class="empty"><b>아직 아무도 말을 걸지 않았어요</b>' +
      '브리핑을 읽다가 한 줄 남기면 여기 모입니다.</div>';
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
  return '<div class="c' + (isRep ? ' rep' : '') + '" data-i="' + c.id + '">' +
    '<span class="k">' + esc(c.nick) + '</span>' +
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
  fetch(API.replace(/[/]$/, '') + '/recent?n=60')
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d && d.off) {
        app.innerHTML = '<div class="empty"><b>코멘트를 잠시 닫았어요</b>곧 다시 열립니다.</div>';
        return;
      }
      render((d && d.items) || []);
    })
    .catch(function () {
      if (first) app.innerHTML = '<div class="empty">불러오지 못했어요.</div>';
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

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>순살 한마디 — 독자들이 남긴 말</title>
<meta name="description" content="순살브리핑 독자들이 스토리마다 남긴 한 줄을 한자리에 모았습니다."/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;800&display=swap" rel="stylesheet"/>
<script src="/ss-config.js"></script>
<style>{CSS}</style></head><body><div class="wrap">
<h1>한마디</h1>
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
