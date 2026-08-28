#!/usr/bin/env bash
# 로컬 웹 발행 — 스크립트는 soonsal-internal 에만 둔다(성역 격리). kdvol 본체
# (~/kdvol.github.io)는 순수 웹으로 두고 절대 안 건드린다.
#
# 왜 래퍼인가: 빌드 스크립트 13개가 straddle 한다 — 한 ROOT 로 내부(content/)를
# 읽고 웹(index·chart)을 쓴다. 그래서 내부+웹이 **한 트리**에 있어야 돈다.
# 클라우드 Actions 가 하는 것과 똑같이: 전용 작업 체크아웃에 내부를 겹쳐
# (overlay) deploy.py 를 돌리고, 웹은 kdvol 로 push, 내부 상태는 여기로 회수한다.
# 빌드 스크립트는 한 줄도 안 고친다.
#
# 사용:
#   bash ~/soonsal-internal/publish_local.sh <source.html> [deploy.py 인자...]
#   예) bash ~/soonsal-internal/publish_local.sh ~/Downloads/순살브리핑_20260827.html --no-instagram
set -euo pipefail
INT="$HOME/soonsal-internal"
WORK="$HOME/.soonsal-web-work"
SRC="${1:?사용: publish_local.sh <source.html> [deploy 인자...]}"; shift || true
[ -f "$SRC" ] || { echo "❌ 소스 파일 없음: $SRC"; exit 1; }

echo "▶ 작업 체크아웃 준비 ($WORK)"
if [ ! -d "$WORK/.git" ]; then
  echo "  최초 1회 — kdvol clone (shallow, _publish 없어 가벼움)…"
  git clone --quiet --depth 1 https://github.com/kdvol/kdvol.github.io.git "$WORK"
else
  git -C "$WORK" fetch -q --depth 1 origin main
  git -C "$WORK" reset -q --hard origin/main
  git -C "$WORK" clean -qfd     # 이전 회차 잔재 정리 (gitignore된 내부는 아래 overlay가 새로 덮음)
fi

echo "▶ 내부 겹치기 (overlay — 내부만, 웹은 그대로)"
python3 "$INT/ci/crossrepo_sync.py" overlay --int "$INT" --web "$WORK" >/dev/null

echo "▶ deploy.py 실행 (작업트리에서, 웹→kdvol push)"
KDVOL_ROOT="$WORK" INSTAGRAM_PIPELINE="$HOME/instagram_pipeline" \
  python3 "$WORK/deploy.py" "$SRC" "$@"

echo "▶ 내부 상태 회수 (작업트리 → soonsal-internal)"
python3 "$INT/ci/crossrepo_sync.py" harvest --int "$INT" --web "$WORK" >/dev/null || true
git -C "$INT" add -A
if ! git -C "$INT" diff --cached --quiet; then
  git -C "$INT" commit -q -m "local publish: 내부 상태 회수 ($(basename "$SRC"))" || true
  git -C "$INT" pull --rebase -q origin main 2>/dev/null || true
  git -C "$INT" push -q origin main 2>/dev/null || true
fi

echo "✓ 발행 완료 — 웹→kdvol, 내부→soonsal-internal. ~/kdvol.github.io 본체는 안 건드림."
echo "  최신 웹 로컬에서 보려면:  git -C ~/kdvol.github.io pull"
