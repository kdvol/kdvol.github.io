#!/usr/bin/env python3
"""C43 — 고쳐 놓고 **안 올린 것**을 잡는다.

KD 2026-08-19: *"고쳤으면 배포를 해야지 왜 안 해? 규칙에 안 넣어둘래?"*

## 왜

오늘만 두 번 났다.

  · 뉴스레터 목록의 스토리 다섯 줄 — 코드를 고치고 로컬 파일까지 고쳐 놓고
    **커밋·푸시를 안 했다.** KD 가 라이브를 보고 「아직 안 됐는데?」라고 했다.
  · 순살차트 8/19 — 원고·검수·스테이징까지 끝내 놓고 사이트에 안 올렸다.
    KD 가 「오늘 아직도 안 올라갔음」이라고 했다.

둘 다 **일은 다 해 놓고 마지막 한 걸음을 안 밟은 것**이다. 로컬에서는
멀쩡히 보이니까 끝난 걸로 착각한다. 사람이 라이브를 열어 봐야만 드러난다 —
그게 제일 비싼 발견 방식이다.

## 무엇을 보나

  · 사이트 저장소에 **안 올라간 변경**이 있나 (커밋 안 됨 / 푸시 안 됨)
  · 그중 **발행물**(chart·newsletters·cardnews·topics)이 섞여 있나
  · 오늘자 순살차트가 사이트에 **파일로 있나**

빌더가 매번 밀어 넣는 빈 줄 같은 잡음은 빼고 센다 — 그것까지 세면
늘 빨간불이라 아무도 안 본다.

    python3 scripts/deploy_debt.py           # 지금 안 올라간 게 있나
    python3 scripts/deploy_debt.py --date 2026-08-19
"""

import argparse
import subprocess
import sys
from datetime import date as _date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# 발행물이 사는 자리 — 여기가 밀리면 독자가 못 본다
LIVE = ("chart/", "newsletters/", "cardnews/", "topics/", "index.html")


def _git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return (r.stdout or "").strip()


def _substantive(path: str) -> bool:
    """빌더가 밀어 넣는 빈 줄만 바뀐 파일은 빼고 센다."""
    diff = _git("diff", "--", path) or _git("diff", "--cached", "--", path)
    body = [l for l in diff.splitlines()
            if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    return any(l[1:].strip() for l in body)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=_date.today().isoformat())
    ARGS = ap.parse_args()

    problems: list[str] = []

    dirty = [l[3:] for l in _git("status", "--porcelain").splitlines() if l[3:]]
    live_dirty = [p for p in dirty if p.startswith(LIVE) and _substantive(p)]
    if live_dirty:
        problems.append(f"커밋 안 한 발행물 {len(live_dirty)}개: "
                        + ", ".join(live_dirty[:4])
                        + (" …" if len(live_dirty) > 4 else ""))

    unpushed = _git("log", "--oneline", "@{u}..HEAD")
    if unpushed:
        n = len(unpushed.splitlines())
        problems.append(f"푸시 안 한 커밋 {n}개: {unpushed.splitlines()[0][:52]}")

    mmdd = ARGS.date.replace("-", "")[4:]
    yyyy = ARGS.date[:4]
    chart = ROOT / "chart" / yyyy / f"{mmdd}.html"
    if not chart.is_file():
        problems.append(f"{ARGS.date} 순살차트가 사이트에 없다 — "
                        f"stage-site 를 안 돌렸거나 검수가 안 끝났다")

    if not problems:
        print("  ✅ 고쳐 놓고 안 올린 것 없음")
        return 0
    print(f"⛔ 안 올라간 게 {len(problems)}가지")
    for p in problems:
        print(f"   · {p}")
    print("   올린다:  git add -A && git commit && git push origin main")
    return 1


if __name__ == "__main__":
    sys.exit(main())
