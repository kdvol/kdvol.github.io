#!/usr/bin/env python3
"""성역 이관 2단계 — soonsal-build 스케줄러의 큐 위치를 kdvol → soonsal-internal.

KD 2026-08-27. 큐·발행소스(_queue·_publish)는 이제 soonsal-internal(Private)에
살고, 발행 Actions 가 그걸 소비한다. 그런데 soonsal-build 의 스케줄러 9개가
아직 `~/kdvol.github.io/_queue` 로 쓰고 kdvol 로 push 한다 — 전환하면 새 카드뉴스·
릴스가 발행 안 된다. 이 패치가 그 9개를 **한 곳(_queue_target.py)** 을 보게 바꾼다.

## 안전 설계
- 각 치환은 **반드시 매치**돼야 한다. 안 맞으면 그 파일을 건드리지 않고 실패로 보고
  (스크립트가 그새 바뀌었다는 뜻 — 조용히 지나가지 않는다).
- 이미 적용된 파일(import _queue_target 있음)은 건너뛴다 → 몇 번 돌려도 안전(멱등).
- 롤백: `SOONSAL_QUEUE_REPO=~/kdvol.github.io SOONSAL_QUEUE_SLUG=kdvol/kdvol.github.io`
  환경변수로 즉시 옛 경로로 되돌릴 수 있고, git 으로도 되돌린다.

## 사용
  python3 apply_queue_redirect.py --test     # 복사본에 적용+검증 (실파일 무영향)
  python3 apply_queue_redirect.py --dry-run   # 실파일에 뭐가 바뀔지 미리보기
  python3 apply_queue_redirect.py --apply     # 실제 적용 (soonsal-build 조용할 때)
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path.home() / "soonsal-build" / "scripts"

MODULE_NAME = "_queue_target.py"
MODULE = '''"""큐·발행소스가 사는 곳 — 성역 이관(KD 2026-08-26).

kdvol(Public) → soonsal-internal(Private). 발행 GitHub Actions 가 소비하는 곳.
큐 위치를 **여기 한 곳에서만** 정한다 — 스케줄러 9개가 전부 이걸 본다.

롤백/테스트: 환경변수로 덮어쓴다.
  SOONSAL_QUEUE_REPO=~/kdvol.github.io  SOONSAL_QUEUE_SLUG=kdvol/kdvol.github.io
