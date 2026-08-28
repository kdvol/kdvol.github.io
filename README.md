# soonsal-internal

순살 웹(kdvol.github.io)의 자동화·발행 파이프라인 **비공개** 저장소.

2026-08-26 성역 규칙(KD)에 따라 `kdvol.github.io`(Public)에서 분리됐다.
kdvol 은 **웹 결과물만** 담고, 제작·발행 코드·규칙·큐·원장은 전부 여기 있다.

> 웹사이트에 실제로 보이는 것만 Public. 그 외 내부 정보는 전부 여기(Private).

## 구조
- `scripts/`, `ci/`, `ig_pipeline/`, `workers/` — 자동화 코드
- `content/`, `_queue/`, `_publish/`, `ops/`, `docs/` — 상태·원장·큐

## cross-repo 배선 (핵심)

GitHub Actions 는 **이 저장소**를 checkout 해 파이프라인을 돌린다.
웹 산출물만 kdvol 로 나가고, 내부 상태는 여기 커밋된다.

| 산출물 | 분류 | 커밋 대상 |
|---|---|---|
| `api/signals.json`·`sitemap.xml`·`rss.xml`·`robots.txt` | 웹 | → kdvol (deploy key) |
| `_queue/`→`done/`·`content/signals.json`·원장·`_publish/` | 내부 | → soonsal-internal |

- **웹/내부 분류 기준**: `scripts/block_internal.py` 의 `is_internal()` (단일 진실)
- **kdvol write 자격**: deploy key, `KDVOL_DEPLOY_KEY` secret
- **분리/조립 로직**: `ci/crossrepo_sync.py` (로컬에서 selftest 가능)

## 왜 스크립트는 그대로인가

발행 스크립트는 kdvol 에서 돌던 것과 **한 글자도 안 바꿨다**. Actions 가
kdvol 웹트리와 이 저장소를 한 작업트리로 합쳐(경로가 서로 겹치지 않는다)
스크립트를 예전과 똑같은 환경에서 돌린 뒤, 결과만 웹/내부로 갈라 커밋한다.
「기존에 없던 오류가 안 난다」가 이 설계의 최상위 제약이다(KD 2026-08-26).
