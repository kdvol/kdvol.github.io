
(function(){
  if(window.__ssHdr)return;window.__ssHdr=1;
  var API='https://api.soonsal.com';
  function run(){
    var h=document.querySelector('.site-header');if(!h)return;
    var css=document.createElement('style');css.id='ss-hdr-v1';css.textContent=
      '.site-header{position:sticky!important;z-index:9990;background:#111}'+
      '.ss-hl,.ss-hr{position:absolute;grid-area:auto;top:50%;transform:translateY(-50%);display:flex;align-items:center;gap:4px;z-index:2}'+
      '.ss-hl{left:max(10px,calc(50% - 400px))}.ss-hr{right:max(10px,calc(50% - 400px));gap:8px}'+
      '.ss-hl .search-btn-header,.ss-hr .sub-btn-header{position:static!important;transform:none!important;margin:0!important;inset:auto!important}'+
      '.ss-burger,.ss-acct{width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:50%;'+
      'background:none;border:0;color:#e8e4dc;cursor:pointer;padding:0;text-decoration:none}'+
      '.ss-acct{position:relative}.ss-acct .bd{position:absolute;top:-2px;right:-4px;min-width:17px;height:17px;padding:0 4px;border-radius:9px;background:#F07040;color:#12100e;font-size:10.5px;font-weight:800;line-height:17px;text-align:center}'+
      '.ss-dr a.li.soc{display:flex;justify-content:space-between}.ss-dr a.li.soc em{font-style:normal;background:#F07040;color:#12100e;border-radius:9px;padding:0 7px;font-size:11px;font-weight:800;line-height:18px}'+
      '.ss-burger:hover,.ss-acct:hover{background:#1f1f1f}.ss-acct img{width:30px;height:30px;border-radius:50%;object-fit:cover}'+
      '.ss-ov{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:100000;opacity:0;pointer-events:none;transition:opacity .2s}'+
      '.ss-dr{position:fixed;top:0;bottom:0;left:0;width:min(84vw,320px);background:#151515;z-index:100001;transform:translateX(-102%);'+
      'transition:transform .22s ease;overflow-y:auto;padding:18px 16px 40px;color:#e8e4dc;'+
      "font-family:'Pretendard',-apple-system,BlinkMacSystemFont,sans-serif}"+
      '.ss-open .ss-ov{opacity:1;pointer-events:auto}.ss-open .ss-dr{transform:none}'+
      '.ss-dr .acc{display:flex;gap:12px;align-items:center;background:#1c1c1c;border:1px solid #2a2a2a;border-radius:14px;'+
      'padding:14px;margin:6px 0 14px;text-decoration:none;color:inherit}.ss-dr .acc img{width:42px;height:42px;border-radius:50%}'+
      '.ss-dr .acc .ph{width:42px;height:42px;border-radius:50%;background:#262626;display:flex;align-items:center;justify-content:center;font-size:20px}'+
      '.ss-dr .acc b{display:block;font-size:15px}.ss-dr .acc span{font-size:12.5px;color:#9a958a}'+
      '.ss-dr .gp{font-size:11.5px;font-weight:800;letter-spacing:.08em;color:#7c756c;margin:18px 6px 2px}'+
      '.ss-dr a.li{display:block;padding:9px 6px;font-size:15.5px;font-weight:700;color:#e8e4dc;text-decoration:none}'+
      '.ss-dr a.li.mine{border:1px solid #2a2a2a;border-radius:10px;padding:11px 12px;margin-bottom:4px}'+
      '.ss-dr .ft{display:block;text-align:center;font-size:12px;color:#7c756c;margin-top:14px;text-decoration:none}'+
      '.ss-dr a.li:hover{color:#F59B75}.ss-dr .sub{display:block;text-align:center;background:#F07040;color:#12100e;border-radius:12px;'+
      'padding:13px;font-weight:800;margin:16px 0 4px;text-decoration:none}'+
      '.ss-dr .x{position:absolute;top:10px;right:10px;width:36px;height:36px;border:0;background:none;color:#aaa;font-size:22px;cursor:pointer}'+
      '@media(max-width:420px){.site-header>.logo-link{position:absolute!important;grid-area:auto!important;left:50%;top:50%;transform:translate(-50%,-50%);margin:0!important}'+
      '.site-header .logo-text{font-size:14.5px!important}.site-header .logo-link img{height:22px!important}.site-header .logo-link{gap:6px!important}'+
      '.ss-hr .sub-btn-header{padding:8px 11px!important;font-size:12.5px!important}.ss-hl{left:6px}.ss-hr{right:6px;gap:4px}}';
    document.head.appendChild(css);
    var tk=document.getElementById('soonsal-live-ticker');
    // 시세 띠는 시세를 받아 온 뒤에야 보여서(처음엔 display:none) 재는 순간 높이가 0 일 수 있다 —
    //   띠가 있으면 34px(띠 높이 고정값) 아래에 붙이고, 띠 크기가 바뀌면 다시 맞춘다.
    function setTop(){h.style.top=(tk?Math.max(tk.offsetHeight,34):0)+'px'}
    setTop();if(tk&&window.ResizeObserver)new ResizeObserver(setTop).observe(tk);
    if(!/relative|absolute|sticky|fixed/.test(getComputedStyle(h).position))h.style.position='sticky';

    var L=document.createElement('div');L.className='ss-hl';
    var bg=document.createElement('button');bg.type='button';bg.className='ss-burger';bg.setAttribute('aria-label','메뉴 열기');
    bg.innerHTML='<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>';
    L.appendChild(bg);var sb=h.querySelector('.search-btn-header');if(sb)L.appendChild(sb);h.appendChild(L);

    var R=document.createElement('div');R.className='ss-hr';
    var ac=document.createElement('a');ac.className='ss-acct';ac.href='/account/';ac.rel='nofollow';ac.setAttribute('aria-label','내 계정');
    ac.innerHTML='<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/></svg>';
    R.appendChild(ac);var su=h.querySelector('.sub-btn-header');if(su)R.appendChild(su);h.appendChild(R);

    var LINKS=[["읽기", [["/newsletters/", "뉴스레터"], ["/chart/", "순살차트"], ["/cardnews/", "카드뉴스"], ["/youtube/", "YouTube"]]], ["찾기", [["/search/", "검색"], ["/topics/", "주제별"], ["/english/", "금융 영어"]]], ["참여", [["/talk/", "순살톡"], ["/school/", "순살스쿨"]]], ["순살과 함께", [["/collab/", "광고·협업 문의"]]]];
    var wrap=document.createElement('div');
    wrap.innerHTML='<div class="ss-ov"></div><aside class="ss-dr" aria-label="전체 메뉴"><button class="x" aria-label="닫기">×</button>'+
      '<a class="acc" href="/account/" rel="nofollow"><span class="ph">🙂</span><span><b>로그인하고 스크랩 모으기</b><span>카카오·구글로 1초 · 폰·PC 에서 같이</span></span></a>'+
      '<a class="li mine" id="ss-mine" href="/saved/" rel="nofollow">🐟 내가 모은 글</a>'+
      '<a class="li soc" id="ss-nt" href="/account/#notices" rel="nofollow" hidden><span>🔔 알림</span><em hidden></em></a>'+
      '<a class="li soc" id="ss-mc" href="/account/#comments" rel="nofollow" hidden><span>💬 내가 남긴 댓글</span></a>'+
      LINKS.map(function(g){return '<div class="gp">'+g[0]+'</div>'+g[1].map(function(x){return '<a class="li" href="'+x[0]+'">'+x[1]+'</a>'}).join('')}).join('')+
      '<a class="sub" href="https://subscribe.soonsal.com/subscribe" target="_blank" rel="noopener">무료 구독하기</a>'+
      '<a class="ft" href="/privacy/">개인정보 처리 안내</a></aside>';
    document.body.appendChild(wrap);
    var root=document.documentElement;
    function open(v){root.classList.toggle('ss-open',v);document.body.style.overflow=v?'hidden':''}
    bg.onclick=function(){open(true)};wrap.querySelector('.ss-ov').onclick=function(){open(false)};
    wrap.querySelector('.x').onclick=function(){open(false)};
    document.addEventListener('keydown',function(e){if(e.key==='Escape')open(false)});

    var authed=false;try{authed=localStorage.getItem('ss_auth')==='1'}catch(e){}
    if(authed)fetch(API+'/me',{credentials:'include'}).then(function(r){return r.json()}).then(function(j){
      var u=j&&j.user;if(!u){try{localStorage.removeItem('ss_auth')}catch(e){}return}
      window.ssMe=u;try{document.dispatchEvent(new CustomEvent('ss-me',{detail:u}))}catch(e){}  // 페이지가 /me 를 또 부르지 않게 나눠 준다
      var nm=String(u.nick||u.name||'순살 독자').replace(/[<>&"]/g,'');
      var av=u.avatar?String(u.avatar).replace(/["<>]/g,''):'';
      if(av)ac.innerHTML='<img src="'+av+'" alt="">';
      var acc=wrap.querySelector('.acc');
      acc.innerHTML=(av?'<img src="'+av+'" alt="">':'<span class="ph">🙂</span>')+'<span><b>'+nm+'</b><span>내 계정 · 스크랩 보기</span></span>';
      // 소셜 (KD 2026-10-08): 알림 배지 · 내 댓글 · 이 브라우저를 계정에 묶기(한 번만) · 댓글 별명을 계정 별명으로
      // 「내가 모은 글」은 로그인하면 계정 것 하나로 (KD 2026-10-08 「데이터 구조 통일」):
      //   이 브라우저에만 있던 스크랩·반응·한마디 표시를 계정으로 자동으로 올리고, 링크도 계정 화면으로.
      wrap.querySelector('#ss-mine').href='/account/#saved';
      try{var rd=function(k){try{return JSON.parse(localStorage.getItem(k)||'{}')||{}}catch(e){return {}}};
        var syn=rd('ss_synced'),its=[];
        [['ss_scrap','scrap'],['ss_react','react'],['ss_cmt','cmt']].forEach(function(p){Object.keys(rd(p[0])).forEach(function(s){if(!syn[s])its.push({story:s,kind:p[1]})})});
        if(its.length)fetch(API+'/me/merge',{method:'POST',credentials:'include',headers:{'content-type':'application/json'},body:JSON.stringify({items:its.slice(0,500)})})
          .then(function(r){if(r.ok){its.forEach(function(x){syn[x.story]=1});localStorage.setItem('ss_synced',JSON.stringify(syn))}}).catch(function(){});
      }catch(e){}
      var un=u.unread|0,nt=wrap.querySelector('#ss-nt');nt.hidden=false;wrap.querySelector('#ss-mc').hidden=false;
      if(un){var em=nt.querySelector('em');em.textContent=un>99?'99+':un;em.hidden=false;
        var bd=document.createElement('span');bd.className='bd';bd.textContent=un>9?'9+':un;ac.appendChild(bd);ac.setAttribute('aria-label','내 계정 · 새 알림 '+un+'개')}
      try{var v=localStorage.getItem('ss_vid')||'';
        if(/^[a-z0-9-]{8,32}$/.test(v)&&localStorage.getItem('ss_vlink')!==u.id+':'+v)
          fetch(API+'/me/vid',{method:'POST',credentials:'include',headers:{'content-type':'application/json'},body:JSON.stringify({v:v})})
            .then(function(r){if(r.ok)localStorage.setItem('ss_vlink',u.id+':'+v)}).catch(function(){});
        if(u.nick&&/^[가-힣a-zA-Z0-9._ -]{1,12}$/.test(u.nick)){var pr=JSON.parse(localStorage.getItem('ss_prof')||'null')||{n:'',i:'',c:'',sc:0};
          if(pr.n!==u.nick){pr.n=u.nick;localStorage.setItem('ss_prof',JSON.stringify(pr));localStorage.setItem('ss_nick',u.nick)}}
      }catch(e){}
    }).catch(function(){});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();
})();
