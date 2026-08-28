#!/usr/bin/env bash
# 순살차트 로컬 발행 — publish_local.sh(뉴스레터)의 차트판.
#
# 왜 필요한가: 3a 성역 이관으로 kdvol 본체에서 scripts/ 가 빠지면서,
# `content_os.py stage-site --site-root ~/kdvol.github.io` 는 build_nav.py 를
# 못 찾아 **티커 띠·로고 후처리를 건너뛴다**(티커 없는 차트가 발행됨).
# 그래서 뉴스레터와 똑같이 overlay 로 돌린다:
#   work-tree 를 origin 으로 리셋 → 내부 스크립트를 겹침(build_nav·_ticker 포함)
#   → stage-site 가 그 트리에서 티커까지 주입 → chart/ 만 kdvol push.
# ~/kdvol.github.io 본체는 안 건드린다. 빌드 스크립트는 한 줄도 안 고친다.
#
# 사용:
#   bash ~/soonsal-internal/publish_chart_local.sh <YYYY-MM-DD> [--dedupe-why '…'] [--no-push]
set -euo pipefail
INT="$HOME/soonsal-internal"
WORK="$HOME/.soonsal-web-work"
BUILD="$HOME/soonsal-build"
DATE="${1:?사용: publish_chart_local.sh <YYYY-MM-DD> [--dedupe-why '…'] [--no-push]}"; shift || true

DEDUPE=()
NOPUSH=0
while [ $# -gt 0 ]; do
  case "$1" in
    --no-push)    NOPUSH=1; shift;;
    --dedupe-why) DEDUPE=(--dedupe-why "$2"); shift 2;;
    *) echo "❌ 모르는 인자: $1"; exit 1;;
  esac
done

YEAR="${DATE:0:4}"
MMDD="${DATE:5:2}${DATE:8:2}"
PAGE="chart/$YEAR/$MMDD.html"

echo "▶ 작업 체크아웃 준비 ($WORK)"
if [ ! -d "$WORK/.git" ]; then
  git clone --quiet --depth 1 https://github.com/kdvol/kdvol.github.io.git "$WORK"
else
  git -C "$WORK" fetch -q --depth 1 origin main
  git -C "$WORK" reset -q --hard origin/main
  git -C "$WORK" clean -qfd
fi

echo "▶ 내부 겹치기 (overlay — build_nav·_ticker 포함)"
python3 "$INT/ci/crossrepo_sync.py" overlay --int "$INT" --web "$WORK" >/dev/null

echo "▶ stage-site (차트 굽기 + 티커 주입)"
# content_os 는 input/·output/ 을 CWD 기준으로 읽는다 → 반드시 soonsal-build 에서 실행.
# --site-root(절대경로 $WORK)로 쓰기 대상만 작업트리로 돌린다.
( cd "$BUILD" && python3 scripts/content_os.py stage-site --date "$DATE" --site-root "$WORK" --apply ${DEDUPE[@]+"${DEDUPE[@]}"} )

# 티커 주입 검증 — 안 들어갔으면 발행 중단 (티커 없는 차트를 라이브에 올리지 않는다)
if [ ! -f "$WORK/$PAGE" ]; then
  echo "❌ 차트 페이지 없음: $PAGE — stage-site 실패"; exit 1
fi
TICKS="$(grep -c 'ticker' "$WORK/$PAGE" || true)"
if [ "${TICKS:-0}" -lt 1 ]; then
  echo "❌ 티커 미주입 (마커 0개) — build_nav 가 안 돌았다. 발행 중단"; exit 1
fi
echo "  ✅ 티커 마커 $TICKS 개"

echo "▶ chart/ 만 커밋 (다른 페이지의 티커 갱신은 안 싣는다)"
git -C "$WORK" add chart/
if git -C "$WORK" diff --cached --quiet; then
  echo "  변경 없음 — 끝"; exit 0
fi
git -C "$WORK" -c user.name=soonsal-bot -c user.email=bot@soonsal.com \
  commit -q -m "chart: $DATE 발행"
# build_nav 가 건드린 chart/ 밖 페이지의 미스테이지 변경은 버린다 (다음 리셋서 어차피 새로)
git -C "$WORK" checkout -q -- . 2>/dev/null || true

if [ "$NOPUSH" = "1" ]; then
  echo "▶ [--no-push] 커밋만 만들고 멈춤: $(git -C "$WORK" rev-parse --short HEAD)"
  echo "  나갈 파일:"; git -C "$WORK" show --stat --oneline HEAD | sed 's/^/    /'
  exit 0
fi

echo "▶ kdvol push (웹만)"
git -C "$WORK" pull --rebase -q origin main
git -C "$WORK" push -q origin main && echo "  ✅ push 완료 → soonsal.com/$PAGE"

echo "▶ 내부 상태 회수 (작업트리 → soonsal-internal)"
python3 "$INT/ci/crossrepo_sync.py" harvest --int "$INT" --web "$WORK" >/dev/null || true
git -C "$INT" add -A
if ! git -C "$INT" diff --cached --quiet; then
  git -C "$INT" commit -q -m "local chart publish: 내부 상태 회수 ($DATE)" || true
  git -C "$INT" pull --rebase -q origin main 2>/dev/null || true
  git -C "$INT" push -q origin main 2>/dev/null || true
fi
echo "✓ 차트 발행 완료 — 웹→kdvol, 내부→soonsal-internal. ~/kdvol.github.io 본체는 안 건드림."
