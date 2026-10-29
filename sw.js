/* 순살 앱 알림 전용 서비스 워커 — 페이지 캐시 없음(fetch 처리기 없음). scripts/build_pwa.py 가 만든다. */
var API='https://api.soonsal.com';
self.addEventListener('install',function(){self.skipWaiting()});
self.addEventListener('activate',function(e){e.waitUntil(self.clients.claim())});
self.addEventListener('push',function(e){e.waitUntil((async function(){
  var m=null;
  try{var s=await self.registration.pushManager.getSubscription();
    var r=await fetch(API+'/push/latest?ep='+encodeURIComponent(s?s.endpoint:''),{cache:'no-store'});m=await r.json()}catch(x){}
  if(!m||!m.title)m={title:'🐟 순살브리핑',body:'오늘의 순살이 도착했어요',url:'/?src=push',tag:'soonsal',badge:0};
  try{if(m.badge&&self.navigator.setAppBadge)await self.navigator.setAppBadge(m.badge)}catch(x){}
  await self.registration.showNotification(m.title,{body:m.body,icon:'/assets/app/icon-192.png',tag:m.tag||'soonsal',renotify:true,data:{url:m.url||'/?src=push'}});
})())});
self.addEventListener('notificationclick',function(e){e.notification.close();
  var u=new URL((e.notification.data&&e.notification.data.url)||'/?src=push',self.location.origin).href;
  e.waitUntil(self.clients.matchAll({type:'window',includeUncontrolled:true}).then(function(ws){
    for(var i=0;i<ws.length;i++){if('focus' in ws[i]){return ws[i].navigate(u).then(function(w){return (w||ws[i]).focus()}).catch(function(){return self.clients.openWindow(u)})}}
    return self.clients.openWindow(u)}))});
