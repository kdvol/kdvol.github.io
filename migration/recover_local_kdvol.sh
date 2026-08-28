#!/usr/bin/env bash
# 3b(히스토리 force-push) 직후 로컬 ~/kdvol.github.io 를 새 히스토리로 복구한다.
#
# 왜 필요한가: force-push 는 모든 커밋 해시를 바꾼다. 로컬 클론은 옛 히스토리에
# 앉아 있어 `git pull` 이 갈라진다. 이 스크립트가 **웹 미커밋 작업만 살리고**
# 새 히스토리로 리셋한다. 내부 파일(deploy.py·ops·workers·.claude 등)은 버린다 —
# 이미 soonsal-internal(Private)에 있고, kdvol 은 이제 웹만.
#
# 안전: 웹/내부 분류는 kdvol 의 block_internal.is_internal() 하나로. 미커밋 웹은
# 백업했다 되살린다. 아무것도 조용히 안 지운다.
set -euo pipefail
KDVOL="$HOME/kdvol.github.io"
BK="$HOME/kdvol-recovery-$(date +%Y%m%d-%H%M%S)"
cd "$KDVOL"

echo "═ 로컬 kdvol 복구 — 웹 미커밋 백업 → 새 히스토리 리셋 → 복원"
echo "  현재 HEAD: $(git rev-parse --short HEAD)"

# 1) 미커밋 중 '웹'만 백업 (is_internal=False). 내부는 버린다.
mkdir -p "$BK"
mapfile -d '' FILES < <(git status --porcelain -z | cut -c4- | tr '\n' '\0' 2>/dev/null || true)
python3 - "$KDVOL" "$BK" <<'PY'
import sys, os, shutil, subprocess
kdvol, bk = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(kdvol, "scripts"))
try:
    from block_internal import is_internal
except Exception:
    # 3a 후 로컬 scripts/ 가 지워졌을 수 있음 → soonsal-internal 사본 사용
    sys.path.insert(0, os.path.join(os.path.expanduser("~"), "soonsal-internal", "scripts"))
    from block_internal import is_internal
r = subprocess.run(["git","-C",kdvol,"status","--porcelain","-z"],capture_output=True)
saved=0
for ent in r.stdout.split(b"\0"):
    if len(ent) < 4: continue
    path = ent[3:].decode("utf-8","surrogateescape")
    if is_internal(path):  # 내부는 안 살린다
        continue
    src = os.path.join(kdvol, path)
    if os.path.isfile(src):
        dst = os.path.join(bk, path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst); saved += 1
        print(f"  백업(웹): {path}")
print(f"  웹 미커밋 {saved}개 백업")
PY

# 2) 새 히스토리 채택
echo "  fetch + reset --hard origin/main …"
git fetch -q origin main
git reset --hard origin/main
echo "  새 HEAD: $(git rev-parse --short HEAD)"

# 3) 웹 백업 복원
if [ -n "$(ls -A "$BK" 2>/dev/null)" ]; then
    cp -R "$BK"/. "$KDVOL"/
    echo "  ✓ 웹 미커밋 복원"
fi
echo "  ✓ 복구 완료. 백업 보관: $BK (확인 후 지워도 됨)"
echo "  ※ 내부 파일(deploy.py 등)은 이제 로컬에서 untracked/ignored 로 남거나 없음 — soonsal-internal 에 있음."
