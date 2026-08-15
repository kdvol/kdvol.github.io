#!/usr/bin/env python3
"""충돌 표시가 발행물에 섞였는지 본다. 섞였으면 종료코드 1.

2026-08-16 에 `<<<<<<< HEAD` 가 soonsal.com/topics/ 상단에 그대로 떴다.
리베이스가 충돌로 멈춰 있는 줄 모르고 `git add -A && git commit` 을 해서,
충돌 표시가 든 파일 20개가 그대로 커밋되고 배포됐다.

빌드 산출물이라 양쪽 내용이 사실상 같았고 — 그래서 눈으로는 안 걸렸다.
사람이 알아채는 걸 기대하면 안 되는 종류의 사고다. 그래서 문으로 만든다.

훅으로 걸어 두면 커밋 전에 걸린다:
  git config core.hooksPath .githooks

사용:
  python3 scripts/check_conflict_markers.py            # 작업 트리 전부
  python3 scripts/check_conflict_markers.py --staged   # 스테이지된 것만
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 줄 맨 앞에 올 때만 충돌 표시다. 본문에 나오는 `>>>` 따위와 구별한다.
MARKER = re.compile(r"^(<{7} |={7}$|>{7} |\|{7} )", re.M)

SKIP_DIRS = {".git", "node_modules", ".claude", "__pycache__"}
SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".mp4",
               ".woff", ".woff2", ".ttf", ".zip", ".pdf"}


def targets(staged: bool) -> list[Path]:
    if staged:
        out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                             cwd=ROOT, capture_output=True, text=True).stdout.split("\n")
        return [ROOT / f for f in out if f.strip()]
    return [p for p in ROOT.rglob("*") if p.is_file()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--staged", action="store_true")
    a = ap.parse_args()

    bad: list[tuple[Path, int]] = []
    for p in targets(a.staged):
        if not p.is_file() or p.suffix.lower() in SKIP_SUFFIX:
            continue
        if any(d in p.parts for d in SKIP_DIRS):
            continue
        # 이 파일 자신은 표시를 예시로 들고 있다
        if p.name == Path(__file__).name:
            continue
        try:
            s = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        n = len(MARKER.findall(s))
        if n:
            bad.append((p.relative_to(ROOT), n))

    if bad:
        print(f"⛔ 충돌 표시가 {len(bad)}개 파일에 남아 있다 — 발행하면 화면에 그대로 뜬다")
        for f, n in bad[:20]:
            print(f"   {f}  {n}곳")
        if len(bad) > 20:
            print(f"   … 외 {len(bad)-20}개")
        print("\n  리베이스가 멈춰 있는지 먼저 본다: git status")
        print("  빌드 산출물이면 생성기를 다시 돌린다 (예: scripts/build_topics.py)")
        return 1
    print("✅ 충돌 표시 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
