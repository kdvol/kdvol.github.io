
(function(){
  if(window.__ssHdr)return;window.__ssHdr=1;
  var API='https://api.soonsal.com';
  // ── 글 끝 구독칸 (KD 2026-10-08 개선 1번) ─────────────────────────────
  //   검색·공유로 처음 온 사람이 글을 다 읽은 자리에서 이메일만 넣고 바로 구독. 메일에서 온 구독자에겐 안 보인다.
  //   구독자 표시(?ss=16hex.회차 / ?s=)·메일 유입 표시는 soonsal.js 가 주소에서 지우기 전에 여기서 먼저 본다(문서 순서상 먼저 실행).
  function lsg(k){try{return localStorage.getItem(k)}catch(e){return null}}
  function lss(k,v){try{localStorage.setItem(k,v)}catch(e){}}
  try{var qs=location.search;
    if(/[?&]ss=[a-f0-9]{16}\.|[?&]s=[a-f0-9]{16}\b|utm_source=mail|utm_medium=email|[?&]m=1\b/.test(qs))lss('ss_is_sub','1')}catch(e){}
  // ── 팔로우 버튼 (KD 2026-10-09 개선 3번) — /wiki/<slug>.html(회사·인물)·/topics/<slug>.html(주제) 제목 아래 ──
  function followBtn(u){
    var m=location.pathname.match(/^\/(wiki|topics)\/([a-z0-9-]+)\.html$/);if(!m||m[2]==='index')return;
    var h1=document.querySelector('h1');if(!h1||document.querySelector('.ss-fol'))return;
    var kind=m[1]==='wiki'?'e':'t',slug=m[2],key=kind+':'+slug;
    var name=(h1.textContent||'').replace(/\s*타임라인\s*$/,'').replace(/\s*관련.*$/,'').trim();
    var st=document.createElement('style');st.textContent=
      '.ss-fol{display:inline-flex;align-items:center;gap:6px;margin:8px 0 4px;padding:8px 14px;border-radius:999px;border:1px solid #F07040;'+
      'background:#F07040;color:#12100e;font:700 13.5px/1.2 Pretendard,-apple-system,sans-serif;cursor:pointer;text-decoration:none}'+
      '.ss-fol.on{background:transparent;color:#F59B75}.ss-fol small{font-weight:400;opacity:.8}';
    document.head.appendChild(st);
    var on=!!(u&&(u.follows||[]).indexOf(key)>=0);
    var b=document.createElement(u?'button':'a');b.className='ss-fol'+(on?' on':'');
    if(!u){b.href='/account/';b.rel='nofollow';b.innerHTML='＋ '+name+' 팔로우 <small>· 새 소식 알림</small>';}
    else{b.type='button';
      var paint=function(){b.className='ss-fol'+(on?' on':'');b.innerHTML=on?'✓ 팔로우 중 <small>· 새 브리핑에 나오면 알림</small>':'＋ '+name+' 팔로우 <small>· 새 소식 알림</small>'};paint();
      b.onclick=function(){var nx=!on;b.disabled=true;
        fetch(API+'/me/follow',{method:'POST',credentials:'include',headers:{'content-type':'application/json'},body:JSON.stringify({kind:kind,slug:slug,on:nx})})
          .then(function(r){if(r.ok){on=nx;paint()}}).catch(function(){}).then(function(){b.disabled=false})};}
    h1.parentNode.insertBefore(b,h1.nextSibling);
  }
  function subCard(){
    if(lsg('ss_is_sub')==='1'||lsg('ss_subbed')==='1')return;
    var x=parseInt(lsg('ss_subx')||'0',10);if(x&&Date.now()-x<7*864e5)return;   // 닫으면 일주일 쉰다
    var all=document.querySelectorAll('[data-ss-story]'),at=null,story=null;
    if(all.length){
      var hm=(location.hash||'').match(/^#story-(\d+)$/);
      if(hm)at=document.getElementById('story-'+hm[1]);          // 검색으로 그 스토리에 왔다면 그 글 바로 뒤
      if(!at||!at.hasAttribute('data-ss-story'))at=all[all.length-1];
      story=at.getAttribute('data-ss-story');
    }else if(/^\/(wiki|topics)\/[^/]+\.html$/.test(location.pathname)){
      // 타임라인(/wiki/)·주제(/topics/) — 검색 유입 착지 페이지. 다섯 번째 줄 뒤(앞부분을 훑어본 자리)
      var rows=document.querySelectorAll('.wrap .story, .item');if(!rows.length)return;
      at=rows[Math.min(4,rows.length-1)];
    }else return;
    var st=document.createElement('style');st.textContent=
      '.ss-subc{margin:22px 0;padding:18px 18px 14px;border-radius:14px;background:#FFF4EC;border:1px solid #F7D3BE;color:#3a2f27;'+
      'font-family:Pretendard,-apple-system,BlinkMacSystemFont,sans-serif;line-height:1.55;box-sizing:border-box;text-align:left}'+
      '.ss-subc *{box-sizing:border-box}.ss-subc b.t{display:block;font-size:16.5px;font-weight:800;color:#1f1a16;letter-spacing:-.02em}'+
      '.ss-subc .d{font-size:13px;color:#7a6a5c;margin:3px 0 11px}'+
      '.ss-subc .fl{display:block;font-size:13px;font-weight:700;color:#3a2f27;margin:12px 0 5px}.ss-subc .fl i{color:#E55A00;font-style:normal;margin-left:2px}'+
      '.ss-subc .ob{font-size:11px;font-weight:400;color:#9a8878;margin-left:3px}'+
      '.ss-subc .in{display:block;width:100%;height:44px;border:1px solid #E8C4AE;border-radius:10px;padding:0 12px;font-size:15px;background:#fff;color:#1f1a16;font-family:inherit}'+
      '.ss-subc .pl{display:flex;gap:7px;align-items:center;font-size:13px;color:#3a2f27;margin-top:14px;cursor:pointer}.ss-subc .pl input{width:17px;height:17px;accent-color:#F07040}'+
      '.ss-subc .ad{font-size:11.5px;color:#9a8878;margin-top:10px;line-height:1.6}.ss-subc .ad summary{cursor:pointer;margin-top:3px}.ss-subc .ad div{margin-top:4px}'+
      '.ss-subc button.go{display:block;width:100%;height:48px;margin-top:12px;border:0;border-radius:10px;background:#F07040;color:#12100e;font-weight:800;font-size:15.5px;cursor:pointer}'+
      '.ss-subc button.go:disabled{opacity:.55}'+
      '.ss-subc .more{font-size:11.5px;color:#9a8878;margin:5px 0 0 24px}'+
      '.ss-subc summary{list-style:none}.ss-subc summary::-webkit-details-marker{display:none}'+
      '.ss-subc details summary{cursor:pointer;color:#9a8878}.ss-subc details div{margin-top:5px;font-size:11.5px;color:#7a6a5c;line-height:1.65}'+
      '.ss-subc .x{float:right;border:0;background:none;color:#b8a898;font-size:16px;cursor:pointer;margin:-8px -6px 0 0}'+
      '.ss-subc .ok{font-size:15px;font-weight:800;color:#1f1a16}.ss-subc .er{font-size:12.5px;color:#C24A00;margin-top:6px;min-height:1px}'+
      '.ss-subc .hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}'+
      '.ss-subc .opt{margin-top:9px;font-size:12.5px}.ss-subc .opt summary{cursor:pointer;color:#C24A00;font-weight:700;list-style:none}'+
      '.ss-subc .opt summary::-webkit-details-marker{display:none}.ss-subc .opt summary span{color:#9a8878;font-weight:400}'+
      '.ss-subc .r2{display:flex;gap:7px;margin-top:9px}.ss-subc .r2 input,.ss-subc .r2 select,.ss-subc .cu{flex:1;min-width:0;height:40px;border:1px solid #E8C4AE;border-radius:10px;padding:0 10px;font-size:14px;background:#fff;color:#1f1a16}'+
      '.ss-subc .cu{width:100%;margin-top:8px}.ss-subc .tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}'+
      '.ss-subc .tg{border:1px solid #E8C4AE;background:#fff;color:#5a4a3e;border-radius:999px;padding:5px 11px;font-size:12.5px;cursor:pointer}'+
      '.ss-subc .tg.on{background:#F07040;border-color:#F07040;color:#12100e;font-weight:700}';
    document.head.appendChild(st);
    var c=document.createElement('section');c.className='ss-subc';c.setAttribute('aria-label','뉴스레터 무료 구독');
    // ★ 기존 구독 화면(subscribe.soonsal.com)과 같은 칸·순서·문구를 처음부터 다 보여 준다 (KD 2026-10-09
    //   「이메일만 받으면 의미가 적다 — 기존 구독 화면을 재현」). 이메일 → 이름 → 출생연도 → 관심분야 → 하는 일 → 동의 → 구독하기 → 광고 안내.
    var yrs='<option value="">선택</option>';for(var y=2010;y>=1960;y--)yrs+='<option value="'+y+'">'+y+'</option>';
    c.innerHTML='<button type="button" class="x" aria-label="닫기">×</button>'+
      '<b class="t">🐟 순살브리핑 뉴스레터 구독</b>'+
      '<div class="d">월~금 매일 아침, 글로벌 금융·경제·크립토 소식을 살코기만 발라드립니다</div>'+
      '<form novalidate>'+
      '<label class="fl">이메일 주소<i>*</i></label><input type="email" class="in em" placeholder="example@email.com" autocomplete="email" required>'+
      '<label class="fl">이름 (또는 닉네임) <span class="ob">선택</span></label><input class="in nm" placeholder="이름 또는 닉네임" maxlength="30" autocomplete="nickname">'+
      '<label class="fl">출생연도 <span class="ob">선택</span></label><select class="in by">'+yrs+'</select>'+
      '<label class="fl">관심분야 <span class="ob">선택, 복수 가능</span></label><div class="tags">'+
        ['주식','크립토','부동산','경제·매크로','취업·이직','창업·사업','정보습득','기타'].map(function(x){return '<button type="button" class="tg" data-v="'+x+'">'+x+'</button>'}).join('')+'</div>'+
      '<label class="fl">현재 하는일 <span class="ob">선택</span></label><input class="in cu" placeholder="예: 소속 기관, 업무, 산업분야 등" maxlength="40">'+
      '<input class="hp" name="website" tabindex="-1" aria-hidden="true">'+
      '<label class="pl"><input type="checkbox" class="ag"> <b>(필수)</b> 개인정보 수집 및 이용에 동의합니다.</label>'+
      '<details class="more"><summary>내용 보기 ▾</summary><div>뉴스레터 발송을 위한 최소한의 개인정보를 수집하고 이용합니다. 수집된 정보는 더 나은 뉴스레터 제작 및 구독자 통계 작성 등, 아래 서술된 목적으로 사용됩니다.<br><br>'+
        '<b>- 구독자 관리:</b> 구독자 본인의 구독 의사 확인, 피싱/스팸성 구독자의 접근 방지, 구독신청 회수 제한, 불만처리 등 민원처리, 공지사항 전달 등<br><br>'+
        '<b>- 서비스 개선 및 마케팅, 광고에의 활용:</b> 구독자의 순살브리핑 서비스 이용에 대한 통계 확인, 서비스의 유효성 확인, 이벤트 및 광고성 정보 제공, 접속 빈도 파악 등<br><br>'+
        '<b>- 뉴스레터 링크를 통한 웹 열람 기록:</b> 메일 안의 링크에는 회차 번호와 되돌릴 수 없게 처리한 구독자 표시가 붙어, 어느 회차의 어떤 글이 언제 열렸는지를 구독자 단위로 셉니다(읽은 사람 수·재방문, 글·주제별 분석, 구독자군별 경향, 재안내 판단, 광고주용 집계 지표, 오류 확인, 구성·발송 시각 조정). 저장소는 Cloudflare(미국)이며 국외에 저장될 수 있습니다. 열람·정정·삭제·처리정지를 언제든 요구하실 수 있고, <b>제3자에게 제공하지 않습니다.</b> 낱개 기록은 구독 기간 동안 보관하고, 해지하시거나 연결 끄기를 요청하시면 지웁니다. 자세한 내용은 <a href="/privacy/" style="color:#C24A00">수집 안내</a>에 있습니다.<br><br>'+
        '구독자 개인정보는 원칙적으로 서비스가 종료되거나 구독을 해지할 경우 지체없이 파기합니다.</div></details>'+
      '<button class="go" type="submit">구독하기</button>'+
      '</form>'+
      '<div class="er" role="status"></div>'+
      '<div class="ad">순살 뉴스레터를 구독하면 제휴 콘텐츠, 프로모션 등 광고성 정보 수신에 동의한 것으로 간주됩니다.'+
      '<details><summary>광고성 정보 수신 ▾</summary><div>순살 뉴스레터에는 가끔 제휴 콘텐츠나 프로모션이 포함될 수 있습니다. 광고가 포함된 콘텐츠에는 항상 (광고) 표시를 합니다. 원하지 않을 경우 뉴스레터 하단의 수신 거부를 통해 언제든지 구독을 해지할 수 있습니다.</div></details></div>';
    at.parentNode.insertBefore(c,at.nextSibling);
    var f=c.querySelector('form'),em=f.querySelector('.em'),go=f.querySelector('.go'),ag=c.querySelector('.ag'),er=c.querySelector('.er');
    c.querySelector('.x').onclick=function(){lss('ss_subx',String(Date.now()));c.parentNode.removeChild(c)};
    [].forEach.call(c.querySelectorAll('.tg'),function(b){b.onclick=function(){b.classList.toggle('on')}});
    f.onsubmit=function(e){e.preventDefault();er.textContent='';
      var v=(em.value||'').trim();
      if(!/^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/.test(v)){er.textContent='이메일 주소를 확인해 주세요.';em.focus();return}
      if(!ag.checked){er.textContent='개인정보 수집 및 이용 동의에 체크해 주세요.';ag.focus();return}
      go.disabled=true;go.textContent='보내는 중…';
      fetch(API+'/subscribe',{method:'POST',headers:{'content-type':'application/json'},
        body:JSON.stringify({email:v,agree:true,story:story,path:location.pathname,v:lsg('ss_vid')||'',hp:f.querySelector('.hp').value,
          name:c.querySelector('.nm').value,birthyear:c.querySelector('.by').value,current:c.querySelector('.cu').value,
          interest:[].map.call(c.querySelectorAll('.tg.on'),function(b){return b.getAttribute('data-v')}).join(',')})})
      .then(function(r){return r.json()}).then(function(j){
        if(j&&j.ok){lss('ss_subbed','1');lss('ss_is_sub','1');
          c.innerHTML='<div class="ok">'+(j.already?'이미 구독 중이에요 🐟 내일 아침에 만나요.':'구독 완료! 🐟 내일 아침 메일함에서 만나요.')+'</div>'+
            '<div class="d" style="margin:6px 0 0">첫 메일이 안 보이면 스팸함·프로모션함도 확인해 주세요.</div>';return}
        go.disabled=false;go.textContent='구독하기';
        er.textContent=j&&j.error==='email'?'이메일 주소를 확인해 주세요.':j&&j.error==='too many'?'잠시 뒤 다시 시도해 주세요.':'지금은 구독을 못 받았어요. 잠시 뒤 다시 시도해 주세요.'})
      .catch(function(){go.disabled=false;go.textContent='구독하기';er.textContent='연결이 불안정해요. 잠시 뒤 다시 시도해 주세요.'})};
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',subCard);else subCard();
  function run(){
    var h=document.querySelector('.site-header');if(!h)return;
    var css=document.createElement('style');css.id='ss-hdr-v1';css.textContent=
      '.site-header{position:sticky!important;z-index:9990;background:#111}'+
      '@media(max-width:640px){#soonsal-live-ticker{position:relative!important;top:auto!important}}'+
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
    // 폰에서는 시세 띠가 같이 붙어 있으면 화면 위 100px 가까이를 늘 차지한다 → 띠는 스크롤과 함께 올라가고
    //   헤더(☰·구독하기)만 맨 위에 남긴다 (KD 2026-10-08 개선 7번). PC 는 그대로 띠 아래 고정.
    var MOB=window.matchMedia('(max-width:640px)');
    function setTop(){h.style.top=(tk&&!MOB.matches?Math.max(tk.offsetHeight,34):0)+'px'}
    try{MOB.addEventListener('change',setTop)}catch(e){}
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
    if(!authed)try{followBtn(null)}catch(e){}
    if(authed)fetch(API+'/me',{credentials:'include'}).then(function(r){return r.json()}).then(function(j){
      var u=j&&j.user;if(!u){try{localStorage.removeItem('ss_auth')}catch(e){}try{followBtn(null)}catch(e){}return}
      window.ssMe=u;try{document.dispatchEvent(new CustomEvent('ss-me',{detail:u}))}catch(e){}  // 페이지가 /me 를 또 부르지 않게 나눠 준다
      try{followBtn(u)}catch(e){}
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
