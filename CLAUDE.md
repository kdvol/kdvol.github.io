
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

거는 자리 — **인스타는 발행 뒤 캡션 수정이 안 되므로 첫 댓글**,
유튜브는 설명란, 스레드는 마지막 편, 웹은 페이지 하단.

## 뉴스레터 링크에 구독자 표시 (2026-08-16)

메일 안의 순살 웹 링크에는 `?s=<16자리 hex>&i=<회차>` 를 붙인다. 안 붙이면
읽은 사람 수를 못 센다 — 메일 앱은 브라우저 저장소를 매번 비워서 같은 사람이
매일 새 사람으로 잡힌다.

절차와 금지 사항: `~/soonsal-build/rules/newsletter_link_tagging.md`

고지·동의는 이미 갱신했다(`/privacy/`, 구독 페이지). 가명 처리된 정보이므로
**개인별 발송·타게팅·제3자 제공은 하지 않는다.** 낱개 기록은 90일.

```bash
python3 scripts/reads_admin.py --status          # 쌓이고 있나
python3 scripts/reads_admin.py --optout <표시값>  # 연결 끄기
```
