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
.when{color:#5c5c5c;font-size:.74rem;white-space:nowrap;padding-top:3px}
.spark{background:#161616;border:1px solid #232323;border-radius:10px;padding:12px 16px 10px;margin-bottom:6px}
.spark .sl{font-size:.75rem;color:#888;margin-bottom:9px}
.spark .bars{display:flex;align-items:flex-end;gap:3px;height:36px}
.spark .bars i{flex:1;background:#F07040;border-radius:2px 2px 0 0;opacity:.85;min-height:2px}
@media(max-width:520px){.when{display:none}.row{gap:9px}}
.empty{color:#777;font-size:.9rem;padding:22px 4px}
h2{font-size:.95rem;color:#ddd;margin:30px 0 10px;letter-spacing:-.01em}
h2 small{color:#666;font-weight:400;font-size:.78rem;margin-left:7px}
.kpi.hero .v{font-size:1.9rem}
.kpi .d{font-size:.7rem;color:#5f5f5f;margin-top:3px}
.card{background:#161616;border:1px solid #232323;border-radius:10px;padding:14px 16px;margin-bottom:10px}
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
"""

DASH_JS = r"""
var EMO = ['👍','🤔','🔥'];
var SS = window.SS_CFG || {};
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
var KIND_KO = { read: '끝까지 읽음', react: '반응', share: '공유', telegram: '텔레그램 이동',
                instagram: '인스타 이동' };

function renderCommunity() {
  var ins = D.insights;
  if (!ins) { app.innerHTML = '<div class="empty">방문 집계를 불러오지 못했습니다.</div>'; return; }
  var daily = ins.daily || [], v = ins.visitors || {};
  if (!daily.length) {
    app.innerHTML = '<div class="card"><b style="color:#F07040">아직 방문 기록이 없습니다.</b>' +
      '<p class="note">방금 붙인 집계라 지금부터 쌓입니다. 페이지를 한 번 열어보면 바로 잡힙니다.<br>' +
      '수집 항목: 익명 난수 ID·경로·유입 경로뿐. 쿠키·IP·UA는 쓰지 않습니다.</p></div>';
    return;
  }

  var today = daily[daily.length - 1] || { hits: 0, uniq: 0 };
  var sumH = 0, sumU = 0;
  daily.forEach(function (d) { sumH += d.hits; sumU += d.uniq; });
  var last7 = daily.slice(-7), h7 = 0, u7 = 0;
  last7.forEach(function (d) { h7 += d.hits; u7 += d.uniq; });
  // 일별 순방문 합은 이틀 온 사람을 두 번 센다 → 실제 사람 수는 active7
  var people7 = (v.active7 === undefined || v.active7 === null) ? u7 : v.active7;

  var eng = {};
  (ins.engage || []).forEach(function (e) { eng[e.kind] = (eng[e.kind] || 0) + e.n; });
  var acts = (eng.react || 0) + (eng.share || 0) + (eng.telegram || 0) + (eng.instagram || 0);

  // views.uniq는 '경로별' 첫 방문이라 한 사람이 3페이지를 보면 3으로 잡힌다.
  // 사람 수는 visitors 테이블에서 온 값(v.today / v.active7)을 쓴다.
  var people0 = (v.today === undefined || v.today === null) ? today.uniq : v.today;

  var h = '<div class="sum">' +
    kpi(people0, '오늘 방문자', today.hits + '뷰', true) +
    kpi(people7, '7일 방문자', h7 + '뷰 · 중복 제외', true) +
    kpi(pct(v.repeat_v, v.total) + '%', '재방문율', (v.repeat_v || 0) + '/' + (v.total || 0) + '명', true) +
    kpi(pct(acts, sumU) + '%', '참여율', acts + '건 / ' + sumU + '순방문', true) +
    '</div>';

  // 일별 추이 — 뷰(주황) 위에 순방문자(파랑)를 겹쳐 보여준다
  var max = 1;
  daily.forEach(function (d) { if (d.hits > max) max = d.hits; });
  h += '<h2>일별 추이 <small>최근 ' + ins.days + '일</small></h2><div class="card"><div class="trend">' +
    daily.map(function (d) {
      return '<i style="height:' + Math.max(2, d.hits / max * 60) + 'px" title="' + d.day +
        ' · ' + d.hits + '뷰 / 순방문 ' + d.uniq + '"><i class="u" style="position:absolute;left:0;right:0;bottom:0;height:' +
        Math.max(1, d.uniq / max * 60) + 'px"></i></i>';
    }).join('') +
    '</div><div class="tl"><span>' + daily[0].day.slice(5) + '</span><span>' +
    daily[daily.length - 1].day.slice(5) + '</span></div>' +
    '<div class="lgd"><span><b style="background:#F07040"></b>페이지뷰</span>' +
    '<span><b style="background:#3f6fd8"></b>페이지 순방문</span></div></div>';

  // 커뮤니티 지표 — 온 사람 중 얼마나 남기고 가는가
  h += '<h2>참여 <small>방문자가 실제로 한 행동</small></h2><div class="card">' +
    bars(Object.keys(KIND_KO).map(function (k) { return [KIND_KO[k], eng[k] || 0]; }), '건') +
    '<p class="note">끝까지 읽음 = 페이지 70%까지 내려갔거나 45초 이상 머문 방문. ' +
    '읽음률 ' + pct(eng.read || 0, sumU) + '% · 반응률 ' + pct(eng.react || 0, sumU) + '%</p></div>';

  h += '<h2>유입 경로</h2><div class="card">' +
    bars((ins.refs || []).map(function (r) { return [SRC_KO[r.src] || r.src, r.n]; }), '명') + '</div>';

  h += '<h2>많이 본 페이지</h2><div class="card">' +
    bars((ins.top || []).slice(0, 12).map(function (r) {
      var m = r.path.match(/(\d{4})(-crypto)?\.html$/);
      var nm = m ? (m[1].slice(0, 2) + '/' + m[1].slice(2) + (m[2] ? ' 크립토' : '') + ' 브리핑') : r.path;
      return [nm, r.hits];
    }), '뷰') + '</div>';

  h += '<p class="note">쿠키·IP·UA를 저장하지 않습니다. 브라우저 localStorage의 익명 난수 ID로 ' +
    '같은 사람인지만 구분하고, 원본 로그 없이 일자별 집계만 남깁니다. ' +
    '재방문 = 서로 다른 날에 2일 이상 방문한 사람.</p>';
  app.innerHTML = h;
}

// ── 반응 화면 ────────────────────────────────────────────
function sparkline(events, now) {
  var b = new Array(24).fill(0), max = 0;
  events.forEach(function (e) {
    if (e[2] !== 1) return;
    var hh = Math.floor((now - e[0]) / 3600);
    if (hh >= 0 && hh < 24) b[23 - hh]++;
  });
  b.forEach(function (n) { if (n > max) max = n; });
  if (!max) return '';
  var bs = b.map(function (n, i) {
    var hh = new Date((now - (23 - i) * 3600) * 1000).getHours();
    return '<i style="height:' + Math.max(2, Math.round(n / max * 34)) + 'px" title="' +
           hh + '시 · ' + n + '건"></i>';
  }).join('');
  return '<div class="spark"><div class="sl">최근 24시간 (시간대별)</div><div class="bars">' + bs + '</div></div>';
}

function renderReactions() {
  var obj = D.counts || {}, act = D.activity;
  var last = (act && act.last) || {}, events = (act && act.events) || [];
  var now = (act && act.now) || Math.floor(Date.now() / 1000);

  var by = {};
  Object.keys(obj).forEach(function (s) { by[s] = obj[s]; });
  var keys = Object.keys(by).sort(function (a, b) {
    var sa = 0, sb = 0;
    EMO.forEach(function (e) { sa += by[a][e] || 0; sb += by[b][e] || 0; });
    if (sb !== sa) return sb - sa;
    return (last[b] || 0) - (last[a] || 0);
  });
  if (!keys.length) { app.innerHTML = '<div class="empty">아직 반응이 없습니다.</div>'; return; }

  var tot = 0, st = keys.length;
  keys.forEach(function (k) { EMO.forEach(function (e) { tot += by[k][e] || 0; }); });
  var d1 = 0, d7 = 0, newest = 0;
  events.forEach(function (e) {
    if (e[2] !== 1) return;
    if (now - e[0] < 86400) d1++;
    if (now - e[0] < 604800) d7++;
  });
  Object.keys(last).forEach(function (k) { if (last[k] > newest) newest = last[k]; });

  var h = '<div class="sum">' + kpi(tot, '전체 반응') + kpi(d1, '최근 24시간') +
    kpi(d7, '최근 7일') + kpi(st, '반응받은 스토리') + '</div>' + sparkline(events, now) +
    (newest ? '<p class="sub" style="margin:14px 0 4px">마지막 반응 ' + ago(newest, now) + '</p>' : '');

  keys.forEach(function (k) {
    var m = SMAP[k] || { t: k, d: '', u: '#' };
    h += '<a class="row" href="' + m.u + '"><span class="dt">' + (m.d || '').slice(5) + '</span>' +
      '<span class="ti">' + m.t + '</span><span class="when">' + ago(last[k], now) + '</span>' +
      '<span class="cnt">' + EMO.map(function (e) {
        var n = by[k][e] || 0;
        return '<span class="' + (n ? '' : 'z') + '">' + e + ' ' + n + '</span>';
      }).join('') + '</span></a>';
  });
  app.innerHTML = h;
}

// ── 탭 ───────────────────────────────────────────────────
var TABS = [['community', '커뮤니티'], ['reactions', '반응']];
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
  TAB === 'community' ? renderCommunity() : renderReactions();
});

function fail() { app.innerHTML = '<div class="empty">집계를 불러오지 못했습니다.</div>'; }

if (API) {
  var base = API.replace(/[/]$/, '');
  var get = function (p) {
    return fetch(base + p).then(function (r) { return r.json(); }).catch(function () { return null; });
  };
  Promise.all([get('/counts'), get('/activity'), get('/insights?days=30')])
    .then(function (res) {
      D.counts = res[0] || {};
      D.activity = res[1];
      D.insights = res[2];
      paintTabs();
      renderCommunity();
    }).catch(fail);
} else { setup(); }
"""


def build(atoms=None):
    if atoms is None:
        atoms = json.loads(ATOMS.read_text(encoding="utf-8")) if ATOMS.exists() else []
    OUT.mkdir(exist_ok=True)
    # 최근 60일치만 심는다(파일 크기 관리)
    recent = sorted(atoms, key=lambda a: a.get("date", ""), reverse=True)[:400]
    smap = {a["id"]: {"t": re.sub(r"^[^\w<>&\"']{1,4}\s+", "", a["title"]).strip(),
                      "d": a["date"], "u": a["url"]} for a in recent}

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
<div id="app"><div class="empty">불러오는 중…</div></div>
</div>
<script>
var SMAP = {json.dumps(smap, ensure_ascii=False)};
{DASH_JS}
</script>
</body></html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print("📊 stats: /stats/ 반응 통계(운영자용)")
    return 1


if __name__ == "__main__":
    build()
