#!/usr/bin/env python3
"""뉴스레터 열람 기록 관리 — 고지에 적은 약속을 실제로 지키는 도구.

`/privacy/` 에 세 가지를 적어 두었다. 적어만 두고 안 지키면 그게 더 나쁘다.

  1. 낱개 기록은 **90일** 보관 후 합계만 남기고 삭제
  2. **연결 끄기** 요청 시 이후 기록 안 하고 기존 기록도 삭제
  3. 구독 해지 시 그 표시의 기록도 삭제

사용:
  python3 scripts/reads_admin.py --purge              # 90일 지난 낱개 줄 삭제
  python3 scripts/reads_admin.py --optout <표시값>     # 연결 끄기 + 기존 삭제
  python3 scripts/reads_admin.py --status            # 지금 무엇이 쌓였나

표시값(sub)은 발송 시스템에서 만든 16자리 값이다. 이메일을 넣지 않는다 —
여기서는 이메일을 다루지 않고, 다룰 수도 없다.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKERS = ROOT / "workers"
DB = "soonsal-react"
KEEP_DAYS = 90


def sql(command: str) -> list[dict]:
    r = subprocess.run(
        ["npx", "wrangler", "d1", "execute", DB, "--remote", "--json",
         "--command", command],
        cwd=WORKERS, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.strip()[-400:])
        raise SystemExit(1)
    try:
        out = json.loads(r.stdout)
    except json.JSONDecodeError:
        # --json 을 못 먹는 버전이면 원문을 보여준다
        print(r.stdout.strip()[-600:])
        return []
    rows = []
    for blk in out if isinstance(out, list) else [out]:
        rows.extend((blk.get("results") or []))
    return rows


def status() -> int:
    rows = sql("select count(*) as rows, count(distinct sub) as subs, "
               "min(day) as oldest, max(day) as newest from reads")
    r = rows[0] if rows else {}
    print("═ 뉴스레터 열람 기록")
    print(f"  낱개 줄 {r.get('rows') or 0}개 · 구독자 표시 {r.get('subs') or 0}개")
    print(f"  기간 {r.get('oldest') or '—'} ~ {r.get('newest') or '—'}")
    old = sql(f"select count(*) as n from reads "
              f"where day < date('now', '-{KEEP_DAYS} days')")
    n = (old[0].get("n") if old else 0) or 0
    print(f"  {KEEP_DAYS}일 지난 줄 {n}개" + ("  ← --purge 로 지운다" if n else ""))
    off = sql("select count(*) as n from reads_optout")
    print(f"  연결 끈 표시 {(off[0].get('n') if off else 0) or 0}개")
    return 0


def purge() -> int:
    """90일 지난 낱개 줄을 지운다. 합계는 views·dau 에 이미 있다."""
    before = sql(f"select count(*) as n from reads "
                 f"where day < date('now', '-{KEEP_DAYS} days')")
    n = (before[0].get("n") if before else 0) or 0
    if not n:
        print(f"  {KEEP_DAYS}일 지난 줄이 없다 — 지울 것 없음")
        return 0
    sql(f"delete from reads where day < date('now', '-{KEEP_DAYS} days')")
    print(f"  🧹 {n}개 줄 삭제 ({KEEP_DAYS}일 경과)")
    return 0


def optout(sub: str) -> int:
    if not (len(sub) == 16 and all(c in "0123456789abcdef" for c in sub)):
        print("  표시값은 16자리 hex 다. 이메일이나 이름을 넣지 않는다")
        return 1
    sql(f"insert into reads_optout (sub, at) values ('{sub}', unixepoch()) "
        f"on conflict(sub) do nothing")
    had = sql(f"select count(*) as n from reads where sub = '{sub}'")
    n = (had[0].get("n") if had else 0) or 0
    sql(f"delete from reads where sub = '{sub}'")
    print(f"  ✅ 연결 끔 — 이후 기록하지 않음 · 기존 {n}줄 삭제")
    print("  ※ 발송 시스템에서도 이 구독자의 링크에 표시를 붙이지 않도록 해야 한다")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--purge", action="store_true")
    ap.add_argument("--optout", metavar="표시값")
    a = ap.parse_args()
    if a.optout:
        return optout(a.optout.strip())
    if a.purge:
        return purge()
    return status()


if __name__ == "__main__":
    sys.exit(main())
