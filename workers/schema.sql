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

-- ── 방문·참여 트래킹 (2026-08-11) ──────────────────────────────
-- 목표는 페이지뷰 숫자가 아니라 "다시 오는 사람이 있는가, 반응하는가".
-- 원본 로그를 쌓지 않고 일자별로 집계만 남긴다(용량·프라이버시 양쪽).
-- 개인정보는 저장하지 않는다 — IP·UA·쿠키 없음, localStorage의 익명 난수 ID만.

create table if not exists views (
  day  text not null,              -- KST 기준 YYYY-MM-DD
  path text not null,
  hits integer not null default 0,
  uniq integer not null default 0, -- 그날 그 페이지를 처음 연 사람 수
  primary key (day, path)
);

create table if not exists visitors (
  vid       text primary key,      -- 익명 난수(브라우저 localStorage)
  first_day text not null,
  last_day  text not null,
  days      integer not null default 1,   -- 방문한 날짜 수 → 재방문 판정
  hits      integer not null default 0
);
create index if not exists idx_visitors_last on visitors(last_day);

create table if not exists engage (
  day  text not null,
  kind text not null,              -- read / react / share / telegram / instagram
  n    integer not null default 0,
  primary key (day, kind)
);

create table if not exists refs (
  day text not null,
  src text not null,               -- direct / telegram / instagram / search / mail / other
  n   integer not null default 0,
  primary key (day, src)
);
