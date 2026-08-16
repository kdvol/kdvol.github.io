#!/usr/bin/env python3
"""운영자용 반응 통계 페이지 (/stats/).

스토리별 👍🤔🔥 집계를 한 화면에 보여준다. 데이터는 Cloudflare Worker(D1)의
/counts 엔드포인트에서 브라우저가 직접 읽는다. 미설정 시엔 설정 안내를 표시.
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
/* 기간 고르개 — 어떤 범위를 보고 있는지 화면에 늘 적혀 있어야 한다 */
/* 기간 고르개 — 손가락으로 누른다. 가로 스크롤로 넘긴다 */
.rng{display:flex;gap:6px;overflow-x:auto;-webkit-overflow-scrolling:touch;
padding:2px 0 4px;margin:10px 0 2px;scrollbar-width:none}
.rng::-webkit-scrollbar{display:none}
.rng button{flex:0 0 auto;font:inherit;font-size:13px;font-weight:700;padding:9px 15px;
border-radius:999px;border:1px solid #ddd6cb;background:#fff;color:#6b665e;cursor:pointer;
min-height:40px}
.rng button.on{background:#1e1e1e;border-color:#1e1e1e;color:#fff}
/* 차트 둘을 나란히, 좁으면 위아래로 */
.two{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.ch .cht{font-size:12px;font-weight:800;color:#6b665e;margin-bottom:8px}
.ch .trend{display:flex;align-items:flex-end;gap:2px;height:58px}
.ch .trend i{flex:1;border-radius:2px 2px 0 0;min-width:2px}
details.cov{margin-top:18px}
details.cov summary{cursor:pointer;font-size:12px;color:#8a857c;font-weight:700}
@media(max-width:560px){
  .two{grid-template-columns:1fr}
  h2{font-size:15px;margin-top:22px}
  .sum{grid-template-columns:1fr 1fr;gap:8px}
  .kpi .v{font-size:26px}
  .rng button{padding:10px 14px}
}
.daybar{display:flex;align-items:center;gap:9px;margin:10px 0 4px;flex-wrap:wrap}
/* [hidden] 은 UA 규칙이라 위 display:flex 에 진다. 명시적으로 이긴다 */
.daybar[hidden]{display:none}
.daybar label{font-size:12px;color:#8a857c;font-weight:700}
.daybar select{font:inherit;font-size:13px;padding:6px 10px;border-radius:8px;
border:1px solid #ddd6cb;background:#fff;color:#2b2b2b}
.daybar .scope{font-size:12px;color:#9a958a}
@media(max-width:560px){.daybar select{flex:1;min-width:0}}
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
.kpi{background:#161616;border:1px solid #232323;border-radius:12px;padding:12px 16px;min-width:104px}
.kpi .v{font-size:1.5rem;font-weight:800;color:#F07040;line-height:1.2}
.kpi .l{font-size:.75rem;color:#888;margin-top:2px}
.row{display:flex;gap:12px;align-items:baseline;padding:12px 4px;border-bottom:1px solid #1c1c1c}
.dt{color:#666;font-size:.76rem;white-space:nowrap;font-variant-numeric:tabular-nums;padding-top:2px}
.ti{flex:1;font-size:.94rem;line-height:1.45}
.row:hover .ti{color:#F07040}
.cnt{display:flex;gap:9px;white-space:nowrap;font-size:.85rem;color:#aaa;font-variant-numeric:tabular-nums}
.cnt span.z{color:#3a3a3a}
.when{color:#5c5c5c;font-size:.74rem;white-space:nowrap;padding-top:3px}
.spark{background:#161616;border:1px solid #232323;border-radius:12px;padding:12px 16px 10px;margin-bottom:6px}
.spark .sl{font-size:.75rem;color:#888;margin-bottom:9px}
.spark .bars{display:flex;align-items:flex-end;gap:3px;height:36px}
.spark .bars i{flex:1;background:#F07040;border-radius:2px 2px 0 0;opacity:.85;min-height:2px}
@media(max-width:520px){.when{display:none}.row{gap:9px}}
.empty{color:#777;font-size:.9rem;padding:22px 4px}
h2{font-size:.95rem;color:#ddd;margin:30px 0 10px;letter-spacing:-.01em}
h2 small{color:#666;font-weight:400;font-size:.78rem;margin-left:7px}
.kpi.hero .v{font-size:1.9rem}
.kpi .d{font-size:.7rem;color:#5f5f5f;margin-top:3px}
.card{background:#161616;border:1px solid #232323;border-radius:12px;padding:14px 16px;margin-bottom:10px}
.trend{display:flex;align-items:flex-end;gap:2px;height:64px;margin-top:4px;justify-content:flex-start}
.trend i{flex:1 1 0;max-width:28px;background:#F07040;border-radius:2px 2px 0 0;min-height:2px;opacity:.85;position:relative}
.trend i.u{background:#3f6fd8}
.tl{display:flex;justify-content:space-between;font-size:.7rem;color:#5f5f5f;margin-top:6px}
.lgd{display:flex;gap:14px;font-size:.72rem;color:#888;margin-top:8px}
.lgd b{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:5px}
.bar{display:flex;align-items:center;gap:10px;padding:7px 2px;font-size:.85rem}
.bar .nm{width:104px;color:#bbb;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar .tr{flex:1;background:#1c1c1c;border-radius:3px;height:9px;overflow:hidden}
.bar .fl{height:100%;background:#F07040;border-radius:3px}
.bar .vn{width:62px;text-align:right;color:#999;font-variant-numeric:tabular-nums;font-size:.8rem}
.note{color:#5f5f5f;font-size:.75rem;line-height:1.7;margin-top:10px}
.tabs{display:flex;gap:6px;margin-bottom:16px}
.tabs button{background:#161616;border:1px solid #232323;color:#888;border-radius:7px;padding:6px 13px;
font-size:.8rem;cursor:pointer;font-family:inherit}
.tabs button.on{border-color:#F07040;color:#F07040}
.hop{display:flex;align-items:center;gap:8px;padding:8px 2px;border-bottom:1px solid #1c1c1c;font-size:.82rem}
.hop .p{color:#ddd;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hop .ar{color:#5f5f5f;flex:0 0 auto}
.hop b{color:#F07040;font-weight:700;flex:0 0 auto}
.sortbar{margin:18px 0 4px;align-items:center}
.sortbar .cn{color:#5f5f5f;font-size:.74rem;margin-left:auto}
#more{text-align:center;padding:14px 0}
#more button.more{background:#151515;border:1px solid #262626;color:#8a8578;border-radius:8px;
padding:9px 20px;font-size:.8rem;cursor:pointer;font-family:inherit}
#more button.more:hover{border-color:#F07040;color:#F07040}
.cm{display:flex;gap:10px;padding:10px 2px;border-bottom:1px solid #1c1c1c;font-size:.86rem;line-height:1.6}
.cm .k{color:#8a8578;font-weight:700;white-space:nowrap;font-size:.78rem;padding-top:2px}
.cm .b{flex:1;color:#ddd;word-break:break-word}
.cm .s{color:#666;font-size:.72rem;white-space:nowrap;padding-top:3px}
.cm .j{color:#5f5f5f;font-size:.72rem;display:block;margin-top:3px}
.tag{display:inline-block;font-size:.68rem;padding:1px 6px;border-radius:4px;margin-right:5px;
border:1px solid #333;color:#999}
.tag.hold{border-color:#7a5a20;color:#c99a3a}
.tag.spam{border-color:#7a2020;color:#d06060}
.tag.live{border-color:#20603a;color:#4ea87a}
.act{display:flex;gap:5px;white-space:nowrap}
.act button{background:#1c1c1c;border:1px solid #2c2c2c;color:#999;border-radius:6px;padding:3px 9px;
font-size:.72rem;cursor:pointer;font-family:inherit}
.act button:hover{border-color:#F07040;color:#F07040}
"""

