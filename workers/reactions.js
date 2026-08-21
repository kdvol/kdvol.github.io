/**
 * 순살 반응 집계 Worker — Cloudflare Workers + D1 (무료)
 *
 * ⚠️ KV에서 D1로 이전한 이유 (2026-08-07)
 *   KV 무료 티어는 list()가 하루 1,000회 제한인데, 스토리별 카운트 조회에 list를 써서
 *   페이지뷰 1회당 list 5회가 나갔다 → 약 200뷰 만에 한도 소진, 집계가 끊김.
 *   D1은 하루 읽기 500만 / 쓰기 10만 행이라 같은 무료 조건에서 100배 여유.
 *
 * 배포:  cd workers && npx wrangler deploy
 * 스키마: npx wrangler d1 execute soonsal-react --remote --file schema.sql
 *
 * 엔드포인트
 *   GET  /counts?issue=0806   → {"0806-1":{"👍":3}, ...}   ← 페이지 1회 호출(권장)
 *   GET  /counts?story=0806-1 → {"👍":3,"🔥":1}
 *   GET  /counts              → 전체(운영자 통계용)
 *   GET  /activity            → {last:{story:ts}, events:[[ts,story,delta],...]} (최근 14일)
 *   POST /react {story,emoji,delta:±1} → 해당 스토리 카운트
 *   POST /t  {t:"hit"|"ev"|"topic", ...} → 방문·참여·토픽 집계 (204, 본문 없음)
 *   GET  /insights?days=30             → 운영자 대시보드용 집계
 *   GET  /topic-insights?days=30       → 토픽별 view/dwell/반응/댓글/공유
 *
 * 트래킹 원칙: 개인정보를 저장하지 않는다. IP·UA·쿠키를 쓰지 않고,
 *   브라우저 localStorage의 익명 난수 ID만 받는다. 원본 로그도 남기지 않고
 *   일자별 집계만 갱신한다.
 *
 * 시각 기록: reactions.updated_at(마지막 반응) + events(클릭 로그).
 *   집계 테이블만으론 "발행 직후 언제 몰렸는지"를 알 수 없어 로그를 따로 남긴다.
 */

const ALLOW_ORIGINS = ['https://soonsal.com', 'https://www.soonsal.com'];
const EMOJI = ['👍', '🤔', '🔥'];
const LEGACY_STORY_RE = /^[0-9]{4}c?-[0-9]{1,2}$/; // 0805-1 / 0805c-3
const MORNING_STORY_RE = /^m[0-9]{8}-[a-z0-9]+(?:-[a-z0-9]+)*$/;
const STORY_RE = /^(?:[0-9]{4}c?-[0-9]{1,2}|m[0-9]{8}-[a-z0-9]+(?:-[a-z0-9]+)*)$/;
const ISSUE_RE = /^(?:[0-9]{4}c?|m[0-9]{8})$/; // 0806 / 0806c / m20260812

function cors(origin) {
  const allow = ALLOW_ORIGINS.includes(origin) ? origin : ALLOW_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': allow,
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'content-type, x-admin-key',
    'Access-Control-Max-Age': '86400',
  };
}

function json(data, origin, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      ...cors(origin), ...extra,
    },
  });
}

// ── 트래킹 상수 ──────────────────────────────────────────────
// 9999는 테스트 전용 회차다. 그런 회차 페이지는 없지만 순살톡은 회차와
// 무관하게 최근 글을 모아 보여줘서, 테스트 글이 그대로 공개 피드에 떴다.
// 조회에서 걸러낸다 — 쓰기는 막지 않는다(테스트를 계속 할 수 있어야 한다).
const TEST_ISSUE = '9999';

// 클라이언트가 보내는데 목록에 없으면 **조용히 버려진다**. 2026-08-16 에
// finish·home 이 그렇게 두 달 넘게 사라지고 있었다. 보내는 쪽과 맞춘다.
// subscribe 는 이 사이트의 유일한 전환점인데 아예 재지 않고 있었다.
// ── 민감정보 제외 장치 (지금은 비어 있다) ────────────────────────────
//   2026-08-16 에 건강 관련 경로를 통째로 뺐다가 되돌렸다. 과대 해석이었다.
//
//   법제처 유권해석(19-0314)은 민감정보 범위를 두고 "지나치게 확장할 우려"를
//   지적하며 **좁은 해석**을 택했고, 판단 기준으로 "개인정보처리자가 곧바로
//   인식할 수 있어야 한다"를 들었다. 경제 기사를 읽은 사실에서 그 사람의
//   건강 상태를 곧바로 인식할 수는 없다 — 제약 기사를 읽는 건 투자 관심이지
//   병력이 아니다. 순살은 경제 매체이고 약을 권하지 않는다.
//
//   장치는 남겨 둔다. 환자 관점의 글(증상·치료 후기 같은 것)을 싣게 되면
//   그때 여기에 경로를 넣는다. 지금은 해당 없음.
const SENSITIVE = [];
function sensitivePath(p) {
  return SENSITIVE.some(function (re) { return re.test(p); });
}

const SUB_RE = /^[a-f0-9]{16}$/;      // 일방향 처리값 16자리
const ISS_RE = /^[0-9a-z-]{3,12}$/;   // 회차 표시
const KIND = ['read', 'finish', 'react', 'share', 'telegram', 'instagram',
              'comment', 'school', 'talk', 'home', 'subscribe',
              'human'];
const TOPIC_KIND = ['impression', 'view', 'dwell', 'share'];
// threads·youtube 는 2026-08-17 에 더했다. 그 전엔 'other' 로 뭉개져서,
// 스레드 마지막 편에 건 링크가 사람을 데려왔는지 셀 수가 없었다.
// 이 배열에 없는 값은 서버가 'other' 로 바꾼다 — 클라이언트만 고치면 샌다.
const SRC = ['direct', 'telegram', 'instagram', 'threads', 'youtube',
             'search', 'mail', 'other'];
// 하이픈 허용 — 'agent-...' 형태를 정상적인 ID로 받기 위해서다. 형식 검증에
// 걸려 거부되면 집계 제외가 '우연히' 동작하는 셈이라, 의도한 AGENT_VID 검사가
// 실제로 도는지 확인할 수 없다.
const VID_RE = /^[a-z0-9-]{8,32}$/;
// KST 자정 기준 날짜. UTC로 끊으면 한국 새벽 방문이 전날로 잡힌다.
const DAY = "date(unixepoch() + 32400, 'unixepoch')";

// ── 코멘트 상수 ──────────────────────────────────────────────
const NICK_RE = /^[가-힣a-zA-Z0-9._ -]{1,12}$/;
// 브랜드·운영자 사칭 차단. 기본 닉네임이 여기 걸리면 닉네임을 비운 사람이
// 전부 등록에 실패한다 — 기본값을 '독자'로 둔 이유다.
const NICK_BAN = /순살|운영자|관리자|admin|soonsal/i;
const BODY_MAX = 140;

// 자동 보류 규칙 — 걸리는 것만 잡아두고 나머지는 즉시 게시.
// 보류 건은 사람이 아니라 LLM(scripts/moderate_comments.py)이 하루 단위로 푼다.
const AGENT_VID = /^agent-/i;   // 집계에서 항상 빼는 개발용 브라우저

