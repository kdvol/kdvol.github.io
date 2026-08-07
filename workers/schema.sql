-- 순살 반응 집계 스키마 (Cloudflare D1)
-- 적용: npx wrangler d1 execute soonsal-react --remote --file schema.sql

create table if not exists reactions (
  story text not null,
  emoji text not null,
  count integer not null default 0,
  updated_at integer,              -- 마지막 반응 시각(unix seconds, UTC)
  primary key (story, emoji)
);
create index if not exists idx_reactions_story on reactions(story);

-- 시간대별 분포를 보려면 집계 테이블만으론 부족해서 클릭 로그를 따로 남긴다.
-- (발행 직후 몇 시간에 몰리는지, 회차별 반응 곡선 등)
create table if not exists events (
  id integer primary key autoincrement,
  story text not null,
  emoji text not null,
  delta integer not null,          -- +1 반응 / -1 취소
  ts integer not null              -- unix seconds, UTC
);
create index if not exists idx_events_ts on events(ts);
