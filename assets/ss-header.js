
(function(){
  if(window.__ssHdr)return;window.__ssHdr=1;
  var API='https://api.soonsal.com';
  // ── 글 끝 구독칸 (KD 2026-10-08 개선 1번) ─────────────────────────────
  //   검색·공유로 처음 온 사람이 글을 다 읽은 자리에서 이메일만 넣고 바로 구독. 메일에서 온 구독자에겐 안 보인다.
  //   구독자 표시(?ss=16hex.회차 / ?s=)·메일 유입 표시는 soonsal.js 가 주소에서 지우기 전에 여기서 먼저 본다(문서 순서상 먼저 실행).
  function lsg(k){try{return localStorage.getItem(k)}catch(e){return null}}
  function lss(k,v){try{localStorage.setItem(k,v)}catch(e){}}

  // ── 순살 통조림 팡 (KD 2026-10-11 「통조림 속 물고기가 꿈틀대며 뛰어오르는 — confetti 같은 효과를 우리만의 브랜딩으로」) ──
  //   주요 버튼(구독·스크랩·반응·팔로우·투표·완주)을 누른 자리에서 통조림 뚜껑이 젖혀지고, 물고기들이 꼬리를 흔들며
  //   포물선으로 튀어 올랐다 떨어진다. 그림은 SVG 몇 줄, 움직임은 Web Animations — 외부 파일 없음.
  //   window.ssCan(x, y, {big}) · window.ssCanAt(el, {big}). 움직임 줄이기 설정이면 아무것도 안 한다.
  // 로고 그대로 — 통조림은 로고의 검정 캔(어두운 화면에선 흰 로고 버전), 물고기는 로고 연어색 #F88C62 + 단순한 표정 (KD 2026-10-11)
  var FC='#F88C62',INK='#1a1a1a';
  function fishSvg(mood,W){W=W||40;
    var face=mood===1?'<path d="M29.3 8.6q1.9-2.3 3.8 0" fill="none" stroke="'+INK+'" stroke-width="1.5" stroke-linecap="round"/><path d="M33.6 12.2q1.6 1.5 3.2 0" fill="none" stroke="'+INK+'" stroke-width="1.3" stroke-linecap="round"/>'
      :mood===2?'<circle cx="31.2" cy="8.2" r="2.5" fill="#fff"/><circle cx="31.6" cy="8.2" r="1.35" fill="'+INK+'"/><ellipse cx="35.3" cy="12.4" rx="1.2" ry="1.5" fill="'+INK+'"/>'
      :'<circle cx="31.2" cy="8.4" r="2.4" fill="#fff"/><circle cx="31.7" cy="8.6" r="1.3" fill="'+INK+'"/><path d="M33.4 12.3q1.7 1.4 3.4 0" fill="none" stroke="'+INK+'" stroke-width="1.3" stroke-linecap="round"/>';
    return '<svg viewBox="0 0 40 20" width="'+W+'" height="'+(W/2)+'" style="display:block;overflow:visible">'+
      '<path d="M9.5 10C3.6 3 1.8 2.6 1 3.3c1.6 2.2 2.4 4.4 2.4 6.7S2.6 14.5 1 16.7c.8.7 2.6.3 8.5-6.7z" fill="'+FC+'"/>'+
      '<path d="M7.5 10C14 .8 31 .4 38.6 10 31 19.6 14 19.2 7.5 10z" fill="'+FC+'"/>'+
      '<ellipse cx="27" cy="12.6" rx="2" ry="1.2" fill="#ff6a55" opacity=".45"/>'+face+'</svg>';
  }
  // 로고(180px 아이콘) 실측 그대로 — 몸통 x33~148·바닥 타원 ry17, 테 타원 rx57.5/ry17, 입구(흰) rx50/ry12.5,
  //   뚜껑 = 테와 같은 타원을 왼쪽 경첩(33,80)에서 -27° 젖힌 것, 몸통 물고기는 45px·살짝 위로 (KD 2026-10-11 「로고와 정확히 같은 비율」)
  var CAN_VB='30 28 122 124',FISHP='<path d="M9.5 10C3.6 3 1.8 2.6 1 3.3c1.6 2.2 2.4 4.4 2.4 6.7S2.6 14.5 1 16.7c.8.7 2.6.3 8.5-6.7z" fill="'+FC+'"/><path d="M7.5 10C14 .8 31 .4 38.6 10 31 19.6 14 19.2 7.5 10z" fill="'+FC+'"/>';
  function canBack(dark){var C=dark?'#fafaf7':'#000',IN=dark?'#262626':'#fafaf7';
    return '<svg viewBox="'+CAN_VB+'" width="64" height="65" style="display:block;overflow:visible"><ellipse cx="90.5" cy="80" rx="57.5" ry="17" fill="'+C+'"/>'+
      '<ellipse cx="92" cy="82" rx="50" ry="12.5" fill="'+IN+'"/></svg>'}
  function canFront(dark){var C=dark?'#fafaf7':'#000';   // 앞판 — 입구 아래 테두리 + 몸통 (물고기를 가린다)
    return '<svg viewBox="'+CAN_VB+'" width="64" height="65" style="display:block;overflow:visible">'+
      '<path d="M33 80L33 130A57.5 17 0 0 0 148 130L148 80A57.5 17 0 0 1 145.6 85.8L142 82A50 12.5 0 0 1 42 82L35 85.4A57.5 17 0 0 1 33 80z" fill="'+C+'"/>'+
      '<g transform="translate(67 110) rotate(-10 22 11) scale(1.12)">'+FISHP+'</g></svg>'}
  function canLid(dark){var C=dark?'#fafaf7':'#000',E=dark?'#d6d6d0':'#2a2a2a';
    return '<svg viewBox="'+CAN_VB+'" width="64" height="65" style="display:block;overflow:visible"><ellipse cx="90.5" cy="80" rx="57.5" ry="17" fill="'+C+'"/>'+
      '<ellipse cx="90.5" cy="80" rx="49" ry="12.8" fill="none" stroke="'+E+'" stroke-width="1.6"/>'+          // 뚜껑 홈(닫혀 있을 때만 보임)
      '<path d="M139 76.5q7.5-1 9 3.5q-1.5 4.5-9 3.5" fill="none" stroke="'+E+'" stroke-width="2.2" stroke-linecap="round"/></svg>'}   // 따개 고리
  function darkAt(x,y){   // 누른 자리 뒤 배경이 어두우면 흰 로고 버전
    try{var el=document.elementFromPoint(x,y);
      while(el&&el!==document.documentElement){var c=getComputedStyle(el).backgroundColor,m=c&&c.match(/[\d.]+/g);
        if(m&&(m.length<4||+m[3]>.5))return (0.299*m[0]+0.587*m[1]+0.114*m[2])<128;el=el.parentElement}
      var b=getComputedStyle(document.body).backgroundColor.match(/[\d.]+/g);return b?(0.299*b[0]+0.587*b[1]+0.114*b[2])<128:true}catch(e){return true}}
  function ssCan(x,y,o){
    o=o||{};
    try{if(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)return}catch(e){}
    if(!document.body||!document.body.animate)return;
    var big=!!o.big,dark=darkAt(x,y),sc=big?1.3:1,T=2400;
    var host=document.createElement('div');
    host.style.cssText='position:fixed;left:'+x+'px;top:'+y+'px;width:0;height:0;z-index:2147483000;pointer-events:none';
    // 층: 뒤판(테·입구) → 물고기 → 앞판(몸통·앞 테두리) → 뚜껑. 앞판이 입구 아래를 가려 물고기가 캔 「안」에서 올라온다.
    //   좌표: 캔 64×65px, 입구 중심이 (33, 28) 근처 → 누른 점에 입구가 오게 놓는다.
    var K=64/122,OX=(92-30)*K,OY=(82-28)*K,HX=(33-30)*K,HY=(80-28)*K;
    var canw=document.createElement('div');canw.style.cssText='position:absolute;left:'+(-OX)+'px;top:'+(-OY)+'px;width:64px;height:65px;transform-origin:'+OX+'px '+(OY+20)+'px';
    var back=document.createElement('div');back.style.cssText='position:absolute;left:0;top:0';back.innerHTML=canBack(dark);
    var front=document.createElement('div');front.style.cssText='position:absolute;left:0;top:0';front.innerHTML=canFront(dark);
    var lid=document.createElement('div');lid.style.cssText='position:absolute;left:0;top:0;transform-origin:'+HX+'px '+HY+'px';lid.innerHTML=canLid(dark);
    var fishes=document.createElement('div');fishes.style.cssText='position:absolute;left:'+OX+'px;top:'+OY+'px';
    canw.appendChild(back);canw.appendChild(fishes);canw.appendChild(front);canw.appendChild(lid);host.appendChild(canw);document.body.appendChild(host);
    var A=function(el,k,d,dl,e){return el.animate(k,{duration:d,delay:dl||0,easing:e||'linear',fill:'both'})};
    // 통조림: 퐁 → (물고기 움찔할 때) 덜덜 → 뚜껑 따는 순간 꿀렁 → 물고기 다 나간 뒤 가라앉으며 사라짐
    A(canw,[{transform:'scale(0) translateY(14px)',opacity:0},{transform:'scale('+sc*1.12+') translateY(-3px)',opacity:1,offset:.07},{transform:'scale('+sc+')',offset:.12},
      {transform:'scale('+sc+') rotate(-2.5deg)',offset:.18},{transform:'scale('+sc+') rotate(2.5deg)',offset:.21},{transform:'scale('+sc+') rotate(-1.5deg)',offset:.24},{transform:'scale('+sc+') rotate(0)',offset:.27},
      {transform:'scale('+sc*1.05+','+sc*.93+')',offset:.3},{transform:'scale('+sc+')',offset:.35},
      {transform:'scale('+sc+') rotate(-2deg)',offset:.4},{transform:'scale('+sc+') rotate(2deg)',offset:.43},{transform:'scale('+sc+')',offset:.46},   // 물고기 움찔할 때 같이 덜덜
      {transform:'scale('+sc+')',opacity:1,offset:.86},{transform:'scale('+sc*.55+') translateY(20px)',opacity:0}],T,0,'ease-out');
    // 뚜껑 따기: 고리 걸림(살짝 들림) → 멈칫 → 오른쪽부터 쭉 벗겨지며 젖힘 → 살짝 넘어갔다 → 로고 각도(-27°)에 안착
    A(lid,[{transform:'rotate(0)',offset:0},{transform:'rotate(0)',offset:.15},{transform:'rotate(-4deg)',offset:.19,easing:'ease-out'},
      {transform:'rotate(-3deg)',offset:.24},{transform:'rotate(-5deg)',offset:.27,easing:'cubic-bezier(.3,0,.2,1)'},
      {transform:'rotate(-33deg)',offset:.33,easing:'ease-in-out'},{transform:'rotate(-25deg)',offset:.37,easing:'ease-in-out'},{transform:'rotate(-27deg)',offset:.41}],T,0);
    var n=big?8:5,g=1600;
    for(var i=0;i<n;i++)(function(i){
      // 3겹: 경로(pos) · 방향·회전(rot) · 몸짓(body: 움찔·찌그러짐·꼬리 파닥)
      var pos=document.createElement('div'),rot=document.createElement('div'),body=document.createElement('div');
      // 표정이 보이게 크게 — 보통 54px, 큰 버전 62px
      var FW=big?50:44;                       // 캔 폭의 약 60% — 로고 속 물고기 비율
      pos.style.cssText='position:absolute;left:0;top:0';rot.style.cssText='position:absolute;left:-'+(FW/2)+'px;top:-'+(FW/4)+'px;transform-origin:'+(FW/2)+'px '+(FW/4)+'px';
      body.style.cssText='transform-origin:'+(FW*.3)+'px '+(FW/4)+'px';body.innerHTML=fishSvg(i%3,FW);
      rot.appendChild(body);pos.appendChild(rot);fishes.appendChild(pos);
      var spread=n>1?(i/(n-1)-.5)*2:0,vx=(spread*150+(Math.random()*50-25))*(big?1.45:1),vy=-(380+Math.random()*180)*(big?1.2:1);
      // 순서: 뚜껑 걸림(0.4s)→벗겨져 열림(~0.75s)→그 뒤에야 빼꼼→움찔→발사
      var peek=800+Math.random()*120,launch=1080+i*45+Math.random()*70,fly=950+Math.random()*350,end=launch+fly;
      var face=vx<0?' scaleX(-1)':'';       // 왼쪽으로 가는 놈은 좌우 뒤집어 머리가 진행 방향
      var mx=Math.max(-16,Math.min(16,spread*15)),fr=[],steps=20;
      fr.push({transform:'translate('+mx+'px,16px)',offset:0});                          // 캔 안(작게 접혀 앞판 뒤에 숨어 있음)
      fr.push({transform:'translate('+mx+'px,16px)',offset:.82*peek/end});
      fr.push({transform:'translate('+mx+'px,-6px)',offset:peek/end*0.75,easing:'ease-out'});   // 고개 빼꼼 — 입구 위로
      fr.push({transform:'translate('+mx+'px,2px)',offset:launch/end*0.97});              // 움찔하며 다시 웅크림
      for(var k=0;k<=steps;k++){var t=k/steps*fly/1000;
        fr.push({transform:'translate('+(mx+vx*t).toFixed(1)+'px,'+(-1+vy*t+.5*g*t*t).toFixed(1)+'px)',offset:Math.min(1,(launch+k/steps*fly)/end)})}
      A(pos,fr,end,0);
      // 방향: 빼꼼할 땐 위를 보고 → 날아가며 진행 방향, 일부는 공중제비(360°)·스핀
      var trick=Math.random(),rk=[{transform:'rotate(-90deg)'+face,offset:0},{transform:'rotate(-90deg)'+face,offset:launch/end*.97}];
      for(var k2=0;k2<=10;k2++){var t2=k2/10*fly/1000,vyt=vy+g*t2,ang=Math.atan2(vyt,Math.abs(vx)||1)*180/Math.PI;
        if(vx<0)ang=-ang;                                     // 뒤집힌 놈은 각도도 거울로
        var extra=trick<.25?(vx<0?-1:1)*360*k2/10:(trick<.4?Math.sin(k2/10*Math.PI)*40:0);
        rk.push({transform:'rotate('+(ang+extra).toFixed(1)+'deg)'+face,offset:Math.min(1,(launch+k2/10*fly)/end)})}
      A(rot,rk,end,0);
      // 몸짓: 빼꼼 뒤 움찔움찔(찌그러졌다 폈다) → 발사 순간 길게 늘어남 → 날며 꼬리 파닥 → 사라짐
      var bk=[{transform:'scale(.5)',opacity:1,offset:0},{transform:'scale(.5)',opacity:1,offset:.82*peek/end},{transform:'scale(1)',opacity:1,offset:peek/end}],tw=launch-peek,b0=peek/end;
      for(var j=1;j<=6;j++){var o2=(peek+tw*j/7)/end;bk.push({transform:(j%2?'rotate(-16deg) scale(1.12,.82)':'rotate(14deg) scale(.92,1.1)'),opacity:1,offset:o2})}
      bk.push({transform:'scale(.8,1.25)',offset:launch/end*.99});                          // 웅크렸다가
      bk.push({transform:'scale(1.35,.72)',offset:Math.min(1,(launch+60)/end)});             // 쭉 늘어나며 발사
      for(var w=1;w<=8;w++){var ow=(launch+fly*w/9)/end;bk.push({transform:'skewY('+(w%2?14:-14)+'deg) scale('+(w%2?.9:1.06)+',1)',opacity:w>6?.6:1,offset:Math.min(.999,ow)})}
      bk.push({transform:'scale(.9)',opacity:0,offset:1});
      A(body,bk,end,0);
    })(i);
    // 기름 방울 — 발사 순간 튐
    for(var j=0;j<(big?10:6);j++)(function(){var d=document.createElement('div');
      d.style.cssText='position:absolute;left:-3px;top:-6px;width:6px;height:6px;border-radius:50%;background:'+(Math.random()<.5?'#F88C62':'#ffc4a8');host.appendChild(d);
      var a=-Math.PI/2+(Math.random()-.5)*2.4,r=34+Math.random()*50;
      A(d,[{transform:'translate(0,0) scale(.3)',opacity:0},{transform:'translate('+(Math.cos(a)*r*.6)+'px,'+(Math.sin(a)*r*.6)+'px) scale(1)',opacity:1,offset:.4},
        {transform:'translate('+(Math.cos(a)*r)+'px,'+(Math.sin(a)*r+28)+'px) scale(.5)',opacity:0}],720,1080+Math.random()*140,'ease-out')})();
    setTimeout(function(){if(host.parentNode)host.parentNode.removeChild(host)},T+600);
  }
  function ssCanAt(el,o){try{var r=el.getBoundingClientRect();ssCan(r.left+r.width/2,r.top+r.height/2,o)}catch(e){}}
  window.ssCan=ssCan;window.ssCanAt=ssCanAt;
  // 스크랩 🐟 — 켜질 때만 (ss-scrap.js 는 따로 도는 스크립트라 클릭을 여기서 받는다)
  document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('.ss-scrap');if(!b)return;
    setTimeout(function(){if(b.classList.contains('on'))ssCanAt(b)},0)});
  try{var qs=location.search;
    if(/[?&]ss=[a-f0-9]{16}\.|[?&]s=[a-f0-9]{16}\b|utm_source=mail|utm_medium=email|[?&]m=1\b/.test(qs))lss('ss_is_sub','1')}catch(e){}
  // ── 팔로우 버튼 (KD 2026-10-09 개선 3번) — /wiki/<slug>.html(회사·인물)·/topics/<slug>.html(주제) 제목 아래 ──
  function followBtn(u){
    var m=location.pathname.match(/^\/(wiki|topics)\/([a-z0-9-]+)\.html$/);if(!m||m[2]==='index')return;
    var h1=document.querySelector('h1');if(!h1||document.querySelector('.ss-fol'))return;
    var kind=m[1]==='wiki'?'e':'t',slug=m[2],key=kind+':'+slug;
    var name=(h1.textContent||'').replace(/\s*타임라인\s*$/,'').replace(/\s*관련.*$/,'').replace(/^[^0-9A-Za-z가-힣]+/,'').trim();   // 앞 이모지 떼기
    var st=document.createElement('style');st.textContent=
      /* 팔로우는 보조 동작 — 꽉 찬 주황(구독하기 몫) 대신 테두리 버튼 (KD 2026-10-09 검수) */
      '.ss-fol{display:inline-flex;align-items:center;gap:6px;margin:14px 0 6px;padding:7px 13px;min-height:0;border-radius:999px;border:1px solid #5a3524;'+
      'background:transparent;color:#F59B75;font:700 13px/1.2 Pretendard,-apple-system,sans-serif;cursor:pointer;text-decoration:none}'+
      '.ss-fol:hover{border-color:#F07040}.ss-fol.on{background:#2a1a12;border-color:#5a3524;color:#F59B75}.ss-fol small{font-weight:500;color:#8a8378;font-size:12px}';
    document.head.appendChild(st);
    var on=!!(u&&(u.follows||[]).indexOf(key)>=0);
    var b=document.createElement(u?'button':'a');b.className='ss-fol'+(on?' on':'');
    if(!u){b.href='/account/';b.rel='nofollow';b.innerHTML='＋ '+name+' 팔로우 <small>· 새 소식 알림</small>';}
    else{b.type='button';
      var paint=function(){b.className='ss-fol'+(on?' on':'');b.innerHTML=on?'✓ 팔로우 중 <small>· 새 브리핑에 나오면 알림</small>':'＋ '+name+' 팔로우 <small>· 새 소식 알림</small>'};paint();
      b.onclick=function(){var nx=!on;b.disabled=true;
        fetch(API+'/me/follow',{method:'POST',credentials:'include',headers:{'content-type':'application/json'},body:JSON.stringify({kind:kind,slug:slug,on:nx})})
          .then(function(r){if(r.ok){on=nx;paint();if(on)ssCanAt(b)}}).catch(function(){}).then(function(){b.disabled=false})};}
    h1.parentNode.insertBefore(b,h1.nextSibling);
  }
  // ── 알림 패널 (KD 2026-10-09 「사이트 알림을 깔끔한 UX로」) — 로그인하면 계정 아이콘이 패널을 연다 ──
  function notiPanel(u,ac){
    var st=document.createElement('style');st.textContent=
      '.ss-np{position:fixed;z-index:10050;top:64px;right:max(10px,calc(50% - 400px));width:min(380px,calc(100vw - 20px));max-height:min(72vh,560px);'+
      'display:flex;flex-direction:column;background:#161616;border:1px solid #2c2c2c;border-radius:16px;box-shadow:0 18px 50px rgba(0,0,0,.55);'+
      'font-family:Pretendard,-apple-system,BlinkMacSystemFont,sans-serif;color:#ece7de;overflow:hidden;opacity:0;transform:translateY(-6px);transition:opacity .16s,transform .16s}'+
      '.ss-np.on{opacity:1;transform:none}.ss-np[hidden]{display:none}'+
      '.ss-np .hd{display:flex;align-items:center;gap:10px;padding:14px 16px 10px;border-bottom:1px solid #232323}'+
      '.ss-np .hd img,.ss-np .hd .ph{width:34px;height:34px;border-radius:50%;object-fit:cover;background:#2a2a2a;display:flex;align-items:center;justify-content:center}'+
      '.ss-np .hd b{display:block;font-size:14.5px}.ss-np .hd small{display:block;font-size:12px;color:#F59B75;margin-top:1px}'+
      '.ss-np .tl{display:flex;justify-content:space-between;align-items:baseline;padding:12px 16px 6px;font-size:13px;font-weight:800;color:#bdb6aa}'+
      '.ss-np .tl span{font-weight:600;color:#7d776e;font-size:12px}'+
      '.ss-np .ls{overflow-y:auto;padding:0 8px 6px}'+
      '.ss-np .it{display:flex;gap:11px;padding:10px 9px;border-radius:12px;text-decoration:none;color:inherit;position:relative}'+
      '.ss-np .it:hover{background:#1f1f1f}.ss-np .it .ic{flex:0 0 32px;height:32px;border-radius:50%;background:#262019;display:flex;align-items:center;justify-content:center;font-size:15px}'+
      '.ss-np .it .tx{flex:1;min-width:0}.ss-np .it .m{font-size:13.5px;line-height:1.45;color:#ece7de}.ss-np .it .m b{color:#fff}'+
      '.ss-np .it .s{font-size:12.5px;color:#9b958b;line-height:1.45;margin-top:2px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}'+
      '.ss-np .it .t{font-size:11.5px;color:#6f695f;margin-top:3px}'+
      '.ss-np .it.new::after{content:"";position:absolute;right:10px;top:16px;width:7px;height:7px;border-radius:50%;background:#F07040}'+
      '.ss-np .em{padding:22px 16px 24px;text-align:center;font-size:13px;color:#8b8578;line-height:1.7}'+
      '.ss-np .ft{display:flex;border-top:1px solid #232323}.ss-np .ft a{flex:1;text-align:center;padding:12px 4px;font-size:12.5px;font-weight:700;color:#cfc8bb;text-decoration:none}'+
      '.ss-np .ft a+a{border-left:1px solid #232323}.ss-np .ft a:hover{color:#F59B75}';
    document.head.appendChild(st);
    var esc=function(v){return String(v||'').replace(/[<>&"]/g,'')};
    var nm=esc(u.nick||u.name||'순살 독자'),av=u.avatar?esc(u.avatar):'',sk=u.streak|0;
    var pn=document.createElement('div');pn.className='ss-np';pn.hidden=true;pn.setAttribute('role','dialog');pn.setAttribute('aria-label','알림');
    pn.innerHTML='<div class="hd">'+(av?'<img src="'+av+'" alt="">':'<span class="ph">🙂</span>')+'<div><b>'+nm+'</b><small>'+(sk>=2?'🐟 '+sk+'일 연속 읽음':'오늘도 반가워요')+'</small></div></div>'+
      '<div class="tl">알림<span class="cn"></span></div><div class="ls"><div class="em">불러오는 중…</div></div>'+
      '<div class="ft"><a href="/account/" rel="nofollow">내 계정 · 모은 글 · 댓글 · 팔로우 →</a></div>';
    document.body.appendChild(pn);
    function surl(stry){stry=String(stry||'');var mm=stry.match(/^m(\d{4})(\d{2})(\d{2})-([a-z0-9-]+)$/);
      if(mm)return '/chart/'+mm[1]+'/'+mm[2]+mm[3]+'.html#'+mm[4];var m=stry.match(/^(\d{4})(c?)-(\d+)$/);
      return m?'/newsletters/2026/'+m[1]+m[2]+'.html#story-'+m[3]:'/talk/'}
    function ago(t){var d=Math.floor(Date.now()/1000)-t;return d<60?'방금':d<3600?Math.floor(d/60)+'분 전':d<86400?Math.floor(d/3600)+'시간 전':Math.floor(d/86400)+'일 전'}
    var loaded=false;
    function load(){if(loaded)return;loaded=true;
      Promise.all([fetch(API+'/me/notices',{credentials:'include'}).then(function(r){return r.json()}),
                   fetch('/saved/stories.json').then(function(r){return r.json()}).catch(function(){return {}})]).then(function(v){
        var it=(v[0]&&v[0].items)||[],SM=v[1]||{},ls=pn.querySelector('.ls');
        pn.querySelector('.cn').textContent=(v[0]&&v[0].n)?'새 알림 '+v[0].n+'개':'';
        if(!it.length){ls.innerHTML='<div class="em">아직 알림이 없어요.<br>내 댓글에 답글·좋아요가 달리거나<br>팔로우한 회사·주제가 브리핑에 나오면 여기 떠요.</div>';return}
        ls.innerHTML=it.slice(0,12).map(function(x){
          var ic=x.kind==='reply'?'💬':x.kind==='follow'?'📌':'❤️',m,sub;
          if(x.kind==='reply'){m='<b>'+esc(x.who||'누군가')+'</b>님이 내 댓글에 답글을 남겼어요';sub=x.reply?'“'+esc(x.reply)+'”':esc(x.mine)}
          else if(x.kind==='follow'){m='팔로우한 <b>'+esc(x.who)+'</b> 새 이야기';sub=esc((SM[x.story]||[])[0]||'')}
          else{m='내 댓글이 좋아요를 받았어요';sub=esc(x.mine)}
          return '<a class="it'+(x.seen?'':' new')+'" href="'+surl(x.story)+'"><span class="ic">'+ic+'</span><span class="tx"><span class="m">'+m+'</span>'+
            (sub?'<span class="s">'+sub+'</span>':'')+'<span class="t">'+ago(x.ts)+'</span></span></a>'}).join('');
        if(v[0]&&v[0].n)fetch(API+'/me/notices',{method:'POST',credentials:'include',headers:{'content-type':'application/json'},body:'{}'}).catch(function(){});
      }).catch(function(){pn.querySelector('.ls').innerHTML='<div class="em">알림을 불러오지 못했어요. 잠시 뒤 다시 열어 주세요.</div>'})}
    function open(v){if(v){var hh=ac.closest('.site-header');pn.style.top=Math.max(8,(hh?hh.getBoundingClientRect().bottom:56)+8)+'px';pn.hidden=false;requestAnimationFrame(function(){pn.classList.add('on')});load();
        var bd=ac.querySelector('.bd');if(bd)bd.parentNode.removeChild(bd);}
      else{pn.classList.remove('on');setTimeout(function(){pn.hidden=true},160)}}
    ac.addEventListener('click',function(e){e.preventDefault();open(pn.hidden)});
    document.addEventListener('click',function(e){if(!pn.hidden&&!pn.contains(e.target)&&!ac.contains(e.target))open(false)});
    document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!pn.hidden)open(false)});
  }
  // ── 구독 양식 — 페이지 안 칸과 팝업이 같은 부품을 쓴다 (KD 2026-10-11) ──────────────────────────────
  function subCss(){if(document.getElementById('ss-subc-css'))return;
    // 기존 구독 화면(subscribe.soonsal.com)과 같은 색·글꼴 — 검정 바탕·흰 글씨·진한 주황 (KD 2026-10-11 「연한 살색 애매, 더 진하고 강렬하게」)
    var st=document.createElement('style');st.id='ss-subc-css';st.textContent=
      '.ss-subc{margin:28px 0;padding:24px 20px 18px;border-radius:16px;background:#111;border:1px solid #2a2a2a;color:#fff;'+
      'font-family:Pretendard,-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;line-height:1.55;box-sizing:border-box;text-align:left;position:relative}'+
      '.ss-subc *{box-sizing:border-box}'+
      '.ss-subc div,.ss-subc span,.ss-subc label,.ss-subc b,.ss-subc summary{white-space:normal;padding-top:0;font-variant-numeric:normal;background:transparent;box-shadow:none;max-width:none}'+
      '.ss-subc .hd{text-align:center;margin:0 0 18px}'+
      '.ss-subc .lg{width:46px;height:46px;margin:0 auto 12px;background:#E55A00;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:24px}'+
      '.ss-subc b.t{display:block;font-size:21px;font-weight:800;color:#fff;letter-spacing:-.03em}.ss-subc b.t em{font-style:normal;color:#E55A00}'+
      '.ss-subc .d{display:block;font-size:13px;color:#a8a8a8;margin:6px 0 0;text-align:center}.ss-subc .d2{display:block;font-size:12px;color:#7a7a7a;margin:2px 0 0;text-align:center}'+
      '.ss-subc .fl{display:block;font-size:13px;font-weight:700;color:#ddd;margin:14px 0 6px}.ss-subc .fl i{color:#E55A00;font-style:normal;margin-left:2px}'+
      '.ss-subc .ob{font-size:11.5px;font-weight:400;color:#777;margin-left:4px}'+
      '.ss-subc .in{display:block;width:100%;height:44px;border:1px solid #333;border-radius:9px;padding:0 13px;font-size:15px;background:#1a1a1a;color:#fff;font-family:inherit;outline:none;-webkit-appearance:none;appearance:none}'+
      '.ss-subc select.in{background-image:linear-gradient(45deg,transparent 50%,#888 50%),linear-gradient(135deg,#888 50%,transparent 50%);background-position:calc(100% - 18px) 19px,calc(100% - 13px) 19px;background-size:5px 5px;background-repeat:no-repeat}'+
      '.ss-subc .in:focus{border-color:#E55A00}.ss-subc .in::placeholder{color:#555}'+
      '.ss-subc .tags{display:flex;flex-wrap:wrap;gap:7px}'+
      '.ss-subc .tg{border:1px solid #333;background:transparent;color:#bbb;border-radius:20px;padding:6px 13px;font-size:13px;cursor:pointer;min-height:0!important;font-family:inherit}'+
      '.ss-subc .tg.on{background:#E55A00;border-color:#E55A00;color:#fff;font-weight:700}'+
      '.ss-subc .pl{display:flex;gap:8px;align-items:center;font-size:13px;color:#ddd;margin-top:18px;padding-top:16px;border-top:1px solid #222;cursor:pointer}.ss-subc .pl input{width:18px;height:18px;accent-color:#E55A00;flex:0 0 auto}'+
      '.ss-subc .pl b{color:#E55A00}'+
      '.ss-subc .more{font-size:12px;color:#777;margin:6px 0 0 26px}'+
      '.ss-subc summary{list-style:none;cursor:pointer}.ss-subc summary::-webkit-details-marker{display:none}'+
      '.ss-subc details div{margin-top:6px;font-size:11.5px;color:#999;line-height:1.65}.ss-subc details a{color:#F07040}'+
      '.ss-subc button.go{display:block;width:100%;height:50px;margin-top:16px;border:0;border-radius:10px;background:#E55A00;color:#fff;font-weight:800;font-size:16px;cursor:pointer;font-family:inherit;letter-spacing:-.01em}'+
      '.ss-subc button.go:hover{background:#F07040}.ss-subc button.go:disabled{opacity:.55}'+
      '.ss-subc .ad{font-size:11.5px;color:#777;margin-top:12px;line-height:1.6}.ss-subc .ad summary{margin-top:3px}'+
      '.ss-subc .ss-sbnl{font-size:11.5px;color:#888;margin-top:12px;padding:12px 0 0;border-top:1px solid #222;line-height:1.7}.ss-subc .ss-sbnl b{color:#ddd}'+
      '.ss-subc .x{position:absolute;top:10px;right:10px;width:36px;height:36px;border:0;background:none;color:#888;font-size:22px;cursor:pointer;min-height:0!important}'+
      '.ss-subc .ok{font-size:17px;font-weight:800;color:#fff;text-align:center;margin-top:6px}.ss-subc .er{font-size:12.5px;color:#ff8a5c;margin-top:8px;min-height:1px}'+
      '.ss-subc .hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}';
    document.head.appendChild(st);
  }
  function subForm(story,onClose){subCss();
    var c=document.createElement('section');c.className='ss-subc';c.setAttribute('aria-label','뉴스레터 무료 구독');
    // ★ 기존 구독 화면(subscribe.soonsal.com)과 같은 칸·순서·문구를 처음부터 다 보여 준다 (KD 2026-10-09
    //   「이메일만 받으면 의미가 적다 — 기존 구독 화면을 재현」). 이메일 → 이름 → 출생연도 → 관심분야 → 하는 일 → 동의 → 구독하기 → 광고 안내.
    var yrs='<option value="">선택</option>';for(var y=2010;y>=1960;y--)yrs+='<option value="'+y+'">'+y+'</option>';
    c.innerHTML='<button type="button" class="x" aria-label="닫기">×</button>'+
      '<div class="hd"><div class="lg">🐟</div><b class="t"><em>순살브리핑</em> 뉴스레터 구독</b>'+
      '<span class="d">모건스탠리 홍콩 출신 금융인의 글로벌 금융·경제·크립토 뉴스 살코기</span>'+
      '<span class="d2">월~금 매일 아침 10시, 살코기만 발라드립니다</span></div>'+
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
      '<details><summary>광고성 정보 수신 ▾</summary><div>순살 뉴스레터에는 가끔 제휴 콘텐츠나 프로모션이 포함될 수 있습니다. 광고가 포함된 콘텐츠에는 항상 (광고) 표시를 합니다. 원하지 않을 경우 뉴스레터 하단의 수신 거부를 통해 언제든지 구독을 해지할 수 있습니다.</div></details></div>'+
      '<div class="ss-sbnl">구독할 뉴스레터 — <b>순살브리핑</b> 글로벌 시장·경제 핵심 뉴스를 매일 5분 안에 · <b>순살크립토</b> 크립토 시장 흐름과 온체인 인사이트<br>구독 후 환경설정에서 개별 선택 가능합니다.</div>';
    var f=c.querySelector('form'),em=f.querySelector('.em'),go=f.querySelector('.go'),ag=c.querySelector('.ag'),er=c.querySelector('.er');
    c.querySelector('.x').onclick=function(){onClose&&onClose()};
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
            '<div class="d" style="margin:8px 0 0">첫 메일이 안 보이면 스팸함·프로모션함도 확인해 주세요.</div>';
          try{var rr=c.getBoundingClientRect();window.ssCan&&window.ssCan(rr.left+rr.width/2,rr.top+Math.min(rr.height/2,160),{big:true})}catch(_){}return}
        go.disabled=false;go.textContent='구독하기';
        er.textContent=j&&j.error==='email'?'이메일 주소를 확인해 주세요.':j&&j.error==='too many'?'잠시 뒤 다시 시도해 주세요.':'지금은 구독을 못 받았어요. 잠시 뒤 다시 시도해 주세요.'})
      .catch(function(){go.disabled=false;go.textContent='구독하기';er.textContent='연결이 불안정해요. 잠시 뒤 다시 시도해 주세요.'})};
    return c;
  }
  // 페이지 안 칸 — **뉴스레터 회차 페이지에만, 한 번** (KD 2026-10-11 「검색·타임라인 등 여기저기 난무」).
  //   홈은 첫 화면 「매일 아침 메일로 받기」, 다른 페이지는 우측 상단 「구독하기」(팝업)가 맡는다.
  function subCard(){
    if(lsg('ss_is_sub')==='1'||lsg('ss_subbed')==='1')return;
    var x=parseInt(lsg('ss_subx')||'0',10);if(x&&Date.now()-x<7*864e5)return;   // 닫으면 일주일 쉰다
    if(!/^\/newsletters\/\d{4}\/[^/]+\.html$/.test(location.pathname))return;
    var all=document.querySelectorAll('[data-ss-story]');if(!all.length)return;
    var hm=(location.hash||'').match(/^#story-(\d+)$/),at=null;
    if(hm)at=document.getElementById('story-'+hm[1]);          // 검색으로 그 스토리에 왔다면 그 글 바로 뒤
    if(!at||!at.hasAttribute('data-ss-story'))at=all[all.length-1];
    var c=subForm(at.getAttribute('data-ss-story'),function(){lss('ss_subx',String(Date.now()));c.parentNode.removeChild(c)});
    at.parentNode.insertBefore(c,at.nextSibling);
  }
  // 팝업 — 사이트 버튼(우측 상단·메뉴·홈 첫 화면)은 새 페이지로 보내지 않고 이 자리에서 바로 받는다.
  //   뉴스레터 본문(메일 원본) 안의 구독 링크는 그대로 subscribe.soonsal.com 으로 간다.
  function subModal(){
    if(document.getElementById('ss-subm'))return;subCss();
    var st=document.getElementById('ss-subm-css');
    if(!st){st=document.createElement('style');st.id='ss-subm-css';st.textContent=
      '#ss-subm{position:fixed;inset:0;z-index:100010;display:flex;align-items:center;justify-content:center;padding:20px 14px;background:rgba(0,0,0,.72);opacity:0;transition:opacity .18s}'+
      '#ss-subm.on{opacity:1}#ss-subm .ss-subc{margin:0;width:100%;max-width:420px;max-height:calc(100vh - 40px);max-height:calc(100dvh - 40px);overflow-y:auto;overscroll-behavior:contain;'+
      'box-shadow:0 24px 60px rgba(0,0,0,.6);transform:translateY(14px) scale(.98);transition:transform .22s cubic-bezier(.2,.9,.3,1.2)}#ss-subm.on .ss-subc{transform:none}'+
      '@media(max-width:560px){#ss-subm .ss-subc{padding:20px 16px 16px;border-radius:16px}#ss-subm .ss-subc .hd{margin-bottom:12px}#ss-subm .ss-subc .lg{width:40px;height:40px;font-size:21px;margin-bottom:8px}'+
      '#ss-subm .ss-subc b.t{font-size:19px}#ss-subm .ss-subc .fl{margin:11px 0 5px}#ss-subm .ss-subc .in{height:42px}}';
      document.head.appendChild(st)}
    var ov=document.createElement('div');ov.id='ss-subm';ov.setAttribute('role','dialog');ov.setAttribute('aria-modal','true');ov.setAttribute('aria-label','뉴스레터 무료 구독');
    var prev=document.body.style.overflow;
    function close(){ov.classList.remove('on');document.body.style.overflow=prev;document.removeEventListener('keydown',esc);setTimeout(function(){if(ov.parentNode)ov.parentNode.removeChild(ov)},180)}
    function esc(e){if(e.key==='Escape')close()}
    ov.appendChild(subForm(null,close));
    ov.addEventListener('click',function(e){if(e.target===ov)close()});
    document.addEventListener('keydown',esc);
    document.body.appendChild(ov);document.body.style.overflow='hidden';
    requestAnimationFrame(function(){ov.classList.add('on');var em=ov.querySelector('.em');if(em&&window.matchMedia('(min-width:561px)').matches)em.focus()});
  }
  document.addEventListener('click',function(e){
    var a=e.target.closest&&e.target.closest('a[href*="subscribe.soonsal.com"]');if(!a)return;
    if(!a.closest('.site-header, .ss-dr, .hero'))return;          // 사이트 버튼만 — 본문 링크는 원래대로
    if(e.metaKey||e.ctrlKey||e.shiftKey||e.button===1)return;      // 새 탭으로 열려는 클릭은 막지 않는다
    e.preventDefault();
    if(document.documentElement.classList.contains('ss-open')){document.documentElement.classList.remove('ss-open');document.body.style.overflow=''}
    subModal();
  });
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',subCard);else subCard();
  // ── 오늘의 질문 투표 (KD 2026-10-09 개선 4번) — 홈(히어로 아래)·그날 뉴스레터(질문이 나온 스토리 뒤) ──
  function pollCard(){
    var home=!!(document.getElementById('nlwrap')&&document.querySelector('.hero'));   // 홈 구조로 판별
    var iss=document.querySelector('[data-ss-issue]');
    if(!home&&!iss)return;
    fetch(API+'/poll').then(function(r){return r.json()}).then(function(j){
      var p=j&&j.poll;if(!p)return;
      // ★ 질문은 그 질문이 나온 스토리 안(끝)에 — 맥락 없이 따로 떠 있으면 와닿지 않았다 (KD 2026-10-09).
      //   노출은 맥락을 붙인 채로 더한다: 홈 「오늘의 순살」 목록의 그 스토리 바로 아래 한 줄, 뉴스레터 목차의 그 스토리 옆 🗳️.
      var sm=String(p.story||'').match(/-(\d+)$/),sn=sm&&sm[1];if(!sn)return;
      var scope=home?document.getElementById('nlwrap'):document;
      if(!home&&iss.getAttribute('data-ss-issue')!==p.day.slice(5,7)+p.day.slice(8,10))return;   // 그날 회차에서만
      if(!scope)return;
      var at=scope.querySelector('#story-'+sn);
      if(!at||document.querySelector('.ss-poll'))return;
      var light=!!at.closest('.wrapper,.nl');
      var st=document.createElement('style');st.textContent=
        '.ss-poll{margin:34px 0 30px;padding:16px 2px 4px;border-top:1px solid #2a2622;color:#e8e3da;'+
        'font-family:Pretendard,-apple-system,BlinkMacSystemFont,sans-serif;line-height:1.5;box-sizing:border-box}'+
        '.ss-poll *{box-sizing:border-box}.ss-poll .k{font-size:12px;font-weight:800;color:#bdb6aa;letter-spacing:.04em}'+
        '.ss-poll .q{font-size:15.5px;font-weight:800;margin:4px 0 10px;color:#f6f1e8;letter-spacing:-.02em}'+
        '.ss-poll .bt{display:flex;gap:8px}.ss-poll .bt button{flex:1;height:40px;border-radius:999px;border:1px solid #3a332c;background:transparent;color:#e8e3da;font:700 14px Pretendard,sans-serif;cursor:pointer}'+
        '.ss-poll .bt button:hover{border-color:#F07040;color:#F59B75}'+
        '.ss-poll .rs div{position:relative;height:34px;border-radius:999px;background:#262019;margin-bottom:7px;overflow:hidden;display:flex;align-items:center;padding:0 12px;font-size:14px;font-weight:700}'+
        '.ss-poll .rs i{position:absolute;left:0;top:0;bottom:0;background:#5a3524}.ss-poll .rs .me i{background:#F07040}'+
        '.ss-poll .rs span{position:relative;flex:1}.ss-poll .rs b{position:relative;color:#f6f1e8}.ss-poll .rs .me span{color:#12100e}'+
        '.ss-poll .n{font-size:12px;color:#8b8578;margin-top:2px}'+
        /* 밝은 뉴스레터 본문용 */
        '.ss-poll.lt{margin:24px 0 8px;padding:18px 18px 14px;border:1px solid #ece6dc;border-radius:14px;background:#fffaf5;color:#2a2420}'+
        '.ss-poll.lt .k{color:#6f695f}.ss-poll.lt .q{color:#1f1a16;font-size:16px}'+
        '.ss-poll.lt .bt button{border-color:#e3d9cc;color:#3a2f27;background:#fff}.ss-poll.lt .bt button:hover{border-color:#F07040;color:#C24A00}'+
        '.ss-poll.lt .rs div{background:#f1ebe2;color:#3a2f27}.ss-poll.lt .rs i{background:#f6d4c0}.ss-poll.lt .rs .me i{background:#F07040}'+
        '.ss-poll.lt .rs b{color:#3a2f27}.ss-poll.lt .rs .me span{color:#12100e}.ss-poll.lt .n{color:#9a8f82}.ss-poll.lt .n a{color:#C24A00}'+
        '.ss-pt{display:block;margin:-6px 0 10px 30px;padding:10px 12px;border-radius:10px;background:#1a1512;border:1px solid #3a2a20;color:#e8e3da;font-size:13.5px;line-height:1.5;text-decoration:none}'+
        '.ss-pt span{color:#bdb6aa;font-weight:800}.ss-pt b{color:#F07040}.ss-pt:hover{border-color:#F07040}'+
        '.ss-pi{font-size:.8em;font-weight:700;color:#C24A00;white-space:nowrap}';
      document.head.appendChild(st);
      var c=document.createElement('section');c.className='ss-poll'+(light?' lt':'');c.id='ss-poll';c.setAttribute('aria-label','오늘의 질문');
      var key='ss_poll_'+p.day,mine=0;try{mine=parseInt(localStorage.getItem(key)||'0',10)||0}catch(e){}
      var esc=function(v){return String(v||'').replace(/[<>&"]/g,'')};
      function draw(na,nb){
        var tot=na+nb;
        if(!mine){c.innerHTML='<div class="k">🗳️ 오늘의 질문 · 이 이야기, 어떻게 보세요?</div><div class="q">'+esc(p.q)+'</div>'+
          '<div class="bt"><button type="button" data-c="1">'+esc(p.a)+'</button><button type="button" data-c="2">'+esc(p.b)+'</button></div>'+
          '<div class="n">누르면 다른 독자들 선택이 보여요'+(tot?' · '+tot+'명 참여':'')+'</div>';
          [].forEach.call(c.querySelectorAll('.bt button'),function(b){b.onclick=function(){vote(parseInt(b.getAttribute('data-c'),10))}});return}
        var pa=tot?Math.round(na*100/tot):0,pb=tot?100-pa:0;
        c.innerHTML='<div class="k">🗳️ 오늘의 질문 · 이 이야기, 어떻게 보세요?</div><div class="q">'+esc(p.q)+'</div><div class="rs">'+
          '<div class="'+(mine===1?'me':'')+'"><i style="width:'+pa+'%"></i><span>'+esc(p.a)+(mine===1?' ✓':'')+'</span><b>'+pa+'%</b></div>'+
          '<div class="'+(mine===2?'me':'')+'"><i style="width:'+pb+'%"></i><span>'+esc(p.b)+(mine===2?' ✓':'')+'</span><b>'+pb+'%</b></div></div>'+
          '<div class="n">'+tot+'명 참여 · 결과는 다음 브리핑에서 이야기해요 · <a href="#" class="ch" style="color:#F59B75">다시 고르기</a></div>';
        c.querySelector('.ch').onclick=function(e){e.preventDefault();mine=0;draw(na,nb)};
      }
      function vote(v){var vid='';try{vid=localStorage.getItem('ss_vid')||''}catch(e){}
        try{var vb=c.querySelector('.bt button[data-c="'+v+'"]');if(vb)ssCanAt(vb)}catch(e){}
        mine=v;try{localStorage.setItem(key,String(v))}catch(e){}
        draw((p.na||0)+(v===1?1:0),(p.nb||0)+(v===2?1:0));   // 낙관적 표시 → 서버 값으로 맞춤
        if(!/^[a-z0-9-]{8,32}$/.test(vid))return;
        fetch(API+'/poll',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({day:p.day,v:vid,c:v})})
          .then(function(r){return r.json()}).then(function(j){if(j&&j.ok){p.na=j.na;p.nb=j.nb;draw(j.na,j.nb)}}).catch(function(){})}
      draw(p.na||0,p.nb||0);
      // 스토리 안쪽 끝 — 반응 줄·한마디 칸이 그려진 뒤에 오도록 조금 기다렸다 붙인다
      setTimeout(function(){at.appendChild(c)},600);
      // 맥락 붙은 추가 노출
      var go=function(e){e.preventDefault();var w=document.getElementById('nlwrap'),bx=document.getElementById('expand');
        if(w&&!w.classList.contains('open')){w.classList.add('open');if(bx)bx.textContent='접기 ↑'}
        setTimeout(function(){var y=c.getBoundingClientRect().top+window.scrollY-90;window.scrollTo({top:y,behavior:'smooth'})},80)};
      if(home){var row=document.querySelector('.hero .hs[data-n="'+sn+'"]');
        if(row){var t=document.createElement('a');t.className='ss-pt';t.href='#ss-poll';
          t.innerHTML='<span>🗳️ 오늘의 질문</span> '+esc(p.q)+' <b>→</b>';t.onclick=go;row.parentNode.insertBefore(t,row.nextSibling)}}
      else{var li=document.querySelector('.ss-story-index a[href$="#story-'+sn+'"]');
        if(li&&!li.querySelector('.ss-pi')){var m=document.createElement('span');m.className='ss-pi';m.textContent=' 🗳️ 투표';li.appendChild(m)}}
    }).catch(function(){});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',pollCard);else pollCard();
  // ── 카카오톡 공유 (KD 2026-10-09 개선 5번) — 스토리마다 「💬 카톡」 버튼, 카드 이미지는 /share/<id>.jpg ──
  //   JavaScript 키는 원래 웹페이지에 공개되는 키다(앱 479808, JS SDK 도메인 soonsal.com 등록됨). SDK 는 누를 때만 받는다.
  var KAKAO_JS='d0bec18d3bfd804f9d714e562a93ae70';
  function kakaoSdk(cb){
    if(window.Kakao&&window.Kakao.Share){if(!Kakao.isInitialized())Kakao.init(KAKAO_JS);return cb()}
    var sc=document.createElement('script');sc.src='https://t1.kakaocdn.net/kakao_js_sdk/2.7.4/kakao.min.js';sc.crossOrigin='anonymous';
    sc.onload=function(){try{if(!Kakao.isInitialized())Kakao.init(KAKAO_JS);cb()}catch(e){}};document.head.appendChild(sc);
  }
  function kakaoShare(el){
    var sid=el.getAttribute('data-ss-story')||'',m=sid.match(/-(\d+)$/);
    var t=el.querySelector('[id$="-title"],.story-title,h2,h3');var title=(t?t.textContent:document.title).replace(/\s+/g,' ').trim();
    var li=el.querySelector('.bullet')||el.querySelector('li');var desc=(li?li.textContent:'').replace(/\s+/g,' ').trim().slice(0,90);
    var url=location.origin+location.pathname+(m?'#story-'+m[1]:'');
    var img=/^\d{4}c?-\d{1,2}$/.test(sid)?location.origin+'/share/'+sid+'.jpg':(document.querySelector('meta[property="og:image"]')||{}).content;
    kakaoSdk(function(){Kakao.Share.sendDefault({objectType:'feed',
      content:{title:title,description:desc||'글로벌 금융·경제 뉴스, 매일 아침 5분 살코기만',imageUrl:img,imageWidth:1200,imageHeight:630,
        link:{mobileWebUrl:url,webUrl:url}},
      buttons:[{title:'순살에서 읽기',link:{mobileWebUrl:url,webUrl:url}}]})});
  }
  // 반응 줄 정돈 (KD 2026-10-09 「버튼 정렬·모양이 뒤죽박죽, 만들다 만 페이지 같다」):
  //   왼쪽 반응 3개 = 같은 높이 알약, 오른쪽 = 같은 크기 동그란 아이콘 2개(링크 복사 · 카카오톡).
  var IC_LINK='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.07 0l2.83-2.83a5 5 0 0 0-7.07-7.07L11.5 4.43"/><path d="M14 11a5 5 0 0 0-7.07 0L4.1 13.83a5 5 0 0 0 7.07 7.07l1.33-1.33"/></svg>';
  var IC_KAKAO='<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 3.5c-5.25 0-9.5 3.3-9.5 7.37 0 2.62 1.76 4.92 4.4 6.23l-.9 3.32c-.08.3.26.54.52.37l3.95-2.6c.5.06 1.01.1 1.53.1 5.25 0 9.5-3.3 9.5-7.42S17.25 3.5 12 3.5z"/></svg>';
  var rxCss=false;
  function kakaoButtons(){
    if(!rxCss&&document.querySelector('.ss-react')){rxCss=true;var st=document.createElement('style');st.textContent=
      '.ss-react{gap:8px!important;align-items:center!important;margin:16px 0 6px!important}.ss-react .ss-rg{gap:8px!important}'+
      '.ss-react .ss-rb{height:36px;display:inline-flex;align-items:center;justify-content:center;gap:5px;padding:0 14px!important;'+
      'border-radius:999px!important;font-size:13px!important;font-weight:600;line-height:1!important;box-sizing:border-box;min-height:0!important;min-width:0!important}'+
      '.ss-react .ss-rb b:empty{display:none}.ss-react .ss-rb svg{flex:0 0 auto}'+
      '.ss-react .ss-sh,.ss-react .ss-kk{width:36px;padding:0!important;gap:0}'+
      '.ss-react .ss-sh{margin-left:auto!important}.ss-react .ss-kk{margin-left:0!important}'+
      '.ss-react .ss-kk:hover{border-color:#E5C800!important;color:#3A1D1D!important;background:#FEE500!important}'+
      '@media(max-width:430px){.ss-react{gap:6px!important}.ss-react .ss-rg{gap:6px!important}'+
      '.ss-react .ss-rb{height:34px;padding:0 10px!important;font-size:12.5px!important}.ss-react .ss-sh,.ss-react .ss-kk{width:34px}'+
      '.ss-react{flex-wrap:nowrap!important}}';
      document.head.appendChild(st)}
    [].forEach.call(document.querySelectorAll('[data-ss-story]'),function(el){
      if(el.querySelector('.ss-kk'))return;
      var sh=el.querySelector('.ss-sh');if(!sh)return;               // 반응 줄(👍🤔🔥🔗)이 그려진 뒤에 붙인다
      sh.innerHTML=IC_LINK;sh.setAttribute('aria-label','링크 복사·공유');sh.title='링크 복사·공유';
      var b=document.createElement('button');b.type='button';b.className='ss-rb ss-kk';b.innerHTML=IC_KAKAO;
      b.title='카카오톡으로 공유';b.setAttribute('aria-label','카카오톡으로 공유');b.onclick=function(e){e.preventDefault();kakaoShare(el)};
      sh.parentNode.insertBefore(b,sh.nextSibling);
    });
  }
  var kkTries=0;(function kkLoop(){kakaoButtons();if(++kkTries<12)setTimeout(kkLoop,800)})();
  // ★ 로고 「Soonsal」 = Yeseva One (브랜드 원본 로고 글꼴, KD 2026-10-09 「앞으로 계속 이걸로, 들쭉날쭉 금지」).
  //   모든 페이지의 헤더 로고를 여기 한 곳에서 맞춘다 — 페이지마다 다른 글꼴이 박혀 있어도 여기서 덮는다.
  function brandLogo(h){
    if(!document.getElementById('ss-yeseva')){var lk=document.createElement('link');lk.id='ss-yeseva';lk.rel='stylesheet';
      lk.href='https://fonts.googleapis.com/css2?family=Yeseva+One&display=swap';document.head.appendChild(lk)}
    [].forEach.call(h.querySelectorAll('.logo-text'),function(t){
      if(t.querySelector('.ss-yes'))return;
      var s=t.textContent||'';if(s.indexOf('Soonsal')<0)return;
      var ko=s.replace('Soonsal','').trim();
      t.innerHTML=(ko?'<span class="ss-ko">'+ko.replace(/[<>&]/g,'')+'</span> ':'')+'<span class="ss-yes">Soonsal</span>';
    });
  }
  function run(){
    var h=document.querySelector('.site-header');if(!h)return;
    try{brandLogo(h)}catch(e){}
    var css=document.createElement('style');css.id='ss-hdr-v1';css.textContent=
      '.site-header{position:sticky!important;z-index:9990;background:#111}'+
      '@media(max-width:640px){#soonsal-live-ticker{position:relative!important;top:auto!important}}'+
      '.ss-hl,.ss-hr{position:absolute;grid-area:auto;top:50%;transform:translateY(-50%);display:flex;align-items:center;gap:4px;z-index:2}'+
      '.ss-hl{left:max(10px,calc(50% - 400px))}.ss-hr{right:max(10px,calc(50% - 400px));gap:14px}'+
      '.ss-hl .search-btn-header,.ss-hr .sub-btn-header{position:static!important;transform:none!important;margin:0!important;inset:auto!important}'+
      '.ss-burger,.ss-acct{width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:50%;'+
      'background:none;border:0;color:#e8e4dc;cursor:pointer;padding:0;text-decoration:none}'+
      /* 화면 아래 떠 있는 「공유하기」는 뺀다 — 스토리마다 링크·카톡 버튼이 있다 (KD 2026-10-09 버튼 정리) */
      '.ss-pageshare{display:none!important}'+
      /* 💬 순살톡 배지 — 버튼 밖으로 파랗게 삐져나오던 숫자를 계정 배지와 같은 꼴로 */
      '.ss-fab .ss-fabn{position:absolute!important;top:-3px!important;right:-3px!important;min-width:20px;height:20px;padding:0 5px;border-radius:10px;'+
      'background:#fff!important;color:#C24A00!important;font:800 11px/20px Pretendard,-apple-system,sans-serif!important;text-align:center;box-shadow:0 0 0 2px #F07040}'+
      '.ss-fab{position:fixed}'+
      '.site-header .ss-yes{font-family:"Yeseva One",Georgia,"Times New Roman",serif!important;font-weight:400!important;letter-spacing:.01em}'+
      '.site-header .ss-ko{font-family:Pretendard,-apple-system,BlinkMacSystemFont,sans-serif;font-weight:800}'+
      /* 폰에선 깡통 로고 + Soonsal 만 — Yeseva 가 넓어 한글까지 넣으면 계정 아이콘을 덮었다 */
      '@media(max-width:420px){.site-header .ss-ko{display:none}.site-header .ss-yes{font-size:20px}}'+
      '.ss-acct{position:relative}.ss-acct .bd{position:absolute;top:1px;right:1px;min-width:15px;height:15px;padding:0 3px;border-radius:8px;background:#F07040;color:#12100e;font-size:9.5px;font-weight:800;line-height:15px;text-align:center;box-shadow:0 0 0 2px #111}'+
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
      '.ss-dr .acc em.nb{font-style:normal;font-weight:800;color:#F59B75}.ss-dr [hidden]{display:none!important}'+
      '.ss-dr .gp{font-size:11.5px;font-weight:800;letter-spacing:.08em;color:#7c756c;margin:18px 6px 2px}'+
      '.ss-dr a.li{display:block;padding:9px 6px;font-size:15.5px;font-weight:700;color:#e8e4dc;text-decoration:none}'+
      '.ss-dr a.li.mine{border:1px solid #2a2a2a;border-radius:10px;padding:11px 12px;margin-bottom:4px}'+
      '.ss-dr .ft{display:block;text-align:center;font-size:12px;color:#7c756c;margin-top:14px;text-decoration:none}'+
      '.ss-dr a.li:hover{color:#F59B75}.ss-dr .sub{display:block;text-align:center;background:#F07040;color:#12100e;border-radius:12px;'+
      'padding:13px;font-weight:800;margin:16px 0 4px;text-decoration:none}'+
      '.ss-dr .x{position:absolute;top:10px;right:10px;width:36px;height:36px;border:0;background:none;color:#aaa;font-size:22px;cursor:pointer}'+
      '@media(max-width:420px){.site-header>.logo-link{position:absolute!important;grid-area:auto!important;left:50%;top:50%;transform:translate(-50%,-50%);margin:0!important}'+
      '.site-header .logo-text{font-size:13.5px!important}.site-header .logo-link img{height:20px!important}.site-header .logo-link{gap:5px!important}'+
      '.ss-acct{width:32px;height:32px}'+
      '.ss-hr .sub-btn-header{padding:8px 11px!important;font-size:12.5px!important}.ss-hl{left:6px}.ss-hr{right:6px;gap:8px}}';
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

    var LINKS=[["읽기", [["/newsletters/", "뉴스레터"], ["/chart/", "순살차트"], ["/cardnews/", "카드뉴스"], ["/youtube/", "YouTube"]]], ["찾기", [["/search/", "검색"], ["/topics/", "주제별"]]], ["참여", [["/talk/", "순살톡"], ["/school/", "순살스쿨"]]], ["순살과 함께", [["/collab/", "광고·협업 문의"]]]];
    var wrap=document.createElement('div');
    wrap.innerHTML='<div class="ss-ov"></div><aside class="ss-dr" aria-label="전체 메뉴"><button class="x" aria-label="닫기">×</button>'+
      '<a class="acc" href="/account/" rel="nofollow"><span class="ph">🙂</span><span><b>로그인하고 스크랩 모으기</b><span>카카오·구글로 1초 · 폰·PC 에서 같이</span></span></a>'+
      '<a class="li mine" id="ss-mine" href="/saved/" rel="nofollow" hidden>🐟 이 브라우저에 모은 글</a>'+
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
    // 메뉴 중복 정리 (KD 2026-10-09 「중복 streamline」): 회원 메뉴는 계정 카드 하나 — 알림·모은 글·댓글은 카드 너머 내 계정에,
    //   손님은 이 브라우저에 모은 게 있을 때만 「모은 글」 줄을 보인다. 구독 중이면 구독 버튼(헤더·메뉴)을 거둔다.
    function hideSub(){var a=wrap.querySelector('.sub');if(a)a.hidden=true;if(su)su.style.display='none'}
    if(lsg('ss_is_sub')==='1'||lsg('ss_subbed')==='1')hideSub();
    if(!authed)try{var hasL=['ss_scrap','ss_react'].some(function(k){try{return Object.keys(JSON.parse(localStorage.getItem(k)||'{}')||{}).length>0}catch(e){return false}});
      wrap.querySelector('#ss-mine').hidden=!hasL}catch(e){}
    if(!authed)try{followBtn(null)}catch(e){}
    if(authed)fetch(API+'/me',{credentials:'include'}).then(function(r){return r.json()}).then(function(j){
      var u=j&&j.user;if(!u){try{localStorage.removeItem('ss_auth')}catch(e){}try{followBtn(null)}catch(e){}return}
      if(u.is_sub===1){lss('ss_is_sub','1');hideSub()}   // 뉴스레터 구독 중인 회원엔 구독칸·구독 버튼을 띄우지 않는다
      window.ssMe=u;try{document.dispatchEvent(new CustomEvent('ss-me',{detail:u}))}catch(e){}  // 페이지가 /me 를 또 부르지 않게 나눠 준다
      try{followBtn(u)}catch(e){}
      var nm=String(u.nick||u.name||'순살 독자').replace(/[<>&"]/g,'');
      var av=u.avatar?String(u.avatar).replace(/["<>]/g,''):'';
      if(av)ac.innerHTML='<img src="'+av+'" alt="">';
      var acc=wrap.querySelector('.acc');
      var sk=u.streak|0;   // 연속 읽기(평일 기준) — KD 2026-10-09 개선 4번
      var un=u.unread|0;
      acc.innerHTML=(av?'<img src="'+av+'" alt="">':'<span class="ph">🙂</span>')+'<span><b>'+nm+'</b><span>'+
        (un?'<em class="nb">새 알림 '+(un>99?'99+':un)+'</em>':sk>=2?'🐟 '+sk+'일 연속 읽음':'알림 · 모은 글 · 댓글 · 팔로우')+'</span></span>';
      // 소셜 (KD 2026-10-08): 알림 배지 · 내 댓글 · 이 브라우저를 계정에 묶기(한 번만) · 댓글 별명을 계정 별명으로
      // 「내가 모은 글」은 로그인하면 계정 것 하나로 (KD 2026-10-08 「데이터 구조 통일」):
      //   이 브라우저에만 있던 스크랩·반응·한마디 표시를 계정으로 자동으로 올리고, 링크도 계정 화면으로.
      try{var rd=function(k){try{return JSON.parse(localStorage.getItem(k)||'{}')||{}}catch(e){return {}}};
        var syn=rd('ss_synced'),its=[];
        [['ss_scrap','scrap'],['ss_react','react'],['ss_cmt','cmt']].forEach(function(p){Object.keys(rd(p[0])).forEach(function(s){if(!syn[s])its.push({story:s,kind:p[1]})})});
        if(its.length)fetch(API+'/me/merge',{method:'POST',credentials:'include',headers:{'content-type':'application/json'},body:JSON.stringify({items:its.slice(0,500)})})
          .then(function(r){if(r.ok){its.forEach(function(x){syn[x.story]=1});localStorage.setItem('ss_synced',JSON.stringify(syn))}}).catch(function(){});
      }catch(e){}
      wrap.querySelector('#ss-mine').hidden=true;
      try{notiPanel(u,ac)}catch(e){}
      if(un){var bd=document.createElement('span');bd.className='bd';bd.textContent=un>9?'9+':un;ac.appendChild(bd);ac.setAttribute('aria-label','내 계정 · 새 알림 '+un+'개')}
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
