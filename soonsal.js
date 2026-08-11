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
    /* 좁은 화면(375px 가용폭 311px)에 반응3+코멘트+공유 5개를 한 줄에 넣는다.
       아이콘만 남기고, 코멘트 pill은 카운트가 없을 때 예약 폭도 뺀다.
       반응 버튼의 예약 폭은 그대로 둔다 — 눌렀을 때 폭이 변하면 정렬이 흔들린다. */
    '@media(max-width:430px){.ss-react{gap:5px}.ss-rg{gap:5px}' +
    '.ss-rb{padding:5px 9px;font-size:11px}.ss-sh .lb,.ss-cbtn .lb{display:none}' +
    '.ss-sh,.ss-cbtn{padding:5px 8px}.ss-cbtn b:empty{display:none}}' +
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
    /* 수집 안내 */
    '.ss-notice{text-align:center;font-size:11px;color:#9a958a;line-height:1.7;padding:14px 16px 18px;font-family:inherit}' +
    '.ss-notice a{color:#9a958a;text-decoration:underline}' +
    /* 코멘트 */
    '.ss-cbtn{margin-left:0}' +
    '.ss-cwrap{margin:8px 0 4px;padding:12px 14px;border:1px solid #e8e8e0;border-radius:10px;background:#fafaf7;font-family:inherit}' +
    '.ss-cin{width:100%;border:1px solid #e0ddd5;border-radius:8px;padding:9px 11px;font-size:13px;font-family:inherit;box-sizing:border-box;resize:none;background:#fff}' +
    '.ss-cin:focus{outline:none;border-color:#F07040}' +
    '.ss-crow{display:flex;gap:7px;align-items:center;margin-top:8px}' +
    '.ss-cnick{flex:0 0 96px;font-size:12px}' +
    '.ss-cnt{margin-left:auto;font-size:11px;color:#b0aca2;font-variant-numeric:tabular-nums}' +
    '.ss-cgo{background:#E55A00;color:#fff;border:none;border-radius:7px;padding:8px 15px;font-size:12px;font-weight:700;cursor:pointer;font-family:inherit}' +
    '.ss-cgo:disabled{background:#d8d4c8;cursor:default}' +
    '.ss-clist{margin-top:10px}' +
    '.ss-ci{display:flex;gap:8px;padding:7px 0;border-top:1px solid #eceae2;font-size:13px;line-height:1.6;color:#333}' +
    '.ss-ck{color:#8a8578;font-weight:700;white-space:nowrap;font-size:12px;padding-top:1px}' +
    '.ss-cb{flex:1;word-break:break-word}' +
    '.ss-ct{color:#b0aca2;font-size:11px;white-space:nowrap;padding-top:2px}' +
    '.ss-chold{color:#b0aca2;font-size:11px;margin-left:5px}' +
    '.ss-cnote{color:#b0aca2;font-size:11px;line-height:1.7;margin-top:9px}' +
    '.ss-hp{position:absolute;left:-9999px;width:1px;height:1px}' +
    '.ss-sh{margin-left:auto;color:#9a958a}' +
    '.ss-sh b{display:none}';

  function esc(s) {
    return (s || '').replace(/[&<>]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c];
    });
  }

  // ── 방문·참여 트래킹 ─────────────────────────────────────
  // 목표는 페이지뷰 숫자가 아니라 "다시 오는 사람이 있는가, 반응하는가".
  // 개인정보는 보내지 않는다 — 쿠키·IP·UA 없이 localStorage 난수 ID 하나만.
  var VID_KEY = 'ss_vid', SEEN_KEY = 'ss_seen';

  function vid() {
    try {
      var v = localStorage.getItem(VID_KEY);
      if (!v || !/^[a-z0-9]{8,24}$/.test(v)) {
        v = (Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2)).slice(0, 16);
        localStorage.setItem(VID_KEY, v);
      }
      return v;
    } catch (e) { return null; }   // 프라이빗 모드 등 → 트래킹 포기
  }

  // 오늘 이 경로를 처음 여는가 (순방문 계산용, 브라우저에서만 판단)
  function firstToday(path) {
    try {
      var today = new Date(Date.now() + 324e5).toISOString().slice(0, 10);   // KST
      var s = JSON.parse(localStorage.getItem(SEEN_KEY) || '{}');
      if (s.d !== today) s = { d: today, p: [] };
      if (s.p.indexOf(path) >= 0) return 0;
      s.p.push(path);
      localStorage.setItem(SEEN_KEY, JSON.stringify(s));
      return 1;
    } catch (e) { return 0; }
  }

  function refSrc() {
    var r = document.referrer || '';
    if (/utm_source=mail|[?&]m=1\b/.test(location.search)) return 'mail';
    if (!r) return 'direct';
    if (/t\.me|telegram/i.test(r)) return 'telegram';
    if (/instagram|ig\.me/i.test(r)) return 'instagram';
    if (/google\.|naver\.|daum\.|bing\.|duckduckgo/i.test(r)) return 'search';
    if (r.indexOf(location.origin) === 0) return 'direct';   // 사이트 내 이동
    return 'other';
  }

  function beacon(body) {
    if (!API) return;
    var url = API.replace(/[/]$/, '') + '/t';
    var s = JSON.stringify(body);
    // sendBeacon은 프리플라이트 없이 나가고 페이지를 떠나도 살아남는다
    try {
      if (navigator.sendBeacon && navigator.sendBeacon(url, s)) return;
    } catch (e) {}
    try { fetch(url, { method: 'POST', body: s, keepalive: true }).catch(function () {}); } catch (e) {}
  }

  // 서버에도 제외를 남긴다 — localStorage만 믿으면 그 브라우저를 정리하는 순간
  // 다시 섞이고, 이미 쌓인 방문자 기록도 남는다.
  function forgetMe() {
    var v = vid();
    if (v) beacon({ t: 'forget', v: v });
  }
  window.ssForgetMe = forgetMe;   // /stats/ 버튼에서 호출

  function track(kind) {          // read / react / share / telegram / instagram / comment
    if (optedOut()) return;
    var v = vid();
    if (v) beacon({ t: 'ev', v: v, k: kind });
  }

  // 이 브라우저를 집계에서 뺀다 (/stats/의 '내 방문 빼기' 버튼이 세운다).
  // 운영자가 하루에 몇 번씩 확인하는 방문이 지표를 부풀리는 걸 막는 용도.
  function optedOut() {
    try { return localStorage.getItem('ss_optout') === '1'; } catch (e) { return false; }
  }

  function trackView() {
    if (!API) return;
    if (navigator.webdriver) return;                       // 자동화 브라우저 제외
    if (optedOut()) return;                                // 운영자 본인 브라우저
    if (/\/stats\//.test(location.pathname)) return;       // 운영자 화면은 집계 안 함
    var v = vid();
    if (!v) return;
    var path = location.pathname;
    beacon({ t: 'hit', v: v, p: path, f: firstToday(path), r: refSrc() });

    // "읽었다" 판정 — 70%까지 내려갔거나 45초 이상 머물렀을 때 1회
    var done = false;
    function mark() {
      if (done) return;
      done = true;
      track('read');
      window.removeEventListener('scroll', onScroll);
    }
    function onScroll() {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      if (h <= 0 || (window.scrollY + window.innerHeight) / (h + window.innerHeight) >= 0.7) mark();
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    setTimeout(mark, 45000);
  }


  // 수집 안내 한 줄. 푸터가 있는 페이지(뉴스레터·허브)는 푸터 안에, 없는 페이지
  // (topics/wiki/search 등 생성 페이지)는 본문 끝에 붙인다. 사이트 공통 푸터가
  // 없어서 이 파일이 전 페이지를 덮는 유일한 경로다.
  function mountNotice() {
    if (document.querySelector('.ss-notice')) return;
    var d = document.createElement('div');
    d.className = 'ss-notice';
    d.innerHTML = '쿠키 없이 익명 방문 통계만 수집합니다 · ' +
      '<a href="/privacy/">수집 안내</a>';
    var f = document.querySelector('.footer-inner') || document.querySelector('.footer');
    (f || document.body).appendChild(d);
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
    fab.addEventListener('click', function () { track('telegram'); });
    document.body.appendChild(fab);

    var sb = document.createElement('button');
    sb.className = 'ss-pageshare';
    sb.type = 'button';
    sb.innerHTML = '🔗 <span>공유하기</span>';
    sb.setAttribute('aria-label', '공유하기');
    sb.addEventListener('click', function () { track('share'); openShare(); });
    document.body.appendChild(sb);

    // 딥링크(#story-N)로 들어오면 그 스토리로 확실히 스크롤
    if (location.hash && location.hash.indexOf('#story-') === 0) {
      var target = document.getElementById(location.hash.slice(1));
      if (target) setTimeout(function () { target.scrollIntoView(true); }, 80);
    }

    // data-ss-ev가 붙은 링크(논점 블록의 텔레그램·인스타)는 위임으로 한 번에
    document.addEventListener('click', function (e) {
      var a = e.target && e.target.closest && e.target.closest('[data-ss-ev]');
      if (a) track(a.getAttribute('data-ss-ev'));
    });

    mountReactions();   // 스토리별 무로그인 반응
    mountTalk();        // 오늘의 논점 → 텔레그램
    trackView();        // 방문 집계 (익명, /stats/ 제외)
    mountNotice();      // 수집 안내(전 페이지 공통 푸터가 없어 여기서)
  }

  // ── 스토리별 반응 (무로그인) ─────────────────────────────
  // 숫자는 항상 보인다. Worker(D1)가 붙어 있으면 공유 집계,
  // 없으면 내 클릭만 로컬 집계 — 어느 쪽이든 버튼이 "죽어" 보이지 않게.
  var REACTS = [['👍', '좋았음'], ['🤔', '글쎄'], ['🔥', '중요함']];
  var CFG = window.SS_CFG || {};
  var API = CFG.worker || null;              // Cloudflare Worker(권장)
  var HAS_BACKEND = !!API;

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
    var btns = wrap.querySelectorAll('.ss-rg .ss-rb');   // 반응 3개만 — 다른 pill이 끼어들어도 안전
    for (var i = 0; i < btns.length; i++) {
      var emoji = REACTS[i][0];
      var n = shared[emoji] || 0;
      if (!HAS_BACKEND && mine === emoji) n += 1;    // 백엔드 없어도 내 반응은 보이게
      btns[i].className = 'ss-rb' + (mine === emoji ? ' on' : '');
      btns[i].querySelector('.n').textContent = n ? ' ' + n : '';
    }
  }


  // ── 스토리별 한 줄 코멘트 ───────────────────────────────────
  // 접힌 상태의 비용을 0에 수렴시킨다 — 0건이면 pill 하나만 늘고, 빈 입력창이나
  // "아직 댓글이 없습니다" 문구는 그리지 않는다. 그 문구가 죽은 사이트 신호다.
  var CMTS = {};        // storyKey → [{i,k,b,t}]
  var COPEN = null;     // 동시에 하나만 펼친다
  var CBTN = {};        // storyKey → pill

  function nickOf() {
    try { return localStorage.getItem('ss_nick') || ''; } catch (e) { return ''; }
  }
  function setNick(n) { try { localStorage.setItem('ss_nick', n); } catch (e) {} }

  function cAgo(ts) {
    var s = Math.max(0, Math.floor(Date.now() / 1000) - ts);
    if (s < 60) return '방금';
    if (s < 3600) return Math.floor(s / 60) + '분';
    if (s < 86400) return Math.floor(s / 3600) + '시간';
    return Math.floor(s / 86400) + '일';
  }

  function paintPill(key) {
    var b = CBTN[key];
    if (!b) return;
    var n = (CMTS[key] || []).length;
    b.querySelector('.n').textContent = n ? n : '';
    b.querySelector('.lb').textContent = n ? ' 한마디' : ' 한 줄 남기기';
  }

  function closeC() {
    if (COPEN && COPEN.parentNode) COPEN.parentNode.removeChild(COPEN);
    COPEN = null;
  }

  function openC(key, pill) {
    if (COPEN && COPEN._key === key) { closeC(); return; }
    closeC();
    var w = document.createElement('div');
    w._key = key;
    w.className = 'ss-cwrap';
    var nick = nickOf();
    w.innerHTML =
      '<textarea class="ss-cin" rows="2" maxlength="140" placeholder="한 줄로 남겨주세요"></textarea>' +
      '<input class="ss-hp" name="website" tabindex="-1" aria-hidden="true"/>' +
      '<div class="ss-crow">' +
        '<input class="ss-cin ss-cnick" maxlength="12" placeholder="닉네임" value="' + esc(nick) + '"/>' +
        '<span class="ss-cnt">0/140</span>' +
        '<button type="button" class="ss-cgo" disabled>남기기</button>' +
      '</div>' +
      '<div class="ss-clist"></div>' +
      '<div class="ss-cnote">남긴 글의 책임은 작성자에게 있습니다. 투자 권유·광고·비방은 ' +
      '사전 통보 없이 숨겨집니다.</div>';

    var ta = w.querySelector('.ss-cin');
    var go = w.querySelector('.ss-cgo');
    var cnt = w.querySelector('.ss-cnt');
    ta.addEventListener('input', function () {
      cnt.textContent = ta.value.length + '/140';
      go.disabled = !ta.value.trim();
    });
    go.addEventListener('click', function () { submitC(key, w, go); });

    renderC(key, w);
    pill.parentNode.parentNode.insertBefore(w, pill.parentNode.nextSibling);
    COPEN = w;
    setTimeout(function () { ta.focus(); }, 50);
  }

  function renderC(key, w) {
    var list = w.querySelector('.ss-clist');
    var items = CMTS[key] || [];
    list.innerHTML = items.map(function (c) {
      return '<div class="ss-ci"><span class="ss-ck">' + esc(c.k) + '</span>' +
        '<span class="ss-cb">' + esc(c.b) + (c.held ? '<span class="ss-chold">검토 중</span>' : '') +
        '</span><span class="ss-ct">' + cAgo(c.t) + '</span></div>';
    }).join('');
  }

  function submitC(key, w, go) {
    var ta = w.querySelector('.ss-cin');
    var ni = w.querySelector('.ss-cnick');
    var body = ta.value.trim();
    var nick = (ni.value || '').trim() || '순살독자';
    if (!body) return;
    go.disabled = true;
    setNick(nick);
    var v = vid();
    if (!API || !v) { toast('잠시 후 다시 시도해주세요'); go.disabled = false; return; }

    fetch(API.replace(/[/]$/, '') + '/comment', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ story: key, v: v, nick: nick, body: body,
                             hp: w.querySelector('.ss-hp').value }),
    }).then(function (r) { return r.json(); }).then(function (res) {
      if (res && res.error) {
        toast(res.error === 'too fast' ? '조금 뒤에 다시 남겨주세요'
            : res.error === 'too many' ? '오늘은 여기까지만'
            : '남기지 못했습니다');
        go.disabled = false;
        return;
      }
      ta.value = '';
      w.querySelector('.ss-cnt').textContent = '0/140';
      // 보류(state 0)여도 본인 화면에는 남긴다 — 실패로 보이면 다시 쓰고 도배가 된다
      var mine = { i: res.id, k: nick, b: body, t: Math.floor(Date.now() / 1000),
                   held: res.state === 0 };
      (CMTS[key] = CMTS[key] || []).push(mine);
      if (!mine.held) paintPill(key);
      renderC(key, w);
      track('comment');
      toast(mine.held ? '확인 후 보여드릴게요 🐟' : '남겼음 🐟');
    }).catch(function () { toast('남기지 못했습니다'); go.disabled = false; });
  }

  function mountComment(body, key, wrap) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'ss-rb ss-cbtn';
    b.innerHTML = '💬<span class="lb"> 한 줄 남기기</span><b class="n"></b>';
    b.addEventListener('click', function () { openC(key, b); });
    wrap.insertBefore(b, wrap.querySelector('.ss-sh'));
    CBTN[key] = b;
    paintPill(key);
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
        sh.addEventListener('click', function () { track('share'); openShare(s); });
        wrap.appendChild(sh);

        body.appendChild(wrap);
        mountComment(body, key, wrap);
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
    fetch(API.replace(/[/]$/, '') + '/page?issue=' + issue)
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var counts = (d && d.counts) || {};
        var cm = (d && d.comments) || {};
        Object.keys(WRAPS).forEach(function (k) {
          WRAPS[k]._shared = counts[k] || {};
          render(WRAPS[k], k);
          if (cm[k]) { CMTS[k] = cm[k]; paintPill(k); }
        });
        if (d && d.off && COPEN) closeC();
      }).catch(function () {});
  }

  function vote(key, emoji, wrap) {
    if (localVotes()[key] !== emoji) track('react');   // 취소 클릭은 세지 않는다
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
      '<a class="ss-talk-b" data-ss-ev="telegram" href="https://t.me/soonsal" target="_blank" rel="noopener">' +
      '텔레그램 수다방 →</a>' +
      '<a class="ss-talk-b ig" data-ss-ev="instagram" href="https://instagram.com/soonsal.brief" target="_blank" rel="noopener">' +
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
