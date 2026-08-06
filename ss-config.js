/* 순살 공용 설정 — 반응 집계 백엔드 (Cloudflare Worker + KV, 무료)
 * Worker 소스: workers/reactions.js  ·  배포: cd workers && npx wrangler deploy
 * 집계 확인: /stats/ */
window.SS_CFG = { worker: "https://soonsal-react.kd-d0a.workers.dev" };
