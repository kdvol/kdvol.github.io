#!/usr/bin/env python3
"""보관 기간이 지난 데이터를 지운다. — 자동 실행하지 않는다.

데이터는 쌓일수록 자산이라는 판단이라, 정기 삭제는 걸지 않았다.
필요할 때만 직접 돌린다:

    SOONSAL_ADMIN_KEY=... python3 scripts/purge_old.py

지금 방침은 보관 기간을 따로 약속하지 않는다. 나중에 처리방침에 기간을 적게
되면 그때 이 스크립트를 auto-improve 워크플로에 붙이면 된다.
"""

import json
import os
import urllib.request

WORKER = os.environ.get("SOONSAL_WORKER", "https://soonsal-react.kd-d0a.workers.dev")
RULES = [("notices", 90), ("hops", 180), ("events", 180)]


def main():
    admin = os.environ.get("SOONSAL_ADMIN_KEY")
    if not admin:
        print("ℹ️ purge: 관리자 키 없음 — 건너뜀")
        return 0

    body = json.dumps({"rules": [{"table": t, "days": d} for t, d in RULES]}).encode()
    req = urllib.request.Request(
        WORKER.rstrip("/") + "/purge", data=body,
        headers={"content-type": "application/json", "x-admin-key": admin,
                 "Origin": "https://soonsal.com",
                 # UA를 안 주면 Python-urllib으로 나가고 Cloudflare가 1010으로 막는다
                 "user-agent": "soonsal-purge/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            res = json.loads(r.read())
    except Exception as e:
        print(f"⚠️ purge 실패: {type(e).__name__}")
        return 0

    total = sum(res.get("deleted", {}).values())
    if total:
        detail = " · ".join(f"{k} {v}건" for k, v in res["deleted"].items() if v)
        print(f"🧹 purge: {detail}")
    else:
        print("🧹 purge: 지울 것 없음")
    return total


if __name__ == "__main__":
    main()
