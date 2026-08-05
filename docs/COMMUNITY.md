# 순살 커뮤니티 실험 (1·2·3단계)

목표: 리멤버(고퀄) × 토스(쉬운 참여)의 중간. **앱 없이 웹만 고도화**, 인프라 대공사 없이.

---

## 1단계 — 텔레그램에서 씨앗 뿌리기 (코드 0줄)

링크만 던지면 읽고 끝남 → **논점을 던져야 답이 온다.** 매일 브리핑 공유 시 셋 중 하나:

| 유형 | 왜 | 예시 |
|---|---|---|
| **Poll** (권장 1순위) | 탭 한 번이라 침묵하던 사람도 참여 | "이 딜 성사될까? ①된다 ②안 된다 ③조건부" |
| **경험 질문** | 실무자 답변 = 리멤버식 고퀄 | "금융권 계신 분들, 실제 분위기 이런가요?" |
| **논쟁형** | 반대 의견이 대화를 만듦 | "관세는 별거 아니라는 증거일까, 잠깐 들른 돈일까?" |

**핵심 순환:** poll 결과·좋은 답변을 **다음날 브리핑에 인용** → "쓰면 실린다"를 학습 → 더 쓴다.
답글엔 반드시 리액션. 초기 커뮤니티는 "말하면 반응이 온다"가 전부.

---

## 2단계 — 웹에 참여 장치 (구현 완료, 무료)

`soonsal.js` 한 파일에 구현 → 전 페이지 자동 적용, 페이지 재주입 불필요.

- **스토리별 반응 버튼** (👍 좋아요 / 🤔 글쎄요 / 🔥 중요) — 로그인 없음.
  기본은 로컬 기록, Supabase 설정 시 **공유 집계로 자동 승격**.
- **오늘의 논점 블록** — 브리핑 하단에서 텔레그램 토론으로 유도 (웹→텔레그램).
- 역방향(텔레그램→웹)은 스토리별 공유 링크(`/s/{id}.html`)로 이미 연결됨.

---

## 3단계 — Supabase 무료 티어 (키만 넣으면 활성화)

**비용 0**: 프리티어 500MB DB · 5만 MAU면 순살 규모에 한참 남음. 카드 등록 불필요.

### 설정 순서

1. [supabase.com](https://supabase.com) 무료 프로젝트 생성
2. SQL 편집기에서 아래 실행:

```sql
create table reactions (
  story text not null,
  emoji text not null,
  count int not null default 0,
  primary key (story, emoji)
);
alter table reactions enable row level security;
-- 누구나 읽기 가능(집계 표시용)
create policy "read" on reactions for select using (true);

-- 반응 증감은 RPC로만(직접 UPDATE 차단 → 어뷰징 방지)
create or replace function react(p_story text, p_emoji text, p_delta int)
returns void language plpgsql security definer as $$
begin
  insert into reactions(story, emoji, count) values (p_story, p_emoji, greatest(p_delta,0))
  on conflict (story, emoji)
  do update set count = greatest(reactions.count + p_delta, 0);
end; $$;
```

3. 프로젝트 설정에서 **URL**과 **anon public key**를 복사해, 사이트 `<head>` 어딘가에
   (또는 `soonsal.js` 로드 전에) 다음 한 줄 추가:

```html
<script>window.SS_CFG={supabase:{url:"https://xxxx.supabase.co",key:"eyJhbGci..."}}</script>
```

> anon key는 공개돼도 되는 키(RLS로 보호). 서비스 키는 절대 웹에 넣지 말 것.

4. 끝. 반응 버튼이 자동으로 공유 집계 모드가 되고, 숫자가 버튼에 표시됨.

### 다음 확장(원할 때)
- 카카오 로그인 → 닉네임 + 자기신고 배지("IB 5년차", "개인투자자")
  = 실명 부담 없이 발언에 무게. 리멤버×토스 하이브리드의 핵심.
- 댓글 테이블 추가(같은 RLS 패턴)
