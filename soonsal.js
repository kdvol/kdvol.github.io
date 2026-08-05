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
    '.ss-react{display:flex;gap:8px;margin:14px 0 4px;flex-wrap:wrap}' +
    '.ss-rb{background:transparent;border:1px solid #d8d4c8;color:#8a8578;border-radius:16px;' +
    'padding:5px 13px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;' +
    'transition:all .15s;line-height:1.5}' +
    '.ss-rb:hover{border-color:#F07040;color:#F07040}' +
    '.ss-rb.on{border-color:#F07040;background:#F0704014;color:#F07040}' +
    '.ss-rb b{font-weight:700;margin-left:4px}' +
    /* 오늘의 논점 블록 */
    '.ss-talk{margin:26px 0 8px;padding:18px 20px;border:1px solid #e5e1d6;border-radius:12px;' +
    'background:#faf8f3}' +
    '.ss-talk-h{font-size:12px;font-weight:700;color:#F07040;letter-spacing:.04em;margin-bottom:8px}' +
    '.ss-talk-q{font-size:15px;line-height:1.6;color:#2a2a2a;margin-bottom:14px;font-weight:600}' +
    '.ss-talk-btns{display:flex;gap:8px;flex-wrap:wrap}' +
    '.ss-talk-b{display:inline-flex;align-items:center;gap:7px;background:#229ED9;color:#fff;' +
    'text-decoration:none;padding:11px 20px;border-radius:9px;font-size:14px;font-weight:700;' +
    'transition:filter .15s}' +
    '.ss-talk-b:hover{filter:brightness(.92)}' +
    '.ss-talk-b.ig{background:#E1306C}';

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
    sb.addEventListener('click', openShare);
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
  // 저장소: Supabase 설정(SS_CFG.supabase)이 있으면 공유 집계, 없으면 로컬 기록.
  // 어느 쪽이든 UI·동작은 동일 — 나중에 키만 넣으면 자동 승격.
  var REACTS = [['👍', '좋아요'], ['🤔', '글쎄요'], ['🔥', '중요']];

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

  function mountReactions() {
    var stories = document.querySelectorAll('.story');
    if (!stories.length) return;
    var mine = localVotes();
    for (var i = 0; i < stories.length; i++) {
      (function (s) {
        var key = storyKey(s);
        var body = s.querySelector('.story-body') || s;
        if (!key || s.querySelector('.ss-react')) return;
        var wrap = document.createElement('div');
        wrap.className = 'ss-react';
        REACTS.forEach(function (r) {
          var b = document.createElement('button');
          b.type = 'button';
          b.className = 'ss-rb' + (mine[key] === r[0] ? ' on' : '');
          b.innerHTML = r[0] + ' ' + r[1] + '<b class="n"></b>';
          b.addEventListener('click', function () { vote(key, r[0], wrap); });
          wrap.appendChild(b);
        });
        body.appendChild(wrap);
        refresh(key, wrap);
      })(stories[i]);
    }
  }

  function vote(key, emoji, wrap) {
    var mine = localVotes();
    if (mine[key] === emoji) { delete mine[key]; } else { mine[key] = emoji; }
    try { localStorage.setItem('ss_react', JSON.stringify(mine)); } catch (e) {}
    var btns = wrap.querySelectorAll('.ss-rb');
    for (var i = 0; i < btns.length; i++) {
      btns[i].className = 'ss-rb' + (REACTS[i][0] === mine[key] ? ' on' : '');
    }
    if (mine[key]) toast('반응 고마워요!');
    send_react(key, emoji, !!mine[key], wrap);
  }

  var CFG = window.SS_CFG || {};   // {supabase:{url,key}} 넣으면 공유 집계로 승격

  function send_react(key, emoji, added, wrap) {
    if (!CFG.supabase) return;    // 미설정 → 로컬만
    fetch(CFG.supabase.url + '/rest/v1/rpc/react', {
      method: 'POST',
      headers: { 'content-type': 'application/json', apikey: CFG.supabase.key },
      body: JSON.stringify({ p_story: key, p_emoji: emoji, p_delta: added ? 1 : -1 })
    }).then(function () { refresh(key, wrap); }).catch(function () {});
  }

  function refresh(key, wrap) {
    if (!CFG.supabase) return;
    fetch(CFG.supabase.url + '/rest/v1/reactions?story=eq.' + key,
      { headers: { apikey: CFG.supabase.key } })
      .then(function (r) { return r.json(); })
      .then(function (rows) {
        var counts = {};
        (rows || []).forEach(function (r) { counts[r.emoji] = r.count; });
        var btns = wrap.querySelectorAll('.ss-rb');
        for (var i = 0; i < btns.length; i++) {
          var n = counts[REACTS[i][0]] || 0;
          btns[i].querySelector('.n').textContent = n ? ' ' + n : '';
        }
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
      '<div class="ss-talk-h">💬 오늘의 논점</div>' +
      '<div class="ss-talk-q">오늘 브리핑, 어떻게 보셨나요?<br>' +
      '텔레그램에서 의견을 나누고, 인스타에서 카드뉴스로 다시 보세요.</div>' +
      '<div class="ss-talk-btns">' +
      '<a class="ss-talk-b" href="https://t.me/soonsal" target="_blank" rel="noopener">' +
      '✈️ 텔레그램에서 이야기하기</a>' +
      '<a class="ss-talk-b ig" href="https://instagram.com/soonsal.brief" target="_blank" rel="noopener">' +
      '📸 인스타그램</a>' +
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
  function payload() {
    var s = currentStory();
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

  function openShare() {
    var p = payload();
    var bg = document.createElement('div');
    bg.className = 'ss-modal-bg';
    var m = document.createElement('div');
    m.className = 'ss-modal';
    m.innerHTML =
      '<h3>공유하기</h3>' +
      '<div class="ss-preview"><div class="ss-pt">' + esc(p.title) + '</div>' +
      (p.summary ? '<div class="ss-ps">' + esc(p.summary) + '</div>' : '') + '</div>' +
      '<textarea class="ss-cm" rows="2" placeholder="한마디 덧붙이기 (선택)"></textarea>' +
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
      navigator.clipboard.writeText(text).then(function () { toast('공유 내용이 복사됐어요 — 붙여넣기 하세요'); });
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
