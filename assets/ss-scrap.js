
/* 스토리 스크랩 ☆ — 로그인 전엔 이 브라우저(ss_scrap), 로그인(ss_auth=1)이면 계정에 저장 (KD 2026-10-07) */
(function(){
  var API='https://api.soonsal.com';
  function ls(k,d){try{return JSON.parse(localStorage.getItem(k)||'')||d}catch(e){return d}}
  function save(o){try{localStorage.setItem('ss_scrap',JSON.stringify(o))}catch(e){}}
  var authed=false;try{authed=localStorage.getItem('ss_auth')==='1'}catch(e){}
  var stories=document.querySelectorAll('.story[data-ss-story]');
  if(!stories.length)return;
  var css=document.createElement('style');
  css.textContent='.ss-scrap{display:inline-block;margin:-7px 0 15px 10px;font-size:11px;color:#9a958a;background:none;'+
    'border:0;cursor:pointer;font-family:inherit;padding:0}.ss-scrap.on{color:#E55A00;font-weight:700}'+
    '.ss-scrap:hover{color:#E55A00;text-decoration:underline}';
  document.head.appendChild(css);
  var mine=ls('ss_scrap',{});
  function paint(b,on){b.classList.toggle('on',on);b.textContent=on?'★ 스크랩함':'☆ 스크랩';b.setAttribute('aria-pressed',on)}
  function hint(){if(authed||sessionStorage.getItem('ss_scrap_hint'))return;try{sessionStorage.setItem('ss_scrap_hint','1')}catch(e){}
    var d=document.createElement('div');d.style.cssText='position:fixed;left:50%;bottom:84px;transform:translateX(-50%);background:#222;'+
    'color:#fff;padding:10px 14px;border-radius:10px;font-size:13px;z-index:99999;max-width:90%';
    d.innerHTML='이 브라우저에 스크랩했어요. <a href="/account/" style="color:#F59B75">로그인</a>하면 폰·PC에서 같이 봐요';
    document.body.appendChild(d);setTimeout(function(){d.remove()},4200)}
  [].forEach.call(stories,function(el){
    var key=el.getAttribute('data-ss-story');var anchor=el.querySelector('.ss-story-permalink');
    var b=document.createElement('button');b.type='button';b.className='ss-scrap';paint(b,!!mine[key]);
    b.onclick=function(){var on=!b.classList.contains('on');paint(b,on);
      if(on)mine[key]=Math.floor(Date.now()/1000);else delete mine[key];save(mine);
      if(authed)fetch(API+'/me/scrap',{method:'POST',credentials:'include',headers:{'content-type':'application/json'},
        body:JSON.stringify({story:key,on:on})}).then(function(r){if(r.status===401){try{localStorage.removeItem('ss_auth')}catch(e){}}});
      else if(on)hint();};
    if(anchor)anchor.insertAdjacentElement('afterend',b);else el.insertBefore(b,el.firstChild);
  });
})();
