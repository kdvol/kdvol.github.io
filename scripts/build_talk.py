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
.wrap{max-width:600px;margin:0 auto;padding:20px 0 96px}
.hd{padding:0 16px 16px}
h1{font-size:1.44rem;font-weight:800;margin:0 0 5px;letter-spacing:-.025em;color:#f2efe8}
.sub{color:#8b8578;font-size:.86rem;margin:0;line-height:1.6}
.live{display:inline-flex;align-items:center;gap:5px;font-size:.7rem;color:#8b8578;
background:#161616;border:1px solid #262626;border-radius:20px;padding:3px 9px;margin-left:6px}
.live b{width:6px;height:6px;border-radius:50%;background:#4ea87a;display:inline-block;
animation:bp 2.4s ease-in-out infinite}
@keyframes bp{0%,100%{opacity:1}50%{opacity:.35}}

/* 스레드 = 카드가 아니라 '줄'. 트위터처럼 경계선만으로 나눈다 —
   모바일에서 카드마다 테두리가 있으면 화면이 조각조각 나 보인다. */
.th{border-top:1px solid #1c1c1c;padding:15px 16px 7px;transition:background .5s}
.th.new{background:#17130f}
/* 원글이 무슨 이야기였는지가 스레드 머리에 있어야 댓글이 대화로 읽힌다.
   한 줄짜리 회색 링크로는 아무도 안 누르고, 문맥도 안 준다.
   다만 카드가 너무 세면 대화가 아니라 기사 목록처럼 보인다 — 배경을 한 톤만
   올리고 왼쪽에 선을 둬서 '인용된 원글'로 읽히게 한다. */
.src{display:block;text-decoration:none;background:#141414;border:1px solid #1f1f1f;
border-left:2px solid #E55A00;border-radius:8px;padding:10px 13px;margin-bottom:10px}
.src:hover{background:#181818;border-color:#2a2a2a;border-left-color:#F07040}
.src .lb{display:block;font-size:.62rem;font-weight:800;letter-spacing:.07em;
color:#8a6f5c;margin-bottom:4px}
.src .ti{display:block;font-size:.88rem;font-weight:700;letter-spacing:-.02em;
color:#d8d3ca;line-height:1.4}
.src:hover .ti{color:#fff}
/* 두 줄까지만. 더 길면 카드가 대화보다 커진다 */
.src .ld{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
font-size:.78rem;line-height:1.55;color:#7a756c;margin-top:5px}
.src:hover .ld{color:#8f8a80}
.src .mt{display:block;font-size:.68rem;color:#5a554d;margin-top:6px}
.src:hover .mt{color:#E55A00}


/* 코멘트 한 줄 — 아바타 + 본문. 인스타·링크드인 공통 문법이다. */
.c{display:flex;gap:10px;padding:5px 0}
.c.rep{padding-left:30px;position:relative}
.c.rep:before{content:"";position:absolute;left:15px;top:0;bottom:0;width:1.5px;background:#232323}
.av{flex:0 0 auto;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;
justify-content:center;font-size:.78rem;font-weight:800;color:#111;letter-spacing:-.02em}
.c.rep .av{width:26px;height:26px;font-size:.68rem}
.bd{flex:1;min-width:0}
.nm{display:flex;align-items:baseline;gap:6px;flex-wrap:wrap;line-height:1.3}
.nm .k{font-weight:700;color:#f0ede6;font-size:.87rem}
.nm .g{font-size:.65rem;color:#8b8578;background:#1e1e1e;border-radius:4px;padding:1px 6px}
.nm .t{font-size:.7rem;color:#4a453d}
.tx{color:#ccc6bb;font-size:.93rem;line-height:1.62;margin-top:3px;word-break:break-word}
/* 멘션은 '누구에게 하는 말인가'지 강조가 아니다. 주황은 행동(답글·원문 보기)에
   쓰는 색이라 여기 쓰면 본문보다 태그가 먼저 읽힌다. 한 톤 낮추고 굵기만 준다. */
.tx .at{color:#8f8578;font-weight:600}
.c.op .nm .k{color:#F5A481}
.ob{font-size:.62rem;font-weight:700;color:#fff;background:#E55A00;border-radius:4px;padding:1px 6px}
.ob.bot{background:#5a6b7a}

/* 액션 — 아이콘 + 숫자, 탭 영역을 넉넉히 */
.act{display:flex;gap:4px;margin:5px 0 0 -8px}
.act button{display:flex;align-items:center;gap:5px;background:none;border:none;
padding:7px 8px;font-size:.76rem;color:#6b665e;cursor:pointer;font-family:inherit;
border-radius:16px;transition:background .15s,color .15s;min-height:32px}
.act button:hover{background:#1c1c1c;color:#b8b2a8}
.act .like:hover{color:#E55A00}
.act .like.on{color:#E55A00;font-weight:700}
.act .like.on:hover{background:#1f1613}

/* 답글 입력 — 아바타 옆에 붙여 대화가 이어지는 느낌 */
.rf{display:none;gap:10px;padding:9px 0 12px 30px}
.rf.on{display:flex}
.rf .bx{flex:1;min-width:0}
.rf textarea{width:100%;border:1px solid #2a2a2a;border-radius:16px;padding:10px 14px;
font-size:16px;font-family:inherit;resize:none;background:#181818;color:#eee;line-height:1.5}
.rf textarea:focus{outline:none;border-color:#F07040;background:#1c1a18}
.rf .row{display:flex;align-items:center;gap:8px;margin-top:8px}
.rf .who{flex:1;font-size:.74rem;color:#8b8578;overflow:hidden;text-overflow:ellipsis;
white-space:nowrap;cursor:pointer;display:flex;align-items:center;gap:6px}
.rf .who em{font-style:normal;color:#F07040;font-size:.68rem;background:#1f1713;
border-radius:5px;padding:2px 7px;flex:0 0 auto}
.rf .who:hover em{background:#2a1d16}
.rf button.go{background:#E55A00;color:#fff;border:none;border-radius:18px;padding:8px 18px;
font-size:.8rem;font-weight:700;cursor:pointer;font-family:inherit;min-height:34px}
.rf button.go:disabled{background:#242424;color:#5f5a52}
.rf button.x{background:none;border:none;color:#6b665e;font-size:.76rem;cursor:pointer;
font-family:inherit;padding:8px 4px}

.empty{color:#7a756c;text-align:center;padding:56px 20px;line-height:1.75;font-size:.9rem}
.empty b{display:block;color:#f0ede6;font-size:1.14rem;margin-bottom:10px;letter-spacing:-.02em}
.empty .ecta{display:inline-block;margin-top:20px;background:#E55A00;color:#fff;
text-decoration:none;font-weight:700;font-size:.87rem;border-radius:22px;padding:13px 24px}
.empty .ecta:hover{background:#F07040}

/* 브리핑으로 돌아가는 길만 작게 남긴다. 내용보다 커 보이지 않게 함 */
.fab{position:fixed;right:18px;bottom:calc(18px + env(safe-area-inset-bottom));z-index:50}
.fab a{display:inline-flex;align-items:center;gap:8px;background:#211d1a;border:0;
border-radius:999px;padding:10px 14px;color:#b7afa5;font-size:.8rem;font-weight:700;
text-decoration:none;box-shadow:0 10px 28px rgba(0,0,0,.28)}
.fab a:hover{background:#29231f;color:#f4eee7}
.fab .arrow{color:#F07040;font-size:1rem;line-height:1}
@media(min-width:620px){.wrap{padding-bottom:80px}}
"""


JS = r"""
// ss-config.js 하나가 못 뜨면(네트워크 블립·차단기) 페이지 전체가
// '불러오지 못했습니다'가 된다. 주소는 공개값이라 여기 적어 둔다.
var API = (window.SS_CFG && window.SS_CFG.worker) || 'https://soonsal-react.kd-d0a.workers.dev';
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
// 이름에서 색을 뽑아 아바타를 만든다. 이미지 없이도 누가 누군지 구분된다.
var AVC = ['#F0A070','#8FB0A0','#A09CD8','#D89AA8','#C8B060','#7FA8C8','#B8A090','#98B87F'];
function avatar(nick, isOp) {
  var h = 0, s = String(nick || '?');
  for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  var bg = isOp === 2 ? '#5a6b7a' : isOp ? '#E55A00' : AVC[h % AVC.length];
  var ch = s.replace(/[^가-힣A-Za-z0-9]/g, '').charAt(0) || '?';
  return '<span class="av" style="background:' + bg + (isOp ? ';color:#fff' : '') + '">' +
    esc(ch) + '</span>';
}

function whoLabel() {
  var n = prof().n || '';
  return (n ? esc(n) : '이름 없음') + '<em>✎ 바꾸기</em>';
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
  var m = SMAP[story], x = /^(\d{4})(c?)-(\d+)$/.exec(story);
  if (!m || !x) return '#';
  return '/newsletters/' + m.y + '/' + x[1] + (x[2] ? '-crypto' : '') +
         '.html#story-' + x[3];
}
// 0812-3 → 08.12. 날짜를 따로 심지 않는다.
function sdate(story) {
  var x = /^(\d{2})(\d{2})c?-/.exec(story);
  return x ? x[1] + '.' + x[2] : '';
}
function slabel(story) {
  var m = SMAP[story];
  return m && m.l ? m.l : '';
}
function slead(story) {
  var m = SMAP[story];
  return m && m.s ? m.s : '';
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
  NICK = {};
  items.forEach(function (c) {
    NICK[c.id] = c.nick;
    if (!roots[c.root_id]) { roots[c.root_id] = []; order.push(c.root_id); }
    roots[c.root_id].push(c);
  });

  var html = order.map(function (rid) {
    var list = roots[rid], head = list[0];
    var isNew = !first && !seen[head.id];
    return '<div class="th' + (isNew ? ' new' : '') + '" data-r="' + rid + '">' +
      '<a class="src" href="' + href(head.story) + '">' +
        (slabel(head.story) ? '<span class="lb">' + esc(slabel(head.story)) + '</span>' : '') +
        '<span class="ti">' + esc(label(head.story)) + '</span>' +
        (slead(head.story) ? '<span class="ld">' + esc(slead(head.story)) + '…</span>' : '') +
        '<span class="mt">' + sdate(head.story) + ' 브리핑 · 원문 보기 →</span>' +
      '</a>' +

      list.map(function (c) { return one(c, c.parent_id); }).join('') +
      '<div class="rf" data-r="' + rid + '">' +
        '<div class="bx">' +
          '<textarea rows="1" maxlength="140" placeholder="답글 남기기"></textarea>' +
          '<div class="row"><span class="who"></span>' +
            '<button type="button" class="x">취소</button>' +
            '<button type="button" class="go" disabled>남기기</button></div>' +
        '</div>' +
      '</div></div>';
  }).join('');
  app.innerHTML = html;
  items.forEach(function (c) { seen[c.id] = 1; });
  first = false;
  wire();
}

var NICK = {};   // id → 닉네임. 답글 본문의 @태그를 정확히 집어내는 데 쓴다

function atHTML(body, toNick) {
  var s = esc(body);
  if (!toNick) return s;
  var tag = esc('@' + toNick);
  return s.indexOf(tag) === 0
    ? '<span class="at">' + tag + '</span>' + s.slice(tag.length)
    : s;
}

function one(c, isRep) {
  var tag = [c.tag, c.co].filter(Boolean).join(' · ');
  return '<div class="c' + (isRep ? ' rep' : '') + (c.op ? ' op' : '') +
    '" data-i="' + c.id + '">' +
    avatar(c.nick, c.op) +
    '<div class="bd">' +
      '<div class="nm"><span class="k">' + esc(c.nick) + '</span>' +
        (c.op ? '<span class="ob' + (c.op === 2 ? ' bot' : '') + '">' +
          (c.op === 2 ? '🤖 봇' : '순살 팀') + '</span>' : '') +
        (tag ? '<span class="g">' + esc(tag) + '</span>' : '') +
        '<span class="t">' + ago(c.ts) + '</span></div>' +
      '<div class="tx">' + atHTML(c.body, NICK[c.parent_id] || '') + '</div>' +
      '<div class="act">' +
        '<button type="button" class="like' + (liked[c.id] ? ' on' : '') +
          '" data-i="' + c.id + '">' + (liked[c.id] ? '♥' : '♡') +
          '<span>' + (c.likes || '') + '</span></button>' +
        '<button type="button" class="repb" data-i="' + c.id +
          '" data-k="' + esc(c.nick) + '" data-s="' + esc(c.story) + '">' +
          '↩ <span>답글</span></button>' +
      '</div>' +
    '</div></div>';
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
        b.innerHTML = (res.on ? '♥' : '♡') + '<span>' + (res.n || '') + '</span>';
      }).catch(function () { b.disabled = false; });
    });
  });

  app.querySelectorAll('.repb').forEach(function (b) {
    b.addEventListener('click', function () {
      var th = b.closest('.th'), rf = th.querySelector('.rf');
      var ta = rf.querySelector('textarea'), go = rf.querySelector('.go');
      rf.className = 'rf on';
      // 답글 버튼이 그대로 있으면 같은 기능이 두 군데 있는 것처럼 보인다
      th.querySelectorAll('.repb').forEach(function (x) { x.style.visibility = 'hidden'; });
      rf._btns = th;
      rf._pid = parseInt(b.getAttribute('data-i'), 10);
      rf._story = b.getAttribute('data-s');
      var tag = '@' + b.getAttribute('data-k') + ' ';
      if (ta.value.indexOf('@') !== 0) ta.value = tag + ta.value;
      rf.querySelector('.who').innerHTML = whoLabel();
      go.disabled = !ta.value.trim();
      ta.focus();
    });
  });

  // 답글 폼의 '누구로' 줄을 눌러 이름을 바꾼다. 스토리 댓글창에만 있고
  // 여기엔 없어서, 순살톡에서 답글만 다는 사람은 이름을 못 바꿨다.
  app.querySelectorAll('.who').forEach(function (el) {
    el.addEventListener('click', function () {
      var p = prof();
      var v = prompt('이름을 바꿔요 (12자까지)', p.n || '');
      if (v === null) return;
      v = v.trim().slice(0, 12);
      if (!v) return;
      p.n = v;
      try { localStorage.setItem('ss_prof', JSON.stringify(p));
            localStorage.setItem('ss_nick', v); } catch (e) {}
      app.querySelectorAll('.who').forEach(function (x) {
        if (x.textContent) x.innerHTML = whoLabel();
      });
    });
  });

  app.querySelectorAll('.rf').forEach(function (rf) {
    var ta = rf.querySelector('textarea'), go = rf.querySelector('.go');
    ta.addEventListener('input', function () {
      go.disabled = !ta.value.trim();
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
    });
    ta.addEventListener('focus', function () { typing = true; });
    ta.addEventListener('blur', function () { typing = false; });
    rf.querySelector('.x').addEventListener('click', function () {
      rf.className = 'rf'; ta.value = ''; typing = false;
      if (rf._btns) rf._btns.querySelectorAll('.repb').forEach(function (x) {
        x.style.visibility = '';
      });
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
      story: rf._story, v: v, nick: p.n || '순살러', body: body,
      tag: p.i || '', co: p.sc ? (p.c || '') : '', parent: rf._pid || 0,
    }),
  }).then(function (r) { return r.json(); }).then(function (res) {
    go.disabled = false;
    if (res && res.error) { alert('남기지 못했어요'); return; }
    ta.value = ''; rf.className = 'rf'; typing = false;
    if (rf._btns) rf._btns.querySelectorAll('.repb').forEach(function (x) { x.style.visibility = ''; });
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


def _lead(body: str) -> str:
    """첫 불렛의 앞머리. 카드에서 두 줄로 잘려 보이므로 넉넉히 80자만 남긴다."""
    b = re.sub(r"<[^>]+>", "", body or "")
    parts = b.split("◾")
    s = parts[1] if len(parts) > 1 else b
    s = re.sub(r"\s+", " ", s).strip()
    return s[:80]


def build(atoms=None):
    if atoms is None:
        atoms = json.loads(ATOMS.read_text(encoding="utf-8")) if ATOMS.exists() else []
    OUT.mkdir(exist_ok=True)

    recent = sorted(atoms, key=lambda a: a.get("date", ""), reverse=True)[:600]
    # 주소는 id에서 되살릴 수 있다(0716c-4 → /newsletters/2026/0716-crypto.html#story-4).
    # 600건 × 38자를 심을 이유가 없다. 그 자리를 섹션 라벨에 쓴다 — 카드에서
    # '무슨 이야기인지'를 먼저 알려주는 건 제목보다 라벨이다.
    # 제목만으로는 '무슨 이야기에 달린 댓글인지' 안 잡힌다. 첫 불렛 앞머리를
    # 같이 심는다. 다만 600건 전부에 붙이면 전송량이 20KB → 63KB가 된다.
    # 댓글은 최근 회차에 달리니 최근 150건에만 붙이고 나머지는 제목까지만.
    LEAD_N = 150
    smap = {}
    for i, a in enumerate(recent):
        d = {"t": re.sub(r"^[^\w<>&\"']{1,4}\s+", "", a["title"]).strip()[:44],
             "l": (a.get("label") or "")[:26],
             "y": a.get("date", "")[:4]}
        if i < LEAD_N:
            s = _lead(a.get("body", ""))
            if s:
                d["s"] = s
        smap[a["id"]] = d

    try:
        import build_nav
        nav = "<style>" + build_nav.HEADER_CSS + "</style>" + build_nav.header_html("/talk/")
    except Exception:
        nav = ""

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>순살톡 — 순살러들이 남긴 말</title>
<meta name="description" content="순살브리핑을 읽는 순살러들이 스토리마다 남긴 한 줄을 한자리에 모았습니다. 금융·경제 뉴스에 대한 의견과 질문 — 순살톡."/>
<link rel="canonical" href="https://soonsal.com/talk/"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="순살톡 — 순살러들이 남긴 한마디"/>
<meta property="og:description" content="브리핑을 읽다 남긴 한 줄이 회차 상관없이 여기 모입니다."/>
<meta property="og:url" content="https://soonsal.com/talk/"/>
<script type="application/ld+json">{{
"@context":"https://schema.org","@type":"CollectionPage",
"name":"순살톡 — 순살러 한마디","url":"https://soonsal.com/talk/",
"inLanguage":"ko","isPartOf":{{"@type":"WebSite","name":"순살브리핑","url":"https://soonsal.com/"}},
"about":{{"@type":"Thing","name":"글로벌 금융·경제·크립토 뉴스에 대한 순살러 의견"}},
"publisher":{{"@type":"Organization","name":"순살브리핑","url":"https://soonsal.com/"}}
}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;800&display=swap" rel="stylesheet"/>
<script src="/ss-config.js"></script>
<style>{CSS}</style></head><body>
{nav}
<div class="wrap">
<div class="hd">
<h1>순살톡<span class="live"><b></b>실시간</span></h1>
<p class="sub">브리핑을 읽다 남긴 한 줄이 회차 상관없이 여기 모입니다.</p>
</div>
<div id="app"><div class="empty">불러오는 중…</div></div>
</div>
<div class="fab"><a href="/"><span aria-hidden="true">💬</span>
<span>브리핑에 한마디 남기기</span><span class="arrow" aria-hidden="true">→</span></a></div>
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
