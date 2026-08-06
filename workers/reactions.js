/**
 * 순살 반응 집계 Worker — Cloudflare Workers + KV (무료 티어)
 *
 * 배포(대시보드, 5분):
 *   1) Workers & Pages → Create → Worker → 이름 `soonsal-react` → Deploy
 *   2) Settings → Variables → KV Namespace Bindings → Add
 *      Variable name: REACTIONS  /  KV namespace: 새로 만들기(`soonsal-reactions`)
 *   3) Edit code → 이 파일 전체 붙여넣기 → Deploy
 *   4) 배포된 주소(https://soonsal-react.<계정>.workers.dev)를 /ss-config.js 에 넣기
 *
 * 엔드포인트
 *   POST /react     {story, emoji, delta:±1}  → 집계 증감 후 해당 스토리 카운트 반환
 *   GET  /counts?story=0805-1                 → {"👍":3,"🔥":1}
 *   GET  /counts                              → {"0805-1":{"👍":3}, ...}  (운영자 통계용)
 *
 * 저장 구조: key `r:{story}:{emoji}` , metadata {c:count}
 *   → list() 한 번으로 카운트까지 읽어 KV read 요청을 아낌(무료 한도 보호)
 */

const ALLOW_ORIGINS = ['https://soonsal.com', 'https://www.soonsal.com'];
const EMOJI = ['👍', '🤔', '🔥'];
const STORY_RE = /^[0-9]{4}c?-[0-9]{1,2}$/;   // 0805-1 / 0805c-3

function cors(origin) {
  const allow = ALLOW_ORIGINS.includes(origin) ? origin : ALLOW_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': allow,
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'content-type',
    'Access-Control-Max-Age': '86400',
  };
}

function json(data, origin, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', ...cors(origin) },
  });
}

async function countsFor(env, story) {
  const out = {};
  const list = await env.REACTIONS.list({ prefix: `r:${story}:` });
  for (const k of list.keys) {
    const emoji = k.name.split(':').pop();
    out[emoji] = (k.metadata && k.metadata.c) || 0;
  }
  return out;
}

async function countsAll(env) {
  const out = {};
  let cursor;
  do {
    const list = await env.REACTIONS.list({ prefix: 'r:', cursor });
    for (const k of list.keys) {
      const parts = k.name.split(':');           // r : story : emoji
      const story = parts[1], emoji = parts[2];
      const c = (k.metadata && k.metadata.c) || 0;
      if (!c) continue;
      (out[story] = out[story] || {})[emoji] = c;
    }
    cursor = list.list_complete ? null : list.cursor;
  } while (cursor);
  return out;
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: cors(origin) });
    }
    if (!env.REACTIONS) {
      return json({ error: 'KV binding REACTIONS 가 설정되지 않았습니다' }, origin, 500);
    }

    // 집계 조회
    if (request.method === 'GET' && url.pathname === '/counts') {
      const story = url.searchParams.get('story');
      if (story) {
        if (!STORY_RE.test(story)) return json({}, origin);
        return json(await countsFor(env, story), origin);
      }
      return json(await countsAll(env), origin);
    }

    // 반응 증감
    if (request.method === 'POST' && url.pathname === '/react') {
      let body;
      try { body = await request.json(); } catch (e) { return json({ error: 'bad json' }, origin, 400); }
      const { story, emoji } = body || {};
      const delta = Number(body && body.delta);

      if (!STORY_RE.test(String(story || ''))) return json({ error: 'bad story' }, origin, 400);
      if (!EMOJI.includes(emoji)) return json({ error: 'bad emoji' }, origin, 400);
      if (delta !== 1 && delta !== -1) return json({ error: 'bad delta' }, origin, 400);

      const key = `r:${story}:${emoji}`;
      const cur = await env.REACTIONS.getWithMetadata(key);
      const now = Math.max(((cur.metadata && cur.metadata.c) || 0) + delta, 0);
      await env.REACTIONS.put(key, String(now), { metadata: { c: now } });

      return json(await countsFor(env, story), origin);
    }

    return json({ ok: true, endpoints: ['/counts', '/counts?story=', 'POST /react'] }, origin);
  },
};