// ── 봇인가 사람인가 (KD 2026-08-18) ──────────────────────────────────
//   조회는 페이지 안의 JS 가 쏜다. 그래서 JS 를 안 돌리는 고전 크롤러는
//   애초에 안 잡힌다 — 다만 **표시가 없어서 확인할 방법이 없었다.**
//   요즘은 JS 를 도는 수집기가 흔하다(AI 크롤러·미리보기 페처·헤드리스).
//
//   봇은 `views.bot_hits` 로만 센다. `visitors`·`dau` 에는 **안 넣는다** —
//   사람 수는 사람 수여야 한다. 봇을 섞으면 그 숫자를 못 믿게 되고,
//   못 믿는 숫자는 안 보게 된다.
const BOT_UA = new RegExp([
  'bot', 'crawl', 'spider', 'slurp', 'scrape', 'fetcher', 'monitor',
  'headless', 'puppeteer', 'playwright', 'phantomjs', 'selenium',
  'facebookexternalhit', 'whatsapp', 'telegrambot', 'skypeuripreview',
  'discordbot', 'slackbot', 'linkedinbot', 'embedly', 'quora link preview',
  'gptbot', 'claudebot', 'anthropic', 'perplexity', 'ccbot', 'bytespider',
  'amazonbot', 'applebot', 'google-extended', 'chatgpt', 'oai-searchbot',
].join('|'), 'i');

function isBot(request) {
  const ua = request.headers.get('user-agent') || '';
  if (!ua) return 1;                 // UA 가 없는 요청은 브라우저가 아니다
  return BOT_UA.test(ua) ? 1 : 0;
}

// 댓글에 붙는 업종 태그. 프리셋에서만 고르게 한다 — 자유입력을 받으면
// '금감원 국장' 같은 직함 참칭이 가능해지고, 검증할 방법이 없는 소속이
// 투자 얘기에 가짜 권위를 실어준다. 표시용 문자열이 곧 화이트리스트다.
const TAGS = new Set([
  '금융·투자', 'IT·개발', '제조·엔지니어링', '유통·소비재', '헬스케어·바이오',
  '미디어·광고', '법률·회계', '교육', '공공·비영리', '창업·자영업', '학생', '기타',
]);

const HOLD_RULES = [
  ['url', /https?:\/\/|www\.|\b[a-z0-9-]+\.(com|net|co\.kr|kr|io|me|link|xyz|top|cc|shop)\b/i],
  // '텔레그램'·'DM' 같은 낱말만으로 잡으면 오탐이 난다 — 순살은 텔레그램 수다방을
  // 운영하고 독자가 그 얘기를 정상적으로 한다. 실제 유인 형태만 본다.
  ['invite', /t\.me\/|open\.kakao|오픈\s?카톡|오픈\s?채팅|카톡\s?(아이디|아디)|텔레그램\s*(방|링크|초대|주소)|디엠\s*(주세요|주시면|보내)/i],
  ['lead', /리딩\s?방|수익\s?인증|원금\s?보장|급등주|종목\s?추천|무료\s?체험|단타\s?방|수익률\s?보장/],
  ['tel', /01[016-9][-. ]?\d{3,4}[-. ]?\d{4}/],
  ['spam', /(.)\1{9,}/],
];

function holdReason(body) {
  for (const [name, re] of HOLD_RULES) if (re.test(body)) return name;
  if (new Set(body.replace(/\s/g, '')).size < 3) return 'spam';
  return null;
}

// 운영자 즉시 알림. 토큰이 없으면 아무 일도 하지 않는다.
// 응답을 기다리지 않는다 — 알림이 늦거나 실패해도 코멘트 등록은 성공해야 한다.
function notify(env, ctx, text) {
  if (!env.TG_TOKEN || !env.TG_CHAT) return;
  const p = fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      chat_id: env.TG_CHAT, text, parse_mode: 'HTML', disable_web_page_preview: true,
    }),
  }).catch(() => {});
  if (ctx && ctx.waitUntil) ctx.waitUntil(p);
}

const esc = (s) => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// 길이를 흘리지 않는 비교 (관리자 키 검증용)
function adminOk(request, env) {
  const key = request.headers.get('x-admin-key') || '';
  return !!env.ADMIN_KEY && keyEq(key, env.ADMIN_KEY);
}

function keyEq(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || !a || !b) return false;
  let d = a.length ^ b.length;
  const n = Math.max(a.length, b.length);
  for (let i = 0; i < n; i++) d |= (a.charCodeAt(i % a.length) ^ b.charCodeAt(i % b.length));
  return d === 0;
}

// 경로 카디널리티를 묶는다 — 스토리 앵커·쿼리·해시는 버리고 페이지 단위로만
function normPath(p) {
  if (typeof p !== 'string') return null;
  p = p.split('?')[0].split('#')[0].slice(0, 80);
  if (!/^\/[A-Za-z0-9/_.-]*$/.test(p)) return null;
  return p === '' ? '/' : p;
}

function issueOf(story) {
  if (LEGACY_STORY_RE.test(story)) return story.replace(/-[0-9]{1,2}$/, '');
  if (MORNING_STORY_RE.test(story)) return story.slice(0, 9);
  return null;
}

function storyLink(story) {
  const morning = String(story).match(/^m([0-9]{4})([0-9]{2})([0-9]{2})-([a-z0-9]+(?:-[a-z0-9]+)*)$/);
  if (morning) return `https://soonsal.com/chart/${morning[1]}/${morning[2]}${morning[3]}.html#${morning[4]}`;
  const legacy = String(story).match(/^([0-9]{4})(c?)-([0-9]{1,2})$/);
  if (!legacy) return 'https://soonsal.com';
  return `https://soonsal.com/newsletters/${new Date().getFullYear()}/${legacy[1]}`
    + `${legacy[2] ? '-crypto' : ''}.html#story-${legacy[3]}`;
}

function kstDay() {
  return new Date(Date.now() + 32400000).toISOString().slice(0, 10);
}

// 같은 브라우저인지 세는 데 raw vid를 저장하지 않는다. 토픽·종류·날짜까지
// secret과 함께 해시해 다른 토픽의 행동을 서로 연결할 수도 없게 한다.
async function topicSignature(env, topic, kind, vid) {
  if (!env.ADMIN_KEY || !VID_RE.test(vid)) return null;
  const raw = `${env.ADMIN_KEY}:${kstDay()}:${topic}:${kind}:${vid}`;
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(raw));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('').slice(0, 32);
}

const byStory = (rows) => {
  const out = {};
  for (const r of rows) (out[r.story] = out[r.story] || {})[r.emoji] = r.count;
  return out;
};

