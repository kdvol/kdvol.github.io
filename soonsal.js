/* soonsal.js — 전 페이지 공용 위젯(플로팅 텔레그램 버튼 + 스토리 공유).
 * 페이지엔 <script src="/soonsal.js" defer> 한 줄만. 동작 변경은 이 파일만 고치면
 * 전 페이지에 즉시 반영 — 페이지마다 재주입할 필요 없음. */
(function () {
  if (window.__ssWidgets) return;
  window.__ssWidgets = 1;

  var CSS =
    ':root{--ss-r:999px;--ss-fill:#C24A00;--ss-fill-h:#A83F00;--ss-accent:#F07040;--ss-ink:#1F1D1A;--ss-line:#DCD7CB;--ss-mute:#8a8578}' +
    '.ss-fab{position:fixed;right:16px;bottom:16px;z-index:9999;width:54px;height:54px;overflow:visible;' +
    'border-radius:50%;background:#F07040;box-shadow:0 4px 14px rgba(0,0,0,.35);display:flex;' +
    'align-items:center;justify-content:center;text-decoration:none;font-size:26px;line-height:1;' +
    'transition:transform .15s}.ss-fab:hover,.ss-fab:active{transform:scale(1.08)}' +
    '@media(min-width:640px){.ss-fab{width:58px;height:58px;right:24px;bottom:24px;font-size:28px}}' +
    '.ss-pageshare{position:fixed;left:16px;bottom:16px;z-index:9999;background:var(--ss-ink);color:#fff;border:none;' +
    'border-radius:var(--ss-r);padding:12px 22px;font-size:14px;font-weight:800;cursor:pointer;font-family:inherit;' +
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
    '.ss-preview{background:#f4f5f7;border-radius:12px;padding:12px 14px;margin-bottom:12px}' +
    '.ss-pt{font-weight:700;font-size:.92rem;line-height:1.4}' +
    '.ss-ps{color:#66707d;font-size:.82rem;line-height:1.5;margin-top:5px}' +
    '.ss-cm{width:100%;border:1px solid #d8dbe0;border-radius:12px;padding:10px 12px;font-size:.9rem;' +
    'font-family:inherit;resize:none;box-sizing:border-box}.ss-cm:focus{outline:none;border-color:#F07040}' +
    '.ss-row{display:flex;gap:8px;margin-top:12px}.ss-row button{flex:1;padding:12px;border-radius:12px;' +
    'border:none;font-size:.95rem;font-weight:700;cursor:pointer;font-family:inherit}' +
    '.ss-cancel{background:#eceef1;color:#555}.ss-go{background:#F07040;color:#fff}' +
    '@media(min-width:640px){.ss-modal-bg{align-items:center}.ss-modal{border-radius:16px}}' +
    /* 스토리별 반응 버튼 */
    '.ss-react{display:flex;gap:8px;margin:14px 0 4px;flex-wrap:wrap;align-items:center}' +
    /* 반응 3개는 한 덩어리로 — 자기들끼리 줄바꿈되지 않게 */
    '.ss-rg{display:flex;gap:8px;flex-wrap:nowrap}' +
    '.ss-rb{background:transparent;border:1px solid var(--ss-line);color:var(--ss-mute);border-radius:var(--ss-r);' +
    'padding:5px 13px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;' +
    'transition:border-color .15s,background .15s,color .15s;line-height:1.5;white-space:nowrap;' +
    'flex:0 0 auto}' +
    '.ss-rb:hover{border-color:#F07040;color:#F07040}' +
    '.ss-rb.on{border-color:#F07040;background:#F0704014;color:#F07040}' +
    /* 숫자 자리를 미리 비워둔다 — 눌러서 카운트가 생겨도 버튼 폭이 안 변함 */
    '.ss-rb b{font-weight:700;margin-left:3px;display:inline-block;min-width:8px;text-align:left}' +
    /* 누른 순간 — 버튼이 한 번 튀고 조각이 흩어진다 */
    '.ss-rb.pop{animation:ss-pop 420ms cubic-bezier(.34,1.56,.64,1)}' +
    '@keyframes ss-pop{0%{transform:scale(1)}38%{transform:scale(1.22)}100%{transform:scale(1)}}' +
    '.ss-burst{position:fixed;z-index:2147483000;pointer-events:none;width:0;height:0}' +
    '.ss-burst span{position:absolute;left:0;top:0;font-size:19px;line-height:1;' +
    'will-change:transform,opacity;animation:ss-fly 900ms cubic-bezier(.15,.7,.3,1) forwards}' +
    '.ss-burst span.d{width:9px;height:9px;border-radius:50%;background:#F07040}' +
    '.ss-burst span.d:nth-child(6n){background:#E55A00}' +
    '.ss-burst span.d:nth-child(9n){background:#F5A481}' +
    '@keyframes ss-fly{0%{transform:translate(-50%,-50%) scale(.4);opacity:0}' +
    '18%{opacity:1}' +
    '100%{transform:translate(calc(-50% + var(--x)),calc(-50% + var(--y) + 26px)) ' +
    'scale(1) rotate(var(--r));opacity:0}}' +
    '@media(prefers-reduced-motion:reduce){.ss-rb.pop{animation:none}.ss-burst{display:none}}' +
    /* 완주 — 끝까지 읽은 사람에게만 보이는 자리 */
    '.ss-conf{position:fixed;inset:0;z-index:2147483000;pointer-events:none;overflow:hidden}' +
    '.ss-conf span{position:absolute;top:-8vh;font-size:22px;line-height:1;' +
    'will-change:transform,opacity;' +
    'animation:ss-fall var(--dur) cubic-bezier(.35,.1,.5,1) forwards}' +
    '.ss-conf span.d{width:11px;height:11px;border-radius:2px;background:#F07040}' +
    '.ss-conf span.d:nth-child(5n){background:#E55A00}' +
    '.ss-conf span.d:nth-child(7n){background:#F5A481}' +
    '@keyframes ss-fall{0%{transform:translate(0,0) rotate(0);opacity:0}' +
    '8%{opacity:1}85%{opacity:1}' +
    '100%{transform:translate(var(--sway),112vh) rotate(var(--r));opacity:0}}' +
    '@media(prefers-reduced-motion:reduce){.ss-conf{display:none}}' +
    '.ss-home{display:inline-block;cursor:pointer;border-radius:var(--ss-r);' +
    'transition:opacity .18s ease,transform .18s ease}' +
    '.ss-home:hover{opacity:.72;transform:translateY(-1px)}' +
    '.ss-home:focus-visible{outline:2px solid #F07040;outline-offset:3px}' +
    '.ss-fin{margin:26px 0 8px;padding:17px 19px;border-radius:12px;text-align:center;' +
    'background:linear-gradient(135deg,#F0704016,#F0704006);border:1px solid #F0704040;' +
    'opacity:0;transform:translateY(10px);transition:opacity .5s ease,transform .5s cubic-bezier(.2,.9,.3,1)}' +
    '.ss-fin.in{opacity:1;transform:none}' +
    '.ss-fin b{display:block;font-size:15px;font-weight:800;color:var(--ss-fill);letter-spacing:-.02em}' +
    '.ss-fin span{display:block;margin-top:4px;font-size:12px;color:#8a8578}' +
    '.ss-fin a{display:inline-block;margin-top:11px;font-size:12px;font-weight:700;' +
    'color:#F07040;text-decoration:none}' +
    '.ss-fin a:hover{text-decoration:underline}' +
    '@media(prefers-reduced-motion:reduce){.ss-fin{opacity:1;transform:none;transition:none}}' +
    /* 좁은 화면(375px 기준)에선 4개가 한 줄에 안 들어가 공유는 아이콘만 */
    /* 좁은 화면(375px 가용폭 311px)에 반응3+코멘트+공유 5개를 한 줄에 넣는다.
       아이콘만 남기고, 코멘트 pill은 카운트가 없을 때 예약 폭도 뺀다.
       반응 버튼의 예약 폭은 그대로 둔다 — 눌렀을 때 폭이 변하면 정렬이 흔들린다. */
    '@media(max-width:430px){.ss-react{gap:5px}.ss-rg{gap:5px}' +
    '.ss-rb{padding:5px 9px;font-size:11px}.ss-sh .lb,.ss-cbtn .lb{display:none}' +
    '.ss-sh,.ss-cbtn{padding:5px 8px}.ss-cbtn b:empty{display:none}}' +
    /* 오늘의 논점 블록 */
    /* 3월 재개호 브랜드 팔레트: 주황 #F07040/#E55A00, 크림 #fafaf7, 보더 #e8e8e0 */
    '.ss-talk{margin:26px 0 8px;padding:20px 22px;border:1px solid #e8e8e0;border-radius:12px;' +
    "background:#fafaf7;font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif}" +
    '.ss-talk-h{font-size:12px;font-weight:700;color:#F07040;letter-spacing:.06em;margin-bottom:10px}' +
    '.ss-talk-q{font-size:15px;line-height:1.7;color:#333;margin-bottom:16px;font-weight:600}' +
    '.ss-talk-btns{display:flex;gap:8px;flex-wrap:wrap}' +
    '.ss-talk-b{display:inline-flex;align-items:center;background:var(--ss-fill);color:#fff;' +
    'text-decoration:none;padding:12px 22px;border-radius:var(--ss-r);font-size:14px;font-weight:800;' +
    'border:1px solid var(--ss-fill);transition:background .18s,color .18s,border-color .18s}' +
    '.ss-talk-b:hover{background:var(--ss-fill-h);border-color:var(--ss-fill-h)}' +
    '.ss-talk-b.ig{background:transparent;color:var(--ss-fill);border-color:var(--ss-line)}' +
    '.ss-talk-b.ig:hover{background:#fff;color:var(--ss-fill-h);border-color:var(--ss-accent)}' +
    /* 반응 버튼도 같은 크림/주황 톤으로 */
    '.ss-rb{border-color:#e0ddd5;color:#8a8578}' +
    '.ss-rb:hover{border-color:#F07040;color:#E55A00}' +
    '.ss-rb.on{border-color:#F07040;background:#F0704012;color:#E55A00}' +
    /* 수집 안내 */
    '.ss-notice{text-align:center;font-size:11px;color:#9a958a;line-height:1.7;padding:14px 16px 18px;font-family:inherit}' +
    '.ss-notice a{color:#9a958a;text-decoration:underline}' +
    // 눈에 최대한 안 띄게. 본문보다 두 톤 아래로 두고, 사업자 정보는 접는다.
    '.ss-legal{max-width:600px;margin:10px auto 0;font-size:10.5px;' +
      'line-height:1.85;color:#6a655c}' +
    '.ss-legal a{color:inherit;text-decoration:underline;text-underline-offset:2px}' +
    '.ss-legal .bz{white-space:nowrap}' +
    /* 코멘트 */
    '.ss-cbtn{margin-left:0}' +
    // 폰에서 쓰기 편한 게 최우선. 입력창을 크게 잡고, 나머지는 눌러야 나온다.
    // 글자 크기 16px 미만이면 iOS가 포커스 때 화면을 확대해 버린다.
    '.ss-cwrap{margin:10px 0 4px;font-family:inherit;background:#fff;border:1px solid #F0C4AC;' +
    'border-radius:12px;padding:12px 13px;box-shadow:0 1px 3px rgba(0,0,0,.03)}' +
    '.ss-chd{display:flex;align-items:center;margin-bottom:9px;font-size:12px;color:#8a8578}' +
    '.ss-cx{margin-left:auto;background:none;border:none;color:#b5b0a4;font-size:13px;' +
    'cursor:pointer;font-family:inherit;padding:2px 4px;line-height:1}' +
    '.ss-cx:hover{color:#6b6659}' +
    '.ss-cin{width:100%;border:1px solid #ece8de;border-radius:12px;padding:12px 13px;' +
    'font-size:16px;line-height:1.55;font-family:inherit;box-sizing:border-box;resize:none;' +
    'background:#fff;color:#2b2b2b;-webkit-appearance:none}' +
    '.ss-cin::placeholder{color:#b5b0a4}' +
    '.ss-cin:focus{outline:none;border-color:#F07040;box-shadow:0 0 0 3px rgba(240,112,64,.10)}' +
    '.ss-crow{display:flex;gap:8px;align-items:center;margin-top:8px}' +
    // 이름 + 업종을 한 버튼에. 평소엔 그냥 글씨처럼 보이고 누르면 편집이 열린다.
    '.ss-cprof{flex:1 1 auto;min-width:0;background:none;border:none;padding:5px 0;' +
    'font-family:inherit;font-size:13px;color:#6b6659;cursor:pointer;text-align:left;' +
    'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:flex;' +
    'align-items:baseline;gap:5px}' +
    '.ss-cprof .nm{font-weight:700;color:#3a3a3a;border-bottom:1px dashed #c4bfb2;' +
    'padding-bottom:1px}' +
    '.ss-cprof i{font-style:normal;color:#a8a294;font-size:12px;flex:0 1 auto;' +
    'overflow:hidden;text-overflow:ellipsis}' +
    '.ss-cprof em{font-style:normal;color:#F07040;font-size:11px;background:#fdf0e9;' +
    'border-radius:5px;padding:2px 6px;white-space:nowrap;flex:0 0 auto}' +
    '.ss-cprof:hover .nm{border-bottom-color:#F07040}' +
    '.ss-cnt{font-size:12px;color:#c0bcb2;font-variant-numeric:tabular-nums;flex:0 0 auto}' +
    '.ss-cgo{flex:0 0 auto;background:#E55A00;color:#fff;border:none;border-radius:12px;' +
    'padding:11px 20px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit;' +
    'min-height:42px;-webkit-appearance:none}' +
    '.ss-cgo:disabled{background:#e8e4da;color:#b0aca2;cursor:default}' +
    // 프로필 — 눌러야 열리고, 한 줄에 라벨+입력이 나란히 붙어 자리를 덜 먹는다
    '.ss-cpf{margin-top:10px;padding:12px 13px;background:#faf8f3;border-radius:12px;' +
    'display:flex;flex-direction:column;gap:9px}' +
    // display를 지정하면 [hidden]의 기본 display:none을 이겨 버린다. 명시해야 접힌다.
    '.ss-cpf[hidden],.ss-crt[hidden],.ss-cpl[hidden]{display:none}' +
    '.ss-cpl{display:flex;align-items:center;gap:10px;font-size:12px;color:#8a8578}' +
    '.ss-cpl input,.ss-cpl select{flex:1;min-width:0;border:1px solid #e6e1d5;border-radius:8px;' +
    'padding:9px 10px;font-size:16px;font-family:inherit;background:#fff;color:#2b2b2b;' +
    '-webkit-appearance:none}' +
    '.ss-cpl input:focus,.ss-cpl select:focus{outline:none;border-color:#F07040}' +
    '.ss-csc{display:flex;align-items:center;gap:7px;font-size:12px;color:#8a8578}' +
    '.ss-cpn{font-size:11px;color:#b5b0a4}' +
    // 목록 — 줄마다 선을 긋지 않는다. 간격만으로 나눈다.
    '.ss-clist{margin-top:14px;display:flex;flex-direction:column;gap:2px}' +
    '.ss-ci{display:flex;gap:9px;padding:9px 0;font-size:14px}' +
    '.ss-crep{padding-left:26px;position:relative}' +
    '.ss-crep:before{content:"";position:absolute;left:13px;top:0;bottom:0;width:1.5px;' +
    'background:#eceae2}' +
    '.ss-av{flex:0 0 auto;width:30px;height:30px;border-radius:50%;display:flex;' +
    'align-items:center;justify-content:center;font-size:12px;font-weight:800;color:#3a3a3a;' +
    'letter-spacing:-.02em}' +
    '.ss-crep .ss-av{width:25px;height:25px;font-size:11px}' +
    '.ss-cbd{flex:1;min-width:0}' +
    '.ss-cnm{display:flex;align-items:baseline;gap:5px;flex-wrap:wrap;line-height:1.3}' +
    '.ss-cnm b{font-weight:700;color:#2b2b2b;font-size:13px}' +
    '.ss-cbx{color:#3a3a3a;font-size:14px;line-height:1.62;margin-top:2px;word-break:break-word}' +
    '.ss-cbx .ss-at{color:#8a857c;font-weight:600}' +
    '.ss-ct{color:#b5b0a4;font-size:11px}' +
    '.ss-cg{font-size:10px;color:#8a8578;background:#f2efe7;border-radius:4px;padding:1px 6px}' +
    '.ss-chold{font-size:10px;color:#c08a3a;margin-left:6px}' +
    '.ss-cop .ss-cnm b{color:#E55A00}' +
    '.ss-cob{font-size:9px;font-weight:700;color:#fff;background:#E55A00;border-radius:4px;' +
    'padding:1px 6px}' +
    '.ss-cob.bot{background:#5a6b7a}' +
    // 액션 — 탭 영역을 넉넉히. 모바일에서 작은 글씨는 누르기 어렵다.
    '.ss-cact{display:flex;gap:2px;margin:3px 0 0 -8px}' +
    '.ss-cact button{display:flex;align-items:center;gap:4px;background:none;border:none;' +
    'padding:6px 8px;font-size:12px;color:#a8a294;cursor:pointer;font-family:inherit;' +
    'border-radius:12px;min-height:30px;transition:background .15s,color .15s}' +
    '.ss-cact button:hover{background:#f4f1ea;color:#6b6659}' +
    '.ss-clike.on{color:var(--ss-fill);font-weight:700}' +
    '.ss-crt{display:flex;align-items:center;gap:8px;font-size:12px;color:#6b6659;' +
    'background:#f7f4ec;border-radius:8px;padding:7px 10px;margin-bottom:7px}' +
    '.ss-crt button{background:none;border:none;color:#a8a294;font-size:11px;cursor:pointer;' +
    'font-family:inherit;margin-left:auto;padding:2px 4px}' +
    // 안내문은 입력 중에만
    // 쓰는 자리 — 버튼이 아니라 입력칸처럼 보이고, 펼치면 한 덩어리로 이어진다.
    // 아래 두 규칙은 스쿨 안내 개편 때 함께 빠졌지만 마크업은 계속 사용 중이다.
    '.ss-cbar{display:flex;align-items:center;gap:9px;width:100%;margin:10px 0 2px;' +
    'padding:12px 14px;background:#fff;border:1px solid #e4e0d6;border-radius:12px;' +
    'font-family:inherit;font-size:13px;color:#6b6659;cursor:pointer;text-align:left;' +
    'transition:border-color .15s,box-shadow .15s}' +
    '.ss-cbar[hidden]{display:none}' +
    '.ss-cbar:hover{border-color:#F07040;box-shadow:0 0 0 3px rgba(240,112,64,.08)}' +
    '.ss-cbar .ic{flex:0 0 auto;font-size:15px;line-height:1}' +
    '.ss-cbar .tx{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
    '.ss-cbar .tx.ph{color:#a8a294}' +
    '.ss-cbar .tx b{color:var(--ss-fill);font-weight:700}' +
    '.ss-cbar .tx i{font-style:normal;color:#6b6659}' +
    '.ss-cbar .cta{flex:0 0 auto;font-size:11px;font-weight:700;color:var(--ss-fill);' +
    'background:#fdf0e9;border-radius:6px;padding:5px 10px}' +
    '.ss-call{display:block;text-align:center;margin-top:12px;padding:9px;font-size:12px;' +
    'color:#8a8578;border:1px solid #ece8de;border-radius:12px;text-decoration:none}' +
    '.ss-call:hover{color:var(--ss-fill);border-color:#E55A00}' +
    // 뉴스레터 끝에 붙는 클래스 안내. 본문과 톤이 같으면 안 보이고,
    // 광고처럼 보이면 안 누른다. 카드 하나에 숫자·자격·행동만 남긴다.
    '.ss-sch{position:relative;margin:36px auto 10px;max-width:640px;' +
    'background:linear-gradient(158deg,#241a14,#171310);border-radius:16px;' +
    'padding:24px 22px 22px;color:#f0ede6;overflow:hidden}' +
    '.ss-sch:before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;' +
    'background:linear-gradient(180deg,#F07040,#E55A00)}' +
    '.ss-sch .t{font-size:11px;font-weight:800;letter-spacing:.1em;color:#F5A481;' +
    'text-transform:uppercase;margin-bottom:10px}' +
    '.ss-sch .h{font-size:19px;font-weight:700;line-height:1.42;letter-spacing:-.02em;' +
    'color:#f5f2ea;margin-bottom:9px}' +
    '.ss-sch .h b{font-size:26px;font-weight:800;letter-spacing:-.035em;' +
    'font-variant-numeric:tabular-nums;color:#fff}' +
    '.ss-sch .w{font-size:12px;color:#9a9488;margin-bottom:17px;line-height:1.6}' +
    '.ss-sch .cta{display:block;text-align:center;background:var(--ss-fill);color:#fff;' +
    'text-decoration:none;font-size:15px;font-weight:800;letter-spacing:-.01em;' +
    'border-radius:12px;padding:15px;transition:background .15s}' +
    '.ss-sch .cta:hover{background:#F07040}' +
    '.ss-sch .x{position:absolute;top:12px;right:12px;background:none;border:none;' +
    'color:#5f5a52;font-size:13px;cursor:pointer;font-family:inherit;padding:4px 6px;' +
    'line-height:1}' +
    '.ss-sch .x:hover{color:#9a9488}' +
    '@media(max-width:560px){' +
    '.ss-sch{padding:21px 18px 19px;margin:30px auto 10px}' +
    '.ss-sch .h{font-size:17px}.ss-sch .h b{font-size:23px}' +
    '.ss-sch .cta{font-size:14.5px;padding:14px}}' +
    '.ss-notice{text-align:center;padding:14px 16px 4px}' +
    '.ss-notice .go{display:inline-block;color:var(--ss-fill);font-weight:700;font-size:13px;' +
    'text-decoration:none;border:1px solid #f0d9c8;border-radius:20px;padding:8px 16px}' +
    '.ss-notice .go:hover{background:#FFF3EC}' +
    '.ss-notice .fine{display:block;color:#b5b0a4;font-size:10.5px;margin-top:9px;line-height:1.6}' +
    '.ss-notice .fine a{color:#a8a294}' +
    '.ss-legal{color:#b0aba0}' +
    '.ss-cnote{color:#b5b0a4;font-size:11px;line-height:1.65;margin-top:9px;display:none}' +
    '.ss-cwrap.on .ss-cnote{display:block}' +
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

  // ?ss=agent 를 한 번 열면 이 브라우저는 영구히 집계에서 빠진다.
  // 개발·검증용 브라우저(사람이 아닌 접속)를 위한 스위치다. 자동 감지가 안 되니
  // 명시적으로 표시한다 — 서버가 'agent-' 접두사를 무조건 무시한다.
  try {
    if (/[?&]ss=agent\b/.test(location.search)) {
      var cur = localStorage.getItem('ss_vid') || '';
      // 이미 표시된 브라우저에서 또 열어도 접두사가 겹쳐 붙지 않게 한다
      if (!/^agent-/.test(cur)) {
        localStorage.setItem('ss_vid', ('agent-' + (cur || 'x')).slice(0, 32));
      }
      localStorage.setItem('ss_optout', '1');
    }
  } catch (e) {}

  function vid() {
    try {
      var v = localStorage.getItem(VID_KEY);
      // 하이픈 허용 — 서버 VID_RE와 같아야 한다. 여기서 걸러내면 ?ss=agent가
      // 심어둔 'agent-...' 표식을 다음 호출에서 지우고 새로 만들어 버린다.
      if (!v || !/^[a-z0-9-]{8,32}$/.test(v)) {
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

  // 직전에 본 페이지 — 이동 쌍 집계용. 세션 저장소라 탭을 닫으면 사라지고,
  // 서버에는 경로 쌍만 올라간다(누가 이동했는지는 남기지 않는다).
  function prevPath() {
    try { return sessionStorage.getItem('ss_pv') || ''; } catch (e) { return ''; }
  }
  function setPrevPath(p) { try { sessionStorage.setItem('ss_pv', p); } catch (e) {} }

  // 타임아웃 없는 fetch는 모바일에서 그대로 매달린다. 화면이 '불러오는 중'에
  // 갇히느니 끊고 없는 대로 그리는 편이 낫다.
  function tfetch(url, opts, ms) {
    opts = opts || {};
    var ctl = typeof AbortController !== 'undefined' ? new AbortController() : null;
    if (ctl) opts.signal = ctl.signal;
    var timer = setTimeout(function () { if (ctl) ctl.abort(); }, ms || 10000);
    return fetch(url, opts).then(function (r) {
      clearTimeout(timer); return r;
    }, function (e) { clearTimeout(timer); throw e; });
  }

  // 구독 버튼은 이 사이트의 유일한 전환점인데 클릭을 재지 않고 있었다.
  // 방문이 늘어도 구독으로 이어지는지 알 길이 없었다 (KD 2026-08-16).
  function watchSubscribe() {
    var els = document.querySelectorAll('a[href*="subscribe.soonsal.com"]');
    for (var i = 0; i < els.length; i++) {
      (function (el) {
        if (el.__ssSub) return;
        el.__ssSub = 1;
        el.addEventListener('click', function () { track('subscribe'); });
      })(els[i]);
    }
  }

  function track(kind) {          // read / react / share / telegram / instagram / comment
    if (optedOut()) return;
    var v = vid();
    if (v) beacon({ t: 'ev', v: v, k: kind });
  }

  function trackTopic(kind, story, ms) {
    if (!story || optedOut() || navigator.webdriver) return;
    var key = typeof story === 'string' ? story : storyKey(story);
    if (!/^m\d{8}-[a-z0-9]+(?:-[a-z0-9]+)*$/.test(key || '')) return;
    var v = vid();
    if (!v) return;
    beacon({ t: 'topic', v: v, topic: key, k: kind,
             ms: Math.max(0, Math.min(Number(ms) || 0, 1800000)), r: refSrc() });
  }

  // 토픽별 읽기 신호. 서버에는 토픽·집계 종류·밀리초만 남고 개인별 열람 이력은
  // 만들지 않는다. unique는 Worker가 토픽별 비가역 서명으로 바꾼다.
  function mountTopicTracking() {
    if (!API || !window.IntersectionObserver || navigator.webdriver || optedOut()) return;
    var topics = document.querySelectorAll('.story[data-ss-story^="m"]');
    if (!topics.length) return;
    var state = {};

    function row(el) {
      var key = storyKey(el);
      if (!state[key]) state[key] = { key: key, impression: false, view: false,
                                      timer: null, started: 0 };
      return state[key];
    }
    function stop(s) {
      if (s.timer) { clearTimeout(s.timer); s.timer = null; }
      if (s.started) {
        var elapsed = Date.now() - s.started;
        s.started = 0;
        if (elapsed >= 1000) trackTopic('dwell', s.key, elapsed);
      }
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var s = row(entry.target);
        if (entry.isIntersecting && entry.intersectionRatio > 0 && !s.impression) {
          s.impression = true;
          trackTopic('impression', s.key);
        }
        if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {
          if (!s.started) s.started = Date.now();
          if (!s.view && !s.timer) {
            s.timer = setTimeout(function () {
              s.timer = null;
              s.view = true;
              trackTopic('view', s.key);
            }, 1000);
          }
        } else {
          stop(s);
        }
      });
    }, { threshold: [0, 0.5] });

    for (var i = 0; i < topics.length; i++) observer.observe(topics[i]);
    window.addEventListener('pagehide', function () {
      Object.keys(state).forEach(function (key) { stop(state[key]); });
    });
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) Object.keys(state).forEach(function (key) { stop(state[key]); });
    });
  }

  // 이 브라우저를 집계에서 뺀다 (/stats/의 '내 방문 빼기' 버튼이 세운다).
  // 운영자가 하루에 몇 번씩 확인하는 방문이 지표를 부풀리는 걸 막는 용도.
  function optedOut() {
    try { return localStorage.getItem('ss_optout') === '1'; } catch (e) { return false; }
  }

  // ── 정말 사람이 눌렀나 (KD 2026-08-16) ─────────────────────────────
  //   대기업 메일 보안이 링크를 미리 눌러 본다. 이메일 솔루션의 클릭률에
  //   허수가 많은 이유다. 우리 쪽 판정인 `read`(70% 스크롤 또는 45초 체류)도
  //   스캐너가 페이지를 열어 두면 그대로 켜진다 — 실제로 read 가 조회의 61%다.
  //
  //   기계가 흉내내기 어려운 건 **손**이다. 마우스를 실제로 움직이거나,
  //   손가락으로 만지거나, 키를 누르는 것. 브라우저가 진짜 입력에만 붙여 주는
  //   isTrusted 를 같이 본다(합성 이벤트는 false).
  //   개인정보는 늘지 않는다 — "사람이었다"는 사실 하나만 남긴다.
  // ── 뉴스레터 링크의 구독자 표시 (KD 2026-08-16) ────────────────────
  //   메일 링크에 ?s=<일방향 처리값>&i=<회차> 가 붙어 온다. 이걸 그대로
  //   넘겨 "이 회차를 읽은 구독자 수"를 센다. 고지·동의를 갱신한 뒤에만 쓴다.
  //
  //   주소창에 남겨 두면 공유할 때 남의 표시가 따라간다. 읽고 나서 지운다.
  //   같은 이유로 세션에 넣어 두지 않는다 — 그 페이지 한 번에만 쓴다.
  function newsletterTag() {
    try {
      var q = new URLSearchParams(location.search);
      // ★ 파라미터를 **하나로** 받는다 (2026-08-16).
      //   전에는 ?s=…&i=… 였는데, 메일 HTML 에서 & 가 &amp; 로 이스케이프된 채
      //   그대로 나가 i 가 `amp;i` 로 잡혔다. 두 번째 값이 통째로 사라진다.
      //   & 를 안 쓰면 이 사고가 구조적으로 불가능하다.
      //     ?ss=<16자리>.<회차>
      var sv = '', iv = '';
      var one = (q.get('ss') || '').trim();
      if (one.indexOf('.') > 0) {
        sv = one.split('.')[0];
        iv = one.split('.').slice(1).join('.');
      } else {
        sv = (q.get('s') || '').trim();
        // &amp; 로 깨진 옛 링크도 살려서 받는다
        iv = (q.get('i') || q.get('amp;i') || '').trim();
      }
      if (!/^[a-f0-9]{16}$/.test(sv) || !/^[0-9a-z-]{3,12}$/.test(iv)) return {};
      // 주소창에서 지운다. 뒤로가기 기록도 남기지 않는다.
      q.delete('ss'); q.delete('s'); q.delete('i'); q.delete('amp;i');
      var rest = q.toString();
      history.replaceState(null, '', location.pathname + (rest ? '?' + rest : '') + location.hash);
      return { s: sv, i: iv };
    } catch (e) { return {}; }
  }

  function watchHuman() {
    var fired = false;
    function human(e) {
      if (fired || !e || e.isTrusted !== true) return;
      // 프로그램이 만든 pointermove 는 이동량이 0 인 경우가 많다
      if (e.type === 'pointermove' && !e.movementX && !e.movementY) return;
      fired = true;
      track('human');
      off();
    }
    var evs = ['pointermove', 'touchstart', 'keydown', 'wheel'];
    function off() {
      evs.forEach(function (n) { window.removeEventListener(n, human, true); });
    }
    evs.forEach(function (n) {
      window.addEventListener(n, human, { capture: true, passive: true });
    });
    // 30분이 지나도 손이 안 왔으면 사람이 아니었다고 본다
    setTimeout(off, 18e5);
  }

  function trackView() {
    if (!API) return;
    if (navigator.webdriver) return;                       // 자동화 브라우저 제외
    if (optedOut()) return;                                // 운영자 본인 브라우저
    if (/\/stats\//.test(location.pathname)) return;       // 운영자 화면은 집계 안 함
    var v = vid();
    if (!v) return;
    var path = location.pathname;
    var nl = newsletterTag();
  beacon({ t: 'hit', v: v, p: path, f: firstToday(path), r: refSrc(), pv: prevPath(),
           s: nl.s, i: nl.i });
  watchHuman();
    setPrevPath(path);

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
    // 뉴스레터 푸터에는 이미 순살톡 링크가 한 줄 위에 박혀 있다. 여기에 또
    // 큰 버튼을 얹으니 같은 곳으로 가는 길이 한 화면에 둘이었다.
    // 이미 있으면 안 붙인다 — 푸터가 아예 없는 생성 페이지에서만 길을 낸다.
    var hasTalk = !!document.querySelector('a[href$="/talk/"], a[href*="soonsal.com/talk/"]');
    // 뉴스레터 푸터에는 저작권 줄이 이미 있다. 또 넣으면 한 화면에 두 번 나온다.
    var hasCr = /©\s*\d{4}\s*순살브리핑/.test(document.body.textContent || '');
    // 사업자 정보는 접어 둔다. 필요한 사람은 펴서 보고, 읽으러 온 사람의
    // 눈에는 안 걸리게. 전화번호·통신판매업 신고번호는 확인 전이라 넣지 않았다 —
    // 틀린 번호를 싣는 건 안 싣는 것보다 나쁘다.
    // 줄을 늘리는 대신 가운뎃점으로 잇는다. 구분선도 뺐다 — 안 읽히는 글을
    // 칸까지 나눠 두면 그게 더 눈에 걸린다. 사업자 정보만 펼침으로 남긴다.
    var bits = [];
    if (!hasCr) bits.push('© ' + new Date().getFullYear() + ' (주)순살');
    // 매매 권유가 아니라는 줄은 원래 있었다. 의약·의료 소재를 자주 다루므로
    // 같은 자리에 한 줄 더 둔다 (KD 2026-08-16). 이건 민감정보 판단을 바꾸는
    // 장치가 아니라, 우리 글이 의학적 조언으로 읽히는 걸 막는 줄이다.
    bits.push('정보 제공 목적이며 매매 권유나 의학적 조언이 아닙니다');
    bits.push('쿠키 없이 익명 통계만 · <a href="/privacy/">수집 안내</a>');
    d.innerHTML = (hasTalk ? '' : '<a class="go" href="/talk/">💬 순살톡 — 순살러 한마디</a>') +
      '<p class="ss-legal">' + bits.join(' · ') +
        ' · <span class="biz"><a href="#" class="bz">사업자 정보</a>' +
        '<span class="bd" hidden> — (주)순살 · 대표 신기동 · ' +
        '사업자등록번호 120-88-27830 · 서울시 동작구 현충로 52 · ' +
        '<a href="mailto:team@soonsal.com">team@soonsal.com</a></span></span></p>';
    var bz = d.querySelector('.bz'), bd = d.querySelector('.bd');
    bz.addEventListener('click', function (e) {
      e.preventDefault();
      bd.hidden = !bd.hidden;
      bz.style.display = bd.hidden ? '' : 'none';
    });
    var f = null;
    var cands = document.querySelectorAll('.footer-inner, .footer');
    for (var fi = 0; fi < cands.length; fi++) {
      if (cands[fi].closest && cands[fi].closest('.nl')) continue;   // 심어 온 뉴스레터 안
      f = cands[fi];
    }
    (f || document.body).appendChild(d);
  }

  // ── 완주 ─────────────────────────────────────────────────
  // 폭죽만 터뜨리면 그 순간뿐이다. 쌓이는 게 있어야 내일 또 온다.
  // 서버는 안 쓴다 — 읽었다는 사실은 이 기기의 일이고, 그걸 서버에 보내려면
  // 사람을 식별해야 한다. 그럴 만큼 중요한 값이 아니다.
  function doneLog() {
    try { return JSON.parse(localStorage.getItem('ss_done') || '{}'); } catch (e) { return {}; }
  }
  function ymd(d) {
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }
  function streakOf(log) {
    var days = {}, k;
    for (k in log) if (log[k]) days[log[k]] = 1;
    var n = 0, d = new Date();
    if (!days[ymd(d)]) return 0;
    while (days[ymd(d)]) { n++; d.setDate(d.getDate() - 1); }
    return n;
  }

  function mountFinish() {
    var stories = document.querySelectorAll('.story');
    if (!stories.length || !('IntersectionObserver' in window)) return;
    var page = issueKey() || location.pathname;
    var log = doneLog();
    if (log[page]) return;                       // 한 회차는 한 번만

    // 마지막 스토리를 통째로 감시하면 안 된다. 스토리가 화면보다 크면
    // (실측 1036px vs 800px) 교차 비율이 영영 문턱을 못 넘는다.
    // 끝자락에 납작한 감시점을 두고 그게 보이는지만 본다.
    var last = stories[stories.length - 1];
    var mark = document.createElement('div');
    mark.setAttribute('aria-hidden', 'true');
    mark.style.cssText = 'height:1px;margin:0;padding:0';
    last.parentNode.insertBefore(mark, last.nextSibling);

    var opened = Date.now();
    var fired = false, queued = false;

    // 교차 감시만으로는 부족하다. 뉴스레터는 마지막 스토리 뒤에 순살톡·푸터가
    // 3,000px 더 붙어서, 맨 아래로 한 번에 내리면 감시점을 지나쳐 버린다.
    // '보였나'가 아니라 '여기까지 왔나'를 본다 — 지나친 것도 온 것이다.
    function check() {
      queued = false;
      if (fired) return;
      var top = mark.getBoundingClientRect().top;
      if (top > (window.innerHeight || 0)) return;      // 아직 도달 전
      // 훑어내린 것과 읽은 것은 다르다. 20초를 못 넘기면 읽었다고 보기 어렵다.
      if (Date.now() - opened < 20000) return;
      fired = true;
      window.removeEventListener('scroll', onScroll);
      log[page] = ymd(new Date());
      try { localStorage.setItem('ss_done', JSON.stringify(log)); } catch (e) {}
      showFinish(streakOf(log));
      track('finish');
    }
    function onScroll() {
      if (queued) return;
      queued = true;
      requestAnimationFrame(check);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    // 끝까지 읽고 20초를 채우는 중일 수 있다. 그 사이에도 한 번씩 본다.
    var tick = setInterval(function () {
      if (fired) { clearInterval(tick); return; }
      check();
    }, 4000);
  }

  // 완주는 반응 하나 누른 것과 무게가 다르다. 버튼 옆에서 조각 몇 개가
  // 튀는 걸로는 부족해서, 화면 위에서 쏟아진다.
  function confetti() {
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var host = document.createElement('div');
    host.className = 'ss-conf';
    var bits = ['🎉', '🎊', '✨', '🐟', '🥳'];
    for (var i = 0; i < 70; i++) {
      var s = document.createElement('span');
      var dot = i % 4 === 0;
      if (dot) s.className = 'd';
      else s.textContent = bits[i % bits.length];
      s.style.left = (Math.random() * 100) + 'vw';
      // 떨어지는 시간과 시작 시점을 흩어 놓아야 '쏟아진다'로 보인다
      s.style.setProperty('--dur', (2100 + Math.random() * 1700) + 'ms');
      s.style.setProperty('--sway', (Math.random() * 160 - 80) + 'px');
      s.style.setProperty('--r', (Math.random() * 1080 - 540) + 'deg');
      s.style.animationDelay = (Math.random() * 900) + 'ms';
      host.appendChild(s);
    }
    document.body.appendChild(host);
    setTimeout(function () { host.remove(); }, 5200);
  }

  function showFinish(streak) {
    var box = document.createElement('div');
    box.className = 'ss-fin';
    var line = streak > 1 ? streak + '일 연속 완주' : '오늘 순살 완주';
    box.innerHTML = '<b>' + line + '</b>'
      + '<span>' + (streak > 1 ? '내일도 오면 ' + (streak + 1) + '일' : '끝까지 읽었음 🐟') + '</span>'
      + '<a href="/chart/">지난 순살차트 →</a>';
    var anchor = document.querySelector('.memo-footer') || document.querySelector('footer');
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(box, anchor);
    else document.body.appendChild(box);
    requestAnimationFrame(function () {
      box.classList.add('in');
      confetti();
    });
  }

  // 뉴스레터는 메일 원본 그대로라 사이트 헤더가 없다. 그래서 읽다가
  // 순살로 돌아갈 길이 끊긴다. 새 UI를 얹는 대신 이미 맨 위에 있는 로고를
  // 링크로 만든다 — 로고를 누르면 홈이라는 건 설명이 필요 없다.
  function mountHomeMark() {
    if (document.querySelector('.nav') || document.querySelector('.logo-link')) return;
    var img = document.querySelector('img[alt="순살브리핑"], img[alt="순살"]');
    if (!img || img.closest('a')) return;
    var a = document.createElement('a');
    a.href = '/';
    a.className = 'ss-home';
    a.title = '순살 홈으로';
    a.setAttribute('aria-label', '순살브리핑 홈으로');
    a.addEventListener('click', function () { track('home'); });
    img.parentNode.insertBefore(a, img);
    a.appendChild(img);
  }

  function init() {
    var st = document.createElement('style');
    st.textContent = CSS;
    document.head.appendChild(st);
    mountFinish();
    mountHomeMark();
    watchSubscribe();

    // 이제 사이트 안에 대화가 있다. 텔레그램으로 내보내는 대신 순살톡으로 보낸다.
    // 새 글 수를 배지로 띄워서 '뭔가 올라왔다'가 보이게 한다.
    var fab = document.createElement('a');
    fab.className = 'ss-fab';
    fab.href = '/talk/';
    fab.setAttribute('aria-label', '순살톡 — 순살러 한마디');
    fab.title = '순살톡';
    fab.innerHTML = '💬<b class="ss-fabn" hidden></b>';
    fab.addEventListener('click', function () { track('talk'); markTalkSeen(); });
    if (location.pathname.indexOf('/talk/') !== 0) document.body.appendChild(fab);

    var sb = document.createElement('button');
    sb.className = 'ss-pageshare';
    sb.type = 'button';
    sb.innerHTML = '🔗 <span>공유하기</span>';
    sb.setAttribute('aria-label', '공유하기');
    sb.addEventListener('click', function () {
      var current = currentStory();
      track('share');
      trackTopic('share', current);
      openShare(current);
    });
    // 순살톡은 하단에 고정 바가 있어 공유 버튼과 겹친다. 그 페이지에선 띄우지 않는다.
    if (location.pathname.indexOf('/talk/') !== 0) document.body.appendChild(sb);

    // 딥링크(#story-N / #topic-slug)로 들어오면 해당 블록으로 확실히 스크롤
    if (location.hash) {
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
    mountTopicTracking(); // Morning 토픽별 노출·읽기·체류(집계값만)
    mountNotice();      // 수집 안내(전 페이지 공통 푸터가 없어 여기서)
  }

  // ── 스토리별 반응 (무로그인) ─────────────────────────────
  // 숫자는 항상 보인다. Worker(D1)가 붙어 있으면 공유 집계,
  // 없으면 내 클릭만 로컬 집계 — 어느 쪽이든 버튼이 "죽어" 보이지 않게.
  var REACTS = [['👍', '좋았음'], ['🤔', '글쎄'], ['🔥', '중요함']];
  // 설정 파일이 못 뜨면 반응·코멘트가 통째로 죽는다. 주소는 공개값이다.
  var CFG = window.SS_CFG || {};
  // workers.dev는 광고 차단기·사내망·일부 DNS 필터가 통째로 막는다. 그러면
  // 반응·코멘트가 조용히 죽는다. 여러 호스트를 순서대로 시도하고, 통한 곳을
  // 기억해 다음부터 그것부터 쓴다.
  var HOSTS = CFG.hosts ||
    ['https://api.soonsal.com', 'https://soonsal-react.kd-d0a.workers.dev'];
  try {
    var okHost = localStorage.getItem('ss_host');
    if (okHost && HOSTS.indexOf(okHost) > 0) {
      HOSTS = [okHost].concat(HOSTS.filter(function (h) { return h !== okHost; }));
    }
  } catch (e) {}
  var API = HOSTS[0] || null;                // Cloudflare Worker(권장)

  // 첫 호스트가 막히면 다음으로 넘긴다. tfetch(시간 제한)는 그대로 쓴다.
  function hfetch(path, opts, ms) {
    var i = 0;
    function attempt() {
      var host = HOSTS[i];
      return tfetch(host.replace(/[/]$/, '') + path, opts, ms).then(function (r) {
        if (API !== host) {
          API = host;
          try { localStorage.setItem('ss_host', host); } catch (e) {}
        }
        return r;
      }).catch(function (err) {
        i += 1;
        if (i < HOSTS.length) { return attempt(); }
        throw err;
      });
    }
    return attempt();
  }
  var HAS_BACKEND = !!API;

  var STORY_KEY_RE = /^(?:\d{4}c?-\d{1,2}|m\d{8}-[a-z0-9]+(?:-[a-z0-9]+)*)$/;
  var ISSUE_KEY_RE = /^(?:\d{4}c?|m\d{8})$/;

  function issueKey() {
    var marked = document.querySelector('[data-ss-issue]');
    var explicit = marked && marked.getAttribute('data-ss-issue');
    if (explicit && ISSUE_KEY_RE.test(explicit)) return explicit;
    var m = location.pathname.match(/\/newsletters\/2026\/(\d{4})(-crypto)?\.html/);
    return m ? m[1] + (m[2] ? 'c' : '') : null;
  }

  function storyKey(story) {
    var explicit = story && story.getAttribute && story.getAttribute('data-ss-story');
    if (explicit && STORY_KEY_RE.test(explicit)) return explicit;
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

  // 내가 한마디를 남긴 스토리. 서버는 반응을 합계로만 갖고 개인 기록을 남기지
  // 않는다(그게 맞다). 그래서 '내가 뭘 봤나'를 되살릴 단서는 이 브라우저뿐이다.
  function myComments() {
    try { return JSON.parse(localStorage.getItem('ss_cmt') || '{}'); } catch (e) { return {}; }
  }
  function markMine(key) {
    try {
      var m = myComments();
      m[key] = Math.floor(Date.now() / 1000);
      localStorage.setItem('ss_cmt', JSON.stringify(m));
    } catch (e) {}
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

  // 익명 프로필 — 전부 이 브라우저에만 남는다. 서버로는 닉네임과 업종만 가고,
  // 직장은 본인이 '함께 표시'를 켜지 않는 한 아예 전송하지 않는다.
  var INDS = ['금융·투자', 'IT·개발', '제조·엔지니어링', '유통·소비재', '헬스케어·바이오',
              '미디어·광고', '법률·회계', '교육', '공공·비영리', '창업·자영업', '학생', '기타'];

  // 닉네임을 안 치면 익명 번호에서 유도해 배정한다. 같은 브라우저는 늘 같은 이름이
  // 나와야 해서 난수가 아니라 해시를 쓴다. 뒤 숫자는 동명이인 구분용 —
  // 본인이 고른 이름이 아니라서 두 사람이 겹치면 같은 사람으로 오해받는다.
  var RNAMES = [
    '루피', '조로', '나미', '우솝', '상디', '쵸파', '로빈', '프랑키', '브룩', '징베', '에이스', '사보', '드래곤', '가프',
    '로저', '레일리', '크로커스', '샹크스', '벤베크만', '야소프', '흰수염', '마르코', '조즈', '비스타', '이조', '사치', '위블',
    '미호크', '핸콕', '크로커다일', '도플라밍고', '모리아', '쿠마', '버기', '알비다', '로우', '키드', '킬러', '우루지',
    '호킨스', '드레이크', '보니', '카포네', '아프로', '센고쿠', '아카이누', '아오키지', '키자루', '스모커', '타시기', '코비',
    '헬메포', '후지토라', '츠루', '루치', '카쿠', '칼리파', '블루노', '자부', '후쿠로', '쿠마돌리', '스팬담', '마젤란',
    '한니발', '사디', '이반코프', '쿠자', '빅맘', '카타쿠리', '크래커', '스무디', '브륄레', '푸딩', '페로스페로', '카이도',
    '킹', '퀸', '잭', '우루티', '페이지원', '야마토', '오뎅', '토키', '히요리', '킨에몬', '라이조', '칸주로', '덴지로',
    '모모', '이누아라시', '네코마무시', '페드로', '캐럿', '와노', '에넬', '위퍼', '코니스', '간포', '비비', '이가람', '챠카',
    '페루', '코자', '히루루크', '쿠레하', '와폴', '달튼', '아론', '하치', '쿠로오비', '노지코', '겐조', '벨메일', '아이스버그',
    '파울리', '티본', '카브', '압살롬', '페로나', '리스토', '마리골드', '산다소니아', '니욘', '호디', '넵튠', '시라호시',
    '후카보시', '만보시', '아라딘', '시저', '모네', '베르고', '레베카', '큐로스', '비올라', '트레보루', '피카', '디아만테',
    '슈가', '버팔로', '제프', '요사쿠', '조니', '코알라', '케이미', '파파그', '시키', '록스', '티치', '라피테', '반다',
    '오하라'];

  function autoNick(v) {
    var h = 0;
    for (var i = 0; i < v.length; i++) h = (h * 31 + v.charCodeAt(i)) >>> 0;
    return RNAMES[h % RNAMES.length] + ' ' + (h % 90 + 10);
  }

  function idLabel(pr) {
    // 이름을 바꿀 수 있다는 걸 눈에 보이게 한다. 자동으로 지어준 이름이라
    // 바꿔도 된다는 걸 모르면 그냥 그대로 쓰고 만다.
    return '<span class="nm">' + esc(pr.n || '이름 짓는 중') + '</span>' +
      (pr.i ? '<i>· ' + esc(pr.i) + '</i>' : '') + '<em>✎ 바꾸기</em>';
  }

  function profOf() {
    var p = null;
    try { p = JSON.parse(localStorage.getItem('ss_prof') || 'null'); } catch (e) {}
    if (!p) {                                   // 예전에 닉네임만 쓰던 사람 이어받기
      var old = '';
      try { old = localStorage.getItem('ss_nick') || ''; } catch (e) {}
      p = { n: old, i: '', c: '', sc: 0 };
    }
    if (!p.n) { p.n = autoNick(vid() || 'x'); setProf(p); }
    return p;
  }
  function setProf(p) {
    try {
      localStorage.setItem('ss_prof', JSON.stringify(p));
      localStorage.setItem('ss_nick', p.n || '');   // 옛 키도 맞춰 둔다
    } catch (e) {}
  }
  function nickOf() { return profOf().n || ''; }

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
    var items = CMTS[key] || [], n = items.length;
    var who = n ? items[n - 1].k : '';
    b.innerHTML = n
      ? '<span class="ic">💬</span><span class="tx"><b>' + n + '개</b>의 한마디' +
        (who ? ' · <i>' + esc(who) + '</i>님이 마지막' : '') + '</span>' +
        '<span class="cta">나도 한마디</span>'
      : '<span class="ic">💬</span><span class="tx ph">' + esc(b._prompt) + '</span>' +
        '<span class="cta">쓰기</span>';
  }

  function closeC() {
    if (COPEN) {
      if (COPEN._bar) COPEN._bar.hidden = false;   // 감춰둔 바를 되돌린다
      if (COPEN.parentNode) COPEN.parentNode.removeChild(COPEN);
    }
    COPEN = null;
  }

  function openC(key, pill) {
    if (COPEN && COPEN._key === key) { closeC(); return; }
    closeC();
    var w = document.createElement('div');
    w._key = key;
    w.className = 'ss-cwrap';
    var pr = profOf(), nick = pr.n || '';
    w.innerHTML =
      '<div class="ss-chd"><span>' + esc(pr.n || '') + '(으)로 남기기</span>' +
        '<button type="button" class="ss-cx" aria-label="닫기">✕</button></div>' +
      '<div class="ss-crt" hidden></div>' +
      '<textarea class="ss-cin" rows="3" maxlength="140" ' +
        'placeholder="어떻게 보셨어요? 한 줄이면 충분해요"></textarea>' +
      '<input class="ss-hp" name="website" tabindex="-1" aria-hidden="true"/>' +
      '<div class="ss-crow">' +
        // 이름과 프로필을 버튼 하나로 합쳤다. 이름은 이미 지어져 있으니
        // 대부분은 누를 일이 없고, 누르면 그때 바꾸는 자리가 열린다.
        '<button type="button" class="ss-cprof">' + idLabel(pr) + '</button>' +
        '<span class="ss-cnt"></span>' +
        '<button type="button" class="ss-cgo" disabled>남기기</button>' +
      '</div>' +
      '<div class="ss-cpf" hidden>' +
        '<label class="ss-cpl">이름' +
          '<input class="ss-cnick" maxlength="12" placeholder="닉네임" value="' + esc(nick) + '"/>' +
        '</label>' +
        '<label class="ss-cpl">업종<select class="ss-cind">' +
          '<option value="">안 밝힘</option>' +
          INDS.map(function (i) {
            return '<option' + (i === pr.i ? ' selected' : '') + '>' + i + '</option>';
          }).join('') + '</select></label>' +
        '<label class="ss-csc"><input type="checkbox" class="ss-cscb"' + (pr.sc ? ' checked' : '') +
          '/> 직장도 같이 보이기</label>' +
        '<label class="ss-cpl ss-cco-w"' + (pr.sc ? '' : ' hidden') + '>직장' +
          '<input class="ss-cco" maxlength="20" placeholder="예: 증권사" value="' +
          esc(pr.c || '') + '"/>' +
        '</label>' +
        '<div class="ss-cpn">이 브라우저에만 저장돼요.</div>' +
      '</div>' +
      '<div class="ss-clist"></div>' +
      '<a class="ss-call" href="/talk/">💬 순살톡에서 다른 이야기도 →</a>' +
      '<div class="ss-cnote">투자 권유·광고·비방은 ' +
      '사전 통보 없이 숨겨집니다.</div>';

    var ta = w.querySelector('.ss-cin');
    var go = w.querySelector('.ss-cgo');
    var cnt = w.querySelector('.ss-cnt');
    ta.addEventListener('input', function () {
      var n = ta.value.length;
      // 늘 140을 들이밀 필요는 없다. 얼마 안 남았을 때만 알려준다.
      cnt.textContent = n > 105 ? (140 - n) : '';
      go.disabled = !ta.value.trim();
    });
    ta.addEventListener('focus', function () { w.className = 'ss-cwrap on'; });
    go.addEventListener('click', function () { submitC(key, w, go); });
    w.querySelector('.ss-cx').addEventListener('click', closeC);

    var pf = w.querySelector('.ss-cpf'), pb = w.querySelector('.ss-cprof');
    pb.addEventListener('click', function () { pf.hidden = !pf.hidden; });
    function saveProf() {
      var p = profOf();
      p.i = w.querySelector('.ss-cind').value;
      p.c = (w.querySelector('.ss-cco').value || '').trim();
      p.sc = w.querySelector('.ss-cscb').checked ? 1 : 0;
      p.n = (w.querySelector('.ss-cnick').value || '').trim() || p.n;
      setProf(p);
      pb.innerHTML = idLabel(p);
    }
    ['.ss-cind', '.ss-cco', '.ss-cscb', '.ss-cnick'].forEach(function (s) {
      w.querySelector(s).addEventListener('change', saveProf);
    });
    // 직장은 '같이 보이기'를 켠 사람만 적는다 — 안 보일 걸 적게 할 이유가 없다
    var scb = w.querySelector('.ss-cscb'), cow = w.querySelector('.ss-cco-w');
    scb.addEventListener('change', function () {
      cow.hidden = !scb.checked;
      if (scb.checked) w.querySelector('.ss-cco').focus();
    });

    renderC(key, w);
    // 바가 그대로 있고 그 아래 또 상자가 뜨면 두 개처럼 보인다.
    // 바를 감추고 그 자리에 펼쳐서 '이어지는 한 덩어리'로 만든다.
    w._bar = pill;
    pill.parentNode.insertBefore(w, pill.nextSibling);
    pill.hidden = true;
    COPEN = w;
    setTimeout(function () { ta.focus(); }, 50);
  }

  // 이름에서 색을 뽑아 아바타를 만든다 — /talk/ 와 같은 문법
  var AVC = ['#E8A87C','#8FB0A0','#A09CD8','#D89AA8','#C8B060','#7FA8C8','#B8A090','#98B87F'];
  function avatar(nick, isOp) {
    var h = 0, s = String(nick || '?');
    for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
    var ch = s.replace(/[^가-힣A-Za-z0-9]/g, '').charAt(0) || '?';
    return '<span class="ss-av" style="background:' + (isOp ? '#E55A00' : AVC[h % AVC.length]) +
      (isOp ? ';color:#fff' : '') + '">' + esc(ch) + '</span>';
  }

  function likedSet() {
    try { return JSON.parse(localStorage.getItem('ss_liked') || '{}'); } catch (e) { return {}; }
  }
  function setLiked(m) { try { localStorage.setItem('ss_liked', JSON.stringify(m)); } catch (e) {} }

  function atHTML(body, toNick) {
    var s = esc(body);
    if (!toNick) return s;
    var tag = esc('@' + toNick);
    return s.indexOf(tag) === 0
      ? '<span class="ss-at">' + tag + '</span>' + s.slice(tag.length)
      : s;
  }

  function ciHTML(c, liked, isReply, toNick) {
    var n = c.l || 0;
    return '<div class="ss-ci' + (isReply ? ' ss-crep' : '') + (c.o ? ' ss-cop' : '') +
      '" data-i="' + (c.i || '') + '">' +
      avatar(c.k, c.o) +
      '<div class="ss-cbd">' +
        '<div class="ss-cnm"><b>' + esc(c.k) + '</b>' +
          (c.o ? '<span class="ss-cob' + (c.o === 2 ? ' bot' : '') + '">' +
            (c.o === 2 ? '🤖 봇' : '순살 팀') + '</span>' : '') +
          (c.g ? '<span class="ss-cg">' + esc(c.g) + '</span>' : '') +
          '<span class="ss-ct">' + cAgo(c.t) + '</span></div>' +
        '<div class="ss-cbx">' + atHTML(c.b, toNick) +
          (c.held ? '<span class="ss-chold">검토 중</span>' : '') + '</div>' +
        (c.held ? '' :
          '<div class="ss-cact">' +
            '<button type="button" class="ss-clike' + (liked[c.i] ? ' on' : '') +
              '" data-i="' + c.i + '">' + (liked[c.i] ? '♥' : '♡') +
              '<span>' + (n || '') + '</span></button>' +
            '<button type="button" class="ss-crep-b" data-i="' + c.i +
              '" data-k="' + esc(c.k) + '">↩ <span>답글</span></button>' +
          '</div>') +
      '</div></div>';
  }

  function renderC(key, w) {
    var list = w.querySelector('.ss-clist');
    var items = CMTS[key] || [], liked = likedSet();

    // 뿌리를 기준으로 묶는다. 부모만 보고 묶으면 '답글의 답글'은 부모가 답글이라
    // 어느 원글에도 안 걸려 화면에서 사라진다. 서버가 root(r)를 주지만, 예전
    // 응답에는 없을 수 있어 부모를 거슬러 올라가는 길도 남겨 둔다.
    var byId = {};
    items.forEach(function (c) { byId[c.i] = c; });
    function rootOf(c) {
      if (c.r) return c.r;
      var seen = {}, cur = c;
      while (cur && cur.p && byId[cur.p] && !seen[cur.p]) { seen[cur.p] = 1; cur = byId[cur.p]; }
      return cur ? cur.i : c.i;
    }
    var order = [], groups = {};
    items.forEach(function (c) {
      var rid = rootOf(c);
      if (!groups[rid]) { groups[rid] = []; order.push(rid); }
      groups[rid].push(c);
    });
    // 스레드 안에서는 쓴 순서대로 — 깊이를 더 파지 않고 대화가 이어지게 한다
    list.innerHTML = order.map(function (rid) {
      var g = groups[rid].slice().sort(function (a, b) { return a.i - b.i; });
      return g.map(function (c, i) {
        var par = c.p && byId[c.p];
        return ciHTML(c, liked, i > 0, par ? par.k : '');
      }).join('');
    }).join('');

    list.querySelectorAll('.ss-clike').forEach(function (b) {
      b.addEventListener('click', function () { toggleLike(b, key, w); });
    });
    list.querySelectorAll('.ss-crep-b').forEach(function (b) {
      b.addEventListener('click', function () {
        setReplyTo(w, parseInt(b.getAttribute('data-i'), 10), b.getAttribute('data-k'));
      });
    });
  }

  function toggleLike(btn, key, w) {
    var id = parseInt(btn.getAttribute('data-i'), 10), v = vid();
    if (!API || !v || !id) return;
    btn.disabled = true;
    hfetch('/like', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ id: id, v: v }),
    }, 20000).then(function (r) { return r.json(); }).then(function (res) {
      btn.disabled = false;
      if (!res || !res.ok) return;
      var m = likedSet();
      if (res.on) m[id] = 1; else delete m[id];
      setLiked(m);
      btn.className = 'ss-clike' + (res.on ? ' on' : '');
      btn.innerHTML = (res.on ? '♥' : '♡') + '<span>' + (res.n || '') + '</span>';
      (CMTS[key] || []).forEach(function (c) { if (c.i === id) c.l = res.n; });
    }).catch(function () { btn.disabled = false; });
  }

  function setReplyTo(w, id, nick) {
    w._reply = id;
    w._replyTag = '@' + nick + ' ';
    var bar = w.querySelector('.ss-crt');
    bar.innerHTML = '<span>' + esc(nick) + '님에게 답글</span>' +
      '<button type="button" class="ss-crx">취소</button>';
    bar.hidden = false;

    // 인스타처럼 @닉네임을 미리 넣어 준다. 지우고 쓸 수도 있다.
    var ta = w.querySelector('.ss-cin');
    if (ta.value.indexOf('@') !== 0) ta.value = w._replyTag + ta.value;
    ta.dispatchEvent(new Event('input'));

    bar.querySelector('.ss-crx').addEventListener('click', function () {
      if (w._replyTag && ta.value.indexOf(w._replyTag) === 0) {
        ta.value = ta.value.slice(w._replyTag.length);
        ta.dispatchEvent(new Event('input'));
      }
      w._reply = null; w._replyTag = null; bar.hidden = true;
    });
    ta.focus();
  }

  // ── 알림 ─────────────────────────────────────────────
  // 이메일도 계정도 없으니 익명 번호로 받아 사이트 안에서 보여준다.
  // (1단계) 순살톡에 새로 올라온 글 수를 배지로. 사람이 적을 땐 '누가 말을
  // 걸었다'는 신호 자체가 들어오게 만드는 게 먼저다.
  // (2단계) 사람이 늘면 '내 글에 달린 답글'만 골라 알리는 쪽으로 옮긴다 —
  // 그 준비는 /notices 에 이미 돼 있다.
  function talkSeen() {
    try { return parseInt(localStorage.getItem('ss_talk_seen') || '0', 10) || 0; }
    catch (e) { return 0; }
  }
  function markTalkSeen() {
    try {
      if (window._ssTalkMax) localStorage.setItem('ss_talk_seen', String(window._ssTalkMax));
    } catch (e) {}
  }

  function loadTalkBadge() {
    var f = document.querySelector('.ss-fab');
    if (!API || !f) return;
    hfetch('/recent?n=40', null, 8000)
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var items = (d && d.items) || [];
        if (!items.length) return;
        var max = 0, n = 0, seen = talkSeen();
        items.forEach(function (c) {
          if (c.id > max) max = c.id;
          if (c.id > seen) n++;
        });
        window._ssTalkMax = max;
        if (!seen) {            // 처음 온 사람에겐 전체 개수가 곧 '있다'는 신호다
          n = items.length;
        }
        var b = f.querySelector('.ss-fabn');
        if (n > 0) { b.textContent = n > 99 ? '99+' : n; b.hidden = false; }
      })
      .catch(function () {});
  }

  function loadNotices() {
    var v = vid();
    if (!API || !v) return;
    hfetch('/notices?v=' + encodeURIComponent(v), null, 8000)
      .then(function (r) { return r.json(); })
      .then(function (d) { if (d && d.n) showNotice(d); })
      .catch(function () {});
  }

  function showNotice(d) {
    if (document.querySelector('.ss-nt')) return;
    var b = document.createElement('div');
    b.className = 'ss-nt';
    var first = (d.items || [])[0] || {};
    var msg = d.n === 1
      ? (first.kind === 'reply' ? (first.who || '누군가') + '님이 답글을 남겼어요'
                                : '내 코멘트가 좋아요를 받았어요')
      : '새 소식 ' + d.n + '개';
    b.innerHTML = '<span>🐟 ' + esc(msg) + '</span>' +
      '<a href="' + storyUrl(first.story) + '">보기</a>' +
      '<button type="button" aria-label="닫기">✕</button>';
    document.body.appendChild(b);

    function dismiss() {
      var v = vid();
      if (API && v) {
        fetch(API.replace(/[/]$/, '') + '/notices?v=' + encodeURIComponent(v), { method: 'POST' })
          .catch(function () {});
      }
      if (b.parentNode) b.parentNode.removeChild(b);
    }
    b.querySelector('button').addEventListener('click', dismiss);
    b.querySelector('a').addEventListener('click', dismiss);
  }

  function storyUrl(story) {
    if (!story) return '#';
    var morning = String(story).match(/^m(\d{4})(\d{2})(\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)$/);
    if (morning) return '/chart/' + morning[1] + '/' + morning[2] + morning[3] +
      '.html#' + morning[4];
    var m = String(story).match(/^(\d{4})(c?)-(\d+)$/);
    if (!m) return '#';
    var y = new Date().getFullYear();
    return '/newsletters/' + y + '/' + m[1] + (m[2] ? 'c' : '') + '.html#story-' + m[3];
  }

  function submitC(key, w, go) {
    var ta = w.querySelector('.ss-cin');
    var ni = w.querySelector('.ss-cnick');
    var body = ta.value.trim();
    var nick = (ni.value || '').trim() || profOf().n || autoNick(vid() || 'x');
    if (!body) return;
    go.disabled = true;
    var pr = profOf();
    pr.n = nick;
    setProf(pr);
    // 업종은 프리셋, 직장은 '함께 표시'를 켠 경우에만 보낸다(안 켜면 전송 자체를 안 함)
    var tag = pr.i || '';
    var co = pr.sc ? (pr.c || '') : '';
    var v = vid();
    if (!API || !v) { toast('잠시 후 다시 시도해주세요'); go.disabled = false; return; }

    hfetch('/comment', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ story: key, v: v, nick: nick, body: body, tag: tag, co: co,
                             parent: w._reply || 0,
                             hp: w.querySelector('.ss-hp').value }),
    }, 20000).then(function (r) { return r.json(); }).then(function (res) {
      if (res && res.error) {
        toast(res.error === 'too fast' ? '조금 뒤에 다시 남겨주세요'
            : res.error === 'too many' ? '오늘은 여기까지만'
            : '남기지 못했습니다');
        go.disabled = false;
        return;
      }
      ta.value = '';
      w.querySelector('.ss-cnt').textContent = '';
      // 보류(state 0)여도 본인 화면에는 남긴다 — 실패로 보이면 다시 쓰고 도배가 된다
      var mine = { i: res.id, k: nick, b: body, t: Math.floor(Date.now() / 1000),
                   g: [tag, co].filter(Boolean).join(' · '), p: w._reply || undefined,
                   held: res.state === 0 };
      w._reply = null;
      var rt = w.querySelector('.ss-crt'); if (rt) rt.hidden = true;
      (CMTS[key] = CMTS[key] || []).push(mine);
      markMine(key);      // /saved/에서 내가 말 얹은 스토리를 되찾는 유일한 단서
      if (!mine.held) paintPill(key);
      renderC(key, w);
      track('comment');
      // 한 줄 쓰는 건 반응 누르는 것보다 품이 든다. 보류돼도 축하한다 —
      // 쓴 사람 입장에서는 이미 다 한 일이다.
      burst(go, mine.held ? '🐟' : '💬');
      toast(mine.held ? '확인 후 보여드릴게요 🐟' : '남겼음 🐟');
    }).catch(function (e) {
      // 중간에 끊긴 것과 거절당한 것은 다르다. 끊긴 거라면 서버엔 들어갔을 수
      // 있으니 '실패'라고 단정하면 다시 쓰게 되고 그게 도배가 된다.
      var aborted = e && (e.name === 'AbortError' || String(e).indexOf('abort') >= 0);
      toast(aborted ? '전송이 지연되고 있어요. 새로고침해 확인해 주세요'
                    : '남기지 못했습니다');
      go.disabled = false;
    });
  }

  // 무엇을 쓸지 막막하면 아무도 안 쓴다. 스토리마다 다른 운을 띄운다.
  var PROMPTS = [
    '이 얘기 어떻게 보셨어요?',
    '아는 게 있으면 한 줄 보태주세요',
    '이거 진짜 이렇게 될까요?',
    '읽고 든 생각 한 줄',
    '비슷한 경험 있으신 분?',
    '어느 쪽이 맞다고 보세요?',
  ];

  function mountComment(body, key, wrap) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'ss-cbar';
    var h = 0;
    for (var i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) >>> 0;
    b._prompt = PROMPTS[h % PROMPTS.length];
    b.addEventListener('click', function () { openC(key, b); });
    // 반응 줄 '다음'에 놓는다 — 반응은 한 번 누르고 끝이고, 쓰는 건 그다음이다
    wrap.parentNode.insertBefore(b, wrap.nextSibling);
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
          b.addEventListener('click', function () { vote(key, r[0], wrap, b); });
          rg.appendChild(b);
        });
        wrap.appendChild(rg);
        var sh = document.createElement('button');
        sh.type = 'button';
        sh.className = 'ss-rb ss-sh';
        sh.innerHTML = '🔗<span class="lb"> 공유</span>';
        sh.setAttribute('aria-label', '이 스토리 공유');
        sh.addEventListener('click', function () {
          track('share');
          trackTopic('share', s);
          openShare(s);
        });
        wrap.appendChild(sh);

        // 면책 문구('매수매도 추천 아님…')는 .story-body 밖, 스토리의 마지막 문단이다.
        // .story-body에 붙이면 반응·댓글이 그 위로 올라가 면책이 댓글 아래로 밀린다.
        // 면책은 스토리의 일부이므로 항상 댓글보다 위에 있어야 한다 — 스토리 끝에 붙인다.
        s.appendChild(wrap);
        mountComment(body, key, wrap);
        render(wrap, key);
        WRAPS[key] = wrap;
      })(stories[i]);
    }
    refreshIssue();   // 페이지 전체 카운트를 한 번에 (요청·읽기 절약)
  }

  // 이 페이지의 모든 스토리/토픽 카운트를 1회 요청으로 받아 뿌린다
  function refreshIssue() {
    if (!API) return;
    var issue = issueKey();
    if (!issue) return;
    hfetch('/page?issue=' + encodeURIComponent(issue), null, 10000)
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

  // 누르면 터진다. 반응은 순살에서 유일하게 독자가 뭔가 '하는' 지점인데
  // 지금은 숫자만 1 오르고 끝이라 누른 보람이 없다.
  // 라이브러리는 안 쓴다 — 한 번 쓰자고 번들을 늘릴 이유가 없다.
  function burst(btn, emoji) {
    if (!btn || !btn.getBoundingClientRect) return;
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var r = btn.getBoundingClientRect();
    var host = document.createElement('div');
    host.className = 'ss-burst';
    host.style.left = (r.left + r.width / 2) + 'px';
    host.style.top = (r.top + r.height / 2) + 'px';
    var bits = ['🎉', '✨', emoji, '🐟'];
    for (var i = 0; i < 22; i++) {
      var s = document.createElement('span');
      var dot = i % 3 === 0;
      if (dot) { s.className = 'd'; }
      else { s.textContent = bits[i % bits.length]; }
      // 위쪽으로 넓게 퍼지되 방향은 매번 다르게
      var ang = (-175 + Math.random() * 170) * Math.PI / 180;
      var dist = 52 + Math.random() * 76;
      s.style.setProperty('--x', Math.cos(ang) * dist + 'px');
      s.style.setProperty('--y', Math.sin(ang) * dist + 'px');
      s.style.setProperty('--r', (Math.random() * 540 - 270) + 'deg');
      s.style.animationDelay = (Math.random() * 70) + 'ms';
      host.appendChild(s);
    }
    document.body.appendChild(host);
    btn.classList.remove('pop');
    void btn.offsetWidth;                    // 연타해도 매번 다시 튀게
    btn.classList.add('pop');
    setTimeout(function () { host.remove(); }, 1100);
  }

  function vote(key, emoji, wrap, btn) {
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
    if (v[key]) { burst(btn, emoji); toast('접수했음 🐟'); }
    if (was && was !== emoji) push(key, was, -1, wrap);
    push(key, emoji, v[key] ? 1 : -1, wrap);
  }

  function push(key, emoji, delta, wrap) {
    if (API) {
      fetch(API.replace(/\/$/, '') + '/react', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ story: key, emoji: emoji, delta: delta, v: vid() })
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
      hfetch('/counts?story=' + encodeURIComponent(key), null, 8000)
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

  // ── 오늘의 논점 → 순살톡 ────────────────────────────────
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
      '<div class="ss-talk-q">한 줄이면 충분합니다.<br>' +
      '다른 사람들이 어디에 밑줄 그었는지도 순살톡에 모여 있어요.</div>' +
      '<div class="ss-talk-btns">' +
      '<a class="ss-talk-b" data-ss-ev="talk" href="/talk/">순살톡 가기 →</a>' +
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
    var key = storyKey(story);
    if (/^m\d{8}-/.test(key || '')) {
      return location.origin + location.pathname + (story.id ? '#' + story.id : '');
    }
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

  // ── 스쿨 입구 ────────────────────────────────────────
  // 트래픽은 뉴스레터에 있는데(30일 85회) 스쿨은 3회다. 뉴스레터 어디에도
  // 스쿨 언급이 없었다. 다 읽은 사람에게 맨 끝에서 한 번만 말을 건다 —
  // 읽는 중간을 끊지 않고, 닫으면 한 달간 다시 뜨지 않는다.
  var SCHOOL_HIDE = 30 * 86400 * 1000;

  function schoolMuted() {
    try {
      var v = parseInt(localStorage.getItem('ss_school_x') || '0', 10);
      return v && Date.now() - v < SCHOOL_HIDE;
    } catch (e) { return false; }
  }

  function mountSchool() {
    if (!/^\/newsletters\//.test(location.pathname)) return;
    if (schoolMuted() || document.querySelector('.ss-sch')) return;

    // 뉴스레터는 .footer로 끝난다. 그 바로 앞에 넣어 읽기를 끊지 않는다.
    var host = document.querySelector('.footer') || document.querySelector('footer');
    var d = document.createElement('div');
    d.className = 'ss-sch';
    // 설명을 읽게 만들면 안 누른다. 숫자로 못 박고 문턱 낮은 행동을 준다 —
    // '스쿨 보기'보다 '1분 맛보기'가 누르기 쉽다.
    d.innerHTML =
      '<button type="button" class="x" aria-label="닫기">✕</button>' +
      '<div class="t">현직자가 여는 클래스</div>' +
      '<div class="h">IBD · IPO · M&amp;A<br><b>31강 8시간 48분</b></div>' +
      '<div class="w">전 Deutsche Bank IBD · 현직 홍콩 PM</div>' +
      '<a class="cta" href="/school/">1분 맛보기부터 보기 →</a>';
    if (host && host.parentNode) host.parentNode.insertBefore(d, host);
    else document.body.appendChild(d);

    d.querySelector('.x').addEventListener('click', function () {
      try { localStorage.setItem('ss_school_x', String(Date.now())); } catch (e) {}
      if (d.parentNode) d.parentNode.removeChild(d);
    });
    d.querySelector('.cta').addEventListener('click', function () { track('school'); });
  }

  function boot() {
    init();
    // 알림은 화면이 자리잡은 뒤에 — 첫 렌더를 늦추지 않는다
    setTimeout(loadNotices, 1500);
    setTimeout(loadTalkBadge, 1200);
    setTimeout(mountSchool, 900);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
