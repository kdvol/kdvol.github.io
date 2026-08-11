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
 *   POST /t  {t:"hit"|"ev", ...}       → 방문·참여 집계 (204, 본문 없음)
 *   GET  /insights?days=30             → 운영자 대시보드용 집계
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
const STORY_RE = /^[0-9]{4}c?-[0-9]{1,2}$/;   // 0805-1 / 0805c-3
const ISSUE_RE = /^[0-9]{4}c?$/;              // 0806 / 0806c

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
const KIND = ['read', 'react', 'share', 'telegram', 'instagram', 'comment'];
const SRC = ['direct', 'telegram', 'instagram', 'search', 'mail', 'other'];
const VID_RE = /^[a-z0-9]{8,24}$/;
// KST 자정 기준 날짜. UTC로 끊으면 한국 새벽 방문이 전날로 잡힌다.
const DAY = "date(unixepoch() + 32400, 'unixepoch')";

// ── 코멘트 상수 ──────────────────────────────────────────────
const NICK_RE = /^[가-힣a-zA-Z0-9._ -]{1,12}$/;
const NICK_BAN = /순살|운영자|관리자|admin|soonsal/i;
const BODY_MAX = 140;

// 자동 보류 규칙 — 걸리는 것만 잡아두고 나머지는 즉시 게시.
// 보류 건은 사람이 아니라 LLM(scripts/moderate_comments.py)이 하루 단위로 푼다.
const AGENT_VID = /^agent-/i;   // 집계에서 항상 빼는 개발용 브라우저

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
            'select id, story, nick, body, ts from comments where issue = ?1 and state = 1 order by id limit 200'
          ).bind(issue));
        }
        const res = await env.DB.batch(q);
        const comments = {};
        for (const r of (res[1] && res[1].results) || []) {
          (comments[r.story] = comments[r.story] || []).push(
            { i: r.id, k: r.nick, b: r.body, t: r.ts });
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
        if (!VID_RE.test(vid)) return json({ error: 'bad vid' }, origin, 400);
        if (!NICK_RE.test(nick) || NICK_BAN.test(nick)) return json({ error: 'bad nick' }, origin, 400);
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
        const state = hold ? 0 : 1;

        const ins = await env.DB.prepare(
          `insert into comments (story, issue, nick, body, vid, ts, state, hold)
           values (?1, ?2, ?3, ?4, ?5, unixepoch(), ?6, ?7)`
        ).bind(story, story.split('-')[0], nick, body, vid, state, hold).run();

        const issue = story.split('-')[0];
        notify(env, ctx,
          `💬 <b>${esc(nick)}</b>${hold ? ` <i>(검토 중 · ${hold})</i>` : ''}\n` +
          `${esc(body)}\n\n` +
          `<a href="https://soonsal.com/newsletters/2026/${issue.replace('c', '')}` +
          `${issue.endsWith('c') ? '-crypto' : ''}.html">${story}</a>` +
          (hold ? ' · 자동 판정 대기' : ''));

        return json({ ok: true, state, hold, id: ins.meta && ins.meta.last_row_id }, origin);
      }

      // 신고 3건이면 자동 보류 — 정보통신망법 임시조치를 사람 없이 굴리는 지점
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
        const key = request.headers.get('x-admin-key') || '';
        if (!env.ADMIN_KEY || !keyEq(key, env.ADMIN_KEY)) {
          return json({ error: 'unauthorized' }, origin, 401);
        }
        if (request.method === 'GET') {
          const state = parseInt(url.searchParams.get('state') || '0', 10);
          const { results } = await env.DB.prepare(
            `select id, story, issue, nick, body, ts, hold, flags, judge
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
        // 원본 이벤트를 그대로 내리면 반응이 쌓이는 만큼 응답이 커진다. 화면이
        // 쓰는 건 전부 집계값(24시간 시간대별 막대, 최근 1일·7일 합계)이라
        // 서버에서 접어서 보낸다. 응답 크기는 반응 수와 무관해진다.
        const [lastQ, hourQ, sumQ] = await env.DB.batch([
          env.DB.prepare('select story, max(updated_at) as t from reactions where updated_at is not null group by story'),
          env.DB.prepare('select cast((unixepoch() - ts) / 3600 as integer) as hh, count(*) as n '
                       + 'from events where delta = 1 and ts > unixepoch() - 86400 group by hh'),
          env.DB.prepare('select sum(case when ts > unixepoch() - 86400 then 1 else 0 end) as d1, '
                       + 'count(*) as d7 from events where delta = 1 and ts > unixepoch() - 604800'),
        ]);
        const last = {};
        for (const r of lastQ.results || []) last[r.story] = r.t;
        const hours = new Array(24).fill(0);
        for (const r of hourQ.results || []) {
          if (r.hh >= 0 && r.hh < 24) hours[23 - r.hh] = r.n;
        }
        const s = (sumQ.results || [])[0] || {};
        return json({ last, hours, d1: s.d1 || 0, d7: s.d7 || 0,
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
        if (b.t === 'hit') {
          const path = normPath(b.p);
          if (!path) return new Response(null, { status: 204, headers: cors(origin) });
          const first = b.f ? 1 : 0;                       // 오늘 이 페이지 첫 방문인가
          const src = SRC.includes(b.r) ? b.r : 'other';

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
          );
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
        } else {
          return new Response(null, { status: 204, headers: cors(origin) });
        }

        await env.DB.batch(stmts);
        return new Response(null, { status: 204, headers: cors(origin) });
      }

      // ── 운영자 대시보드 집계 ──────────────────────────────
      if (request.method === 'GET' && url.pathname === '/insights') {
        const days = Math.min(Math.max(parseInt(url.searchParams.get('days') || '30', 10) || 30, 1), 120);
        const since = `date(unixepoch() + 32400, 'unixepoch', '-${days} days')`;

        const [daily, top, eng, ref, vis] = await env.DB.batch([
          env.DB.prepare(
            `select day, sum(hits) as hits, sum(uniq) as uniq from views
             where day >= ${since} group by day order by day`),
          env.DB.prepare(
            `select path, sum(hits) as hits, sum(uniq) as uniq from views
             where day >= ${since} group by path order by hits desc limit 25`),
          env.DB.prepare(
            `select day, kind, n from engage where day >= ${since}`),
          env.DB.prepare(
            `select src, sum(n) as n from refs where day >= ${since} group by src order by n desc`),
          // 재방문 = 서로 다른 날 2일 이상 방문한 사람.
          // active7은 일별 uniq 합과 다르다 — 합계는 이틀 온 사람을 두 번 센다.
          env.DB.prepare(
            `select
               count(*) as total,
               sum(case when days >= 2 then 1 else 0 end) as repeat_v,
               sum(case when last_day >= ${since} then 1 else 0 end) as active,
               sum(case when last_day >= date(unixepoch() + 32400, 'unixepoch', '-7 days')
                        then 1 else 0 end) as active7,
               sum(case when last_day = ${DAY} then 1 else 0 end) as today,
               sum(case when first_day >= ${since} then 1 else 0 end) as fresh
             from visitors`),
        ]);

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

        return json({
          days,
          lifetime: Object.assign({}, (life[0].results || [])[0], (life[1].results || [])[0],
                                  { engage: lifeEng }),
          daily: daily.results || [],
          top: top.results || [],
          engage: eng.results || [],
          refs: ref.results || [],
          visitors: (vis.results || [])[0] || {},
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

        await env.DB.batch([
          env.DB.prepare(
            `insert into reactions (story, emoji, count, updated_at)
             values (?1, ?2, max(?3, 0), unixepoch())
             on conflict(story, emoji) do update set
               count = max(count + ?3, 0), updated_at = unixepoch()`
          ).bind(story, emoji, delta),
          env.DB.prepare(
            `insert into events (story, emoji, delta, ts) values (?1, ?2, ?3, unixepoch())`
          ).bind(story, emoji, delta),
        ]);

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

    return json({ ok: true, endpoints: ['/counts?issue=', '/counts?story=', '/activity', '/insights', 'POST /react', 'POST /t'] }, origin);
  },
};