export default {
  async fetch(request, env, ctx) {
    const origin = request.headers.get('Origin') || '';
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: cors(origin) });
    }
    if (!env.DB) {
      return json({ error: 'D1 binding DB 가 설정되지 않았습니다' }, origin, 500);
    }

    try {
      if (request.method === 'GET' && url.pathname === '/counts') {
        const story = url.searchParams.get('story');
        const issue = url.searchParams.get('issue');

        // 페이지 단위 일괄 조회 — 요청/읽기 수를 스토리 수만큼 줄인다
        if (issue) {
          if (!ISSUE_RE.test(issue)) return json({}, origin);
          const { results } = await env.DB
            .prepare('select story, emoji, count from reactions where story like ?1 and count > 0')
            .bind(issue + '-%').all();
          return json(byStory(results || {}), origin,
                      200, { 'Cache-Control': 'public, max-age=20' });
        }
        if (story) {
          if (!STORY_RE.test(story)) return json({}, origin);
          const { results } = await env.DB
            .prepare('select emoji, count from reactions where story = ?1 and count > 0')
            .bind(story).all();
          const out = {};
          for (const r of results || []) out[r.emoji] = r.count;
          return json(out, origin, 200, { 'Cache-Control': 'public, max-age=20' });
        }
        // 운영자 전체 조회 — 기간을 받으면 그 창에서 일어난 반응만 센다.
        //   지금까지 늘 전체 누적이라, 화면에서 「7일」을 눌러도 반응 수만
        //   안 바뀌었다. 기간 버튼이 붙어 있는데 안 따라오는 값은 오류다
        //   (KD 2026-08-17). reactions 는 누적이라 events 에서 접는다.
        const cDays = Math.min(Math.max(parseInt(url.searchParams.get('days') || '0', 10) || 0, 0), 120);
        const cOne = (url.searchParams.get('day') || '').trim();
        const cIsDay = /^\d{4}-\d{2}-\d{2}$/.test(cOne);
        if (cDays || cIsDay) {
          const TS = cIsDay
            ? `ts >= unixepoch('${cOne}') - 32400 and ts < unixepoch('${cOne}', '+1 day') - 32400`
            : `ts >= unixepoch(date(unixepoch() + 32400, 'unixepoch', '-${cDays - 1} days')) - 32400`;
          const win = await env.DB.prepare(
            `select story, emoji, sum(delta) as count from events where ${TS} `
            + 'group by story, emoji having sum(delta) > 0').all();
          return json(byStory(win.results || []), origin);
        }
        const { results } = await env.DB
          .prepare('select story, emoji, count from reactions where count > 0').all();
        return json(byStory(results || []), origin);
      }

      // ── 코멘트 ────────────────────────────────────────────
      const commentsOff = env.COMMENTS === 'off';   // 사고 시 wrangler 한 줄로 즉시 차단

      // 페이지 진입 시 1회 — 반응 카운트와 코멘트를 함께 준다(요청 수 절약)
      if (request.method === 'GET' && (url.pathname === '/page' || url.pathname === '/comments')) {
        const issue = url.searchParams.get('issue') || '';
        if (!ISSUE_RE.test(issue)) return json({}, origin);

        const q = [env.DB.prepare(
          'select story, emoji, count from reactions where story like ?1 and count > 0'
        ).bind(issue + '-%')];
        if (!commentsOff) {
          q.push(env.DB.prepare(
            `select c.id, c.story, c.nick, c.body, c.ts, c.tag, c.co, c.parent_id, c.op,
                    coalesce(c.root_id, c.id) as root_id,
                    (select count(*) from comment_likes l where l.cid = c.id) as likes
             from comments c where c.issue = ?1 and c.state = 1
             order by coalesce(c.root_id, c.id), c.id limit 300`
          ).bind(issue));
        }
        const res = await env.DB.batch(q);
        const comments = {};
        for (const r of (res[1] && res[1].results) || []) {
          (comments[r.story] = comments[r.story] || []).push(
            { i: r.id, k: r.nick, b: r.body, t: r.ts,
              g: [r.tag, r.co].filter(Boolean).join(' · ') || undefined,
              p: r.parent_id || undefined, r: r.root_id || undefined,
              l: r.likes || undefined,
              o: r.op ? 1 : undefined });
        }
        const out = url.pathname === '/comments'
          ? { comments, off: commentsOff ? 1 : 0 }
          : { counts: byStory(res[0].results || []), comments, off: commentsOff ? 1 : 0 };
        return json(out, origin, 200, { 'Cache-Control': 'public, max-age=20' });
      }

      if (request.method === 'POST' && url.pathname === '/comment') {
        if (commentsOff) return json({ error: 'off' }, origin, 403);
        let b;
        try { b = await request.json(); } catch (e) { return json({ error: 'bad json' }, origin, 400); }

        // 허니팟 — 봇만 채우는 필드. 조용히 버린다(성공처럼 보이게)
        if (b && b.hp) return json({ ok: true, state: 1 }, origin);

        const story = String((b && b.story) || '');
        const vid = String((b && b.v) || '');
        const nick = String((b && b.nick) || '').trim();
        const body = String((b && b.body) || '').replace(/[\u0000-\u001f\u007f]/g, '').trim();

        if (!STORY_RE.test(story)) return json({ error: 'bad story' }, origin, 400);
        const storyIssue = issueOf(story);
        if (!storyIssue) return json({ error: 'bad issue' }, origin, 400);
        if (!VID_RE.test(vid)) return json({ error: 'bad vid' }, origin, 400);
        // NICK_BAN은 '순살·운영자' 사칭을 막는 규칙이다. 키로 증명된 팀 본인은
        // 그 이름을 써야 하므로 예외로 둔다 — 막으려던 대상이 아니다.
        const opNick = adminOk(request, env);
        if (!NICK_RE.test(nick) || (!opNick && NICK_BAN.test(nick))) {
          return json({ error: 'bad nick' }, origin, 400);
        }
        if (!body || body.length > BODY_MAX) return json({ error: 'bad body' }, origin, 400);

        const [blocked, recent, words] = await env.DB.batch([
          env.DB.prepare('select 1 as x from blocks where vid = ?1').bind(vid),
          env.DB.prepare(
            'select count(*) as n, max(ts) as t from comments where vid = ?1 and ts > unixepoch() - 86400'
          ).bind(vid),
          env.DB.prepare('select w from modwords'),
        ]);
        // 차단된 vid에는 성공한 것처럼 응답한다 — 차단을 알려주면 ID를 지우고 돌아온다
        if ((blocked.results || []).length) return json({ ok: true, state: 1 }, origin);

        const rl = (recent.results || [])[0] || { n: 0, t: 0 };
        const now = Math.floor(Date.now() / 1000);
        if (rl.n >= 10) return json({ error: 'too many' }, origin, 429);
        if (rl.t && now - rl.t < 60) return json({ error: 'too fast' }, origin, 429);

        let hold = holdReason(body);
        if (!hold) {
          for (const r of words.results || []) {
            if (r.w && body.indexOf(r.w) >= 0) { hold = 'word'; break; }
          }
        }
        // 답글 대상. 1단계만 허용한다 — 트리가 깊어지면 모바일에서 못 읽는다.
        // 답글의 답글은 같은 스레드의 형제로 붙인다(root_id를 물려받음).
        let parentId = null, rootId = null, parentVid = null, parentNick = null;
        const pid = parseInt((b && b.parent) || 0, 10);
        if (pid > 0) {
          const pr = await env.DB.prepare(
            'select id, story, root_id, state, vid, nick from comments where id = ?1'
          ).bind(pid).all();
          const par = (pr.results || [])[0];
          // 같은 스토리의 공개된 댓글에만 답글을 달 수 있다
          if (par && par.story === story && par.state === 1) {
            parentId = par.id;
            rootId = par.root_id || par.id;
            parentVid = par.vid;
            parentNick = par.nick;
          }
        }

        // 순살 팀이 쓰는 글은 팀 글이라고 화면에 밝힌다. 독자인 척하지 않는다.
        // 관리자 키가 맞을 때만 붙고, 키가 없으면 그냥 일반 코멘트다.
        // 1 = 순살 팀(사람), 2 = 순살 봇(자동). 둘 다 화면에 밝힌다 —
        // 봇을 사람처럼 보이게 두면 그게 속이는 것이다.
        const isOp = adminOk(request, env) ? (b && b.as === 'bot' ? 2 : 1) : 0;

        const state = hold ? 0 : 1;

        // 업종 태그 — 화이트리스트에 없으면 조용히 버린다(에러로 막을 것까진 아니다)
        const rawTag = String((b && b.tag) || '').trim();
        const tag = TAGS.has(rawTag) ? rawTag : null;

        // 직장은 자유입력이라 화이트리스트가 없다. 대신 본문과 똑같은 보류 규칙을
        // 태우고(링크·연락처·유인 문구), 꺾쇠는 지운다. 참칭 판단은 LLM 몫이다.
        const rawCo = String((b && b.co) || '').replace(/[<>]/g, '').trim().slice(0, 20);
        const co = rawCo && !holdReason(rawCo) ? rawCo : null;

        const ins = await env.DB.prepare(
          `insert into comments (story, issue, nick, body, vid, ts, state, hold, tag, co,
                                 parent_id, root_id, op)
           values (?1, ?2, ?3, ?4, ?5, unixepoch(), ?6, ?7, ?8, ?9, ?10, ?11, ?12)`
        ).bind(story, storyIssue, nick, body, vid, isOp ? 1 : state, hold, tag, co,
               parentId, rootId, isOp).run();

        // 답글이 달렸다고 원글 작성자에게 남긴다. 공개된 글에만, 자기 자신 제외.
        if (parentId && parentVid && parentVid !== vid && state === 1) {
          ctx.waitUntil(env.DB.prepare(
            `insert into notices (vid, kind, cid, rid, who, story, ts)
             values (?1, 'reply', ?2, ?3, ?4, ?5, unixepoch())`
          ).bind(parentVid, parentId, ins.meta.last_row_id, nick, story).run());
        }

        // 최상위 글은 자기 자신이 스레드 뿌리다
        if (!rootId) {
          await env.DB.prepare('update comments set root_id = id where id = ?1')
            .bind(ins.meta.last_row_id).run();
        }

        notify(env, ctx,
          `💬 <b>${esc(nick)}</b>${hold ? ` <i>(검토 중 · ${hold})</i>` : ''}\n` +
          `${esc(body)}\n\n` +
          `<a href="${storyLink(story)}">${story}</a>` +
          (hold ? ' · 자동 판정 대기' : ''));

        return json({ ok: true, state, hold, id: ins.meta && ins.meta.last_row_id,
                      to: parentNick || undefined }, origin);
      }

      // 신고 3건이면 자동 보류 — 정보통신망법 임시조치를 사람 없이 굴리는 지점
      // ── 댓글 좋아요 ───────────────────────────────────────
      // 익명 번호당 한 번, 다시 누르면 취소. 스토리 반응(👍🤔🔥)과 별개다.
      if (request.method === 'POST' && url.pathname === '/like') {
        let b;
        try { b = await request.json(); } catch (e) { return json({ error: 'bad json' }, origin, 400); }
        const vid = String((b && b.v) || '');
        const cid = parseInt((b && b.id) || 0, 10);
        if (!VID_RE.test(vid) || !(cid > 0)) return json({ error: 'bad req' }, origin, 400);

        // 공개된 댓글에만 누를 수 있다(숨겨진 글에 카운트가 쌓이면 복구 때 이상해진다)
        const c = await env.DB.prepare('select 1 as x from comments where id = ?1 and state = 1')
          .bind(cid).all();
        if (!(c.results || []).length) return json({ error: 'no comment' }, origin, 404);

        const had = await env.DB.prepare('select 1 as x from comment_likes where cid = ?1 and vid = ?2')
          .bind(cid, vid).all();
        const on = !(had.results || []).length;
        await env.DB.prepare(
          on ? 'insert into comment_likes (cid, vid, ts) values (?1, ?2, unixepoch()) '
             + 'on conflict(cid, vid) do nothing'
             : 'delete from comment_likes where cid = ?1 and vid = ?2'
        ).bind(cid, vid).run();

        // 좋아요를 받았다고 글쓴이에게 남긴다. 켤 때만, 자기 글 제외, 하루 한 번만.
        if (on) {
          ctx.waitUntil(env.DB.prepare(
            // who는 비워 둔다 — 여기에 누른 사람의 익명 번호를 넣으면
            // 받는 사람에게 남의 ID가 그대로 보인다. 좋아요는 익명이다.
            `insert into notices (vid, kind, cid, who, story, ts)
             select c.vid, 'like', c.id, null, c.story, unixepoch() from comments c
             where c.id = ?1 and c.vid <> ?2
               and not exists (select 1 from notices n where n.vid = c.vid
                               and n.kind = 'like' and n.cid = c.id
                               and n.ts > unixepoch() - 86400)`
          ).bind(cid, vid).run());
        }

        const n = await env.DB.prepare('select count(*) as n from comment_likes where cid = ?1')
          .bind(cid).all();
        return json({ ok: true, on: on, n: ((n.results || [])[0] || {}).n || 0 }, origin);
      }

      // ── 전체 코멘트 (스토리 막론) ─────────────────────────
      // 스토리마다 흩어져 있으면 아무도 못 본다. 한 화면에 모아 두면
      // 대화가 이어진다. 공개된 글만, 최신 스레드부터.
      if (request.method === 'GET' && url.pathname === '/recent') {
        const lim = Math.min(Math.max(parseInt(url.searchParams.get('n') || '60', 10) || 60, 1), 200);
        // 최근에 움직인 스레드를 고르고, 그 스레드의 글을 통째로 가져온다.
        // 답글만 새로 달려도 그 스레드가 위로 올라와야 대화가 이어져 보인다.
        const { results } = await env.DB.prepare(
          `with live as (
             select id, story, issue, nick, body, ts, tag, co, parent_id, op,
                    coalesce(root_id, id) as root_id
             from comments where state = 1 and issue <> ?2
           ),
           recent as (
             select root_id, max(ts) as last_ts from live group by root_id
             order by last_ts desc limit ?1
           )
           select l.id, l.story, l.issue, l.nick, l.body, l.ts, l.tag, l.co,
                  l.parent_id, l.root_id, l.op, r.last_ts,
                  (select count(*) from comment_likes k where k.cid = l.id) as likes
           from live l join recent r on r.root_id = l.root_id
           order by r.last_ts desc, l.root_id desc, l.id`
        ).bind(lim, TEST_ISSUE).all();
        return json({ items: results || [], off: commentsOff ? 1 : 0 }, origin, 200,
                     { 'Cache-Control': 'public, max-age=10' });
      }

      // ── 내 알림 ──────────────────────────────────────────
      // 익명 번호로만 조회한다. 번호는 추측할 수 없는 난수이고, 알림에는
      // 개인정보가 없다(상대 닉네임과 내 글 위치뿐).
      if (url.pathname === '/notices') {
        const nvid = String(url.searchParams.get('v') || '');
        if (!VID_RE.test(nvid)) return json({ items: [], n: 0 }, origin);

        if (request.method === 'POST') {      // 읽음 처리
          await env.DB.prepare('update notices set seen = 1 where vid = ?1').bind(nvid).run();
          return json({ ok: true }, origin);
        }
        const { results } = await env.DB.prepare(
          `select n.id, n.kind, n.cid, n.who, n.story, n.ts, n.seen,
                  substr(c.body, 1, 40) as snip
           from notices n left join comments c on c.id = n.cid
           where n.vid = ?1 and n.ts > unixepoch() - 7776000
           order by n.id desc limit 30`
        ).bind(nvid).all();
        const items = results || [];
        return json({ items, n: items.filter((r) => !r.seen).length }, origin);
      }

      // ── 보관 기간 지난 데이터 삭제 ────────────────────────
      // 방침에 적은 기간을 실제로 지키려면 지우는 쪽도 자동이어야 한다.
      // 지울 테이블은 화이트리스트로 고정한다 — 이름을 받아 SQL에 넣는 자리다.
      if (request.method === 'POST' && url.pathname === '/purge') {
        if (!adminOk(request, env)) return json({ error: 'unauthorized' }, origin, 401);
        let b;
        try { b = await request.json(); } catch (e) { return json({ error: 'bad json' }, origin, 400); }

        const ALLOWED = { notices: 'ts', hops: 'day', events: 'ts', human: 'day' };
        const deleted = {};
        for (const r of (b && b.rules) || []) {
          const col = ALLOWED[r.table];
          const days = Math.min(Math.max(parseInt(r.days || 0, 10) || 0, 1), 3650);
          if (!col) continue;
          // day는 'YYYY-MM-DD' 문자열, ts는 유닉스 초 — 컬럼 종류에 맞춰 비교한다
          const res = await env.DB.prepare(
            col === 'day'
              ? `delete from ${r.table} where day < date(unixepoch() + 32400, 'unixepoch', '-${days} days')`
              : `delete from ${r.table} where ts < unixepoch() - ${days * 86400}`
          ).run();
          deleted[r.table] = (res.meta && res.meta.changes) || 0;
        }
        return json({ ok: true, deleted }, origin);
      }

      if (request.method === 'POST' && url.pathname === '/flag') {
        let b;
        try { b = await request.json(); } catch (e) { return json({ ok: true }, origin); }
        const id = parseInt((b && b.id) || 0, 10);
        if (!id) return json({ ok: true }, origin);
        await env.DB.batch([
          env.DB.prepare('update comments set flags = flags + 1 where id = ?1').bind(id),
          env.DB.prepare(
            "update comments set state = 0, hold = 'flag' where id = ?1 and state = 1 and flags >= 3"
          ).bind(id),
        ]);
        return json({ ok: true }, origin);
      }

      // ── 자동 모더레이션용 (관리자 키 필요) ──────────────────
      if (url.pathname === '/mod') {
        if (!adminOk(request, env)) return json({ error: 'unauthorized' }, origin, 401);
        if (request.method === 'GET') {
          const state = parseInt(url.searchParams.get('state') || '0', 10);
          const { results } = await env.DB.prepare(
            `select id, story, issue, nick, body, ts, hold, flags, judge, tag, co
             from comments where state = ?1 order by id desc limit 100`
          ).bind(state).all();
          return json({ state, items: results || [] }, origin);
        }
        if (request.method === 'POST') {
          let b;
          try { b = await request.json(); } catch (e) { return json({ error: 'bad json' }, origin, 400); }
          const id = parseInt((b && b.id) || 0, 10);
          const st = parseInt((b && b.state), 10);
          if (!id || ![1, 0, -1, -2].includes(st)) return json({ error: 'bad args' }, origin, 400);
          const stmts = [env.DB.prepare(
            'update comments set state = ?2, judge = ?3 where id = ?1'
          ).bind(id, st, String((b && b.judge) || '').slice(0, 120))];
          if (b && b.block) {
            stmts.push(env.DB.prepare(
              `insert into blocks (vid, ts, note)
               select vid, unixepoch(), 'auto' from comments where id = ?1
               on conflict(vid) do nothing`
            ).bind(id));
          }
          await env.DB.batch(stmts);
          return json({ ok: true }, origin);
        }
      }

      // 운영자 통계용 — 마지막 반응 시각 + 최근 14일 클릭 로그
      if (request.method === 'GET' && url.pathname === '/activity') {
        if (!adminOk(request, env)) return json({ error: 'unauthorized' }, origin, 401);
        // 원본 이벤트를 그대로 내리면 반응이 쌓이는 만큼 응답이 커진다. 화면이
        // 쓰는 건 전부 집계값(24시간 시간대별 막대, 최근 1일·7일 합계)이라
        // 서버에서 접어서 보낸다. 응답 크기는 반응 수와 무관해진다.
        // 기간 연동 — 24시간·7일이 화면의 기간 버튼과 따로 놀았다 (KD 2026-08-17).
        //   하루를 고르면 그날 24시간을, 창이면 창 합계를 함께 돌려준다.
        const aDays = Math.min(Math.max(parseInt(url.searchParams.get('days') || '0', 10) || 0, 0), 120);
        const aOne = (url.searchParams.get('day') || '').trim();
        const aIsDay = /^\d{4}-\d{2}-\d{2}$/.test(aOne);
        const aTS = aIsDay
          ? `ts >= unixepoch('${aOne}') - 32400 and ts < unixepoch('${aOne}', '+1 day') - 32400`
          : (aDays
            ? `ts >= unixepoch(date(unixepoch() + 32400, 'unixepoch', '-${aDays - 1} days')) - 32400`
            : 'ts > unixepoch() - 604800');
        // 하루를 골랐으면 그날의 KST 시각별로, 아니면 지금 기준 최근 24시간
        const hourSQL = aIsDay
          ? `select cast(strftime('%H', ts + 32400, 'unixepoch') as integer) as hh, count(*) as n `
            + `from events where delta = 1 and ${aTS} group by hh`
          : 'select cast((unixepoch() - ts) / 3600 as integer) as hh, count(*) as n '
            + 'from events where delta = 1 and ts > unixepoch() - 86400 group by hh';
        const [lastQ, hourQ, sumQ, winQ] = await env.DB.batch([
          env.DB.prepare('select story, max(updated_at) as t from reactions where updated_at is not null group by story'),
          env.DB.prepare(hourSQL),
          env.DB.prepare('select sum(case when ts > unixepoch() - 86400 then 1 else 0 end) as d1, '
                       + 'count(*) as d7 from events where delta = 1 and ts > unixepoch() - 604800'),
          env.DB.prepare(`select count(*) as n from events where delta = 1 and ${aTS}`),
        ]);
        const last = {};
        for (const r of lastQ.results || []) last[r.story] = r.t;
        const hours = new Array(24).fill(0);
        for (const r of hourQ.results || []) {
          if (r.hh >= 0 && r.hh < 24) hours[aIsDay ? r.hh : 23 - r.hh] = r.n;
        }
        const s = (sumQ.results || [])[0] || {};
        return json({ last, hours, d1: s.d1 || 0, d7: s.d7 || 0,
                      win: ((winQ.results || [])[0] || {}).n || 0,
                      hoursOf: aIsDay ? aOne : null,
                      now: Math.floor(Date.now() / 1000) }, origin);
      }

      // ── 방문·참여 수집 ────────────────────────────────────
      // 응답 본문이 없다(204). 실패해도 페이지에 영향 주지 않는 게 우선.
      if (request.method === 'POST' && url.pathname === '/t') {
        let b;
        try { b = await request.json(); } catch (e) { return new Response(null, { status: 204, headers: cors(origin) }); }
        const vid = String((b && b.v) || '');
        if (!VID_RE.test(vid)) return new Response(null, { status: 204, headers: cors(origin) });

        // 'forget' — 이 브라우저를 영구 제외하고 그동안의 방문자 기록을 지운다.
        // 페이지뷰 합계는 경로별 집계라 되돌릴 수 없다(개인별 열람 이력을 남기지
        // 않는 설계의 대가). 사람 수 지표는 정확해진다.
        if (b.t === 'forget') {
          await env.DB.batch([
            env.DB.prepare('insert into tracking_optout (vid, ts) values (?1, unixepoch()) '
                         + 'on conflict(vid) do nothing').bind(vid),
            env.DB.prepare('delete from visitors where vid = ?1').bind(vid),
            // 사람 확인 낱개 줄도 같이 지운다 — 이 표는 vid 로 남는다
            env.DB.prepare('delete from human where vid = ?1').bind(vid),
          ]);
          return new Response(null, { status: 204, headers: cors(origin) });
        }

        // 개발·검증용 브라우저는 'agent-'로 시작하는 ID를 쓴다. 자동 감지는 불가능하다 —
        // navigator.webdriver는 false이고 UA도 일반 Chrome과 같다(둘 다 확인함).
        // 그래서 약속된 접두사를 서버가 무조건 무시한다. 저장소를 비워도 ID만 다시
        // 넣으면 그만이고, DB 조회도 필요 없다.
        if (AGENT_VID.test(vid)) {
          return new Response(null, { status: 204, headers: cors(origin) });
        }

        const skip = await env.DB.prepare('select 1 as x from tracking_optout where vid = ?1')
          .bind(vid).all();
        if ((skip.results || []).length) {
          return new Response(null, { status: 204, headers: cors(origin) });
        }

        const stmts = [];
        if (b.t === 'topic') {
          const topic = String((b && b.topic) || '');
          const kind = String((b && b.k) || '');
          if (!MORNING_STORY_RE.test(topic) || !TOPIC_KIND.includes(kind)) {
            return new Response(null, { status: 204, headers: cors(origin) });
          }
          const ms = kind === 'dwell'
            ? Math.min(Math.max(parseInt((b && b.ms) || 0, 10) || 0, 0), 1800000) : 0;
          stmts.push(env.DB.prepare(
            `insert into topic_metrics (day, topic, kind, n, ms)
             values (${DAY}, ?1, ?2, 1, ?3)
             on conflict(day, topic, kind) do update set n = n + 1, ms = ms + ?3`
          ).bind(topic, kind, ms));
          const sig = await topicSignature(env, topic, kind, vid);
          if (sig) {
            stmts.push(env.DB.prepare(
              `insert into topic_uniques (day, topic, kind, sig)
               values (${DAY}, ?1, ?2, ?3)
               on conflict(day, topic, kind, sig) do nothing`
            ).bind(topic, kind, sig));
          }
          if (kind === 'impression') {
            const src = SRC.includes(b.r) ? b.r : 'other';
            stmts.push(env.DB.prepare(
              `insert into topic_refs (day, topic, src, n) values (${DAY}, ?1, ?2, 1)
               on conflict(day, topic, src) do update set n = n + 1`
            ).bind(topic, src));
          }
        } else if (b.t === 'hit') {
          const path = normPath(b.p);
          if (!path) return new Response(null, { status: 204, headers: cors(origin) });
          const bot = isBot(request);
          if (bot) {
            // 봇은 조회 칸만 올리고 여기서 끝낸다. 유입·이동·방문자·행동에는
            // 넣지 않는다 — 그 표들은 「사람이 무엇을 하나」를 보는 자리다.
            await env.DB.prepare(
              `insert into views (day, path, hits, uniq, bot_hits)
               values (${DAY}, ?1, 0, 0, 1)
               on conflict(day, path) do update set bot_hits = bot_hits + 1`
            ).bind(path).run();
            return new Response(null, { status: 204, headers: cors(origin) });
          }
          const first = b.f ? 1 : 0;                       // 오늘 이 페이지 첫 방문인가
          const src = SRC.includes(b.r) ? b.r : 'other';

          // 직전에 본 페이지 → 지금 페이지. 경로 쌍의 합계만 올린다.
          // 방문자 ID는 여기 들어가지 않는다 — 개인별 열람 이력을 만들지 않겠다는
          // 약속을 지키면서 '어디서 와서 무엇을 더 보는지'만 남긴다.
          const frm = normPath(b.pv);
          if (frm && frm !== path) {
            stmts.push(env.DB.prepare(
              `insert into hops (day, frm, to_, n) values (${DAY}, ?1, ?2, 1)
               on conflict(day, frm, to_) do update set n = n + 1`
            ).bind(frm, path));
          }

          stmts.push(
            env.DB.prepare(
              `insert into views (day, path, hits, uniq) values (${DAY}, ?1, 1, ?2)
               on conflict(day, path) do update set hits = hits + 1, uniq = uniq + ?2`
            ).bind(path, first),
            // days는 '오늘 첫 방문'일 때만 +1 → 방문한 날짜 수 = 재방문 판정 근거
            env.DB.prepare(
              `insert into visitors (vid, first_day, last_day, days, hits)
               values (?1, ${DAY}, ${DAY}, 1, 1)
               on conflict(vid) do update set
                 hits = hits + 1,
                 days = days + (case when last_day <> ${DAY} then 1 else 0 end),
                 last_day = ${DAY}`
            ).bind(vid),
            // 그날 왔다는 사실만 남긴다. 같은 사람이 열 번 와도 한 줄이다.
            env.DB.prepare(
              `insert or ignore into dau (day, vid) values (${DAY}, ?1)`
            ).bind(vid),
          );
          // ── 뉴스레터 링크로 들어온 열람 (KD 2026-08-16, 고지·동의 갱신 후) ──
          //   sub 는 구독자 번호를 일방향 처리한 값이다. 되돌리는 열쇠는 발송
          //   시스템에만 있고 여기엔 없다. 그래도 우리가 열쇠를 가지므로
          //   익명이 아니라 **가명 처리된 정보**로 다루고, 90일 뒤 낱개 줄을
          //   지운다. 연결 끄기를 요청한 표시는 아예 기록하지 않는다.
          const sub = String((b && b.s) || '').trim();
          const iss = String((b && b.i) || '').trim();
          if (SUB_RE.test(sub) && ISS_RE.test(iss) && !sensitivePath(path)) {
            const off = await env.DB.prepare(
              'select 1 from reads_optout where sub = ?1').bind(sub).first();
            if (!off) {
              stmts.push(env.DB.prepare(
                `insert into reads (day, sub, iss, path, n) values (${DAY}, ?1, ?2, ?3, 1)
                 on conflict(day, sub, iss, path) do update set n = n + 1`
              ).bind(sub, iss, path));
            }
          }

          if (first) {
            stmts.push(env.DB.prepare(
              `insert into refs (day, src, n) values (${DAY}, ?1, 1)
               on conflict(day, src) do update set n = n + 1`
            ).bind(src));
          }
        } else if (b.t === 'ev') {
          if (!KIND.includes(b.k)) return new Response(null, { status: 204, headers: cors(origin) });
          stmts.push(env.DB.prepare(
            `insert into engage (day, kind, n) values (${DAY}, ?1, 1)
             on conflict(day, kind) do update set n = n + 1`
          ).bind(b.k));
          // ★ 사람 확인은 **사람 수**로도 남긴다 (KD 2026-08-21). engage 는
          //   횟수만 세는 표라, 같은 사람이 세 페이지에서 손을 움직이면 3 이다.
          //   dau 와 같은 꼴로 하루에 한 번만 남겨야 「몇 명이」가 나온다.
          if (b.k === 'human') {
            stmts.push(env.DB.prepare(
              `insert or ignore into human (day, vid) values (${DAY}, ?1)`
            ).bind(vid));
          }
        } else {
          return new Response(null, { status: 204, headers: cors(origin) });
        }

        await env.DB.batch(stmts);
        return new Response(null, { status: 204, headers: cors(origin) });
      }

      // 토픽별 편집 신호. raw vid나 개인별 이동 경로는 반환하지 않는다.
      if (request.method === 'GET' && url.pathname === '/topic-insights') {
        if (!adminOk(request, env)) return json({ error: 'unauthorized' }, origin, 401);
        const days = Math.min(Math.max(parseInt(url.searchParams.get('days') || '30', 10) || 30, 1), 120);
        // ★ N일을 고르면 **오늘 포함 N일**이다 (2026-08-18). `-N days` 로 잡으면
        //   어제부터 오늘까지 N+1 일이 잡힌다 — 「오늘」(days=1)이 이틀치를
        //   보여줬다. `-(N-1) days` 가 맞다. 보관 삭제(521행)는 「N일보다
        //   오래된 것」이라 그대로 둔다 — 거긴 경계의 뜻이 다르다.
        const since = `date(unixepoch() + 32400, 'unixepoch', '-${days - 1} days')`;
        const [metrics, uniques, reacts, comments, refs] = await env.DB.batch([
          env.DB.prepare(
            `select topic,
                    sum(case when kind = 'impression' then n else 0 end) as impressions,
                    sum(case when kind = 'view' then n else 0 end) as views,
                    sum(case when kind = 'dwell' then ms else 0 end) as dwell_ms,
                    sum(case when kind = 'share' then n else 0 end) as shares
             from topic_metrics where day >= ${since} group by topic`),
          env.DB.prepare(
            `select topic, kind, count(*) as n from topic_uniques
             where day >= ${since} group by topic, kind`),
          env.DB.prepare(
            `select story as topic,
                    case when sum(delta) > 0 then sum(delta) else 0 end as reactions
             from events
             where story like 'm%' and date(ts + 32400, 'unixepoch') >= ${since}
             group by story`),
          env.DB.prepare(
            `select story as topic, count(*) as comments, count(distinct vid) as commenters
             from comments where state = 1 and story like 'm%'
               and date(ts + 32400, 'unixepoch') >= ${since} group by story`),
          env.DB.prepare(
            `select topic, src, sum(n) as n from topic_refs
             where day >= ${since} group by topic, src order by n desc`),
        ]);
        const out = {};
        function row(topic) {
          if (!out[topic]) out[topic] = {
            topic, impressions: 0, views: 0, dwell_ms: 0, shares: 0,
            reactions: 0, unique_reactors: 0, comments: 0, unique_commenters: 0,
            unique_viewers: 0, referrals: {},
          };
          return out[topic];
        }
        for (const r of metrics.results || []) Object.assign(row(r.topic), r);
        for (const r of uniques.results || []) {
          if (r.kind === 'react') row(r.topic).unique_reactors = r.n;
          if (r.kind === 'view') row(r.topic).unique_viewers = r.n;
        }
        for (const r of reacts.results || []) row(r.topic).reactions = r.reactions || 0;
        for (const r of comments.results || []) {
          row(r.topic).comments = r.comments || 0;
          row(r.topic).unique_commenters = r.commenters || 0;
        }
        for (const r of refs.results || []) row(r.topic).referrals[r.src] = r.n;
        const topics = Object.values(out).map((r) => {
          r.avg_dwell_seconds = r.views ? Math.round(r.dwell_ms / r.views / 100) / 10 : 0;
          r.engagement_rate = r.views
            ? Math.round((r.reactions + r.comments + r.shares) / r.views * 10000) / 10000 : 0;
          return r;
        }).sort((a, b) => b.engagement_rate - a.engagement_rate || b.views - a.views);
        return json({ days, topics }, origin);
      }

      // ── 운영자 대시보드 집계 ──────────────────────────────
      // 관리자 키 필수. 방문자 수·상위 경로·유입 경로는 광고 단가 협상에 쓰이는
      // 영업 정보다. robots.txt로 크롤러만 막는 걸로는 부족하다 — 주소만 알면
      // 누구나 그대로 가져갈 수 있었다.
      if (request.method === 'GET' && url.pathname === '/insights') {
        if (!adminOk(request, env)) return json({ error: 'unauthorized' }, origin, 401);
        const days = Math.min(Math.max(parseInt(url.searchParams.get('days') || '30', 10) || 30, 1), 120);
        // ★ N일을 고르면 **오늘 포함 N일**이다 (2026-08-18). `-N days` 로 잡으면
        //   어제부터 오늘까지 N+1 일이 잡힌다 — 「오늘」(days=1)이 이틀치를
        //   보여줬다. `-(N-1) days` 가 맞다. 보관 삭제(521행)는 「N일보다
        //   오래된 것」이라 그대로 둔다 — 거긴 경계의 뜻이 다르다.
        const since = `date(unixepoch() + 32400, 'unixepoch', '-${days - 1} days')`;

        // ── 하루만 보기 (KD 2026-08-15: "모든 데이터를 일자별로도 볼 수 있게")
        //    일자별이 있던 건 조회수·댓글·반응뿐이고 경로·유입·이동·방문자는
        //    창 전체 합계만 나왔다. 그래서 "방문 17명" 옆에 "유입 4,683" 같은
        //    값이 나란히 찍혔다. 필드를 늘리는 대신 **범위 자체**를 하루로
        //    좁힌다 — 응답 모양이 그대로라 화면 코드가 갈라지지 않는다.
        //    형식은 정규식으로 못 박는다. 문자열이 SQL 에 그대로 들어간다.
        const one = (url.searchParams.get('day') || '').trim();
        const isDay = /^\d{4}-\d{2}-\d{2}$/.test(one);
        const DCOND = isDay ? `= '${one}'` : `>= ${since}`;
        // 우리 day 는 KST 기준이라, ts 로 자를 땐 9시간을 당겨야 같은 하루가 된다
        const TSCOND = isDay
          ? `ts >= unixepoch('${one}') - 32400 and ts < unixepoch('${one}', '+1 day') - 32400`
          : `ts >= unixepoch(${since})`;

        const [daily, dau, humanD, freshD, top, eng, ref, hop, vis] = await env.DB.batch([
          env.DB.prepare(
            `select day, sum(hits) as hits, sum(uniq) as uniq,
                    sum(bot_hits) as bots from views
             where day ${DCOND} group by day order by day`),
          // 그날 실제로 온 사람 수 — 경로 기준 uniq 와 다르다
          env.DB.prepare(
            `select day, count(*) as people from dau
             where day ${DCOND} group by day order by day`),
          // 그날 **손이 움직인 사람** 수. engage(human) 은 횟수라 사람 수가 안 나온다
          env.DB.prepare(
            `select day, count(*) as people from human
             where day ${DCOND} group by day order by day`),
          // 그날 처음 온 사람 수. 창 합계만 있으면 dau 가 덮는 날짜와 기간이
          // 어긋나 '새 사람 40 / 다시 온 사람 0' 같은 값이 나온다.
          env.DB.prepare(
            `select first_day as day, count(*) as n from visitors
             where first_day ${DCOND} group by first_day order by first_day`),
          env.DB.prepare(
            `select path, sum(hits) as hits, sum(uniq) as uniq,
                    sum(bot_hits) as bots from views
             where day ${DCOND} group by path order by hits desc limit 25`),
          env.DB.prepare(
            `select day, kind, n from engage where day ${DCOND}`),
          env.DB.prepare(
            `select src, sum(n) as n from refs where day ${DCOND} group by src order by n desc`),
          // 이동 쌍 상위 — 어떤 글에서 어떤 글로 넘어가는지
          env.DB.prepare(
            `select frm, to_, sum(n) as n from hops where day ${DCOND}
             group by frm, to_ order by n desc limit 20`),
          // 재방문 = 서로 다른 날 2일 이상 방문한 사람.
          // active7은 일별 uniq 합과 다르다 — 합계는 이틀 온 사람을 두 번 센다.
          env.DB.prepare(
            `select
               count(*) as total,
               sum(case when days >= 2 then 1 else 0 end) as repeat_v,
               sum(case when last_day ${DCOND} then 1 else 0 end) as active,
               sum(case when last_day >= date(unixepoch() + 32400, 'unixepoch', '-7 days')
                        then 1 else 0 end) as active7,
               sum(case when last_day = ${DAY} then 1 else 0 end) as today,
               sum(case when first_day ${DCOND} then 1 else 0 end) as fresh
             from visitors`),
        ]);

        // 댓글 참여자 — 누가 썼는지가 아니라 '어떤 사람들이 오는지'만 본다.
        // 업종 분포·작성자 수·재작성률 전부 집계값이고 개인은 식별하지 않는다.
        const cm = await env.DB.batch([
          env.DB.prepare("select coalesce(tag, '(미기재)') as tag, count(*) as n, "
                       + 'count(distinct vid) as people from comments where state = 1 '
                       + 'group by tag order by n desc'),
          env.DB.prepare('select count(*) as total, count(distinct vid) as writers, '
                       + "sum(case when co is not null then 1 else 0 end) as with_co "
                       + 'from comments where state = 1'),
          env.DB.prepare('select count(*) as repeat_w from (select vid from comments '
                       + 'where state = 1 group by vid having count(*) >= 2)'),
          env.DB.prepare("select date(ts + 32400, 'unixepoch') as day, count(*) as n, "
                       + 'sum(case when op = 0 then 1 else 0 end) as readers '
                       + `from comments where state = 1 and ${TSCOND} `
                       + 'group by day order by day'),
                  env.DB.prepare("select date(ts + 32400, 'unixepoch') as day, "
                       + 'sum(case when delta = 1 then 1 else 0 end) as up, '
                       + 'sum(case when delta = -1 then 1 else 0 end) as undo '
                       + `from events where ${TSCOND} `
                       + 'group by day order by day'),
        ]);

        // ── 지표마다 집계 시작일이 다르다 (KD 2026-08-16) ─────────────
        //   dau 는 08-16 에, views/visitors 는 08-11 에 시작했다. 시작일이
        //   다른 값끼리 나누면 읽음률 94,875% 같은 게 나온다. 실제로 나왔다.
        //   그래서 각 표의 **첫 날**을 같이 보낸다. 화면은 겹치는 구간에서만
        //   비율을 낸다.
        const cov = await env.DB.batch([
          env.DB.prepare('select min(day) as d from views'),
          env.DB.prepare('select min(first_day) as d from visitors'),
          env.DB.prepare('select min(day) as d from dau'),
          env.DB.prepare('select min(day) as d from engage'),
          env.DB.prepare('select min(day) as d from refs'),
          // 행동 종류마다 시작일이 다르다 — finish·home·subscribe 는 목록에
          // 없어서 버려지다가 2026-08-16 에야 받기 시작했다. 표 전체의 시작일로
          // 나누면 그 종류의 비율이 실제보다 낮게 나온다.
          env.DB.prepare('select kind, min(day) as d from engage group by kind'),
        ]);
        const coverage = {
          views: (cov[0].results || [])[0]?.d || null,
          visitors: (cov[1].results || [])[0]?.d || null,
          dau: (cov[2].results || [])[0]?.d || null,
          engage: (cov[3].results || [])[0]?.d || null,
          refs: (cov[4].results || [])[0]?.d || null,
          kinds: Object.fromEntries((cov[5].results || []).map(r => [r.kind, r.d])),
        };

        // 전체 기간 누적 — 창(days)과 무관하게 집계 시작 이후 전부
        const life = await env.DB.batch([
          env.DB.prepare('select sum(hits) as hits, min(day) as since, '
                       + 'count(distinct day) as days from views'),
          env.DB.prepare('select count(*) as people, sum(case when days >= 2 then 1 else 0 end) '
                       + 'as repeat_v from visitors'),
          env.DB.prepare('select kind, sum(n) as n from engage group by kind'),
        ]);
        const lifeEng = {};
        for (const r of (life[2].results || [])) lifeEng[r.kind] = r.n;

        // 회차별 열람 — 뉴스레터 링크로 온 사람 수. 개인 목록은 내보내지 않는다.
        const rd = await env.DB.batch([
          env.DB.prepare(
            `select iss, count(distinct sub) as people, sum(n) as reads
             from reads where day ${DCOND} group by iss order by people desc limit 20`),
          env.DB.prepare(
            `select day, count(distinct sub) as people from reads
             where day ${DCOND} group by day order by day`),
        ]);

        return json({
          days,
          coverage,
          issues: rd[0].results || [],
          readsDaily: rd[1].results || [],
          day: isDay ? one : null,
          scope: isDay ? one : `최근 ${days}일`,
          lifetime: Object.assign({}, (life[0].results || [])[0], (life[1].results || [])[0],
                                  { engage: lifeEng }),
          writers: Object.assign({}, (cm[1].results || [])[0], (cm[2].results || [])[0],
                                 { byTag: cm[0].results || [] }),
          daily: daily.results || [],
          dau: dau.results || [],
          humanDau: humanD.results || [],
          freshDaily: freshD.results || [],
          top: top.results || [],
          engage: eng.results || [],
          refs: ref.results || [],
          hops: hop.results || [],
          visitors: (vis.results || [])[0] || {},
          commentsDaily: cm[3].results || [],
          reactsDaily: cm[4].results || [],
        }, origin);
      }

      if (request.method === 'POST' && url.pathname === '/react') {
        let body;
        try { body = await request.json(); } catch (e) { return json({ error: 'bad json' }, origin, 400); }
        const { story, emoji } = body || {};
        const delta = Number(body && body.delta);

        if (!STORY_RE.test(String(story || ''))) return json({ error: 'bad story' }, origin, 400);
        if (!EMOJI.includes(emoji)) return json({ error: 'bad emoji' }, origin, 400);
        if (delta !== 1 && delta !== -1) return json({ error: 'bad delta' }, origin, 400);

        const updates = [
          env.DB.prepare(
            `insert into reactions (story, emoji, count, updated_at)
             values (?1, ?2, max(?3, 0), unixepoch())
             on conflict(story, emoji) do update set
               count = max(count + ?3, 0), updated_at = unixepoch()`
          ).bind(story, emoji, delta),
          env.DB.prepare(
            `insert into events (story, emoji, delta, ts) values (?1, ?2, ?3, unixepoch())`
          ).bind(story, emoji, delta),
        ];
        const reactVid = String((body && body.v) || '');
        if (delta === 1 && MORNING_STORY_RE.test(story) && VID_RE.test(reactVid)) {
          const sig = await topicSignature(env, story, 'react', reactVid);
          if (sig) updates.push(env.DB.prepare(
            `insert into topic_uniques (day, topic, kind, sig)
             values (${DAY}, ?1, 'react', ?2)
             on conflict(day, topic, kind, sig) do nothing`
          ).bind(story, sig));
        }
        await env.DB.batch(updates);

        const { results } = await env.DB
          .prepare('select emoji, count from reactions where story = ?1 and count > 0')
          .bind(story).all();
        const out = {};
        for (const r of results || []) out[r.emoji] = r.count;
        return json(out, origin);
      }
    } catch (err) {
      return json({ error: 'server', detail: String(err).slice(0, 120) }, origin, 500);
    }

    return json({ ok: true, endpoints: ['/counts?issue=', '/counts?story=', '/activity', '/insights', '/topic-insights', 'POST /react', 'POST /t'] }, origin);
  },
};
