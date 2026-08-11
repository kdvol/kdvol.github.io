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
    'Access-Control-Allow-Headers': 'content-type',
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
const KIND = ['read', 'react', 'share', 'telegram', 'instagram'];
const SRC = ['direct', 'telegram', 'instagram', 'search', 'mail', 'other'];
const VID_RE = /^[a-z0-9]{8,24}$/;
// KST 자정 기준 날짜. UTC로 끊으면 한국 새벽 방문이 전날로 잡힌다.
const DAY = "date(unixepoch() + 32400, 'unixepoch')";

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
  async fetch(request, env) {
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

      // 운영자 통계용 — 마지막 반응 시각 + 최근 14일 클릭 로그
      if (request.method === 'GET' && url.pathname === '/activity') {
        const [lastQ, evQ] = await env.DB.batch([
          env.DB.prepare('select story, max(updated_at) as t from reactions where updated_at is not null group by story'),
          env.DB.prepare("select ts, story, delta from events where ts > unixepoch() - 1209600 order by ts"),
        ]);
        const last = {};
        for (const r of lastQ.results || []) last[r.story] = r.t;
        const events = (evQ.results || []).map((r) => [r.ts, r.story, r.delta]);
        return json({ last, events, now: Math.floor(Date.now() / 1000) }, origin);
      }

      // ── 방문·참여 수집 ────────────────────────────────────
      // 응답 본문이 없다(204). 실패해도 페이지에 영향 주지 않는 게 우선.
      if (request.method === 'POST' && url.pathname === '/t') {
        let b;
        try { b = await request.json(); } catch (e) { return new Response(null, { status: 204, headers: cors(origin) }); }
        const vid = String((b && b.v) || '');
        if (!VID_RE.test(vid)) return new Response(null, { status: 204, headers: cors(origin) });

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

        return json({
          days,
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