DASH_JS = r"""
var EMO = ['👍','🤔','🔥'];
var SS = window.SS_CFG || { worker: 'https://api.soonsal.com' };
var API = SS.worker || null;
var app = document.getElementById('app');
var D = {};                    // counts / activity / insights
var TAB = 'community';

// ── 공통 ─────────────────────────────────────────────────
function ago(ts, now) {
  if (!ts) return '';
  var s = Math.max(0, now - ts);
  if (s < 60) return '방금';
  if (s < 3600) return Math.floor(s / 60) + '분 전';
  if (s < 86400) return Math.floor(s / 3600) + '시간 전';
  return Math.floor(s / 86400) + '일 전';
}
function pct(a, b) { return b > 0 ? Math.round(a / b * 100) : 0; }
// id에서 경로를 되살린다 — SMAP에 url을 담으면 항목당 40바이트가 더 붙는다.
//   0811-3  → /newsletters/2026/0811.html#story-3
//   0811c-2 → /newsletters/2026/0811c.html#story-2
function sUrl(id) {
  var m = String(id).match(/^(\d{4})(c?)-(\d+)$/);
  if (!m) return '#';
  return '/newsletters/' + SYEAR + '/' + m[1] + m[2] + '.html#story-' + m[3];
}

var PMAP = (function () {
  var o = {};
  Object.keys(SMAP).forEach(function (k) {
    var u = sUrl(k).split('#')[0];
    if (u && !o[u]) o[u] = (SMAP[k].d || '') + ' 브리핑';
  });
  return o;
})();

function pname(p) {
  var m = PMAP[p];
  if (m) return m;
  return String(p || '').replace(/^\/(newsletters|topics|english)\//, '').replace(/\.html$/, '') || '/';
}
function kpi(v, l, d, hero) {
  return '<div class="kpi' + (hero ? ' hero' : '') + '"><div class="v">' + v + '</div>' +
         '<div class="l">' + l + '</div>' + (d ? '<div class="d">' + d + '</div>' : '') + '</div>';
}
function bars(items, unit) {
  var max = 0;
  items.forEach(function (i) { if (i[1] > max) max = i[1]; });
  if (!max) return '<div class="empty">아직 데이터가 없습니다.</div>';
  return items.map(function (i) {
    return '<div class="bar"><span class="nm" title="' + i[0] + '">' + i[0] + '</span>' +
      '<span class="tr"><span class="fl" style="width:' + Math.max(2, i[1] / max * 100) + '%"></span></span>' +
      '<span class="vn">' + i[1] + (unit || '') + '</span></div>';
  }).join('');
}
// 대시보드 전체가 관리자 키를 요구한다. 방문 수치는 광고 단가 협상에 쓰이는
// 영업 정보라 주소만 알면 열리는 상태로 두지 않는다.
function gate() {
  app.innerHTML = '<div class="card"><b style="color:#F07040">잠겨 있습니다</b>' +
    '<p class="note">운영자 대시보드입니다. 관리자 키를 한 번 넣으면 이 브라우저에 저장됩니다.</p>' +
    '<div class="tabs" style="margin-top:12px"><button id="gk">관리자 키 입력</button></div></div>';
  document.getElementById('gk').addEventListener('click', function () {
    var k = prompt('관리자 키');
    if (!k) return;
    try { localStorage.setItem('ss_admin', k.trim()); } catch (e) {}
    ADMIN = k.trim();
    location.reload();
  });
}

function setup() {
  app.innerHTML = '<div class="setup"><h2>아직 집계 저장소가 연결되지 않았습니다</h2>' +
    '<p style="color:#bbb;font-size:.9rem;margin-bottom:12px">Cloudflare Worker + D1(무료)을 ' +
    '연결하면 방문·반응이 이 화면에 쌓입니다.</p>' +
    '<ol><li>리포의 <code>workers/</code>에서 <code>npx wrangler d1 create soonsal-react</code></li>' +
    '<li>출력된 <code>database_id</code>를 <code>wrangler.toml</code>의 ' +
    '<code>[[d1_databases]]</code>에 넣기 (binding: <code>DB</code>)</li>' +
    '<li><code>npx wrangler d1 execute soonsal-react --remote --file schema.sql</code></li>' +
    '<li><code>npx wrangler deploy</code> 후 배포 주소를 <code>/ss-config.js</code>에 입력</li></ol>' +
    '<p style="color:#777;font-size:.82rem;margin-top:12px">※ KV는 쓰지 않습니다. ' +
    'list 한도(1,000회/일)가 페이지뷰마다 소진돼 2026-08-07에 D1으로 이전했습니다.</p></div>';
}

// ── 커뮤니티(방문) 화면 ──────────────────────────────────
var SRC_KO = { direct: '직접·북마크', telegram: '텔레그램', instagram: '인스타그램',
               search: '검색', mail: '뉴스레터', other: '기타' };
// 모으고 있는데 화면에 없던 것들: comment·school·talk·home·finish.
// finish·home 은 워커가 아예 버리고 있어 값이 0 이었다 (2026-08-16 수정).
var KIND_KO = { human: '사람 확인(손이 움직임)', read: '끝까지 읽음',
  finish: '완독 도장', react: '반응',
  comment: '댓글 작성', subscribe: '구독 버튼 클릭',
  talk: '순살톡 이동', school: '스쿨 이동', home: '홈으로',
  share: '공유', telegram: '텔레그램 이동',
                instagram: '인스타 이동' };

function renderCommunity() {
  var ins = D.insights;
  if (!ins) { app.innerHTML = '<div class="empty">방문 집계를 불러오지 못했습니다.</div>'; return; }
  var daily = ins.daily || [], v = ins.visitors || {}, L = ins.lifetime || {};
  if (!daily.length) {
    app.innerHTML = '<div class="card"><b style="color:#F07040">아직 방문 기록이 없습니다.</b>' +
      '<p class="note">방금 붙인 집계라 지금부터 쌓입니다.</p></div>';
    return;
  }

  // ── 기간·커버리지 ────────────────────────────────────────────────
  var COV = ins.coverage || {}, KC = COV.kinds || {};
  var DAU = {}, FRESH = {};
  (ins.dau || []).forEach(function (r) { DAU[r.day] = r.people; });
  (ins.freshDaily || []).forEach(function (r) { FRESH[r.day] = r.n; });
  var days = daily.map(function (d) { return d.day; });

  // 비율은 **두 값이 같은 날짜에서 나올 때만** 낸다. 시작일 당일은 반쪽이라 뺀다.
  function daysFor(kind) {
    var from = kind ? KC[kind] : COV.dau;
    return days.filter(function (d) {
      return DAU[d] !== undefined && (!COV.dau || d > COV.dau) && (!from || d > from);
    });
  }
  function sumEng(ds, kinds) {
    var n = 0;
    (ins.engage || []).forEach(function (e) {
      if (ds.indexOf(e.day) >= 0 && (!kinds || kinds.indexOf(e.kind) >= 0)) n += e.n;
    });
    return n;
  }
  function people(ds) { var n = 0; ds.forEach(function (d) { n += (DAU[d] || 0); }); return n; }
  function label(ds) {
    if (!ds.length) return '';
    return ds.length === 1 ? ds[0] : ds[0].slice(5) + '~' + ds[ds.length - 1].slice(5);
  }
  // 비율을 못 내면 왜 못 내는지 말한다. 숫자를 지어내지 않는다.
  function why(kind) {
    var from = kind ? KC[kind] : COV.dau;
    if (!COV.dau) return '방문자 집계 전';
    if (kind && !from) return '이 항목 집계 전';
    return (from > COV.dau ? from : COV.dau) + ' 시작 — 내일부터';
  }
  function ratio(num, ds, lbl) {
    if (!ds.length) return null;
    var den = people(ds);
    if (!den) return null;
    return { v: pct(num, den) + '%', d: num + ' / ' + den + '명 · ' + label(ds) };
  }

  var winDays = daysFor(null);
  var scope = ins.scope || ('최근 ' + ins.days + '일');
  var h = '';

  // ═══ 0. 기본 — 몇 명이 몇 번 봤나 ══════════════════════════════
  //   개편하면서 이걸 없앴다. 우선순위를 매긴다고 "판단용 지표"만 남겼는데,
  //   대시보드를 열었을 때 제일 먼저 알고 싶은 건 그냥 규모다 (KD 2026-08-16).
  var sumHits = 0, sumUniq = 0;
  daily.forEach(function (d) { sumHits += d.hits; sumUniq += d.uniq; });
  var sumPeople = people(days.filter(function (d) { return DAU[d] !== undefined; }));
  var last = daily[daily.length - 1] || { hits: 0, uniq: 0, day: '' };
  var lastPeople = DAU[last.day];

  h += '<h2>' + scope + '</h2><div class="sum">' +
    kpi(sumHits.toLocaleString(), '페이지뷰', '이 기간 열린 횟수', true) +
    (sumPeople
      ? kpi(sumPeople.toLocaleString(), '방문자', '사람 수 · ' + label(days.filter(function (d) { return DAU[d] !== undefined; })), true)
      : kpi('—', '방문자', why(null), true)) +
    kpi(sumUniq.toLocaleString(), '페이지 열람', '한 사람이 3개 글 보면 3', true) +
    kpi(daily.length, '집계된 날', last.day || '', true) +
    '</div>';

  h += '<h2>가장 최근 하루 <small>' + (last.day || '') + '</small></h2><div class="sum">' +
    kpi(last.hits.toLocaleString(), '페이지뷰', null, true) +
    (lastPeople === undefined
      ? kpi('—', '방문자', '이 날짜는 집계 전', true)
      : kpi(lastPeople.toLocaleString(), '방문자', '사람 수', true)) +
    kpi(sumEng([last.day], ['react']), '반응', null, true) +
    kpi(sumEng([last.day], ['comment']), '댓글', null, true) +
    '</div>';

  // ═══ 1. 읽은 사람 — 뉴스레터 사업의 핵심 숫자 ═══════════════════
  var iss = ins.issues || [];
  var totalReaders = 0;
  iss.forEach(function (r) { totalReaders += r.people; });
  h += '<h2>1. 읽은 사람 <small>' + scope + '</small></h2>';
  if (iss.length) {
    h += '<div class="sum">' +
      kpi(totalReaders, '회차 열람 합계', '메일 링크로 들어온 구독자', true) +
      kpi(iss.length, '회차 수', null, true) +
      kpi(Math.round(totalReaders / iss.length), '회차당 평균', '명', true) +
      '</div><div class="card">' +
      bars(iss.map(function (r) { return [r.iss, r.people]; }), '명') +
      '<p class="note">같은 분이 여러 번 열어도 한 명입니다.</p></div>';
  } else {
    h += '<div class="card"><p class="note"><b>아직 셀 수 없습니다.</b> ' +
      '스티비 링크에 <code>?s=$%web_tag%$&i=회차</code> 를 붙여야 쌓입니다. ' +
      '이게 이 화면에서 가장 중요한 숫자입니다.</p></div>';
  }

  // ═══ 2. 사람인가 — 광고주에게 낼 수 있는 유일한 정직한 숫자 ══════
  var hd = daysFor('human');
  var hHits = 0;
  daily.forEach(function (d) { if (hd.indexOf(d.day) >= 0) hHits += d.hits; });
  var hCnt = sumEng(hd, ['human']);
  h += '<h2>2. 진짜 사람인가 <small>메일 보안 자동 클릭 걸러내기</small></h2><div class="sum">' +
    (hd.length && hHits
      ? kpi(pct(hCnt, hHits) + '%', '사람 확인 비율', hCnt + ' / ' + hHits + '뷰 · ' + label(hd), true)
      : kpi('—', '사람 확인 비율', why('human'), true)) +
    '</div><p class="note">마우스·터치·키 입력이 실제로 들어온 열람의 비율입니다. ' +
    '보안 스캐너는 링크를 눌러도 손이 움직이지 않습니다.</p>';

  // ═══ 3. 구독으로 이어지나 ═══════════════════════════════════════
  var sd = daysFor('subscribe');
  var sr = ratio(sumEng(sd, ['subscribe']), sd);
  h += '<h2>3. 구독으로 이어지나 <small>사이트의 유일한 전환점</small></h2><div class="sum">' +
    kpi(sumEng(days, ['subscribe']), '구독 버튼 클릭', scope, true) +
    (sr ? kpi(sr.v, '전환율', sr.d, true) : kpi('—', '전환율', why('subscribe'), true)) +
    '</div>';

  // ═══ 4. 다시 오나 ═══════════════════════════════════════════════
  var fresh = 0;
  winDays.forEach(function (d) { fresh += (FRESH[d] || 0); });
  var ppl = people(winDays);
  h += '<h2>4. 다시 오나</h2><div class="sum">' +
    (winDays.length
      ? kpi(fresh + ' / ' + Math.max(0, ppl - fresh), '새 사람 / 다시 온 사람',
            pct(Math.max(0, ppl - fresh), ppl) + '% 가 재방문 · ' + label(winDays), true)
      : kpi('—', '새 사람 / 다시 온 사람', why(null), true)) +
    kpi(pct(L.repeat_v, L.people) + '%', '전체 기간 재방문',
        (L.repeat_v || 0) + ' / ' + (L.people || 0) + '개 브라우저', true) +
    '</div>' +
    '<p class="note">「브라우저」이지 사람이 아닙니다. 메일 앱에서 열면 저장소가 매번 ' +
    '비워져 같은 분이 새 브라우저로 잡힙니다. 위 <b>1번</b>이 그걸 대신할 숫자입니다.</p>';

  // ═══ 5. 얼마나 오나 — 페이지뷰와 방문자를 따로 본다 ══════════════
  h += '<h2>5. 얼마나 오나 <small>' + scope + '</small></h2>';
  var maxH = 1, maxP = 1;
  daily.forEach(function (d) {
    if (d.hits > maxH) maxH = d.hits;
    if ((DAU[d.day] || 0) > maxP) maxP = DAU[d.day];
  });
  function chart(title, pick, max, color, note) {
    var any = daily.some(function (d) { return pick(d) !== null; });
    return '<div class="card ch"><div class="cht">' + title + '</div>' +
      (any ? '<div class="trend">' + daily.map(function (d) {
        var val = pick(d);
        return '<i style="height:' + (val === null ? 2 : Math.max(2, val / max * 56)) +
          'px;background:' + (val === null ? '#3a3a3a' : color) + '" title="' + d.day +
          ' · ' + (val === null ? '집계 전' : val) + '"></i>';
      }).join('') + '</div><div class="tl"><span>' + days[0].slice(5) + '</span><span>' +
        days[days.length - 1].slice(5) + '</span></div>'
        : '<div class="empty">집계 전</div>') +
      (note ? '<p class="note">' + note + '</p>' : '') + '</div>';
  }
  h += '<div class="two">' +
    chart('페이지뷰', function (d) { return d.hits; }, maxH, '#F07040',
          '열린 횟수. 사람 수가 아닙니다') +
    chart('방문자 수', function (d) { return DAU[d.day] === undefined ? null : DAU[d.day]; },
          maxP, '#3f6fd8', '실제 사람 수. 회색은 집계 전') +
    '</div>';

  // ═══ 6. 무엇이 읽히나 ═══════════════════════════════════════════
  var top = ins.top || [];
  if (top.length) {
    h += '<h2>6. 무엇이 읽히나</h2><div class="card">' +
      bars(top.slice(0, 10).map(function (r) {
        return [r.path.replace(/^\/newsletters\/\d{4}\//, '').replace(/\.html$/, ''), r.hits];
      }), '뷰') + '</div>';
  }

  // ═══ 7. 어디서 오나 ═════════════════════════════════════════════
  var refs = ins.refs || [];
  if (refs.length) {
    h += '<h2>7. 어디서 오나</h2><div class="card">' +
      bars(refs.map(function (r) { return [SRC_KO[r.src] || r.src, r.n]; }), '') +
      '<p class="note">메일 앱은 유입 정보를 주지 않아 「직접」으로 잡힙니다. ' +
      '위 <b>1번</b>이 그 부분을 갈라 줍니다.</p></div>';
  }

  // ═══ 8. 무엇을 하나 ═════════════════════════════════════════════
  var eng = {};
  (ins.engage || []).forEach(function (e) { eng[e.kind] = (eng[e.kind] || 0) + e.n; });
  h += '<h2>8. 무엇을 하나 <small>' + scope + ' 합계</small></h2><div class="card">' +
    bars(Object.keys(KIND_KO).map(function (k) { return [KIND_KO[k], eng[k] || 0]; }), '건') +
    '</div>';

  // ═══ 9. 아카이브가 자산인가 ═════════════════════════════════════
  var recent = 0, archive = 0;
  top.forEach(function (r) {
    var m = /\/(\d{4})\/(\d{4})/.exec(r.path);
    if (!m) { archive += r.hits; return; }
    var d = m[1] + '-' + m[2].slice(0, 2) + '-' + m[2].slice(2);
    (d >= days[0]) ? recent += r.hits : archive += r.hits;
  });
  var lifeTot = recent + archive;
  h += '<h2>9. 아카이브가 자산인가</h2><div class="sum">' +
    (lifeTot ? kpi(pct(archive, lifeTot) + '%', '지난 글이 먹은 조회',
                   archive + ' / ' + lifeTot + '뷰', true)
             : kpi('—', '지난 글이 먹은 조회', '표본 없음', true)) +
    kpi(L.people || 0, '누적 브라우저', (L.hits || 0) + '뷰 · ' + (L.since || '') + '~', true) +
    '</div><p class="note">지난 글 비중이 높을수록 발행일 트래픽에만 기대지 않는다는 뜻입니다.</p>';

  // ═══ 집계 시작일 ════════════════════════════════════════════════
  if (COV.views) {
    var ko = { views: '조회', visitors: '브라우저', dau: '방문자 수', engage: '행동', refs: '유입' };
    var parts = [];
    Object.keys(ko).forEach(function (k) { if (COV[k]) parts.push(ko[k] + ' ' + COV[k]); });
    h += '<details class="cov"><summary>집계 시작일 — 지표마다 다릅니다</summary>' +
      '<p class="note">' + parts.join(' · ') +
      '<br>시작일이 다른 값끼리 나누면 비율이 터집니다. 그래서 비율은 겹치는 날에서만 내고, ' +
      '겹치는 날이 없으면 「—」로 둡니다.</p></details>';
  }

  app.innerHTML = h;
}

var SORTS = [
  ['hot',  '반응 많은 순'],
  ['new',  '최신 반응 순'],
  ['date', '콘텐츠 날짜 순'],
];
var SORT = 'hot';
try { SORT = localStorage.getItem('ss_sort') || 'hot'; } catch (e) {}

var PAGE = 30;   // 한 번에 그리는 줄 수 — 스크롤이 끝에 닿으면 더 그린다

function sparkline(b, now) {
  var max = 0;
  b = b || [];
  b.forEach(function (n) { if (n > max) max = n; });
  if (!max) return '';
  var bs = b.map(function (n, i) {
    var hh = new Date((now - (23 - i) * 3600) * 1000).getHours();
    return '<i style="height:' + Math.max(2, Math.round(n / max * 34)) + 'px" title="' +
           hh + '시 · ' + n + '건"></i>';
  }).join('');
  return '<div class="spark"><div class="sl">최근 24시간 (시간대별)</div><div class="bars">' + bs + '</div></div>';
}

function rowHTML(k, by, last, now) {
  var m = SMAP[k] || { t: k, d: '' };
  m = { t: m.t, d: m.d, u: sUrl(k) };
  return '<a class="row" href="' + m.u + '"><span class="dt">' + (m.d || '').slice(5) + '</span>' +
    '<span class="ti">' + m.t + '</span><span class="when">' + ago(last[k], now) + '</span>' +
    '<span class="cnt">' + EMO.map(function (e) {
      var n = by[k][e] || 0;
      return '<span class="' + (n ? '' : 'z') + '">' + e + ' ' + n + '</span>';
    }).join('') + '</span></a>';
}

function renderReactions() {
  var obj = D.counts || {}, act = D.activity;
  var last = (act && act.last) || {}, hours = (act && act.hours) || [];
  var now = (act && act.now) || Math.floor(Date.now() / 1000);

  var by = {}, sum = {};
  Object.keys(obj).forEach(function (s) {
    by[s] = obj[s];
    var n = 0;
    EMO.forEach(function (e) { n += obj[s][e] || 0; });
    sum[s] = n;
  });

  var keys = Object.keys(by);
  if (!keys.length) { app.innerHTML = '<div class="empty">아직 반응이 없습니다.</div>'; return; }

  var cmp = {
    hot:  function (a, b) { return (sum[b] - sum[a]) || ((last[b] || 0) - (last[a] || 0)); },
    new:  function (a, b) { return ((last[b] || 0) - (last[a] || 0)) || (sum[b] - sum[a]); },
    date: function (a, b) {
      var da = (SMAP[a] || {}).d || '', db = (SMAP[b] || {}).d || '';
      return (db < da ? -1 : db > da ? 1 : 0) || (sum[b] - sum[a]);
    },
  };
  keys.sort(cmp[SORT] || cmp.hot);

  var tot = 0;
  keys.forEach(function (k) { tot += sum[k]; });
  var d1 = (act && act.d1) || 0, d7 = (act && act.d7) || 0, newest = 0;
  Object.keys(last).forEach(function (k) { if (last[k] > newest) newest = last[k]; });

  var h = '<div class="sum">' + kpi(tot, '전체 반응') + kpi(d1, '최근 24시간') +
    kpi(d7, '최근 7일') + kpi(keys.length, '반응받은 스토리') + '</div>' + sparkline(hours, now) +
    (newest ? '<p class="sub" style="margin:14px 0 4px">마지막 반응 ' + ago(newest, now) + '</p>' : '');

  h += '<div class="tabs sortbar">' + SORTS.map(function (s) {
    return '<button data-s="' + s[0] + '"' + (s[0] === SORT ? ' class="on"' : '') + '>' + s[1] + '</button>';
  }).join('') + '<span class="cn">' + keys.length + '개</span></div>' +
    '<div id="rows"></div><div id="more"></div>';
  app.innerHTML = h;

  app.querySelectorAll('.sortbar button').forEach(function (b) {
    b.addEventListener('click', function () {
      SORT = b.getAttribute('data-s');
      try { localStorage.setItem('ss_sort', SORT); } catch (e) {}
      renderReactions();
    });
  });

  // 스크롤이 바닥에 닿을 때만 다음 묶음을 그린다. 400개가 넘어가면 한 번에
  // 다 그리는 비용이 눈에 띄어서, 보이는 만큼만 만든다.
  var rows = document.getElementById('rows'), sent = document.getElementById('more'), n = 0;
  function draw() {
    var part = keys.slice(n, n + PAGE);
    if (!part.length) { sent.innerHTML = ''; return; }
    rows.insertAdjacentHTML('beforeend', part.map(function (k) {
      return rowHTML(k, by, last, now);
    }).join(''));
    n += part.length;
    sent.innerHTML = n < keys.length
      ? '<button class="more">' + (keys.length - n) + '개 더 보기</button>' : '';
    var mb = sent.querySelector('button');
    if (mb) mb.addEventListener('click', draw);
  }
  draw();
  if (window.IntersectionObserver) {
    var io = new IntersectionObserver(function (es) {
      if (es[0].isIntersecting && n < keys.length) draw();
    }, { rootMargin: '300px' });
    io.observe(sent);
  }
}

// ── 탭 ───────────────────────────────────────────────────
// ── 댓글 (자동 판정 감사) ────────────────────────────────
// 사람이 처리하는 대기열이 아니다. moderate_comments.py(LLM)가 이미 판정한 결과를
// 훑어보고, 틀린 게 있을 때만 뒤집는 화면이다. 관리자 키가 없으면 읽기만 된다.
var ADMIN = null;
try { ADMIN = localStorage.getItem('ss_admin'); } catch (e) {}

var ST = { '1': ['live', '공개'], '0': ['hold', '검토 중'], '-1': ['hold', '숨김'], '-2': ['spam', '스팸'] };

function modFetch(path, opts) {
  opts = opts || {};
  opts.headers = Object.assign({ 'x-admin-key': ADMIN || '', 'content-type': 'application/json' },
                               opts.headers || {});
  return fetch(API.replace(/[/]$/, '') + path, opts).then(function (r) {
    if (r.status === 401) throw new Error('unauthorized');
    return r.json();
  });
}

function askKey() {
  var k = prompt('관리자 키를 넣어주세요 (한 번만)');
  if (!k) return;
  try { localStorage.setItem('ss_admin', k.trim()); } catch (e) {}
  ADMIN = k.trim();
  renderComments();
}

function setState(id, st) {
  modFetch('/mod', { method: 'POST', body: JSON.stringify({ id: id, state: st, judge: '수동' }) })
    .then(renderComments)
    .catch(function () { alert('반영하지 못했습니다'); });
}

function cmRow(c, canAct) {
  var s = ST[String(c.state)] || ['', ''];
  var when = new Date(c.ts * 1000);
  var h = '<div class="cm"><span class="k">' + esc(c.nick) + '</span><span class="b">' +
    '<span class="tag ' + s[0] + '">' + s[1] + '</span>' +
    (c.hold ? '<span class="tag">' + esc(c.hold) + '</span>' : '') + esc(c.body) +
    (c.judge ? '<span class="j">판정: ' + esc(c.judge) + '</span>' : '') + '</span>' +
    '<span class="s">' + (when.getMonth() + 1) + '/' + when.getDate() + '</span>';
  if (canAct) {
    h += '<span class="act">' +
      (c.state !== 1 ? '<button data-a="1" data-i="' + c.id + '">공개</button>' : '') +
      (c.state !== -1 ? '<button data-a="-1" data-i="' + c.id + '">숨김</button>' : '') +
      '</span>';
  }
  return h + '</div>';
}

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
  });
}

function renderComments() {
  if (!ADMIN) {
    app.innerHTML = '<div class="card"><b style="color:#F07040">잠겨 있습니다</b>' +
      '<p class="note">댓글은 <code>scripts/moderate_comments.py</code>가 매일 자동으로 판정합니다. ' +
      '이 화면은 그 결과를 확인하고 틀린 것만 뒤집는 용도입니다.</p>' +
      '<div class="tabs" style="margin-top:12px"><button id="kbtn">관리자 키 입력</button></div></div>';
    document.getElementById('kbtn').addEventListener('click', askKey);
    return;
  }
  app.innerHTML = '<div class="empty">불러오는 중…</div>';
  Promise.all([modFetch('/mod?state=0'), modFetch('/mod?state=1'), modFetch('/mod?state=-2')])
    .then(function (r) {
      var held = r[0].items || [], live = r[1].items || [], spam = r[2].items || [];
      var h = '<div class="sum">' + kpi(held.length, '검토 중', '자동 판정 대기') +
        kpi(live.length, '공개') + kpi(spam.length, '스팸 차단') + '</div>';
      if (held.length) {
        h += '<h2>검토 중 <small>다음 자동 실행에서 판정됩니다</small></h2><div class="card">' +
          held.map(function (c) { return cmRow(c, true); }).join('') + '</div>';
      }
      h += '<h2>공개된 댓글</h2><div class="card">' +
        (live.length ? live.map(function (c) { return cmRow(c, true); }).join('')
                     : '<div class="empty">아직 없습니다.</div>') + '</div>';
      if (spam.length) {
        h += '<h2>스팸으로 내려간 것 <small>자동 판정 결과 확인용</small></h2><div class="card">' +
          spam.map(function (c) { return cmRow(c, true); }).join('') + '</div>';
      }
      app.innerHTML = h;
      app.querySelectorAll('.act button').forEach(function (b) {
        b.addEventListener('click', function () {
          setState(parseInt(b.getAttribute('data-i'), 10), parseInt(b.getAttribute('data-a'), 10));
        });
      });
    })
    .catch(function (e) {
      if (String(e.message) === 'unauthorized') {
        try { localStorage.removeItem('ss_admin'); } catch (x) {}
        ADMIN = null;
        renderComments();
        return;
      }
      app.innerHTML = '<div class="empty">불러오지 못했습니다.</div>';
    });
}


// ── 하루만 보기 (KD 2026-08-15: "모든 데이터를 일자별로도 볼 수 있게")
//    창(30일) 합계와 하루 값이 한 화면에 섞여 있어 어느 쪽도 못 믿었다.
//    날짜를 고르면 **모든 패널**이 그날 것만 보여준다. 필드를 늘린 게 아니라
//    서버에서 범위를 좁혀 오므로, 화면 코드는 갈라지지 않는다.
var DAYSEL = null;                 // null = 최근 30일
var load = function () {};         // 아래에서 실제 로더로 바뀐다

function dayQ() { return DAYSEL ? '&day=' + DAYSEL : ''; }

// 기간 프리셋 — 날짜 고르개보다 이게 먼저 눈에 와야 한다 (KD 2026-08-16)
var RANGES = [[1, '오늘'], [7, '7일'], [30, '30일'], [90, '90일'], [120, '전체']];
var WIN = 30;

function paintRange() {
  var el = document.getElementById('rngbar');
  if (!el) return;
  el.innerHTML = RANGES.map(function (r) {
    return '<button data-d="' + r[0] + '"' +
      (!DAYSEL && WIN === r[0] ? ' class="on"' : '') + '>' + r[1] + '</button>';
  }).join('') + '<button data-pick="1"' + (DAYSEL ? ' class="on"' : '') + '>' +
    (DAYSEL || '날짜 고르기') + '</button>';
  el.querySelectorAll('button').forEach(function (b) {
    b.addEventListener('click', function () {
      if (b.getAttribute('data-pick')) {
        var bar = document.getElementById('daybar');
        if (bar) bar.hidden = !bar.hidden;
        return;
      }
      DAYSEL = null; WIN = parseInt(b.getAttribute('data-d'), 10);
      var bar = document.getElementById('daybar');
      if (bar) bar.hidden = true;
      load();
    });
  });
}

function paintDays() {
  var el = document.getElementById('daybar');
  if (!el) return;
  var days = ((D.insights || {}).daily || []).map(function (d) { return d.day; });
  // 하루만 볼 땐 그날 하루치만 오므로, 고르개는 처음 목록을 계속 쓴다
  if (!DAYSEL) DAYS_ALL = days.slice(-30);
  var opts = (DAYS_ALL || days).slice().reverse().map(function (d) {
    return '<option value="' + d + '"' + (DAYSEL === d ? ' selected' : '') + '>' + d + '</option>';
  }).join('');
  el.innerHTML = '<label>기간</label>' +
    '<select id="daypick"><option value="">최근 30일 합계</option>' + opts + '</select>' +
    '<span class="scope">' + ((D.insights || {}).scope || '') + '</span>';
  var sel = document.getElementById('daypick');
  sel.addEventListener('change', function () {
    DAYSEL = sel.value || null;
    load();
  });
}
var DAYS_ALL = null;

var TABS = [['community', '커뮤니티'], ['reactions', '반응'], ['comments', '댓글']];
function paintTabs() {
  document.getElementById('tabs').innerHTML = TABS.map(function (t) {
    return '<button data-t="' + t[0] + '"' + (TAB === t[0] ? ' class="on"' : '') + '>' + t[1] + '</button>';
  }).join('');
}
document.getElementById('tabs').addEventListener('click', function (e) {
  var b = e.target.closest('button');
  if (!b) return;
  TAB = b.getAttribute('data-t');
  paintTabs();
  TAB === 'community' ? renderCommunity()
    : TAB === 'comments' ? renderComments()
    : renderReactions();
});

function fail() {
  app.innerHTML = '<div class="card"><b style="color:#F07040">불러오지 못했습니다</b>' +
    '<p class="note">연결이 끊겼거나 응답이 너무 느립니다.</p>' +
    '<div class="tabs" style="margin-top:12px"><button id="rt">다시 시도</button></div></div>';
  var b = document.getElementById('rt');
  if (b) b.addEventListener('click', function () { location.reload(); });
}

if (!API) {
  setup();
} else if (!ADMIN) {
  gate();                       // 키가 없으면 아무 수치도 부르지 않는다
} else {
  var base = API.replace(/[/]$/, '');
  // 타임아웃이 없으면 모바일에서 요청이 멈췄을 때 '불러오는 중…'이 영원히 남는다.
  // 실제로 폰에서 그렇게 됐다. 12초면 끊고 다시 시도할 수 있게 한다.
  var get = function (p) {
    var ctl = typeof AbortController !== 'undefined' ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctl) ctl.abort(); }, 12000);
    return fetch(base + p, {
      headers: { 'x-admin-key': ADMIN },
      signal: ctl ? ctl.signal : undefined,
    }).then(function (r) {
      clearTimeout(timer);
      if (r.status === 401) throw new Error('unauthorized');
      return r.json();
    }, function (e) {
      clearTimeout(timer);
      throw e;
    });
  };
  // 날짜를 바꾸면 다시 부른다 — 그래서 함수로 묶는다
  load = function () {
  Promise.all([get('/counts'), get('/activity'), get('/insights?days=' + WIN + dayQ())])
    .then(function (res) {
      D.counts = res[0] || {};
      D.activity = res[1];
      D.insights = res[2];
      paintTabs();
      paintRange();
      paintDays();
      TAB === 'comments' ? renderComments()
        : TAB === 'reactions' ? renderReactions() : renderCommunity();
    }).catch(function (e) {
      if (String(e.message) === 'unauthorized') {
        try { localStorage.removeItem('ss_admin'); } catch (x) {}
        ADMIN = null;
        gate();                 // 키가 틀렸으면 지우고 다시 묻는다
        return;
      }
      fail();
    });
  };
  load();
}
"""