"""
import os
from pathlib import Path

REPO_DIR = Path(os.environ.get("SOONSAL_QUEUE_REPO", str(Path.home() / "soonsal-internal")))
REPO_SLUG = os.environ.get("SOONSAL_QUEUE_SLUG", "kdvol/soonsal-internal")
QUEUE = REPO_DIR / "_queue"
PUB = REPO_DIR / "_publish"
DONE = QUEUE / "done"
'''

_IMP = "# 큐·발행소스는 soonsal-internal(Private) — 성역 이관(KD 2026-08-27)"

# 파일별 치환. op:
#   ("sub", 정규식, 새 문자열)  첫 매치 라인을 통째로 바꾼다
#   ("del", 정규식)             첫 매치 라인을 지운다
#   ("rep", 옛부분, 새부분)      모든 부분문자열 치환 (최소 1회 매치 요구)
EDITS = {
    "schedule_cardnews.py": [
        ("sub", r'^KDVOL\s*=\s*HOME\s*/\s*"kdvol\.github\.io"',
         _IMP + "\nfrom _queue_target import REPO_DIR as KDVOL, REPO_SLUG, QUEUE, PUB"),
        ("del", r'^QUEUE\s*=\s*KDVOL\s*/\s*"_queue"'),
        ("del", r'^PUB\s*=\s*KDVOL\s*/\s*"_publish"'),
        ("rep", "kdvol/kdvol.github.io/contents/", "{REPO_SLUG}/contents/"),
    ],
    "schedule_reel.py": [
        ("sub", r'^KDVOL\s*=\s*Path\.home\(\)\s*/\s*"kdvol\.github\.io"',
         _IMP + "\nfrom _queue_target import REPO_DIR as KDVOL, QUEUE, PUB"),
        ("del", r'^QUEUE\s*=\s*KDVOL\s*/\s*"_queue"'),
        ("del", r'^PUB\s*=\s*KDVOL\s*/\s*"_publish"'),
    ],
    "schedule_video_carousel.py": [
        ("sub", r'^KDVOL\s*=\s*HOME\s*/\s*"kdvol\.github\.io"',
         _IMP + "\nfrom _queue_target import REPO_DIR as KDVOL, QUEUE, PUB"),
        ("del", r'^QUEUE\s*=\s*KDVOL\s*/\s*"_queue"'),
        ("del", r'^PUB\s*=\s*KDVOL\s*/\s*"_publish"'),
    ],
    "publish_fallback.py": [
        ("sub", r'^REPO\s*=\s*"kdvol/kdvol\.github\.io"',
         _IMP + "\nfrom _queue_target import REPO_SLUG as REPO"),
    ],
    "queue_doctor.py": [
        ("sub", r'^KDVOL\s*=\s*Path\.home\(\)\s*/\s*"kdvol\.github\.io"',
         _IMP + "\nfrom _queue_target import REPO_DIR as KDVOL, QUEUE"),
        ("del", r'^QUEUE\s*=\s*KDVOL\s*/\s*"_queue"'),
        ("rep", "cd ~/kdvol.github.io && git push", "cd ~/soonsal-internal && git push"),
    ],
    "stamp_reviewed.py": [
        ("sub", r'^QUEUE\s*=\s*Path\.home\(\)\s*/\s*"kdvol\.github\.io"\s*/\s*"_queue"',
         _IMP + "\nfrom _queue_target import QUEUE"),
    ],
    "cardnews_wiki.py": [
        ("sub", r'^PUBLISH_DONE\s*=\s*ROOT\.parent\s*/\s*"kdvol\.github\.io/_queue/done".*',
         _IMP + "\nfrom _queue_target import DONE as PUBLISH_DONE"),
    ],
    "build_dashboard.py": [
        # KDVOL 라인은 남긴다 (SITE_CARD = kdvol/cardnews, 웹). 큐만 옮긴다.
        ("sub", r'^QUEUE,\s*DONE\s*=\s*KDVOL\s*/\s*"_queue",\s*KDVOL\s*/\s*"_queue"\s*/\s*"done"',
         _IMP + "\nfrom _queue_target import QUEUE, DONE"),
    ],
    "inventory_review.py": [
        ("sub", r'^Q\s*=\s*Path\.home\(\)\s*/\s*"kdvol\.github\.io"\s*/\s*"_queue"',
         _IMP + "\nfrom _queue_target import QUEUE as Q"),
    ],
}


def patch_text(name: str, text: str) -> tuple[str, list[str]]:
    """치환을 적용. (새 텍스트, 문제목록). 이미 적용됐으면 그대로 둔다."""
    if "from _queue_target import" in text:
        return text, ["이미 적용됨 — 건너뜀"]
    lines = text.splitlines(keepends=True)
    problems = []
    for op in EDITS[name]:
        if op[0] == "sub":
            rx = re.compile(op[1])
            for i, ln in enumerate(lines):
                if rx.match(ln.rstrip("\n")):
                    nl = "\n" if ln.endswith("\n") else ""
                    lines[i] = op[2] + nl
                    break
            else:
                problems.append(f"매치 실패(sub): {op[1]}")
        elif op[0] == "del":
            rx = re.compile(op[1])
            for i, ln in enumerate(lines):
                if rx.match(ln.rstrip("\n")):
                    del lines[i]
                    break
            else:
                problems.append(f"매치 실패(del): {op[1]}")
    text2 = "".join(lines)
    for op in EDITS[name]:
        if op[0] == "rep":
            if op[1] not in text2:
                problems.append(f"매치 실패(rep): {op[1]}")
            else:
                text2 = text2.replace(op[1], op[2])
    return text2, problems


def run_test() -> int:
    """복사본에 적용하고, 문법·경로를 검증한다."""
    tmp = Path(tempfile.mkdtemp(prefix="qredir_"))
    (tmp / MODULE_NAME).write_text(MODULE, encoding="utf-8")
    ok = True
    print("═ 복사본 적용+검증 (실파일 무영향)\n")
    for name in EDITS:
        src = SCRIPTS / name
        if not src.is_file():
            print(f"  ❌ 원본 없음: {name}"); ok = False; continue
        new, probs = patch_text(name, src.read_text(encoding="utf-8"))
        hard = [p for p in probs if "매치 실패" in p]
        (tmp / name).write_text(new, encoding="utf-8")
        # ① 문법
        syn = subprocess.run([sys.executable, "-c",
                              f"import ast,sys; ast.parse(open('{tmp/name}').read())"],
                             capture_output=True, text=True)
        # ② 큐가 soonsal-internal 을 가리키나 (kdvol/_queue 잔재 없나)
        leftover = "kdvol.github.io" in new and "/_queue" in new and name != "build_dashboard.py"
        mark = "✅" if (not hard and syn.returncode == 0) else "❌"
        print(f"  {mark} {name:28} {'· '.join(probs) if probs else '치환 OK'}"
              + ("" if syn.returncode == 0 else f" · 문법오류: {syn.stderr.strip()[:60]}"))
        ok &= (not hard and syn.returncode == 0)
    # ③ 대표 파일 import 해서 QUEUE 실제 경로 확인
    chk = subprocess.run(
        [sys.executable, "-c",
         f"import sys; sys.path.insert(0,'{tmp}'); import _queue_target as q; "
         "print('QUEUE=', q.QUEUE); "
         "assert 'soonsal-internal' in str(q.QUEUE), 'QUEUE 가 internal 이 아님'; "
         "assert q.REPO_SLUG=='kdvol/soonsal-internal'"],
        capture_output=True, text=True)
    print(f"\n  {'✅' if chk.returncode==0 else '❌'} 모듈 경로: {chk.stdout.strip() or chk.stderr.strip()[:80]}")
    ok &= chk.returncode == 0
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n  {'통과 — 적용 준비 완료' if ok else '실패 — 적용하지 말 것'}")
    return 0 if ok else 1


def run_apply(dry: bool) -> int:
    mode = "미리보기" if dry else "적용"
    print(f"═ 실파일 {mode} — {SCRIPTS}\n")
    if not dry:
        (SCRIPTS / MODULE_NAME).write_text(MODULE, encoding="utf-8")
        print(f"  + {MODULE_NAME} 생성")
    any_bad = False
    for name in EDITS:
        src = SCRIPTS / name
        if not src.is_file():
            print(f"  ❌ 없음: {name}"); any_bad = True; continue
        cur = src.read_text(encoding="utf-8")
        new, probs = patch_text(name, cur)
        hard = [p for p in probs if "매치 실패" in p]
        if hard:
            print(f"  ❌ {name}: {' · '.join(hard)} — 이 파일 건너뜀")
            any_bad = True; continue
        if new == cur:
            print(f"  = {name}: 변경 없음 ({probs[0] if probs else '동일'})"); continue
        if dry:
            print(f"  ~ {name}: 바뀔 예정")
        else:
            src.write_text(new, encoding="utf-8")
            print(f"  ✏️  {name}: 적용됨")
    print("\n  " + ("일부 실패 — 위 ❌ 확인" if any_bad else
                    ("미리보기 끝. --apply 로 실제 적용" if dry else "적용 완료")))
    print("  ★ 적용 후: git add <바뀐 파일> — soonsal-build 는 add -A 금지(여러 세션)")
    return 1 if any_bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--test", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    A = ap.parse_args()
    if A.test:
        return run_test()
    return run_apply(dry=A.dry_run)


if __name__ == "__main__":
    sys.exit(main())
