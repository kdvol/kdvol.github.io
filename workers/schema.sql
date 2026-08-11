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

-- ── 스토리별 익명 코멘트 (2026-08-11) ─────────────────────────
-- state: 1 공개 / 0 보류 / -1 숨김 / -2 스팸
-- 보류 건은 사람이 아니라 scripts/moderate_comments.py(LLM)가 처리한다.
-- issue는 클라이언트 입력을 믿지 않고 서버가 story에서 잘라 넣는다.
create table if not exists comments (
  id    integer primary key autoincrement,
  story text not null,              -- 0811-3 / 0811c-2
  issue text not null,              -- 0811 / 0811c
  nick  text not null,
  body  text not null,
  vid   text not null,              -- 익명 난수(localStorage). 개인정보 아님
  ts    integer not null,
  state integer not null default 1,
  flags integer not null default 0,
  hold  text,                       -- 보류 사유 url/lead/tel/spam/flag/word
  judge text,                       -- LLM 판정 근거(자동 모더레이션 기록)
  tag   text                        -- 자칭 업종(프리셋) — 검증된 소속이 아니다
);
create index if not exists idx_c_issue on comments(issue, state, id desc);
create index if not exists idx_c_vid   on comments(vid, ts);
create index if not exists idx_c_mod   on comments(state, id desc);

create table if not exists blocks (
  vid text primary key, ts integer not null, note text
);

create table if not exists modwords (   -- 재배포 없이 금칙어 추가
  w text primary key, ts integer not null
);

-- 집계에서 뺄 브라우저 (운영자 본인·개발용 접속)
-- localStorage만으로 막으면 그 브라우저를 지우는 순간 다시 섞인다.
-- 서버에도 남겨 두면 같은 ID로 오는 한 영구히 제외된다.
create table if not exists tracking_optout (
  vid text primary key,
  ts  integer not null
);

-- 대댓글: parent_id가 있으면 그 댓글에 달린 답글이다(1단계만 — 트리가 깊어지면
-- 모바일에서 읽을 수 없다). 스레드 정렬은 (root_id, id)로 한다.
-- comments에 아래 두 컬럼을 더한다:
--   parent_id integer  답글 대상 댓글 id
--   root_id   integer  스레드 최상위 id(자기 자신이면 자기 id)

-- 댓글 좋아요. 익명 번호당 한 번, 취소 가능.
create table if not exists comment_likes (
  cid integer not null,
  vid text not null,
  ts  integer not null,
  primary key (cid, vid)
);
create index if not exists idx_cl_cid on comment_likes(cid);

-- 이동 쌍: "A 다음 B를 봤다"를 경로 쌍으로만 센다.
-- 누가 그랬는지는 남기지 않는다 — 개인별 열람 이력을 만들지 않는다는 약속을
-- 지키면서 "어디서 와서 무엇을 더 보는지"만 본다.
create table if not exists hops (
  day  text not null,
  frm  text not null,
  to_  text not null,
  n    integer not null default 0,
  primary key (day, frm, to_)
);
create index if not exists idx_hops_day on hops(day);

-- 알림: 내 댓글에 답글이 달리거나 좋아요를 받으면 한 줄 쌓인다.
-- 이메일 없이 익명 번호로만 전달한다 — 다음 방문 때 사이트에서 보여준다.
-- 읽으면 seen=1, 90일 지난 건 자동 삭제(보관 목적이 없다).
create table if not exists notices (
  id   integer primary key autoincrement,
  vid  text not null,              -- 받는 사람(익명 번호)
  kind text not null,              -- reply | like
  cid  integer not null,           -- 내 댓글 id
  rid  integer,                    -- 답글 id (kind=reply)
  who  text,                       -- 상대 닉네임(표시용)
  story text not null,
  ts   integer not null,
  seen integer not null default 0
);
create index if not exists idx_nt_vid on notices(vid, seen, id desc);