def build(atoms=None):
    if atoms is None:
        atoms = json.loads(ATOMS.read_text(encoding="utf-8")) if ATOMS.exists() else []
    OUT.mkdir(exist_ok=True)
    # 최근 60일치만 심는다(파일 크기 관리)
    # 대시보드가 실제로 보여주는 건 최근 반응·조회다. 400개를 심으면 44KB가
    # 모바일에서 그대로 다운로드된다. 120개면 충분하고, url은 날짜·번호에서
    # 복원할 수 있으니 뺀다(id가 0811-3 → /newsletters/2026/0811.html#story-3).
    recent = sorted(atoms, key=lambda a: a.get("date", ""), reverse=True)[:120]
    smap = {a["id"]: {"t": re.sub(r"^[^\w<>&\"']{1,4}\s+", "", a["title"]).strip()[:34],
                      "d": a["date"][5:]} for a in recent}

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex,nofollow">
<title>순살 대시보드 — 방문·반응</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;800&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet"/>
<script src="/ss-config.js"></script>
<style>{CSS}</style></head><body><div class="wrap">
<h1>순살 대시보드</h1>
<p class="sub">몇 명이 와서 무엇에 반응했는지 — 운영자용 화면 (검색 노출 안 됨)</p>
<div class="tabs" id="tabs"></div>
<div class="rng" id="rngbar"></div>
<div class="daybar" id="daybar" hidden></div>
<div id="app"><div class="empty">불러오는 중…</div></div>
</div>
<script>
var SYEAR = {json.dumps(str(recent[0]["date"][:4]) if recent else "2026")};
var SMAP = {json.dumps(smap, ensure_ascii=False)};
{DASH_JS}
</script>
</body></html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print("📊 stats: /stats/ 반응 통계(운영자용)")
    return 1


if __name__ == "__main__":
    build()
