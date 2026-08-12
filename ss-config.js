/* 순살 공용 설정 — 반응·코멘트 집계 백엔드 (Cloudflare Worker + D1)
 * Worker 소스: workers/reactions.js  ·  배포: cd workers && npx wrangler deploy
 * 집계 확인: /stats/
 *
 * hosts는 시도 순서다. workers.dev는 광고 차단기·사내망·일부 DNS 필터가
 * 통째로 막는 경우가 있다(실제로 겪음). 그럴 때 반응·코멘트·순살톡이 전부
 * 조용히 죽는다. 자사 도메인(api.soonsal.com)을 앞에 두면 그 실패가 사라진다.
 *
 * 2026-08-13: api.soonsal.com을 워커 커스텀 도메인으로 붙이고 맨 앞에 뒀다.
 */
window.SS_CFG = {
  hosts: [
    "https://api.soonsal.com",                      // 자사 도메인 — 차단기에 안 걸린다
    "https://soonsal-react.kd-d0a.workers.dev"      // 예비
  ]
};
window.SS_CFG.worker = window.SS_CFG.hosts[0];   // 예전 코드 호환
