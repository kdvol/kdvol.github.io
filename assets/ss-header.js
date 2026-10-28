
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
  //   포물선으로 튀어 올랐다 떨어진다. 그림은 공식 로고 PNG(아래 LOGOS), 움직임은 Web Animations.
  //   window.ssCan(x, y, {big}) · window.ssCanAt(el, {big}). 움직임 줄이기 설정이면 아무것도 안 한다.
  // ★ 공식 로고만 (KD 2026-10-14 「앞으로 무조건 실제 로고만… 애니메이션에 쓰는 로고 포함, 모든 변형은 정식 로고에서 시작」)
  //   통조림 = 공식 로고 PNG 그대로. 뚜껑은 같은 PNG 를 clip-path 로 오려 경첩 기준 회전만, 튀어 오르는 물고기는
  //   공식 흰 로고에서 주황 픽셀만 오려낸 것(캔버스 추출) — 직접 그린 SVG·표정 없음.
  //   어두운 바탕 = /assets/soonsal-logo-white.png(헤더와 같은 파일, 128px), 밝은 바탕 = /favicon-96x96.png(검정, 96px).
  //   좌표는 각 파일의 픽셀 실측(뚜껑 아래 가장자리 = 입구 위 경계, 앞 테두리 = 입구 아래 경계).
  var FC='#F88C62';
  var LOGOS={
    dark:{src:'/assets/soonsal-logo-white.png',n:128,K:.5,hinge:[3,60],mouth:[70,56],
      lid:[[0,60],[14,64],[30,68.5],[38,66],[44,64],[48,62],[54,60],[58,58],[62,56],[66,54],[68,52],[72,50],[76,48],[78,46],[82,44],[84,42],[88,40.5],[96,38.5],[108,36.5],[128,34]],
      front:[[0,71],[36,71.5],[54,73.5],[66,74],[78,73.5],[94,71.5],[102,69],[108,67],[114,65],[118,63],[122,60],[128,58]]},
    light:{src:'/favicon-96x96.png',n:96,K:64/71,hinge:[15,46],mouth:[55,44],
      lid:[[0,48],[14,48],[31,50],[36,48],[41,46],[45,44],[48,43],[50,41],[53,40],[56,38],[59,36],[61,35],[70,33.5],[80,32],[96,30]],
      front:[[0,52],[35,51.6],[48,52],[62,51.6],[68,50.6],[72,49.6],[76,48.6],[80,47],[84,45],[96,44]]}
  };
  function poly(pts,n){return 'polygon('+pts.map(function(q){return (q[0]/n*100).toFixed(2)+'% '+(q[1]/n*100).toFixed(2)+'%'}).join(',')+')'}
  // 뚜껑 = 경계선 위쪽, 뒤판 = 경계선 아래쪽(뚜껑을 뺀 나머지), 앞판 = 입구 앞 테두리 아래(물고기를 가린다)
  function clips(L){var n=L.n,lidB=L.lid.slice(),fr=L.front.slice();
    return {lid:poly([[0,0],[n,0]].concat(lidB.slice().reverse()),n),
            back:poly(lidB.concat([[n,n],[0,n]]),n),
            front:poly(fr.concat([[n,n],[0,n]]),n)}}
  // 물고기: 공식 흰 로고 → 주황 픽셀만 남기고(경계는 주황 정도만큼 반투명) 잘라낸 그림. 기울기는 로고 그대로(약 -18°).
  var FISH=null,FISH_W=1,FISH_H=1,FISH_TILT=18,assetsP=null;
  function loadImg(src){return new Promise(function(ok,no){var im=new Image();im.onload=function(){ok(im)};im.onerror=no;im.src=src})}
  function cutFish(im){var w=im.naturalWidth,h=im.naturalHeight,c=document.createElement('canvas');c.width=w;c.height=h;
    var x=c.getContext('2d');x.drawImage(im,0,0);var d=x.getImageData(0,0,w,h),p=d.data,x0=w,y0=h,x1=-1,y1=-1;
    for(var i=0;i<p.length;i+=4){var tt=Math.max(0,Math.min(1,(p[i]-p[i+2]-15)/120))*p[i+3]/255;
      if(tt>.03){p[i]=248;p[i+1]=140;p[i+2]=98;p[i+3]=Math.round(tt*255);var k=i/4,px=k%w,py=(k-px)/w;
        if(px<x0)x0=px;if(px>x1)x1=px;if(py<y0)y0=py;if(py>y1)y1=py}else p[i+3]=0}
    if(x1<0)return null;x.putImageData(d,0,0);
    var o=document.createElement('canvas');o.width=x1-x0+1;o.height=y1-y0+1;o.getContext('2d').drawImage(c,x0,y0,o.width,o.height,0,0,o.width,o.height);
    FISH_W=o.width;FISH_H=o.height;return o.toDataURL()}
  function canAssets(){
    if(!assetsP)assetsP=Promise.all([loadImg(LOGOS.dark.src),loadImg(LOGOS.light.src)]).then(function(r){FISH=cutFish(r[0]);return r});
    return assetsP}
  // 첫 클릭이 늦지 않게 한가할 때 미리 받아 둔다 (헤더가 이미 같은 흰 로고를 쓰므로 대개 캐시)
  try{(window.requestIdleCallback||function(f){setTimeout(f,1500)})(function(){canAssets().catch(function(){})})}catch(e){}
  function darkAt(x,y){   // 누른 자리 뒤 배경이 어두우면 흰 로고 버전
    try{var el=document.elementFromPoint(x,y);
      while(el&&el!==document.documentElement){var c=getComputedStyle(el).backgroundColor,m=c&&c.match(/[\d.]+/g);
        if(m&&(m.length<4||+m[3]>.5))return (0.299*m[0]+0.587*m[1]+0.114*m[2])<128;el=el.parentElement}
      var b=getComputedStyle(document.body).backgroundColor.match(/[\d.]+/g);return b?(0.299*b[0]+0.587*b[1]+0.114*b[2])<128:true}catch(e){return true}}
  function ssCan(x,y,o){
    o=o||{};
    try{if(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)return}catch(e){}
    if(!document.body||!document.body.animate||!window.Promise)return;
    canAssets().then(function(){ssCanRun(x,y,o)}).catch(function(){});
  }
  function ssCanRun(x,y,o){
    // SP: 전체 빠르기(1=원래). 궤적 모양은 그대로 두고 시간만 줄인다 (KD 2026-10-11 「조금 더 빨리」)
    var SP=.68,big=!!o.big,dark=darkAt(x,y),sc=big?1.3:1,T=Math.round(2400*SP);
    var L=dark?LOGOS.dark:LOGOS.light,C=clips(L),S=L.n*L.K;
    var host=document.createElement('div');
    host.style.cssText='position:fixed;left:'+x+'px;top:'+y+'px;width:0;height:0;z-index:2147483000;pointer-events:none';
    // 층: 뒤판(공식 로고 − 뚜껑) → 물고기 → 앞판(공식 로고의 입구 앞 테두리 아래) → 뚜껑(공식 로고의 뚜껑 부분). 셋 다 같은 PNG.
    //   누른 점에 입구 가운데가 오게 놓는다.
    var OX=L.mouth[0]*L.K,OY=L.mouth[1]*L.K,HX=L.hinge[0]*L.K,HY=L.hinge[1]*L.K;
    var canw=document.createElement('div');canw.style.cssText='position:absolute;left:'+(-OX)+'px;top:'+(-OY)+'px;width:'+S+'px;height:'+S+'px;transform-origin:'+OX+'px '+(OY+20)+'px';
    function layer(cp,extra){var im=document.createElement('img');im.src=L.src;im.alt='';im.width=S;im.height=S;
      im.style.cssText='position:absolute;left:0;top:0;width:'+S+'px;height:'+S+'px;max-width:none;-webkit-clip-path:'+cp+';clip-path:'+cp+(extra||'');return im}
    var back=layer(C.back),front=layer(C.front),lid=layer(C.lid,';transform-origin:'+HX+'px '+HY+'px');
    var fishes=document.createElement('div');fishes.style.cssText='position:absolute;left:'+OX+'px;top:'+OY+'px';
    canw.appendChild(back);canw.appendChild(fishes);canw.appendChild(front);canw.appendChild(lid);host.appendChild(canw);document.body.appendChild(host);
    var A=function(el,k,d,dl,e){return el.animate(k,{duration:d,delay:dl||0,easing:e||'linear',fill:'both'})};
    // 통조림: 퐁 → (물고기 움찔할 때) 덜덜 → 뚜껑 따는 순간 꿀렁 → 물고기 다 나간 뒤 가라앉으며 사라짐
    A(canw,[{transform:'scale(0) translateY(14px)',opacity:0},{transform:'scale('+sc*1.12+') translateY(-3px)',opacity:1,offset:.07},{transform:'scale('+sc+')',offset:.12},
      {transform:'scale('+sc+') rotate(-2.5deg)',offset:.18},{transform:'scale('+sc+') rotate(2.5deg)',offset:.21},{transform:'scale('+sc+') rotate(-1.5deg)',offset:.24},{transform:'scale('+sc+') rotate(0)',offset:.27},
      {transform:'scale('+sc*1.05+','+sc*.93+')',offset:.3},{transform:'scale('+sc+')',offset:.35},
      {transform:'scale('+sc+') rotate(-2deg)',offset:.4},{transform:'scale('+sc+') rotate(2deg)',offset:.43},{transform:'scale('+sc+')',offset:.46},   // 물고기 움찔할 때 같이 덜덜
      {transform:'scale('+sc+')',opacity:1,offset:.86},{transform:'scale('+sc*.55+') translateY(20px)',opacity:0}],T,0,'ease-out');
    // 뚜껑: 공식 로고 각도(열린 채)에서 시작 → 물고기가 들이받듯 꾹 닫혔다(+18°) → 팡 튀어 열리며 살짝 넘어감 → 로고 각도로 안착.
    //   (KD 2026-10-14 「뚜껑이 움직이면서 바뀌는 건 있을 수 있지만 모든 변형은 정식 로고에서 시작」)
    A(lid,[{transform:'rotate(0)',offset:0},{transform:'rotate(0)',offset:.12},{transform:'rotate(18deg)',offset:.17,easing:'ease-in'},
      {transform:'rotate(15deg)',offset:.2},{transform:'rotate(18deg)',offset:.215,easing:'cubic-bezier(.3,0,.2,1)'},
      {transform:'rotate(-7deg)',offset:.245,easing:'ease-out'},{transform:'rotate(2deg)',offset:.275,easing:'ease-in-out'},{transform:'rotate(0)',offset:.3}],T,0);
    var n=big?8:5,g=1600;
    for(var i=0;i<n;i++)(function(i){
      // 3겹: 경로(pos) · 방향·회전(rot) · 몸짓(body: 움찔·찌그러짐·꼬리 파닥)
      var pos=document.createElement('div'),rot=document.createElement('div'),body=document.createElement('div');
      // 물고기 = 공식 로고에서 오려낸 그림(FISH). 보통 44px, 큰 버전 50px
      var FW=big?50:44,FH=FW*FISH_H/FISH_W;
      pos.style.cssText='position:absolute;left:0;top:0';rot.style.cssText='position:absolute;left:-'+(FW/2)+'px;top:-'+(FH/2)+'px;transform-origin:'+(FW/2)+'px '+(FH/2)+'px';
      body.style.cssText='transform-origin:'+(FW*.4)+'px '+(FH/2)+'px';
      if(FISH){var fi=document.createElement('img');fi.src=FISH;fi.alt='';fi.style.cssText='display:block;width:'+FW+'px;height:'+FH+'px;max-width:none';body.appendChild(fi)}
      rot.appendChild(body);pos.appendChild(rot);fishes.appendChild(pos);
      var spread=n>1?(i/(n-1)-.5)*2:0,vx=(spread*150+(Math.random()*50-25))*(big?1.45:1),vy=-(380+Math.random()*180)*(big?1.2:1);
      // 순서: 뚜껑 걸림(0.4s)→벗겨져 열림(~0.75s)→그 뒤에야 빼꼼→움찔→발사
      var peek=(800+Math.random()*120)*SP,launch=(1080+i*45+Math.random()*70)*SP,flyV=950+Math.random()*350,fly=flyV*SP,end=launch+fly;
      var face=vx<0?' scaleX(-1)':'';       // 왼쪽으로 가는 놈은 좌우 뒤집어 머리가 진행 방향
      // 로고 속 물고기는 머리가 약 18° 들려 있다 → 진행 방향에 맞추려면 그만큼 보정(뒤집힌 놈은 반대), 빼꼼할 땐 머리가 위로
      var TL=vx<0?-FISH_TILT:FISH_TILT,UP=vx<0?90-FISH_TILT:-90+FISH_TILT;
      var mx=Math.max(-16,Math.min(16,spread*15)),fr=[],steps=20;
      // 캔 안: 작게(0.4배) 가운데로 모여 앞판 뒤에 숨어 있음 — 바닥 둥근 모서리 밖으로 안 비치게 깊이 19px·좌우 40%
      fr.push({transform:'translate('+(mx*.4).toFixed(1)+'px,19px)',offset:0});
      fr.push({transform:'translate('+(mx*.4).toFixed(1)+'px,19px)',offset:.82*peek/end,easing:'ease-out'});
      fr.push({transform:'translate('+mx+'px,-6px)',offset:peek/end,easing:'ease-out'});   // 고개 빼꼼 — 입구 위로
      fr.push({transform:'translate('+mx+'px,2px)',offset:launch/end*0.97});              // 움찔하며 다시 웅크림
      for(var k=0;k<=steps;k++){var t=k/steps*flyV/1000;
        fr.push({transform:'translate('+(mx+vx*t).toFixed(1)+'px,'+(-1+vy*t+.5*g*t*t).toFixed(1)+'px)',offset:Math.min(1,(launch+k/steps*fly)/end)})}
      A(pos,fr,end,0);
      // 방향: 빼꼼할 땐 위를 보고 → 날아가며 진행 방향, 일부는 공중제비(360°)·스핀
      var trick=Math.random(),rk=[{transform:'rotate('+UP+'deg)'+face,offset:0},{transform:'rotate('+UP+'deg)'+face,offset:launch/end*.97}];
      for(var k2=0;k2<=10;k2++){var t2=k2/10*flyV/1000,vyt=vy+g*t2,ang=Math.atan2(vyt,Math.abs(vx)||1)*180/Math.PI;
        if(vx<0)ang=-ang;                                     // 뒤집힌 놈은 각도도 거울로
        var extra=trick<.25?(vx<0?-1:1)*360*k2/10:(trick<.4?Math.sin(k2/10*Math.PI)*40:0);
        rk.push({transform:'rotate('+(ang+TL+extra).toFixed(1)+'deg)'+face,offset:Math.min(1,(launch+k2/10*fly)/end)})}
      A(rot,rk,end,0);
      // 몸짓: 빼꼼 뒤 움찔움찔(찌그러졌다 폈다) → 발사 순간 길게 늘어남 → 날며 꼬리 파닥 → 사라짐
      var bk=[{transform:'scale(.4)',opacity:1,offset:0},{transform:'scale(.4)',opacity:1,offset:.82*peek/end},{transform:'scale(1)',opacity:1,offset:peek/end}],tw=launch-peek,b0=peek/end;
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
        {transform:'translate('+(Math.cos(a)*r)+'px,'+(Math.sin(a)*r+28)+'px) scale(.5)',opacity:0}],720*SP,(1080+Math.random()*140)*SP,'ease-out')})();
    setTimeout(function(){if(host.parentNode)host.parentNode.removeChild(host)},T+600);
  }
  // 버튼을 덮지 않게 바로 위에 살짝 띄워 띄운다 — 위 공간이 모자라면 아래로. 좌우는 화면 안쪽으로 (KD 2026-10-11)
  function ssCanAt(el,o){try{var r=el.getBoundingClientRect(),big=o&&o.big,gap=big?58:44,
    x=Math.max(48,Math.min(window.innerWidth-48,r.left+r.width/2)),
    y=r.top-gap>130?r.top-gap:r.bottom+gap+8;
    ssCan(x,y,o)}catch(e){}}
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
      '.ss-subc .ss-sbnl{font-size:12px;color:#888;margin-top:12px;padding:12px 0 0;border-top:1px solid #222;line-height:1.6}'+
      '.ss-subc .ss-sbnl span{display:block}.ss-subc .ss-sbnl .hh{font-weight:700;color:#aaa;margin-bottom:6px}'+
      '.ss-subc .ss-sbnl .li{position:relative;padding-left:12px;margin:3px 0}.ss-subc .ss-sbnl .li:before{content:"";position:absolute;left:2px;top:.62em;width:4px;height:4px;border-radius:50%;background:#E55A00}'+
      '.ss-subc .ss-sbnl b{color:#eee;font-weight:700;margin-right:5px}.ss-subc .ss-sbnl .ft{margin-top:8px;color:#777;font-size:11.5px}'+
      '.ss-subc .x{position:absolute;top:10px;right:10px;width:36px;height:36px;border:0;background:none;color:#888;font-size:22px;cursor:pointer;min-height:0!important}'+
      '.ss-subc .ok{font-size:17px;font-weight:800;color:#fff;text-align:center;margin-top:6px}.ss-subc .er{font-size:12.5px;color:#ff8a5c;margin-top:8px;min-height:1px}'+
      '.ss-subc .hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}';
    document.head.appendChild(st);
  }
  function subForm(story,onClose,src){subCss();
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
      '<label class="fl">이름 (또는 닉네임)<i>*</i></label><input class="in nm" placeholder="이름 또는 닉네임" maxlength="30" autocomplete="nickname">'+
      '<label class="fl">출생연도<i>*</i></label><select class="in by">'+yrs+'</select>'+
      '<label class="fl">관심분야<i>*</i> <span class="ob">복수 가능</span></label><div class="tags">'+
        ['주식','크립토','부동산','경제·매크로','취업·이직','창업·사업','정보습득','기타'].map(function(x){return '<button type="button" class="tg" data-v="'+x+'">'+x+'</button>'}).join('')+'</div>'+
      '<label class="fl">현재 하는일<i>*</i></label><input class="in cu" placeholder="예: 소속 기관, 업무, 산업분야 등" maxlength="40">'+
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
      '<div class="ss-sbnl"><span class="hh">구독할 뉴스레터</span>'+
        '<span class="li"><b>순살브리핑</b> 글로벌 시장·경제 핵심 뉴스를 매일 5분 안에</span>'+
        '<span class="li"><b>순살크립토</b> 크립토 시장 흐름과 온체인 인사이트</span>'+
        '<span class="ft">구독 후 환경설정에서 개별 선택 가능합니다.</span></div>';
    var f=c.querySelector('form'),em=f.querySelector('.em'),go=f.querySelector('.go'),ag=c.querySelector('.ag'),er=c.querySelector('.er'),t0=Date.now();
    c.querySelector('.x').onclick=function(){onClose&&onClose()};
    [].forEach.call(c.querySelectorAll('.tg'),function(b){b.onclick=function(){b.classList.toggle('on')}});
    f.onsubmit=function(e){e.preventDefault();er.textContent='';
      var v=(em.value||'').trim();
      if(!/^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/.test(v)){er.textContent='이메일 주소를 확인해 주세요.';em.focus();return}
      // ★ 모든 칸 필수 (KD 2026-10-15 「봇 구독은 데이터 입력 자세히 하도록 강제」) — 서버(/subscribe)도 같은 규칙으로 막는다
      var nm=c.querySelector('.nm'),by=c.querySelector('.by'),cu=c.querySelector('.cu');
      if(!(nm.value||'').trim()){er.textContent='이름(또는 닉네임)을 적어 주세요.';nm.focus();return}
      if(!by.value){er.textContent='출생연도를 골라 주세요.';by.focus();return}
      if(!c.querySelector('.tg.on')){er.textContent='관심분야를 하나 이상 골라 주세요.';return}
      if(!(cu.value||'').trim()){er.textContent='현재 하는 일을 적어 주세요.';cu.focus();return}
      if(!ag.checked){er.textContent='개인정보 수집 및 이용 동의에 체크해 주세요.';ag.focus();return}
      go.disabled=true;go.textContent='보내는 중…';
      fetch(API+'/subscribe',{method:'POST',headers:{'content-type':'application/json'},
        body:JSON.stringify({email:v,agree:true,story:story,src:src||'inline',path:location.pathname,v:lsg('ss_vid')||'',hp:f.querySelector('.hp').value,t:Date.now()-t0,
          name:c.querySelector('.nm').value,birthyear:c.querySelector('.by').value,current:c.querySelector('.cu').value,
          interest:[].map.call(c.querySelectorAll('.tg.on'),function(b){return b.getAttribute('data-v')}).join(',')})})
      .then(function(r){return r.json()}).then(function(j){
        if(j&&j.ok){lss('ss_subbed','1');lss('ss_is_sub','1');
          c.innerHTML='<div class="ok">'+(j.already?'이미 구독 중이에요 🐟 내일 아침에 만나요.':'구독 완료! 🐟 내일 아침 메일함에서 만나요.')+'</div>'+
            '<div class="d" style="margin:8px 0 0">첫 메일이 안 보이면 스팸함·프로모션함도 확인해 주세요.</div>';
          try{var rr=c.getBoundingClientRect();window.ssCan&&window.ssCan(rr.left+rr.width/2,rr.top+Math.min(rr.height/2,160),{big:true})}catch(_){}return}
        go.disabled=false;go.textContent='구독하기';
        var EM={email:'이메일 주소를 확인해 주세요.','too many':'잠시 뒤 다시 시도해 주세요.',name:'이름(또는 닉네임)을 적어 주세요.',
          birthyear:'출생연도를 골라 주세요.',interest:'관심분야를 하나 이상 골라 주세요.',current:'현재 하는 일을 적어 주세요.'};
        er.textContent=(j&&EM[j.error])||'지금은 구독을 못 받았어요. 잠시 뒤 다시 시도해 주세요.'})
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
  function subModal(src){
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
    ov.appendChild(subForm(null,close,src));
    ov.addEventListener('click',function(e){if(e.target===ov)close()});
    document.addEventListener('keydown',esc);
    document.body.appendChild(ov);document.body.style.overflow='hidden';
    requestAnimationFrame(function(){ov.classList.add('on');var em=ov.querySelector('.em');if(em&&window.matchMedia('(min-width:561px)').matches)em.focus()});
  }
  document.addEventListener('click',function(e){
    var a=e.target.closest&&e.target.closest('a[href*="subscribe.soonsal.com"]');if(!a)return;
    if(!a.closest('.site-header, .ss-dr, .hero')){                  // 본문 링크(뉴스레터 아카이브 하단 등)는 원래대로 가되
      // 어느 페이지에서 눌렀는지 붙여 보낸다 — 구독 페이지가 이걸 api 로 넘겨 새 구독 알림 「📍」에 찍힌다 (KD 2026-10-15)
      try{var u=new URL(a.href);if(!u.searchParams.get('from')){u.searchParams.set('from',location.pathname.slice(0,100));a.href=u.toString()}}catch(_){}
      return}
    if(e.metaKey||e.ctrlKey||e.shiftKey||e.button===1)return;      // 새 탭으로 열려는 클릭은 막지 않는다
    e.preventDefault();
    if(document.documentElement.classList.contains('ss-open')){document.documentElement.classList.remove('ss-open');document.body.style.overflow=''}
    // 어느 버튼으로 들어왔는지 — 새 구독 알림에 찍힌다 (KD 2026-10-13)
    subModal(a.closest('.site-header')?'header':a.closest('.ss-dr')?'drawer':'hero');
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
      // ★ 질문이 **바로 이 스토리** 것일 때만 (KD 2026-10-12 「지난 질문이 오늘 스토리에 붙음」): 번호만 맞추면 홈에선
      //   오늘 질문이 아직 없을 때 지난 회차 질문이 오늘 같은 번호 스토리에 붙었다. 스토리 id(예 1012-3)까지 같아야 한다.
      var sid=at.getAttribute('data-ss-story')||'';if(sid&&sid!==p.story)return;
      if(!sid&&home)return;
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
        /* 홈 「오늘의 순살」 안 질문 줄 — 참여 모양: 주황 배지 · 한 줄 질문 · 투표 버튼 (KD 10/24 「오늘의 질문은 눈에 잘 안 들어옴」) */
        /* 이름 주의: soonsal.js 공유 창 제목이 .ss-pt 라 같은 이름을 쓰면 그 제목이 흰 글씨·주황 상자로 덮인다(KD 10/26 PC 공유 창 제목 안 보임) */
        '.ss-pqrow{display:flex;align-items:center;gap:10px;margin:2px 0 12px 30px;padding:10px 10px 10px 12px;border-radius:12px;background:rgba(240,112,64,.1);'+
        'border:1px solid #6b3a24;color:#f6f1e8;text-decoration:none}'+
        '.ss-pqrow .k{flex:0 0 auto;font-size:11px;font-weight:900;color:#12100e;background:#F07040;border-radius:999px;padding:3px 8px}'+
        '.ss-pqrow .tx{flex:1;min-width:0;font-size:14px;font-weight:700;line-height:1.4;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}'+
        '.ss-pqrow b{flex:0 0 auto;font-size:12.5px;font-weight:800;color:#F59B75}.ss-pqrow:hover{border-color:#F07040}'+
        '.ss-pi{font-size:.8em;font-weight:700;color:#C24A00;white-space:nowrap}';
      document.head.appendChild(st);
      var c=document.createElement('section');c.className='ss-poll'+(light?' lt':'');c.id='ss-poll';c.setAttribute('aria-label','오늘의 질문');
      var key='ss_poll_'+p.day,mine=0;try{mine=parseInt(localStorage.getItem(key)||'0',10)||0}catch(e){}
      var esc=function(v){return String(v||'').replace(/[<>&"]/g,'')};
      function draw(na,nb){
        var tot=na+nb;
        if(!mine){c.innerHTML='<div class="k">🗳️ 오늘의 질문 · 이 이야기, 어떻게 보세요?</div><div class="q">'+esc(p.q)+'</div>'+
          '<div class="bt"><button type="button" class="ss-shine" data-c="1">'+esc(p.a)+'</button><button type="button" class="ss-shine" data-c="2">'+esc(p.b)+'</button></div>'+
          '<div class="n">'+(tot?tot+'명 참여 · ':'')+'고르면 결과가 보여요</div>';
          [].forEach.call(c.querySelectorAll('.bt button'),function(b){b.onclick=function(){vote(parseInt(b.getAttribute('data-c'),10))}});return}
        var pa=tot?Math.round(na*100/tot):0,pb=tot?100-pa:0;
        // 오늘의 질문 페이지와 같게 — 막대를 누르면 답이 바뀐다, 「다시 고르기」·긴 안내 없음 (KD 10/24 「기존 것 중 불필요한 건 통합」)
        c.innerHTML='<div class="k">🗳️ 오늘의 질문</div><div class="q">'+esc(p.q)+'</div><div class="rs">'+
          '<div data-c="1" class="'+(mine===1?'me':'')+'" style="cursor:pointer"><i style="width:'+pa+'%"></i><span>'+esc(p.a)+(mine===1?' ✓':'')+'</span><b>'+pa+'%</b></div>'+
          '<div data-c="2" class="'+(mine===2?'me':'')+'" style="cursor:pointer"><i style="width:'+pb+'%"></i><span>'+esc(p.b)+(mine===2?' ✓':'')+'</span><b>'+pb+'%</b></div></div>'+
          '<div class="n">'+tot+'명 참여 · <a href="/poll/#d-'+p.day+'" style="color:#F59B75;font-weight:700">친구한테 묻기 · 지난 질문 →</a>'+
          // 고른 직후가 관심이 가장 높을 때 — 구독자가 아니면 「내일 질문도 메일로」 (KD 2026-10-23 개선 1번)
          (lsg('ss_is_sub')==='1'||lsg('ss_subbed')==='1'?'':' · <a href="#" class="sub" style="color:#F59B75">📮 내일 질문도 메일로</a>')+'</div>';
        [].forEach.call(c.querySelectorAll('.rs div[data-c]'),function(d){d.onclick=function(){var v=parseInt(d.getAttribute('data-c'),10);if(v!==mine)vote(v)}});
        var sb=c.querySelector('.sub');if(sb)sb.onclick=function(e){e.preventDefault();subModal('poll')};
      }
      function vote(v){var vid='';try{vid=localStorage.getItem('ss_vid')||''}catch(e){}
        try{var vb=c.querySelector('.bt button[data-c="'+v+'"]');if(vb)ssCanAt(vb)}catch(e){}
        var old=mine;mine=v;try{localStorage.setItem(key,String(v))}catch(e){}
        p.na=Math.max(0,(p.na||0)-(old===1?1:0)+(v===1?1:0));p.nb=Math.max(0,(p.nb||0)-(old===2?1:0)+(v===2?1:0));
        draw(p.na,p.nb);   // 낙관적 표시(바꾸면 이전 표를 뺌) → 서버 값으로 맞춤
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
        if(row){var t=document.createElement('a');t.className='ss-pqrow'+(mine?'':' ss-shine');t.href='#ss-poll';
          t.innerHTML='<span class="k">🗳️ 질문</span><span class="tx">'+esc(p.q)+'</span><b>'+(mine?'결과 →':'투표 →')+'</b>';t.onclick=go;row.parentNode.insertBefore(t,row.nextSibling)}}
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
  window.ssSub=function(src){subModal(src||'poll')};
  window.ssIsSub=function(){return lsg('ss_is_sub')==='1'||lsg('ss_subbed')==='1'};
  window.ssKakaoShare=function(el){kakaoShare(el)};
  function kakaoShare(el){
    var sid=el.getAttribute('data-ss-story')||'',m=sid.match(/-(\d+)$/);
    var t=el.querySelector('[id$="-title"],.story-title,h2,h3');var title=(t?t.textContent:document.title).replace(/\s+/g,' ').trim();
    var li=el.querySelector('.bullet')||el.querySelector('li');var desc=(li?li.textContent:'').replace(/\s+/g,' ').trim().slice(0,90);
    // 뉴스레터 스토리(회차 번호)는 어디서 공유하든 /s/<번호>.html — 그날 뉴스레터 그 스토리로 바로(홈에서 공유해도 홈·더보기로 안 감, KD 10/26)
    var url=el.getAttribute('data-ss-url')||(/^\d{4}c?-\d{1,2}$/.test(sid)?location.origin+'/s/'+sid+'.html':(location.origin+location.pathname+(m?'#story-'+m[1]:'')));   // 차트 꼭지는 #slug 를 붙여 둔다
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
    // 아래쪽 로고(뉴스레터·페이지 푸터 「🥫 Soonsal」)도 같은 글꼴 (KD 10/26 「헤더와 동일한 폰트 — 웹사이트 전체 통일」)
    [].forEach.call(document.querySelectorAll('.footer-brand span,.footer-brand b'),function(t){
      if((t.textContent||'').trim()==='Soonsal')t.classList.add('ss-yes','ss-yes-ft');
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
      '.ss-yes-ft{font-family:"Yeseva One",Georgia,"Times New Roman",serif!important;font-weight:400!important;letter-spacing:.01em;font-size:17px!important}'+
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

    var LINKS=[["읽기", [["/newsletters/", "뉴스레터"], ["/chart/", "순살차트"], ["/cardnews/", "순스타그램"], ["/youtube/", "YouTube"]]], ["찾기", [["/search/", "검색"], ["/topics/", "주제별"]]], ["참여", [["/poll/", "오늘의 질문"], ["/talk/", "순살톡"], ["/school/", "순살스쿨"]]], ["순살과 함께", [["/collab/", "광고·협업 문의"]]]];
    var wrap=document.createElement('div');
    wrap.innerHTML='<div class="ss-ov"></div><aside class="ss-dr" aria-label="전체 메뉴"><button class="x" aria-label="닫기">×</button>'+
      '<a class="acc" href="/account/" rel="nofollow"><span class="ph">🙂</span><span><b>로그인하고 스크랩 모으기</b><span>1초 로그인 · 폰·PC 에서 같이</span></span></a>'+
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

(function(){
  if(window.__ssShine)return;window.__ssShine=1;
  var LATEST={"/newsletters/": "2026-10-29", "/chart/": "2026-10-28", "/cardnews/": "2026-10-28", "/poll/": "2026-10-29"};
  function lsg(k){try{return localStorage.getItem(k)}catch(e){return null}}
  function lss(k,v){try{localStorage.setItem(k,v)}catch(e){}}
  var st=document.createElement('style');st.id='ss-shine-css';st.textContent=
    '.ss-shine{position:relative;overflow:hidden;isolation:isolate}'+
    '.ss-shine::before{content:"";position:absolute;top:-20%;bottom:-20%;left:-80%;width:42%;z-index:3;pointer-events:none;'+
    'background:linear-gradient(100deg,rgba(255,255,255,0) 0%,rgba(255,255,255,.18) 30%,rgba(255,255,255,.6) 50%,rgba(255,255,255,.18) 70%,rgba(255,255,255,0) 100%);'+
    'transform:skewX(-22deg);animation:ssSweep 2.8s cubic-bezier(.4,0,.2,1) infinite}'+
    '@keyframes ssSweep{0%,50%{left:-80%}100%{left:140%}}'+
    '.nav>a.ss-new,.ss-dr a.ss-new{background:linear-gradient(105deg,#F59B75 0 30%,#ffd9c4 40%,#ffffff 48%,#ffffff 52%,#ffd9c4 60%,#F59B75 70% 100%);'+
    'background-size:300% 100%;-webkit-background-clip:text;background-clip:text;color:transparent!important;animation:ssGlint 2.6s linear infinite}'+
    '@keyframes ssGlint{0%,35%{background-position:100% 0}100%{background-position:0 0}}'+
    '@media (prefers-reduced-motion:reduce){.ss-shine::before{display:none}.nav>a.ss-new,.ss-dr a.ss-new{animation:none;background:none;color:#F59B75!important}}';
  (document.head||document.documentElement).appendChild(st);
  window.ssShine=function(el){if(el&&el.classList)el.classList.add('ss-shine')};
  function day(off){return new Date(Date.now()+9*3600e3-off*864e5).toISOString().slice(0,10)}
  var path=location.pathname;
  // 지금 보고 있는 섹션은 「봤음」으로 — 다음부터 그 탭은 새 내용이 나올 때만 반짝인다
  Object.keys(LATEST).forEach(function(h){if(path.indexOf(h)===0&&LATEST[h])lss('ss_seen_'+h,LATEST[h])});
  function mark(){Object.keys(LATEST).forEach(function(h){var d=LATEST[h];if(!d||path.indexOf(h)===0)return;
    if(d>(lsg('ss_seen_'+h)||'')&&d>=day(1))[].forEach.call(document.querySelectorAll('.nav>a[href="'+h+'"],.ss-dr a[href="'+h+'"]'),
      function(a){a.classList.add('ss-new');a.title='새 내용'})})}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mark);else mark();
  setTimeout(mark,1200);   // ☰ 메뉴는 늦게 그려진다
})();

(function(){
  if(window.__ssFeat)return;window.__ssFeat=1;
  var API='https://api.soonsal.com';
  function lsg(k){try{return localStorage.getItem(k)}catch(e){return null}}
  function esc(v){return String(v==null?'':v).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  var st=document.createElement('style');st.id='ss-ui-css';st.textContent=
    /* 7. 디자인 규칙 — 색·모양 변수(어두운 사이트 바탕 기준, 밝은 본문 카드는 -lt) */
    ':root{--sn-bg:#111;--sn-card:#171513;--sn-line:#26221e;--sn-ink:#f6f1e8;--sn-text:#e8e3da;--sn-sub:#a39c90;--sn-mute:#7c756c;'+
    '--sn-accent:#F07040;--sn-accent-2:#F59B75;--sn-accent-ink:#C24A00;--sn-kakao:#FEE500;--sn-r-pill:999px;--sn-r-card:16px;'+
    '--sn-lt-card:#fffaf5;--sn-lt-line:#ece6dc;--sn-lt-ink:#1f1a16;--sn-lt-sub:#6f695f}'+
    /* 작은 알약 버튼 — 공유·보조 행동 (32px) */
    '.ss-pill{display:inline-flex;align-items:center;gap:5px;height:32px;padding:0 12px;border-radius:var(--sn-r-pill);border:1px solid #3a2f27;'+
    'background:#1b1715;color:var(--sn-text);font:700 12.5px Pretendard,-apple-system,sans-serif;cursor:pointer;text-decoration:none;white-space:nowrap}'+
    '.ss-pill:hover{border-color:var(--sn-accent)}.ss-pill svg{width:15px;height:15px;flex:0 0 auto}'+
    '.ss-pill.kk{background:var(--sn-kakao);border-color:var(--sn-kakao);color:#191600}.ss-pill.ic{width:32px;padding:0;justify-content:center}'+
    '.ss-pill.sub{background:var(--sn-accent);border-color:var(--sn-accent);color:#12100e}'+
    /* 공유 줄 — 글·차트 꼭지 끝 (밝은 본문 카드 안) */
    '.ss-ask{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:14px 0 4px;padding:12px 14px;border-radius:12px;'+
    'background:var(--sn-lt-card);border:1px dashed #e3d4c4;font-family:Pretendard,-apple-system,sans-serif}'+
    '.ss-ask .hk{flex:1 1 150px;font-size:13.5px;font-weight:800;color:var(--sn-lt-ink)!important;-webkit-text-fill-color:var(--sn-lt-ink)!important;line-height:1.45;word-break:keep-all}'+
    '.ss-ask .bs{display:flex;gap:6px;flex:0 0 auto}'+
    /* 어두운 카드 안(차트 꼭지) */
    '.ss-ask.dk{background:rgba(255,255,255,.03);border-color:#3a2f27}.ss-ask.dk .hk{color:var(--sn-ink)!important;-webkit-text-fill-color:var(--sn-ink)!important}'+
    '.ss-ask.dk .ss-pill{background:#1b1715;border-color:#3a2f27;color:var(--sn-text)}.ss-ask.dk .ss-pill.kk{background:var(--sn-kakao);border-color:var(--sn-kakao);color:#191600}'+
    '.ss-ask .ss-pill{background:#fff;border-color:#e3d9cc;color:#3a2f27}.ss-ask .ss-pill.kk{background:var(--sn-kakao);border-color:var(--sn-kakao);color:#191600}'+
    /* 반응 뒤 말풍선 — 카톡 아이콘 위 */
    '.ss-nudge{position:absolute;bottom:calc(100% + 8px);right:-2px;transform:translateY(4px);opacity:0;white-space:nowrap;'+
    'font:800 12px Pretendard,sans-serif;color:#191600;background:var(--sn-kakao);padding:6px 10px;border-radius:999px;'+
    'box-shadow:0 6px 16px rgba(0,0,0,.18);pointer-events:none;transition:opacity .2s,transform .2s;z-index:5}'+
    '.ss-nudge::after{content:"";position:absolute;top:100%;right:14px;border:5px solid transparent;border-top-color:var(--sn-kakao)}'+
    '.ss-nudge.on{opacity:1;transform:none}'+
    /* 3. 읽은 만큼 차오르는 진행 막대 */
    '#ss-prog{position:fixed;left:0;top:0;height:3px;width:0;background:var(--sn-accent);z-index:100001;transition:width .1s linear;pointer-events:none}'+
    /* 5. 홈 오늘의 순살 반응 표시 */
    '.hero .hs .ss-heat{flex:0 0 auto;margin-left:8px;font-size:11px;font-weight:600;color:var(--sn-mute);font-variant-numeric:tabular-nums;white-space:nowrap;opacity:.85}'+
    '.hero .hs.ss-hot{border-radius:10px}'+
    /* 4. 순스타그램 바둑판 */
    '.ss-grid-bar{display:flex;align-items:center;gap:8px;max-width:800px;margin:0 auto 12px;padding:0 20px}'+
    '.ss-grid-bar .sp{flex:1}.ss-grid-bar .tg{display:inline-flex;padding:3px;border-radius:999px;background:#1b1715;border:1px solid #2e2924}'+
    '.ss-grid-bar .tg button{display:flex;align-items:center;justify-content:center;width:34px;height:28px;border-radius:999px;border:0;background:transparent;color:#8b8578;cursor:pointer}'+
    '.ss-grid-bar .tg button.on{background:#2e2620;color:#f6f1e8}'+
    '.ss-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:3px;max-width:800px;margin:0 auto 40px;padding:0 20px}'+
    '.ss-grid a{position:relative;display:block;aspect-ratio:1/1;overflow:hidden;background:#1b1715;border-radius:4px}'+
    '.ss-grid a .t{display:none!important}.ss-grid a.nt .t{display:-webkit-box!important;top:30px;bottom:auto;background:none;color:#cfc8bc}'+
    '.ss-grid img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .25s}.ss-grid a:hover img{transform:scale(1.04)}'+
    '.ss-grid a .t{position:absolute;left:0;right:0;bottom:0;padding:18px 7px 6px;font:700 11px/1.35 Pretendard,sans-serif;color:#fff;'+
    'background:linear-gradient(transparent,rgba(0,0,0,.78));display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}'+
    '.ss-grid a .d{position:absolute;top:6px;left:6px;font:800 10px Pretendard,sans-serif;color:#fff;background:rgba(0,0,0,.55);padding:2px 6px;border-radius:999px}'+
    '@media(max-width:560px){.ss-grid{padding:0 8px;gap:2px}.ss-grid-bar{padding:0 12px}.ss-grid a .t{font-size:10px;padding:14px 5px 5px}}';
  (document.head||document.documentElement).appendChild(st);

  var IC_KK='<svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 3.5c-5.25 0-9.5 3.3-9.5 7.37 0 2.62 1.76 4.92 4.4 6.23l-.9 3.32c-.08.3.26.54.52.37l3.95-2.6c.5.06 1.01.1 1.53.1 5.25 0 9.5-3.3 9.5-7.42S17.25 3.5 12 3.5z"/></svg>';
  var IC_LN='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.07 0l2.83-2.83a5 5 0 0 0-7.07-7.07L11.5 4.43"/><path d="M14 11a5 5 0 0 0-7.07 0L4.1 13.83a5 5 0 0 0 7.07 7.07l1.33-1.33"/></svg>';
  function toast(t){var el=document.getElementById('ss-toast');if(!el){el=document.createElement('div');el.id='ss-toast';
    el.style.cssText='position:fixed;left:50%;bottom:28px;transform:translateX(-50%);background:#f6f1e8;color:#12100e;font:800 14px Pretendard,sans-serif;padding:11px 18px;border-radius:999px;z-index:100020;opacity:0;transition:opacity .2s;pointer-events:none';
    document.body.appendChild(el)}el.textContent=t;el.style.opacity='1';clearTimeout(el._t);el._t=setTimeout(function(){el.style.opacity='0'},1800)}
  function copyLink(u,txt){var t=(txt?txt+'\n':'')+u;(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){toast('복사했어요 — 단톡방에 붙여 넣기')},function(){prompt('복사해서 보내세요',t)})}

  function onLoad(fn){if(document.readyState==='complete')setTimeout(fn,0);else window.addEventListener('load',fn)}
  function onReady(fn){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',fn);else fn()}
  // 주소보다 페이지 구조로 판별 — 홈은 히어로+전문, 차트 하루 페이지는 꼭지 article, 뉴스레터는 회차 표시
  var P=location.pathname,isHome=!!(document.getElementById('nlwrap')&&document.querySelector('.hero')),
    isChart=!!document.querySelector('article.story.morning-topic[data-ss-story]'),
    isNl=!isHome&&!isChart&&/^\/newsletters\/\d{4}\/[^/]+\.html$/.test(P);

  // ── 3. 뉴스레터 본문: 읽은 만큼 차오르는 막대 ──
  if(isNl){var bar=document.createElement('div');bar.id='ss-prog';document.body.appendChild(bar);
    var tick=0;window.addEventListener('scroll',function(){if(tick)return;tick=1;requestAnimationFrame(function(){tick=0;
      var h=document.documentElement.scrollHeight-innerHeight;bar.style.width=(h>0?Math.min(100,scrollY*100/h):0)+'%'})},{passive:true})}

  // ── 3·6. 공유는 있는 자리에 녹인다 (KD 2026-10-23 「위 공유 버튼이랑 중복 — 대놓고 영역을 크게 차지하며 압박하지 말고 자연스럽게」) ──
  //   기존(0a563a6): 스토리·차트 꼭지 끝마다 「친구한테」 상자. 최신: 상자 없음. 👍🤔🔥 를 누른 순간에만 그 줄의 카톡 아이콘 위에
  //   「친구한테도?」 말풍선이 4초 떴다 사라지고 아이콘에 샤인 스윕 — 스토리마다 한 번만.
  var nudged={},nudging=null;
  // 카톡 공유 버튼에 샤인 스윕 — 한 화면 하나만: 지금 가장 많이 보이는 스토리의 카톡 버튼 (KD 10/23 「카톡 알약에 샤인 스윕이 지나가면
  //   누르고 싶은 생각이 더 들 듯」). 스토리 5개가 다 반짝이면 효과가 죽어서 보이는 것 하나에만.
  // 화면에 보이는 높이가 가장 큰 스토리 — 스크롤 때 직접 잰다(IntersectionObserver 는 숨은 탭에서 안 돌아 단순하게)
  function applyShine(){var kks=document.querySelectorAll('.ss-react .ss-kk');if(!kks.length)return;var best=null,bv=120,H=innerHeight;
    [].forEach.call(kks,function(kk){var host=kk.closest('[data-ss-story]');if(!host)return;var r=host.getBoundingClientRect(),v=Math.min(r.bottom,H)-Math.max(r.top,0);
      if(v>bv){bv=v;best=kk}});
    [].forEach.call(kks,function(kk){kk.classList.toggle('ss-shine',kk===best&&kk!==nudging)})}
  var shTick=0;window.addEventListener('scroll',function(){if(shTick)return;shTick=1;setTimeout(function(){shTick=0;applyShine()},250)},{passive:true});
  [1500,3000,6000].forEach(function(t){setTimeout(applyShine,t)});   // 카톡 버튼이 늦게 그려져도 붙게
  document.addEventListener('click',function(e){
    var b=e.target.closest&&e.target.closest('.ss-react .ss-rb');if(!b||b.classList.contains('ss-sh')||b.classList.contains('ss-kk'))return;
    var row=b.closest('.ss-react'),kk=row&&row.querySelector('.ss-kk'),host=b.closest('[data-ss-story]');if(!kk||!host)return;
    var sid=host.getAttribute('data-ss-story');if(nudged[sid])return;nudged[sid]=1;
    setTimeout(function(){var t=document.createElement('span');t.className='ss-nudge';t.textContent='친구한테도?';
      nudging=kk;kk.classList.remove('ss-shine');kk.style.position='relative';kk.style.overflow='visible';kk.appendChild(t);
      requestAnimationFrame(function(){t.classList.add('on')});
      setTimeout(function(){t.classList.remove('on');setTimeout(function(){t.remove();kk.style.overflow='';nudging=null},250)},4000)},350)});

  // ── 「순살 치킨집」 봇 캐릭터 (KD 2026-10-24 「대놓고 봇 캐릭터를 매력적으로 명확하게 정해서 활용」) ──
  //   사람인 척하지 않는다: 댓글엔 🤖 배지, 아바타는 캐릭터 이모지, 이름을 누르면 「AI가 쓰는 캐릭터」 소개 카드.
  //   글은 soonsal-build scripts/crew_service.py 가 관리자 키(op=2)로 올린다. 같은 이름은 독자가 못 쓴다(Worker CREW_NICK).
  var CREW={
    '반반':{e:'🧮',c:'#7FA8C8',t:'계산부터 하는 반반',i:'좋다·나쁘다 전에 계산부터 해요. 숫자 나오면 제가 갑니다.',w:'실적 · 금리 · 큰 숫자'},
    '양념':{e:'🌶️',c:'#D96A5B',t:'매운맛 삐딱이',i:'다들 좋다면 난 일단 반대편에 서 봄. 매운 거 싫으면 패스 ㅋ',w:'들뜬 주제 · 한쪽으로 쏠린 질문'},
    '후라이드':{e:'💼',c:'#C8B060',t:'기본맛 월급쟁이',i:'평범한 직장인 시선 담당. 뉴스 보면 일단 내 월급부터 떠올려요.',w:'물가 · 월급 · 집 · 회사'},
    '간장':{e:'🐢',c:'#8FB0A0',t:'짠맛 장기투자파',i:'10년 뒤를 보고 삽니다. 급할수록 천천히.',w:'급락·급등장 · 배당 · 빚투'},
    '파닭':{e:'✨',c:'#A09CD8',t:'트렌드 덕후',i:'요즘 뜨는 브랜드·밈·덕질 경제 담당임다. 숫자는 반반님께 패스!',w:'브랜드 · 소비 트렌드 · 스포츠·연예'}};
  window.ssCrew=CREW;
  window.ssCrewCard=function(nick){var c=CREW[nick];if(!c)return;
    var ov=document.getElementById('ss-crew');if(!ov){ov=document.createElement('div');ov.id='ss-crew';document.body.appendChild(ov);
      var cs=document.createElement('style');cs.textContent=
        '#ss-crew{position:fixed;inset:0;z-index:100016;display:none}#ss-crew.on{display:block}'+
        '#ss-crew .bg{position:absolute;inset:0;background:rgba(0,0,0,.6)}'+
        '#ss-crew .pn{position:absolute;left:0;right:0;bottom:0;max-width:560px;margin:0 auto;padding:10px 20px calc(20px + env(safe-area-inset-bottom));'+
        'background:#171513;border-radius:20px 20px 0 0;font-family:Pretendard,-apple-system,sans-serif;color:#e8e3da}'+
        '#ss-crew .gr{width:38px;height:4px;border-radius:4px;background:#3a2f27;margin:0 auto 16px}'+
        '#ss-crew .hd{display:flex;align-items:center;gap:14px}'+
        '#ss-crew .av{width:54px;height:54px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:27px}'+
        '#ss-crew .nm{font-size:19px;font-weight:900;color:#fff}#ss-crew .nm i{font-style:normal;font-size:11px;font-weight:800;color:#b9c4d0;border:1px solid #3d4a57;border-radius:999px;padding:1px 7px;margin-left:6px;vertical-align:3px}'+
        '#ss-crew .tg{font-size:13px;color:#a39c90;margin-top:3px}'+
        '#ss-crew .q{margin:16px 0 0;padding:12px 14px;border-radius:14px;background:#211d19;font-size:15px;line-height:1.6;color:#f6f1e8}'+
        '#ss-crew .w{font-size:12.5px;color:#8b8578;margin-top:10px}#ss-crew .w b{color:#cfc8bc;font-weight:700}'+
        '#ss-crew .rw{display:flex;gap:8px;margin-top:18px;padding-top:14px;border-top:1px solid #26221e;align-items:center}'+
        '#ss-crew .rw span{font-size:11.5px;color:#7c756c;margin-right:2px}'+
        '#ss-crew .rw button{width:34px;height:34px;min-height:0;border-radius:50%;border:2px solid transparent;font-size:17px;cursor:pointer;padding:0}'+
        '#ss-crew .rw button.on{border-color:#f6f1e8}'+
        '#ss-crew .ft{font-size:11.5px;line-height:1.6;color:#6f695f;margin-top:12px}';
      document.head.appendChild(cs);
      ov.addEventListener('click',function(e){if(e.target.classList.contains('bg')){ov.classList.remove('on');return}
        var b=e.target.closest('[data-crew]');if(b)window.ssCrewCard(b.getAttribute('data-crew'))})}
    ov.innerHTML='<div class="bg"></div><div class="pn" role="dialog" aria-label="봇 캐릭터 소개"><div class="gr"></div>'+
      '<div class="hd"><span class="av" style="background:'+c.c+'">'+c.e+'</span><div><div class="nm">'+nick+'<i>🤖 봇</i></div><div class="tg">'+c.t+'</div></div></div>'+
      '<p class="q">'+c.i+'</p><div class="w">주로 나타나는 곳 <b>'+c.w+'</b></div>'+
      '<div class="rw"><span>순살 치킨집</span>'+Object.keys(CREW).map(function(k){return '<button type="button" data-crew="'+k+'" class="'+(k===nick?'on':'')+'" style="background:'+CREW[k].c+'" aria-label="'+k+'">'+CREW[k].e+'</button>'}).join('')+'</div>'+
      '<div class="ft">순살 치킨집 식구들은 AI가 쓰는 봇 캐릭터예요. 정해진 성격대로 이야기하고, 투자 권유는 하지 않아요.</div></div>';
    ov.classList.add('on')};
  // 뉴스레터 댓글(soonsal.js 가 그림): 봇 캐릭터 글이면 아바타를 캐릭터 이모지로, 이름을 누르면 소개 카드
  function crewDeco(){[].forEach.call(document.querySelectorAll('.ss-ci.ss-cop:not([data-crew])'),function(el){
    var b=el.querySelector('.ss-cnk')||el.querySelector('.ss-cnm b'),n=b&&b.textContent.replace(/\s*✓$/,'').trim(),c=CREW[n];el.setAttribute('data-crew',c?n:'');if(!c||!el.querySelector('.ss-cob.bot'))return;
    var av=el.firstElementChild;if(av&&!av.classList.contains('ss-cbd')){av.textContent=c.e;av.style.background=c.c}
    b.style.cursor='pointer';b.setAttribute('role','button')})}
  document.addEventListener('click',function(e){var b=e.target.closest('.ss-ci[data-crew] .ss-cnm b, .ss-ci[data-crew] .ss-cnk');if(!b)return;var n=b.closest('.ss-ci').getAttribute('data-crew');if(n)window.ssCrewCard(n)});
  // 시세 띠처럼 글자만 바뀌는 변화는 무시하고, 댓글(.ss-ci)이 새로 붙을 때만 본다
  if(window.MutationObserver){var crewT=0;new MutationObserver(function(rs){if(crewT)return;
    for(var i=0;i<rs.length;i++){var a=rs[i].addedNodes;for(var j=0;j<a.length;j++){var n=a[j];
      if(n.nodeType===1&&(n.classList.contains('ss-ci')||n.querySelector('.ss-ci'))){crewT=setTimeout(function(){crewT=0;crewDeco()},200);return}}}
  }).observe(document.body||document.documentElement,{childList:true,subtree:true})}
  document.addEventListener('DOMContentLoaded',crewDeco);

  // ── 회원 지난 글 창 (KD 2026-10-24 「로그인한 사람들의 과거 이력들도 눌러서 볼 수 있게 — MLB파크 기존 게시물 보기처럼」) ──
  //   window.ssMember(회원번호, 제목함수?) — 순살톡·오늘의 질문 댓글의 ✓회원 이름을 누르면 아래에서 올라온다. GET /member?u=
  function storyHref(st,ts){var y=new Date((ts||0)*1000).getFullYear()||2026,m=/^(\d{4})(c?)-(\d{1,2})$/.exec(st);
    if(m)return '/newsletters/'+y+'/'+m[1]+(m[2]?'-crypto':'')+'.html#story-'+m[3];
    var c=/^m(\d{4})(\d{4})-(.+)$/.exec(st);return c?'/chart/'+c[1]+'/'+c[2]+'.html#'+c[3]:'#'}
  function sAgo(t){var s=Math.max(0,Math.floor(Date.now()/1000)-t);return s<3600?Math.max(1,Math.floor(s/60))+'분':s<86400?Math.floor(s/3600)+'시간':Math.floor(s/86400)+'일'}
  window.ssMember=function(u,tf){if(!/^[0-9a-f]{16,40}$/.test(u||''))return;
    var ov=document.getElementById('ss-mem');if(!ov){ov=document.createElement('div');ov.id='ss-mem';document.body.appendChild(ov);
      var cs=document.createElement('style');cs.textContent=
        '#ss-mem{position:fixed;inset:0;z-index:100016;display:none}#ss-mem.on{display:block}'+
        '#ss-mem .bg{position:absolute;inset:0;background:rgba(0,0,0,.6)}'+
        '#ss-mem .pn{position:absolute;left:0;right:0;bottom:0;max-width:560px;max-height:82vh;margin:0 auto;overflow:auto;padding:10px 18px calc(18px + env(safe-area-inset-bottom));'+
        'background:#171513;border-radius:20px 20px 0 0;font-family:Pretendard,-apple-system,sans-serif;color:#e8e3da}'+
        '#ss-mem .gr{width:38px;height:4px;border-radius:4px;background:#3a2f27;margin:0 auto 14px}'+
        '#ss-mem .hd{display:flex;align-items:center;gap:12px;padding-bottom:14px;border-bottom:1px solid #26221e}'+
        '#ss-mem .av{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:18px;color:#12100e;background:#F0A070}'+
        '#ss-mem .nm{font-size:17px;font-weight:900;color:#fff}#ss-mem .nm i{font-style:normal;font-size:11px;font-weight:800;color:#F5A481;border:1px solid #5a3524;border-radius:999px;padding:1px 7px;margin-left:6px;vertical-align:2px}'+
        '#ss-mem .st{font-size:12.5px;color:#8b8578;margin-top:3px}#ss-mem .st b{color:#cfc8bc}'+
        '#ss-mem .it{display:block;padding:12px 0;border-bottom:1px solid #1f1c19;text-decoration:none;color:inherit}'+
        '#ss-mem .it .s{font-size:11.5px;color:#7c756c;margin-bottom:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}'+
        '#ss-mem .it .b{font-size:14.5px;line-height:1.6;color:#ece6dc;word-break:break-word}'+
        '#ss-mem .it .m{font-size:11.5px;color:#6f695f;margin-top:4px}#ss-mem .em{padding:30px 0;text-align:center;color:#7c756c;font-size:13.5px}';
      document.head.appendChild(cs);
      ov.addEventListener('click',function(e){if(e.target.classList.contains('bg'))ov.classList.remove('on')})}
    ov.innerHTML='<div class="bg"></div><div class="pn" role="dialog" aria-label="회원 지난 글"><div class="gr"></div><div class="em">불러오는 중…</div></div>';ov.classList.add('on');
    fetch(API+'/member?u='+u).then(function(r){return r.json()}).then(function(j){var m=j&&j.member;if(!m){ov.querySelector('.pn').innerHTML='<div class="gr"></div><div class="em">글을 찾지 못했어요</div>';return}
      var d=m.since?new Date(m.since*1000):null,ch=String(m.nick||'?').replace(/[^가-힣A-Za-z0-9]/g,'').charAt(0)||'?';
      ov.querySelector('.pn').innerHTML='<div class="gr"></div><div class="hd"><span class="av">'+esc(ch)+'</span><div><div class="nm">'+esc(m.nick)+'<i>✓ 회원</i></div>'+
        '<div class="st">한마디 <b>'+m.n+'</b> · 받은 ♥ <b>'+m.likes+'</b>'+(d?' · '+d.getFullYear()+'.'+(d.getMonth()+1)+' 가입':'')+'</div></div></div>'+
        ((j.comments||[]).map(function(c){var t=tf&&tf(c.story);return '<a class="it" href="'+storyHref(c.story,c.ts)+'">'+
          '<div class="s">'+(c.parent_id?'↩ 답글 · ':'')+esc(t||c.story)+'</div><div class="b">'+esc(c.body)+'</div>'+
          '<div class="m">'+sAgo(c.ts)+(c.likes?' · ♥ '+c.likes:'')+(c.replies?' · 답글 '+c.replies:'')+'</div></a>'}).join('')||'<div class="em">아직 공개된 글이 없어요</div>')})
      .catch(function(){ov.querySelector('.pn').innerHTML='<div class="gr"></div><div class="em">불러오지 못했어요</div>'})};

  // ── 5. 홈 「오늘의 순살」 줄마다 반응 수, 가장 뜨거운 줄에 샤인 스윕 ──
  if(isHome){onLoad(function(){
    var any=document.querySelector('#nlwrap [data-ss-story]');if(!any)return;var iss=(any.getAttribute('data-ss-story')||'').split('-')[0];
    fetch(API+'/counts?issue='+encodeURIComponent(iss)).then(function(r){return r.json()}).then(function(j){
      var best=null,bn=0;[].forEach.call(document.querySelectorAll('.hero .hs[data-n]'),function(row){
        var c=j[iss+'-'+row.getAttribute('data-n')]||{},n=0;for(var k in c)n+=c[k]||0;if(!n)return;
        // 👍🤔🔥 를 다 합친 「열기」 하나 (KD 10/23 「하나로 다 모아서 보여 주는 게 좋을 듯」)
        var b=document.createElement('span');b.className='ss-heat';b.textContent='🔥 '+n;b.title='반응 합계 '+n+'(좋았음·글쎄·중요함)';
        b.setAttribute('aria-label','반응 '+n+'개');row.appendChild(b);if(n>bn){bn=n;best=row}});
      if(best&&bn>=3){best.classList.add('ss-shine','ss-hot')}}).catch(function(){})})}

  // ── 4. 순스타그램 목록 = 인스타 프로필처럼 3칸 바둑판 (원래 목록은 「목록」 버튼으로) ──
  if(P==='/cardnews/'||P==='/cardnews/index.html'){onReady(function(){
    var days=document.querySelectorAll('.today');if(!days.length)return;
    var tiles=[];[].forEach.call(days,function(dv){var dt=(dv.querySelector('.today-title')||{}).textContent||'';
      [].forEach.call(dv.querySelectorAll('a[href^="/cardnews/20"]'),function(a){var m=a.getAttribute('href').match(/^\/cardnews\/(\d{4})\/([^/]+)\.html$/);if(!m)return;
        tiles.push({h:a.getAttribute('href'),y:m[1],s:m[2],t:a.textContent.replace(/^\s*Card\s*/,'').replace(/^순살(크립토)?카드뉴스\s*·\s*/,'').trim(),d:dt.slice(5).replace('.','/')})})});
    if(!tiles.length)return;
    var barEl=document.createElement('div');barEl.className='ss-grid-bar';
    // 글자 대신 아이콘 토글 (KD 10/24 「바둑판 목록이라는 워딩 말고 토글 형태로 이모지」)
    var IG='<svg viewBox="0 0 24 24" width="17" height="17" fill="currentColor"><rect x="3" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.5"/></svg>',
        IL='<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg>';
    barEl.innerHTML='<span class="tg"><button type="button" class="on" data-v="g" aria-label="바둑판으로 보기">'+IG+'</button><button type="button" data-v="l" aria-label="목록으로 보기">'+IL+'</button></span><span class="sp"></span>'+
      '<a class="ss-pill sub ss-shine" href="https://instagram.com/soonsal.brief" target="_blank" rel="noopener">📸 인스타 팔로우</a>';
    var g=document.createElement('div');g.className='ss-grid';
    // 바둑판엔 작은 표지(assets/cardnews/t/, 360px) — 없으면 원본, 그것도 없으면 제목 글자 칸 (KD 10/24 「이미지 로딩 시간」)
    g.innerHTML=tiles.map(function(x,i){return '<a href="'+x.h+'"><img loading="'+(i<9?'eager':'lazy')+'" decoding="async" alt="'+esc(x.t)+'" src="/assets/cardnews/t/'+x.s+'.jpg" '+
      'onerror="if(!this.dataset.f){this.dataset.f=1;this.src=\'/assets/cardnews/'+x.s+'.jpg\'}else{this.style.display=\'none\';this.parentNode.classList.add(\'nt\')}">'+
      '<span class="d">'+esc(x.d)+'</span><span class="t">'+esc(x.t)+'</span></a>'}).join('');   // 표지에 제목이 이미 크게 있어 글자는 덧대지 않는다(alt 로만)
    days[0].parentNode.insertBefore(barEl,days[0]);barEl.parentNode.insertBefore(g,barEl.nextSibling);
    function mode(v){var grid=v==='g';g.style.display=grid?'':'none';[].forEach.call(days,function(dv){dv.style.display=grid?'none':''});
      [].forEach.call(barEl.querySelectorAll('button'),function(b){b.classList.toggle('on',b.getAttribute('data-v')===v)});try{localStorage.setItem('ss_cn_view',v)}catch(e){}}
    [].forEach.call(barEl.querySelectorAll('button'),function(b){b.onclick=function(){mode(b.getAttribute('data-v'))}});
    mode(lsg('ss_cn_view')==='l'?'l':'g')})}
})();

/* ── 앱처럼 설치(홈 화면·바탕화면) — KD 2026-10-26 「스카우티처럼 바탕화면에 설치할 수 있게 버튼 만들어서 유도 — 잘 보이고 잘 설치되도록」 ──
   · manifest(/manifest.webmanifest, build_pwa.py)를 여기서 붙인다 — 전 페이지 공통.
   · 안드로이드·PC 크롬·엣지: beforeinstallprompt 를 잡아 「설치」 한 번에 기기 설치 창.
   · 아이폰·아이패드 사파리: 자동 설치가 없어 「공유 → 홈 화면에 추가」 3단계 안내 창.
   · 카톡·인스타·네이버 등 앱 안 브라우저: 설치가 안 되니 「Safari·크롬으로 열기」 안내 + 주소 복사.
   · 이미 앱으로 연 경우(standalone)·설치 끝난 경우엔 아무것도 안 띄운다.
   · 아래 떠 있는 카드: 홈은 늘, 다른 페이지는 세 번째 방문부터. × 누르면 14일 쉼. ☰ 메뉴엔 「📲 앱으로 설치」 늘.
*/
(function(){
  if(window.__ssInst)return;window.__ssInst=1;
  function lsg(k){try{return localStorage.getItem(k)}catch(e){return null}}
  function lss(k,v){try{localStorage.setItem(k,v)}catch(e){}}
  var d=document,ua=navigator.userAgent||'';
  function meta(n,c){if(!d.querySelector('meta[name="'+n+'"]')){var m=d.createElement('meta');m.name=n;m.content=c;d.head.appendChild(m)}}
  if(!d.querySelector('link[rel="manifest"]')){var l=d.createElement('link');l.rel='manifest';l.href='/manifest.webmanifest';d.head.appendChild(l)}
  meta('theme-color','#111111');meta('apple-mobile-web-app-capable','yes');meta('mobile-web-app-capable','yes');
  meta('apple-mobile-web-app-title','순살');meta('apple-mobile-web-app-status-bar-style','black-translucent');
  var standalone=(window.matchMedia&&matchMedia('(display-mode: standalone)').matches)||navigator.standalone===true;
  // ── 앱 집계(KD 10/26 「앱을 몇 명 설치했는지·앱에서 뭘 보는지·구독자인지 비교」) — POST /t, 개인별 열람 이력 없음 ──
  function vidOf(){var v=lsg('ss_vid');if(!v||!/^[a-z0-9-]{8,32}$/.test(v)){v=(Math.random().toString(36).slice(2)+Math.random().toString(36).slice(2)).slice(0,16);lss('ss_vid',v)}return v}
  function isSub(){return (window.ssIsSub&&window.ssIsSub())||lsg('ss_is_sub')==='1'||lsg('ss_subbed')==='1'}
  function tsend(o){try{o.v=vidOf();o.s=isSub()?1:0;o.m=lsg('ss_auth')==='1'?1:0;
    fetch('https://api.soonsal.com/t',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(o),keepalive:true}).catch(function(){})}catch(e){}}
  function step(k){tsend({t:'inst',k:k})}
  // 웹·앱에서 읽은 구독자(KD 10/26 「웹/앱이 흥하면 이메일 열람이 줄어들 위험 — 웹/앱 구독자 트래킹이 확실히」):
  //   구독자 표시가 있는 브라우저가 메일 링크 없이 뉴스레터(홈의 전문 포함)를 열면 채널(web/app)별로 한 번.
  //   메일 링크로 들어온 세션은 메일 쪽(reads)이 이미 세므로 그 세션 내내 뺀다(중복 방지).
  var fromMail=/[?&]ss=[a-f0-9]{16}\.|[?&]s=[a-f0-9]{16}\b|utm_source=mail|utm_medium=email|[?&]m=1\b/.test(location.search);
  try{if(fromMail)sessionStorage.setItem('ss_mail_sess','1');else if(sessionStorage.getItem('ss_mail_sess'))fromMail=true}catch(e){}
  var nlm=location.pathname.match(/^\/newsletters\/\d{4}\/(\d{4})(-crypto)?\.html$/),
      issN=nlm?nlm[1]+(nlm[2]?'c':''):((location.pathname==='/'||location.pathname==='/index.html')?'home':'');
  function sread(ch){if(issN&&!fromMail&&isSub())tsend({t:'sread',ch:ch,i:issN})}
  if(standalone){lss('ss_inst_done','1');
    // 아이폰은 설치 순간을 알려 주지 않는다 → 앱 화면으로 처음 연 날 = 설치일(서버 app_users.first_day)
    setTimeout(function(){tsend({t:'app',p:location.pathname})},600);
    setTimeout(function(){sread('app')},2500);   // 회원이면 /me 가 구독 표시를 채운 뒤
    return}
  setTimeout(function(){sread('web')},2500);
  var iOS=/iPhone|iPad|iPod/.test(ua)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
  var inApp=/KAKAOTALK|Instagram|FBAN|FBAV|NAVER\(|Line\/|DaumApps|everytimeApp|Barcelona|Twitter/i.test(ua);
  var deferred=null,card=null,P=location.pathname,home=P==='/'||P==='/index.html';
  var pv=(+lsg('ss_inst_pv')||0)+1;lss('ss_inst_pv',String(pv));
  function can(){return !!(deferred||iOS||inApp)}
  function eligible(){return !lsg('ss_inst_done')&&Date.now()>(+lsg('ss_inst_snooze')||0)&&(home||pv>=3)}
  var css=d.createElement('style');css.textContent=
    '.ss-inst{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom));z-index:100000;max-width:520px;margin:0 auto;'+
    'display:flex;align-items:center;gap:12px;padding:12px 10px 12px 12px;border-radius:18px;background:#1d1916;border:1px solid #3a2f27;'+
    'box-shadow:0 10px 30px rgba(0,0,0,.45);font-family:Pretendard,-apple-system,sans-serif;transform:translateY(140%);transition:transform .45s cubic-bezier(.2,.9,.3,1.2)}'+
    '.ss-inst.on{transform:none}.ss-inst img{width:44px;height:44px;border-radius:11px;flex:0 0 auto}'+
    '.ss-inst .t{flex:1;min-width:0}.ss-inst .t b{display:block;font-size:15px;font-weight:900;color:#fff;letter-spacing:-.02em}'+
    '.ss-inst .t span{display:block;font-size:12px;color:#a39c90;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}'+
    '.ss-inst .go{flex:0 0 auto;height:38px;min-height:0;padding:0 16px;border:0;border-radius:999px;background:#F07040;color:#12100e;font:800 14px Pretendard,-apple-system,sans-serif;cursor:pointer;position:relative;overflow:hidden}'+
    '.ss-inst .x{flex:0 0 auto;width:28px;height:28px;min-height:0;border:0;background:none;color:#6f695f;font-size:18px;cursor:pointer;padding:0}'+
    'html.ss-inst-on .ss-fab{transform:translateY(-84px)}'+
    '#ss-ig{position:fixed;inset:0;z-index:100017;display:none}#ss-ig.on{display:block}#ss-ig .bg{position:absolute;inset:0;background:rgba(0,0,0,.6)}'+
    '#ss-ig .pn{position:absolute;left:0;right:0;bottom:0;max-width:560px;margin:0 auto;padding:12px 20px calc(22px + env(safe-area-inset-bottom));background:#171513;border-radius:20px 20px 0 0;'+
    'font-family:Pretendard,-apple-system,sans-serif;color:#e8e3da}#ss-ig .gr{width:38px;height:4px;border-radius:4px;background:#3a2f27;margin:0 auto 16px}'+
    '#ss-ig .hd{display:flex;align-items:center;gap:12px;margin-bottom:14px}#ss-ig .hd img{width:52px;height:52px;border-radius:13px}'+
    '#ss-ig .hd b{display:block;font-size:18px;font-weight:900;color:#fff}#ss-ig .hd span{font-size:12.5px;color:#a39c90}'+
    '#ss-ig ol{list-style:none;margin:0;padding:0;counter-reset:s}#ss-ig li{counter-increment:s;display:flex;align-items:center;gap:12px;padding:12px 0;border-top:1px solid #26221e;font-size:15px;line-height:1.5}'+
    '#ss-ig li:before{content:counter(s);flex:0 0 auto;width:26px;height:26px;border-radius:50%;background:#F07040;color:#12100e;font-weight:900;font-size:13px;display:flex;align-items:center;justify-content:center}'+
    '#ss-ig li b{color:#fff}#ss-ig .ic{display:inline-flex;vertical-align:-5px;width:24px;height:24px;border-radius:6px;background:#2a2420;align-items:center;justify-content:center;margin:0 2px;color:#5aa2ff}'+
    '#ss-ig .nt{font-size:12px;color:#7c756c;margin-top:10px;line-height:1.6}'+
    '#ss-ig .cp{display:block;width:100%;height:46px;margin-top:14px;border:0;border-radius:999px;background:#F07040;color:#12100e;font:800 15px Pretendard,-apple-system,sans-serif;cursor:pointer}'+
    /* 화살표 안내(아이폰) — 화면을 어둡게 덮고 공유 버튼 자리를 큰 화살표로 짚는다 (KD 10/26 「스카우티·플랜트리처럼 공유 버튼 근처에 화살표와 메시지」) */
    '#ss-iga{position:fixed;inset:0;z-index:100018;font-family:Pretendard,-apple-system,sans-serif}#ss-iga .dim{position:absolute;inset:0;background:rgba(0,0,0,.78)}'+
    '#ss-iga .arw{position:absolute;width:64px;height:64px;color:#F07040;filter:drop-shadow(0 4px 14px rgba(240,112,64,.55))}'+
    '#ss-iga.t .arw{top:2px;right:16px;animation:ssUp 1s ease-in-out infinite}#ss-iga.b .arw{bottom:4px;left:calc(50% - 32px);animation:ssDn 1s ease-in-out infinite}'+
    '@keyframes ssUp{0%,100%{transform:translateY(8px)}50%{transform:translateY(-2px)}}@keyframes ssDn{0%,100%{transform:translateY(-8px)}50%{transform:translateY(2px)}}'+
    '#ss-iga .bub{position:absolute;left:14px;right:14px;max-width:440px;margin:0 auto;padding:18px 18px 14px;border-radius:20px;background:#1d1916;border:1px solid #F07040;color:#e8e3da;box-shadow:0 14px 40px rgba(0,0,0,.5)}'+
    '#ss-iga.t .bub{top:78px}#ss-iga.b .bub{bottom:84px}'+
    '#ss-iga .h{display:flex;align-items:center;gap:10px;margin-bottom:10px}#ss-iga .h img{width:40px;height:40px;border-radius:10px}#ss-iga .h b{font-size:17px;font-weight:900;color:#fff}'+
    /* 아이콘을 글자 높이에 맞춰 한 줄로(KD 10/26 폰 캡처: 큰 아이콘 칸 때문에 문장이 벌어짐) — 위치 설명은 아래 작은 줄로 */
    '#ss-iga .big{display:flex;align-items:center;gap:8px;font-size:19px;line-height:1.3;font-weight:800;color:#fff;margin:4px 0 4px}'+
    '#ss-iga .big .ic{flex:0 0 auto;width:30px;height:30px;margin:0;border-radius:8px;vertical-align:0}'+
    '#ss-iga .whr{font-size:13px;color:#a39c90;margin:0 0 12px}'+
    '#ss-iga ol{list-style:none;margin:0;padding:0;counter-reset:s}#ss-iga li{counter-increment:s;display:flex;align-items:center;gap:10px;padding:8px 0;border-top:1px solid #2e2620;font-size:14.5px}'+
    '#ss-iga li:before{content:counter(s);flex:0 0 auto;width:22px;height:22px;border-radius:50%;background:#F07040;color:#12100e;font-weight:900;font-size:12px;display:flex;align-items:center;justify-content:center}'+
    '#ss-iga li b{color:#fff}#ss-iga .ic{display:inline-flex;vertical-align:middle;width:22px;height:22px;border-radius:6px;background:#2a2420;align-items:center;justify-content:center;margin:-2px 3px 0;color:#5aa2ff}'+
    '#ss-iga .alt{display:block;margin:10px 0 0;padding:0;min-height:0;border:0;background:none;color:#a39c90;font:600 12.5px Pretendard,-apple-system,sans-serif;text-decoration:underline;cursor:pointer}'+
    '#ss-iga .altx{font-size:12.5px;color:#cfc8bc;line-height:1.6;margin-top:6px}'+
    '#ss-iga .ok{display:block;width:100%;height:44px;min-height:0;margin-top:12px;border:0;border-radius:999px;background:#2a2420;color:#f6f1e8;font:800 14px Pretendard,-apple-system,sans-serif;cursor:pointer}'+
    '@media (prefers-reduced-motion:reduce){.ss-inst{transition:none}#ss-iga .arw{animation:none}}';
  d.head.appendChild(css);
  var SHARE='<span class="ic"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="M7 8l5-5 5 5"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg></span>';
  var ADD='<span class="ic"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="4"/><path d="M12 8v8M8 12h8"/></svg></span>';
  function guide(){var g=d.getElementById('ss-ig');if(!g){g=d.createElement('div');g.id='ss-ig';d.body.appendChild(g);
      g.addEventListener('click',function(e){if(e.target.classList.contains('bg')){g.classList.remove('on');return}
        if(e.target.closest('[data-cp]')){try{navigator.clipboard.writeText(location.href);e.target.textContent='복사했어요 ✓'}catch(_){prompt('주소를 복사해 주세요',location.href)}}})}
    var body=inApp?
      '<ol><li><span>오른쪽 위(또는 아래) <b>⋯ 메뉴</b>를 눌러요</span></li><li><span><b>‘다른 브라우저로 열기’</b>(아이폰은 ‘Safari로 열기’)를 골라요</span></li><li><span>열린 사파리·크롬에서 다시 <b>📲 설치</b>를 눌러요</span></li></ol>'+
      (/KAKAOTALK/i.test(ua)?'<a class="cp" style="display:flex;align-items:center;justify-content:center;text-decoration:none" href="kakaotalk://web/openExternal?url='+encodeURIComponent(location.href)+'">'+(iOS?'Safari':'크롬')+'로 바로 열기</a>':'')+
      '<button class="cp" data-cp="1"'+(/KAKAOTALK/i.test(ua)?' style="background:#2a2420;color:#f6f1e8"':'')+'>주소 복사하기</button><div class="nt">카카오톡·인스타그램 같은 앱 안의 브라우저에서는 홈 화면 설치가 막혀 있어요.</div>'
     :iOS?
      '<ol><li><span>주소창 옆 <b>공유</b> 버튼'+SHARE+'을 눌러요</span></li><li><span>목록을 아래로 내려 <b>홈 화면에 추가</b>'+ADD+'를 골라요</span></li><li><span>오른쪽 위 <b>추가</b>를 누르면 끝</span></li></ol>'+
      '<div class="nt">공유 버튼이 안 보이면 아래쪽 <b>⋯</b> 안에 있어요. 크롬 앱이라면 주소창의 공유 버튼으로 같은 순서예요.</div>'
     :'<ol><li><span>주소창 오른쪽 <b>설치 아이콘(⊕)</b>을 눌러요</span></li><li><span><b>설치</b>를 누르면 바탕화면에 생겨요</span></li></ol><div class="nt">크롬·엣지에서 돼요. 다른 브라우저라면 크롬으로 열어 주세요.</div>';
    g.innerHTML='<div class="bg"></div><div class="pn" role="dialog" aria-label="홈 화면에 순살 추가"><div class="gr"></div>'+
      '<div class="hd"><img src="/assets/app/icon-192.png" alt=""><div><b>홈 화면에 순살 추가</b><span>앱처럼 바로 열려요 · 10초면 끝</span></div></div>'+body+'</div>';
    g.classList.add('on')}
  // 공유 버튼 자리: 사파리 26+(주소창 안 오른쪽)·아이패드·아이폰 크롬/엣지/파폭 = 위 오른쪽 / 사파리 18 이하 아이폰 = 아래 가운데 툴바
  function shareTop(){var m=ua.match(/Version\/(\d+)/),v=m?+m[1]:0;
    return /CriOS|FxiOS|EdgiOS/.test(ua)||/iPad/.test(ua)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1)||v>=26}
  var ARW='<svg viewBox="0 0 64 64" width="64" height="64" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"><path d="M32 58V10"/><path d="M14 27L32 9l18 18"/></svg>';
  function arrowGuide(){var top=shareTop(),o=d.getElementById('ss-iga');if(!o){o=d.createElement('div');o.id='ss-iga';d.body.appendChild(o);
      o.addEventListener('click',function(e){if(e.target.closest('.alt')){var x=o.querySelector('.altx');if(x)x.hidden=!x.hidden;return}
        if(e.target.closest('.ok')||e.target.classList.contains('dim')||e.target.closest('.arw'))o.remove()})}
    o.className=top?'t':'b';o.setAttribute('role','dialog');o.setAttribute('aria-label','홈 화면에 순살 추가 안내');
    o.innerHTML='<div class="dim"></div><div class="arw">'+(top?ARW:ARW.replace('<svg ','<svg style="transform:rotate(180deg)" '))+'</div>'+
      '<div class="bub"><div class="h"><img src="/assets/app/icon-192.png" alt=""><b>홈 화면에 순살 추가</b></div>'+
      '<p class="big">'+SHARE+'<span>공유 버튼을 눌러요</span></p><p class="whr">'+(top?'위쪽 주소창 오른쪽':'아래쪽 가운데')+'에 있어요 '+(top?'↗':'↓')+'</p>'+
      '<ol><li><span>목록을 내려 <b>홈 화면에 추가</b>'+ADD+'</span></li><li><span>오른쪽 위 <b>추가</b> — 끝!</span></li></ol>'+
      '<button type="button" class="alt">공유 버튼이 안 보여요</button><div class="altx" hidden>'+(top?'주소창이 <b>아래</b>에 있으면 아래쪽 <b>⋯</b> → <b>공유</b>를 눌러요.':'주소창 안이나 아래쪽 <b>⋯</b> 안에 <b>공유</b>가 있어요.')+' 크롬 앱은 주소창 오른쪽 공유 버튼이에요.</div>'+
      '<button type="button" class="ok">알겠어요</button></div>'}
  function doInstall(){
    step('click');
    if(deferred){var ev=deferred;deferred=null;step('prompt');ev.prompt();(ev.userChoice||Promise.resolve({})).then(function(c){if(c&&c.outcome==='accepted'){step('accept');lss('ss_inst_done','1');hide()}});return}
    step('guide');
    if(iOS&&!inApp){hide();arrowGuide();return}     // 아래 화살표와 겹치지 않게 카드는 내림
    guide()}
  function hide(){if(card){card.classList.remove('on');d.documentElement.classList.remove('ss-inst-on')}}
  function show(){if(card||!can()||!eligible())return;
    card=d.createElement('div');card.className='ss-inst';card.setAttribute('role','dialog');card.setAttribute('aria-label','앱처럼 설치');
    card.innerHTML='<img src="/assets/app/icon-192.png" alt=""><div class="t"><b>순살을 홈 화면에</b><span>앱처럼 바로 열고 · 아침 브리핑 한 번에</span></div>'+
      '<button type="button" class="go ss-shine" data-ss-install>설치</button><button type="button" class="x" aria-label="닫기">×</button>';
    card.querySelector('.x').onclick=function(){lss('ss_inst_snooze',String(Date.now()+14*864e5));hide()};
    d.body.appendChild(card);
    setTimeout(function(){card.classList.add('on');d.documentElement.classList.add('ss-inst-on');step('card')},2200)}
  function menu(){var dr=d.querySelector('.ss-dr');if(!dr||dr.querySelector('[data-ss-install]')||!can())return;
    var a=d.createElement('a');a.className='li';a.href='#';a.setAttribute('data-ss-install','');a.textContent='📲 앱으로 설치 (홈 화면)';
    var sub=dr.querySelector('a.sub');dr.insertBefore(a,sub||null)}
  d.addEventListener('click',function(e){var b=e.target.closest('[data-ss-install]');if(!b)return;e.preventDefault();
    d.documentElement.classList.remove('ss-open');d.body.style.overflow='';doInstall()});
  window.addEventListener('beforeinstallprompt',function(e){e.preventDefault();deferred=e;menu();show()});
  window.addEventListener('appinstalled',function(){step('installed');lss('ss_inst_done','1');hide()});
  function boot(){menu();if(iOS||inApp)show()}
  if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',boot);else boot();
})();

/* ── 뉴스레터 로그인 벽 (KD 2026-10-26 「뉴스레터는 동시에 열되 로그인을 강제할 수 있으면」) ──
   비로그인은 앞 FREE 개 스토리만, 그 뒤는 🔒 카드(남은 스토리 제목 + 「1초 로그인하고 이어 읽기」) 아래로 가린다.
   본문은 HTML 에 그대로 — 스토리 블록 class="story" 는 그대로 둔다(여러 빌더가 그 문자열로 스토리를 찾음 — seo_patch.py 주석).
   예외: 로그인한 브라우저 · 메일 링크(웹에서 보기)로 온 세션(이미 구독자로 메일 쪽에서 센다).
   로그인 뒤 서버가 원래 주소에 login=ok 를 붙여 돌려보낸다 → 여기서 받아 ss_auth 를 켜고 바로 열림.
*/
(function(){
  if(window.__ssGate)return;window.__ssGate=1;
  function lsg(k){try{return localStorage.getItem(k)}catch(e){return null}}
  function lss(k,v){try{localStorage.setItem(k,v)}catch(e){}}
  var d=document,L=location,FREE=2;
  if(/[?&#]login=ok\b/.test(L.search+L.hash)){lss('ss_auth','1');
    try{var u=L.pathname+L.search.replace(/[?&]login=ok\b/,'').replace(/^&/,'?')+L.hash.replace(/[?&]login=ok\b/,'');history.replaceState(null,'',u)}catch(e){}}
  var isNl=/^\/newsletters\/\d{4}\/\d{4}(-crypto)?\.html$/.test(L.pathname),isHome=L.pathname==='/'||L.pathname==='/index.html';
  if(!isNl&&!isHome)return;
  // 구글 유료벽 표시(KD 10/26): seo_patch.py 가 JSON-LD 에 hasPart cssSelector=.ss-paid 를 달고, 그 .ss-paid 는 여기서 붙인다.
  //   HTML 원본의 class="story" 는 빌더들이 그대로 찾으므로 손대지 않는다 — 구글은 스크립트까지 실행한 화면을 읽는다.
  //   로그인 여부와 상관없이 늘 붙인다(표시는 「이 부분은 유료벽 뒤」라는 사실일 뿐, 모양은 바꾸지 않음).
  if(isNl){var mp=function(){[].slice.call(d.querySelectorAll('.story')).forEach(function(s,i){if(i>=FREE)s.classList.add('ss-paid')})};
    if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',mp);else mp()}
  if(lsg('ss_auth')==='1')return;
  var mail=/[?&]ss=[a-f0-9]{16}\.|[?&]s=[a-f0-9]{16}\b|utm_source=mail|utm_medium=email|[?&]m=1\b/.test(L.search);
  try{if(mail)sessionStorage.setItem('ss_mail_sess','1');else if(sessionStorage.getItem('ss_mail_sess'))mail=true}catch(e){}
  if(mail)return;
  function send(k){try{var v=lsg('ss_vid');if(!v)return;fetch('https://api.soonsal.com/t',{method:'POST',headers:{'content-type':'application/json'},keepalive:true,
    body:JSON.stringify({t:'inst',k:k,v:v,s:(lsg('ss_is_sub')==='1'||lsg('ss_subbed')==='1')?1:0,m:0})}).catch(function(){})}catch(e){}}
  var css=d.createElement('style');css.textContent=
    '.ss-locked{display:none!important}'+
    /* 벽 뒤 미리보기(KD 10/26 「아예 잘라 버리면 2개짜리 뉴스레터처럼 보임 — 희미하게 뭔가 존재하는데 읽을 수는 없는 로그인 월처럼」):
       잠긴 스토리 앞 2개는 흐리게·아래로 사라지게 보여 주고 고를 수·누를 수 없게 */
    '.ss-blur{filter:blur(5px);opacity:.55;pointer-events:none;user-select:none;-webkit-user-select:none;max-height:520px;overflow:hidden;'+
      '-webkit-mask-image:linear-gradient(#000 0,#000 35%,transparent 100%);mask-image:linear-gradient(#000 0,#000 35%,transparent 100%)}'+
    '.ss-blur+.ss-blur{max-height:260px;opacity:.35}'+
    '.ss-gate-hi{animation:ssGateHi 1.6s ease}@keyframes ssGateHi{0%,100%{box-shadow:0 18px 40px rgba(0,0,0,.25)}30%{box-shadow:0 0 0 4px #F07040,0 18px 40px rgba(240,112,64,.45)}}'+
    '.ss-gate{margin:18px 0 14px;padding:22px 20px;z-index:2;box-shadow:0 18px 40px rgba(0,0,0,.25);border-radius:16px;background:linear-gradient(160deg,#241a14,#171310);color:#f0ede6;font-family:Pretendard,-apple-system,sans-serif;position:relative;overflow:hidden}'+
    '.ss-gate:before{content:"";position:absolute;left:0;right:0;top:-60px;height:60px;background:linear-gradient(rgba(255,255,255,0),rgba(255,255,255,.9));pointer-events:none}'+
    '.ss-gate .k{font-size:12px;font-weight:800;letter-spacing:.08em;color:#F5A481}'+
    '.ss-gate h3{margin:6px 0 12px;font-size:19px;font-weight:900;line-height:1.4;color:#fff}'+
    '.ss-gate ol{margin:0 0 16px;padding:0;list-style:none;counter-reset:g}'+
    '.ss-gate li{counter-increment:g;display:flex;gap:10px;padding:8px 0;border-top:1px solid rgba(255,255,255,.08);font-size:14.5px;line-height:1.5;color:#e8e3da}'+
    '.ss-gate li:before{content:"🔒";flex:0 0 auto;font-size:13px;opacity:.8}'+
    '.ss-gate .go{display:flex;align-items:center;justify-content:center;height:50px;border-radius:999px;background:#F07040;color:#12100e;font-weight:900;font-size:15.5px;text-decoration:none;position:relative;overflow:hidden}'+
    '.ss-gate .sm{display:block;text-align:center;margin-top:9px;font-size:12px;color:#a39c90}';
  d.head.appendChild(css);
  function apply(){
    var root=isHome?d.getElementById('nlwrap'):d;if(!root||root.querySelector('.ss-gate'))return;
    var st=[].slice.call(root.querySelectorAll('.story'));if(st.length<=FREE)return;
    var last=st[FREE-1],locked=st.slice(FREE);
    var titles=locked.map(function(s){var t=s.querySelector('.story-title');return t?t.textContent.replace(/🔗\s*공유\s*$/,'').trim():''}).filter(Boolean);
    var g=d.createElement('div');g.className='ss-gate';
    var nx=L.pathname+(L.hash&&/^#story-\d+$/.test(L.hash)?L.hash:'');
    g.innerHTML='<div class="k">🔒 순살러 전용</div><h3>오늘 브리핑 나머지 '+locked.length+'개 스토리, 로그인하면 바로 이어서</h3>'+
      '<ol>'+titles.map(function(t){return '<li>'+t.replace(/[<>&]/g,'')+'</li>'}).join('')+'</ol>'+
      '<a class="go ss-shine" href="/account/?next='+encodeURIComponent(nx)+'" data-gate-login>1초 로그인하고 이어 읽기</a>'+
      '<span class="sm">무료 · 로그인하면 스크랩·답글 알림도 받아요</span>';
    last.parentNode.insertBefore(g,last.nextSibling);
    // 벽 뒤: 잠긴 스토리 앞 2개는 흐린 미리보기(.ss-blur), 그 뒤 스토리·딜딜딜·헤드라인·단어 등은 숨김(.ss-locked).
    //   숨김은 벽에서 위로 올라가며 각 층의 뒤 형제를 — 뉴스레터 본문 상자(.wrapper, 홈은 #nlwrap) 「안」까지만.
    //   (10/26 버그: 상자 자신의 뒤 형제까지 숨겨 홈의 「전체 보기」·아카이브가 통째로 사라졌다 → 상자 경계에서 멈춤)
    var stop=isHome?root:(d.querySelector('.wrapper')||d.body),keep=/ss-legal|footer|ss-notice|ss-gate/;
    locked.forEach(function(s,i){s.classList.add(i<2?'ss-blur':'ss-locked')});
    for(var lv=g;lv&&lv!==stop;lv=lv.parentNode){
      for(var n=lv.nextElementSibling;n;n=n.nextElementSibling){
        if(n.classList.contains('ss-blur')||n.classList.contains('story')||keep.test(n.className||'')||/^(FOOTER|SCRIPT|STYLE)$/.test(n.tagName))continue;
        n.classList.add('ss-locked')}}
    if(/^#story-\d+$/.test(L.hash)&&locked.some(function(s){return '#'+s.id===L.hash}))setTimeout(function(){g.scrollIntoView({block:'center'})},300);
    send('gate');
    g.querySelector('[data-gate-login]').addEventListener('click',function(){send('gate_login')});
  }
  if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',apply);else apply();
  setTimeout(apply,1500);   // soonsal.js 가 스토리를 다시 그리는 경우 대비(이미 있으면 그냥 끝)
})();
