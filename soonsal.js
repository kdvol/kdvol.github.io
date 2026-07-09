/* soonsal.js — 전 페이지 공용 위젯(플로팅 텔레그램 버튼 + 스토리 공유 버튼).
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
    '.ss-share{float:right;margin:2px 0 0 8px;background:transparent;border:1px solid #d8d4c8;' +
    'color:#8a8578;font-size:11px;font-weight:600;padding:3px 10px;border-radius:14px;cursor:pointer;' +
    'line-height:1.4;transition:all .15s;font-family:inherit}.ss-share:hover{border-color:#F07040;color:#F07040}' +
    '.ss-toast{position:fixed;left:50%;bottom:28px;transform:translateX(-50%);background:#222;color:#fff;' +
    'font-size:13px;padding:10px 18px;border-radius:8px;z-index:99999;box-shadow:0 4px 14px rgba(0,0,0,.3)}' +
    '.ss-pageshare{position:fixed;left:16px;bottom:16px;z-index:9999;background:#1f2937;color:#fff;border:none;' +
    'border-radius:26px;padding:13px 22px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit;' +
    'box-shadow:0 4px 14px rgba(0,0,0,.35);display:flex;align-items:center;gap:7px;transition:transform .15s}' +
    '.ss-pageshare:hover,.ss-pageshare:active{transform:scale(1.06)}' +
    '@media(min-width:640px){.ss-pageshare{left:24px;bottom:24px;padding:14px 24px;font-size:15px}}';

  function init() {
    var st = document.createElement('style');
    st.textContent = CSS;
    document.head.appendChild(st);

    // 플로팅 텔레그램 대화방 버튼
    var fab = document.createElement('a');
    fab.className = 'ss-fab';
    fab.href = 'https://t.me/soonsalchat';
    fab.target = '_blank';
    fab.rel = 'noopener';
    fab.setAttribute('aria-label', '텔레그램 실시간 대화방');
    fab.title = '텔레그램 대화방';
    fab.textContent = '💬';
    document.body.appendChild(fab);

    // 하단 큰 공유 버튼 — 지금 보는 페이지(브리핑)를 통째로 공유
    var sb = document.createElement('button');
    sb.className = 'ss-pageshare';
    sb.type = 'button';
    sb.innerHTML = '🔗 <span>공유하기</span>';
    sb.setAttribute('aria-label', '이 페이지 공유');
    sb.addEventListener('click', function () { sharePage(); });
    document.body.appendChild(sb);

    // 스토리별 공유 버튼 (제목이 있는 .story 에만)
    var stories = document.querySelectorAll('.story');
    for (var i = 0; i < stories.length; i++) {
      (function (s) {
        var title = s.querySelector('.story-title');
        if (!title || s.querySelector('.ss-share')) return;
        var b = document.createElement('button');
        b.className = 'ss-share';
        b.type = 'button';
        b.textContent = '🔗 공유';
        b.setAttribute('aria-label', '이 스토리 공유');
        b.addEventListener('click', function () { share(s); });
        title.insertAdjacentElement('afterend', b);
      })(stories[i]);
    }
  }

  function toast(m) {
    var d = document.createElement('div');
    d.className = 'ss-toast';
    d.textContent = m;
    document.body.appendChild(d);
    setTimeout(function () { d.remove(); }, 1800);
  }

  function doShare(t, url) {
    if (navigator.share) {
      navigator.share({ title: t, text: t, url: url }).catch(function () {});
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(url).then(function () { toast('링크가 복사됐어요'); });
    } else {
      toast(url);
    }
  }

  function share(story) {
    var url = location.origin + location.pathname + (story.id ? '#' + story.id : '');
    var el = story.querySelector('.story-title');
    doShare((el ? el.textContent : document.title).trim(), url);
  }

  function sharePage() {
    doShare(document.title.replace(/\s*[—|].*$/, '').trim() || document.title, location.href);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
