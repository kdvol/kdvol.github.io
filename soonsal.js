/* soonsal.js — 전 페이지 공용 위젯(플로팅 텔레그램 버튼 + 스토리 공유).
 * 페이지엔 <script src="/soonsal.js" defer> 한 줄만. 동작 변경은 이 파일만 고치면
 * 전 페이지에 즉시 반영 — 페이지마다 재주입할 필요 없음. */
(function () {
  if (window.__ssWidgets) return;
  window.__ssWidgets = 1;

  var CSS =
    '.ss-fab{position:fixed;right:16px;bottom:16px;z-index:9999;width:54px;height:54px;' +
    'border-radius:50%;background:#F07040;box-shadow:0 4px 14px rgba(0,0,0,.35);display:flex;' +
    'align-items:center;justify-content:center;text-decoration:none;font-size:26px;line-height:1;' +
    'transition:transform .15s}.ss-fab:hover,.ss-fab:active{transform:scale(1.08)}' +
    '@media(min-width:640px){.ss-fab{width:58px;height:58px;right:24px;bottom:24px;font-size:28px}}' +
    '.ss-pageshare{position:fixed;left:16px;bottom:16px;z-index:9999;background:#1f2937;color:#fff;border:none;' +
    'border-radius:26px;padding:13px 22px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit;' +
    'box-shadow:0 4px 14px rgba(0,0,0,.35);display:flex;align-items:center;gap:7px;transition:transform .15s}' +
    '.ss-pageshare:hover,.ss-pageshare:active{transform:scale(1.06)}' +
    '@media(min-width:640px){.ss-pageshare{left:24px;bottom:24px;padding:14px 24px;font-size:15px}}' +
    '.ss-toast{position:fixed;left:50%;bottom:80px;transform:translateX(-50%);background:#222;color:#fff;' +
    'font-size:13px;padding:10px 18px;border-radius:8px;z-index:100001;box-shadow:0 4px 14px rgba(0,0,0,.3)}' +
    '.ss-modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:100000;display:flex;' +
    'align-items:flex-end;justify-content:center}' +
    '.ss-modal{background:#fff;color:#1a2233;width:100%;max-width:460px;border-radius:16px 16px 0 0;' +
    'padding:20px 18px 18px;box-shadow:0 -4px 24px rgba(0,0,0,.3);font-family:inherit;' +
    "font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif}" +
    '.ss-modal h3{font-size:1rem;margin:0 0 12px}' +
    '.ss-preview{background:#f4f5f7;border-radius:10px;padding:12px 14px;margin-bottom:12px}' +
    '.ss-pt{font-weight:700;font-size:.92rem;line-height:1.4}' +
    '.ss-ps{color:#66707d;font-size:.82rem;line-height:1.5;margin-top:5px}' +
    '.ss-cm{width:100%;border:1px solid #d8dbe0;border-radius:10px;padding:10px 12px;font-size:.9rem;' +
    'font-family:inherit;resize:none;box-sizing:border-box}.ss-cm:focus{outline:none;border-color:#F07040}' +
    '.ss-row{display:flex;gap:8px;margin-top:12px}.ss-row button{flex:1;padding:12px;border-radius:10px;' +
    'border:none;font-size:.95rem;font-weight:700;cursor:pointer;font-family:inherit}' +
    '.ss-cancel{background:#eceef1;color:#555}.ss-go{background:#F07040;color:#fff}' +
    '@media(min-width:640px){.ss-modal-bg{align-items:center}.ss-modal{border-radius:16px}}' +
    /* 스토리별 반응 버튼 */
    '.ss-react{display:flex;gap:8px;margin:14px 0 4px;flex-wrap:wrap;align-items:center}' +
    /* 반응 3개는 한 덩어리로 — 자기들끼리 줄바꿈되지 않게 */
    '.ss-rg{display:flex;gap:8px;flex-wrap:nowrap}' +
    '.ss-rb{background:transparent;border:1px solid #d8d4c8;color:#8a8578;border-radius:16px;' +
    'padding:5px 13px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;' +
    'transition:border-color .15s,background .15s,color .15s;line-height:1.5;white-space:nowrap;' +
    'flex:0 0 auto}' +
    '.ss-rb:hover{border-color:#F07040;color:#F07040}' +
    '.ss-rb.on{border-color:#F07040;background:#F0704014;color:#F07040}' +
    /* 숫자 자리를 미리 비워둔다 — 눌러서 카운트가 생겨도 버튼 폭이 안 변함 */
    '.ss-rb b{font-weight:700;margin-left:3px;display:inline-block;min-width:8px;text-align:left}' +
    /* 좁은 화면(375px 기준)에선 4개가 한 줄에 안 들어가 공유는 아이콘만 */
    '@media(max-width:430px){.ss-react{gap:6px}.ss-rg{gap:6px}' +
    '.ss-rb{padding:5px 9px;font-size:11px}.ss-sh .lb{display:none}}' +
    /* 오늘의 논점 블록 */
    /* 3월 재개호 브랜드 팔레트: 주황 #F07040/#E55A00, 크림 #fafaf7, 보더 #e8e8e0 */
    '.ss-talk{margin:26px 0 8px;padding:20px 22px;border:1px solid #e8e8e0;border-radius:10px;' +
    "background:#fafaf7;font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif}" +
    '.ss-talk-h{font-size:12px;font-weight:700;color:#F07040;letter-spacing:.06em;margin-bottom:10px}' +
    '.ss-talk-q{font-size:15px;line-height:1.7;color:#333;margin-bottom:16px;font-weight:600}' +
    '.ss-talk-btns{display:flex;gap:8px;flex-wrap:wrap}' +
    '.ss-talk-b{display:inline-flex;align-items:center;background:#E55A00;color:#fff;' +
    'text-decoration:none;padding:11px 20px;border-radius:6px;font-size:14px;font-weight:700;' +
    'border:1px solid #E55A00;transition:background .2s,color .2s}' +
    '.ss-talk-b:hover{background:#CC4E00;border-color:#CC4E00}' +
    '.ss-talk-b.ig{background:transparent;color:#E55A00;border-color:#e0ddd5}' +
    '.ss-talk-b.ig:hover{background:#fff;color:#CC4E00;border-color:#F07040}' +
    /* 반응 버튼도 같은 크림/주황 톤으로 */
    '.ss-rb{border-color:#e0ddd5;color:#8a8578}' +
    '.ss-rb:hover{border-color:#F07040;color:#E55A00}' +
    '.ss-rb.on{border-color:#F07040;background:#F0704012;color:#E55A00}' +
    '.ss-sh{margin-left:auto;color:#9a958a}' +
    '.ss-sh b{display:none}';

  function esc(s) {
    return (s || '').replace(/[&<>]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c];
    });
  }

  function init() {
    var st = document.createElement('style');
    st.textContent = CSS;
    document.head.appendChild(st);

    var fab = document.createElement('a');
    fab.className = 'ss-fab';
    fab.href = 'https://t.me/soonsal';
    fab.target = '_blank';
    fab.rel = 'noopener';
    fab.setAttribute('aria-label', '텔레그램 실시간 대화방');
    fab.title = '텔레그램 대화방';
    fab.textContent = '💬';
    document.body.appendChild(fab);

    var sb = document.createElement('button');
    sb.className = 'ss-pageshare';
    sb.type = 'button';
    sb.innerHTML = '🔗 <span>공유하기</span>';
    sb.setAttribute('aria-label', '공유하기');
    sb.addEventListener('click', function () { openShare(); });
    document.body.appendChild(sb);

    // 딥링크(#story-N)로 들어오면 그 스토리로 확실히 스크롤
    if (location.hash && location.hash.indexOf('#story-') === 0) {
      var target = document.getElementById(location.hash.slice(1));
      if (target) setTimeout(function () { target.scrollIntoView(true); }, 80);
    }

    mountReactions();   // 스토리별 무로그인 반응
    mountTalk();        // 오늘의 논점 → 텔레그램
  }

  // ── 스토리별 반응 (무로그인) ─────────────────────────────
  // 숫자는 항상 보인다. Supabase 설정(SS_CFG.supabase)이 있으면 공유 집계,
  // 없으면 내 클릭만 로컬 집계 — 어느 쪽이든 버튼이 "죽어" 보이지 않게.
  var REACTS = [['👍', '좋았음'], ['🤔', '글쎄'], ['🔥', '중요함']];
  var CFG = window.SS_CFG || {};
  var API = CFG.worker || null;              // Cloudflare Worker(권장)
  var HAS_BACKEND = !!(API || CFG.supabase);

  function storyKey(story) {
    var m = location.pathname.match(/\/newsletters\/2026\/(\d{4})(-crypto)?\.html/);
    var all = document.querySelectorAll('.story'), idx = 0;
    for (var i = 0; i < all.length; i++) { if (all[i] === story) { idx = i + 1; break; } }
    if (!m || !idx) return null;
    return m[1] + (m[2] ? 'c' : '') + '-' + idx;
  }

  function localVotes() {
    try { return JSON.parse(localStorage.getItem('ss_react') || '{}'); } catch (e) { return {}; }
  }
  function saveVotes(v) {
    try { localStorage.setItem('ss_react', JSON.stringify(v)); } catch (e) {}
  }

  function render(wrap, key) {
    var mine = localVotes()[key];
    var shared = wrap._shared || {};
    var btns = wrap.querySelectorAll('.ss-rb:not(.ss-sh)');
    for (var i = 0; i < btns.length; i++) {
      var emoji = REACTS[i][0];
      var n = shared[emoji] || 0;
      if (!HAS_BACKEND && mine === emoji) n += 1;    // 백엔드 없어도 내 반응은 보이게
      btns[i].className = 'ss-rb' + (mine === emoji ? ' on' : '');
      btns[i].querySelector('.n').textContent = n ? ' ' + n : '';
    }
  }

  var WRAPS = {};   // storyKey → wrap (페이지 단위 일괄 갱신용)

  function mountReactions() {
    var stories = document.querySelectorAll('.story');
    if (!stories.length) return;
    for (var i = 0; i < stories.length; i++) {
      (function (s) {
        var key = storyKey(s);
        var body = s.querySelector('.story-body') || s;
        if (!key || s.querySelector('.ss-react')) return;
        var wrap = document.createElement('div');
        wrap.className = 'ss-react';
        wrap._shared = {};
        var rg = document.createElement('div');
        rg.className = 'ss-rg';
        REACTS.forEach(function (r) {
          var b = document.createElement('button');
          b.type = 'button';
          b.className = 'ss-rb';
          b.innerHTML = r[0] + ' ' + r[1] + '<b class="n"></b>';
          b.addEventListener('click', function () { vote(key, r[0], wrap); });
          rg.appendChild(b);
        });
        wrap.appendChild(rg);
        var sh = document.createElement('button');
        sh.type = 'button';
        sh.className = 'ss-rb ss-sh';
        sh.innerHTML = '🔗<span class="lb"> 공유</span>';
        sh.setAttribute('aria-label', '이 스토리 공유');
        sh.addEventListener('click', function () { openShare(s); });
        wrap.appendChild(sh);

        body.appendChild(wrap);
        render(wrap, key);
        WRAPS[key] = wrap;
      })(stories[i]);
    }
    refreshIssue();   // 페이지 전체 카운트를 한 번에 (요청·읽기 절약)
  }

  // 이 페이지(뉴스레터 1호)의 모든 스토리 카운트를 1회 요청으로 받아 뿌린다
  function refreshIssue() {
    if (!API) return;
    var m = location.pathname.match(/\/newsletters\/2026\/(\d{4})(-crypto)?\.html/);
    if (!m) return;
    var issue = m[1] + (m[2] ? 'c' : '');
    fetch(API.replace(/[/]$/, '') + '/counts?issue=' + issue)
      .then(function (r) { return r.json(); })
      .then(function (obj) {
        Object.keys(WRAPS).forEach(function (k) {
          WRAPS[k]._shared = (obj && obj[k]) || {};
          render(WRAPS[k], k);
        });
      }).catch(function () {});
  }

  function vote(key, emoji, wrap) {
    var v = localVotes(), was = v[key];
    if (was === emoji) { delete v[key]; } else { v[key] = emoji; }
    saveVotes(v);
    var s = wrap._shared || (wrap._shared = {});
    if (HAS_BACKEND) {                        // 낙관적 반영(응답 기다리지 않음)
      if (was) s[was] = Math.max((s[was] || 0) - 1, 0);
      if (v[key]) s[emoji] = (s[emoji] || 0) + 1;
    }
    render(wrap, key);
    if (v[key]) toast('접수했음 🐟');
    if (was && was !== emoji) push(key, was, -1, wrap);
    push(key, emoji, v[key] ? 1 : -1, wrap);
  }

  function push(key, emoji, delta, wrap) {
    if (API) {
      fetch(API.replace(/\/$/, '') + '/react', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ story: key, emoji: emoji, delta: delta })
      }).then(function (r) { return r.json(); })
        .then(function (o) { wrap._shared = o || {}; render(wrap, key); })
        .catch(function () {});
      return;
    }
    if (!CFG.supabase) return;
    fetch(CFG.supabase.url + '/rest/v1/rpc/' + (CFG.supabase.rpc || 'soonsal_react'), {
      method: 'POST',
      headers: { 'content-type': 'application/json', apikey: CFG.supabase.key },
      body: JSON.stringify({ p_story: key, p_emoji: emoji, p_delta: delta })
    }).then(function () { refresh(key, wrap); }).catch(function () {});
  }

  function refresh(key, wrap) {
    if (API) {
      fetch(API.replace(/\/$/, '') + '/counts?story=' + encodeURIComponent(key))
        .then(function (r) { return r.json(); })
        .then(function (o) { wrap._shared = o || {}; render(wrap, key); })
        .catch(function () {});
      return;
    }
    if (!CFG.supabase) return;
    fetch(CFG.supabase.url + '/rest/v1/' + (CFG.supabase.table || 'soonsal_reactions') +
        '?story=eq.' + key + '&select=emoji,count',
      { headers: { apikey: CFG.supabase.key } })
      .then(function (r) { return r.json(); })
      .then(function (rows) {
        var s = {};
        (rows || []).forEach(function (r) { s[r.emoji] = r.count; });
        wrap._shared = s;
        render(wrap, key);
      }).catch(function () {});
  }

  // ── 오늘의 논점 → 텔레그램 ──────────────────────────────
  function mountTalk() {
    if (!/\/newsletters\/2026\//.test(location.pathname)) return;
    if (document.querySelector('.ss-talk')) return;
    var stories = document.querySelectorAll('.story');
    if (!stories.length) return;
    var last = stories[stories.length - 1];
    var el = last.querySelector('.story-title');
    var lead = el ? el.textContent.trim() : '';
    var box = document.createElement('div');
    box.className = 'ss-talk';
    box.innerHTML =
      '<div class="ss-talk-h">💬 오늘 순살, 어땠음?</div>' +
      '<div class="ss-talk-q">혼자 보기 아까우면 —<br>' +
      '텔레그램에선 다들 뭐라 하는지 보고, 인스타에선 카드뉴스로 한 번 더.</div>' +
      '<div class="ss-talk-btns">' +
      '<a class="ss-talk-b" href="https://t.me/soonsal" target="_blank" rel="noopener">' +
      '텔레그램 수다방 →</a>' +
      '<a class="ss-talk-b ig" href="https://instagram.com/soonsal.brief" target="_blank" rel="noopener">' +
      '인스타 구경</a>' +
      '</div>';
    (last.parentNode || document.body).insertBefore(box, last.nextSibling);
  }

  function toast(m) {
    var d = document.createElement('div');
    d.className = 'ss-toast';
    d.textContent = m;
    document.body.appendChild(d);
    setTimeout(function () { d.remove(); }, 2000);
  }

  // 지금 화면에 보이는 스토리(뷰포트 35% 선을 지난 마지막 스토리)
  function currentStory() {
    var stories = document.querySelectorAll('.story');
    if (!stories.length) return null;
    var line = window.innerHeight * 0.35, best = null, bestTop = -1e9, first = null;
    for (var i = 0; i < stories.length; i++) {
      if (!stories[i].querySelector('.story-title')) continue;
      if (!first) first = stories[i];
      var top = stories[i].getBoundingClientRect().top;
      if (top <= line && top > bestTop) { bestTop = top; best = stories[i]; }
    }
    return best || first;
  }

  // 스토리 → 스토리별 OG 페이지(/s/{id}.html) URL. 공유 미리보기가 스토리 기준으로 뜸.
  function shimUrl(story) {
    // id 파싱 금지(광고 스토리 등 커스텀 id가 잘못된 URL을 만들었음) → 위치 기반.
    // atomize의 넘버링과 동일: 전체 .story div 중 몇 번째인가.
    var m = location.pathname.match(/\/newsletters\/2026\/(\d{4})(-crypto)?\.html/);
    var all = document.querySelectorAll('.story');
    var idx = 0;
    for (var i = 0; i < all.length; i++) { if (all[i] === story) { idx = i + 1; break; } }
    if (!m || !idx) return location.origin + location.pathname + (story.id ? '#' + story.id : '');
    var id = m[1] + (m[2] ? 'c' : '') + '-' + idx;
    return location.origin + '/s/' + id + '.html';
  }

  // 공유 대상: {title, summary(1문단), url(스토리 OG 페이지)}
  function payload(story) {
    var s = story || currentStory();
    if (s && s.querySelector('.story-title')) {
      var title = s.querySelector('.story-title').textContent.trim().replace(/🔗\s*공유\s*$/, '').trim();
      var bl = s.querySelector('.story-body .bullet') || s.querySelector('.bullet');
      var summary = bl ? bl.textContent.replace(/^[◾■·•\s]+/, '').trim() : '';
      if (summary.length > 110) summary = summary.slice(0, 110).replace(/\s+\S*$/, '') + '…';
      return { title: title, summary: summary, url: shimUrl(s) };
    }
    var pt = document.title.replace(/\s*[—|].*$/, '').trim() || document.title;
    var md = document.querySelector('meta[name="description"]');
    return { title: pt, summary: md ? md.content : '', url: location.href };
  }

  function openShare(story) {
    var p = payload(story);
    var bg = document.createElement('div');
    bg.className = 'ss-modal-bg';
    var m = document.createElement('div');
    m.className = 'ss-modal';
    m.innerHTML =
      '<h3>친구한테 보내기</h3>' +
      '<div class="ss-preview"><div class="ss-pt">' + esc(p.title) + '</div>' +
      (p.summary ? '<div class="ss-ps">' + esc(p.summary) + '</div>' : '') + '</div>' +
      '<textarea class="ss-cm" rows="2" placeholder="한마디 붙이기 (선택)"></textarea>' +
      '<div class="ss-row"><button class="ss-cancel" type="button">취소</button>' +
      '<button class="ss-go" type="button">공유</button></div>';
    bg.appendChild(m);
    document.body.appendChild(bg);

    var ta = m.querySelector('.ss-cm');
    function close() { bg.remove(); }
    bg.addEventListener('click', function (e) { if (e.target === bg) close(); });
    m.querySelector('.ss-cancel').addEventListener('click', close);
    m.querySelector('.ss-go').addEventListener('click', function () {
      var comment = ta.value.trim();
      // 하나의 메시지: 코멘트 + 제목 + 요약 + 링크(텍스트에 녹여 1개 메시지로)
      var text = (comment ? comment + '\n\n' : '') + p.title +
        (p.summary ? '\n' + p.summary : '') + '\n\n' + p.url;
      close();
      send(text);
    });
    setTimeout(function () { ta.focus(); }, 60);
  }

  function send(text) {
    // url 필드를 따로 주지 않고 text에 링크를 녹여 1개 메시지로 공유
    if (navigator.share) {
      navigator.share({ text: text }).catch(function () {});
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(function () { toast('복사했음! 붙여넣기 하면 됨'); });
    } else {
      toast(text);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
