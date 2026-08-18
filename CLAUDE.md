
## 채널 상호 링크 (순살 브랜드 대원칙)

순살은 같은 이야기를 여러 채널에 낸다. **채널끼리 서로를 가리켜야 한다.**
2026-08-15 실측으로 인스타 400건 중 다른 채널을 가리킨 캡션이 0건이었다.

발행 원장: `~/soonsal-build/content_os/registry/works.jsonl`

```bash
cd ~/soonsal-build
python3 scripts/registry.py gaps       # 링크가 빠진 작품
python3 scripts/registry.py plan MMDD  # 어디에 무슨 링크를 걸지
```

발행 전에 원장을 읽고, 발행 뒤에 나가는 링크를 채운다. 2차 생산
(카드뉴스→숏츠, 순살차트→스레드)도 파생 관계를 원장에 남긴다.

거는 자리 — 유튜브는 설명란, 스레드는 마지막 편, 웹은 페이지 하단.

**인스타에는 링크를 걸지 않는다** (2026-08-16 정정). 캡션도 댓글도 링크가
눌리지 않는다 — 걸어 봐야 아무도 못 누르고 상호 링크로 세지도 못한다.
인스타에서 채널을 잇는 길은 프로필 링크(하나뿐)와 스토리 링크 스티커다.
대신 **첫 댓글은 대화를 부르는 데 쓴다** — 한 줄 요약 + 독자에게 던지는 질문.
댓글 수 자체가 노출 신호다. 130자를 넘지 않는다.

## 뉴스레터 링크에 구독자 표시 (2026-08-16)

메일 안의 순살 웹 링크에는 `?ss=$%web_tag%$.<회차>` 를 붙인다. **`&` 를 쓰지 않는다** — 메일에서 `&amp;` 로 나가 뒷값이 사라진다. 안 붙이면
읽은 사람 수를 못 센다 — 메일 앱은 브라우저 저장소를 매번 비워서 같은 사람이
매일 새 사람으로 잡힌다.

절차와 금지 사항: `~/soonsal-build/rules/newsletter_link_tagging.md`

고지·동의는 이미 갱신했다(`/privacy/`, 구독 페이지). 가명 처리된 정보이므로
**개인별 발송·타게팅·제3자 제공은 하지 않는다.** 낱개 기록은 90일.

```bash
python3 scripts/reads_admin.py --status          # 쌓이고 있나
python3 scripts/reads_admin.py --optout <표시값>  # 연결 끄기
```

## 다른 채널이 배운 것 (2026-08-17)

이 저장소(웹)에서 일할 때도 다른 채널 학습을 먼저 본다. 사람이 옮기지 않으면
안 흐른다.

```bash
cd ~/soonsal-build && python3 scripts/learnings.py inbox --channel web
```

배운 게 있으면 `learnings.py add --evidence "…"` 로 넣는다. 근거 없이는 안 들어간다.
원장은 `~/soonsal-build/content_os/registry/learnings.jsonl`,
웹 사본은 `/ops/learnings.json` (robots.txt 로 색인 차단).

## 만들기 전에 계보를 읽는다 (2026-08-18)

새 꼭지를 기획할 때 **같은 주제로 전에 낸 것**을 먼저 뽑아 읽는다 — 뉴스레터·
차트·스레드·카드뉴스·릴스·숏츠 전부. 발행 직전 관문이 아니라 **기획 첫머리의
재료**다. 이미 검증된 사실·인물·비유는 다시 캐지 않고, 성과가 붙은 편은
짜임새(조각 수·반전 위치·1편 훅·착지)까지 가져온다.

```bash
cd ~/soonsal-build && python3 scripts/lineage.py brief --text "<이번 꼭지 요지>"
```

빌드가 자동으로 `output/distribution/<날짜>/LINEAGE.md` 에 남긴다.
웹 3회차 중복 회피(C28)와 부딪히면 **C28 이 이긴다.**

