#!/usr/bin/env python3
"""보관 기간이 지난 데이터를 지운다.

쌓이기만 하는 데이터는 언젠가 부담이 된다 — 용량이 아니라 책임 쪽이다.
개인정보처리방침에 적은 보관 기간을 실제로 지키려면 지우는 쪽도 자동이어야 한다.

  notices  90일  알림은 읽고 나면 보관할 이유가 없다
  hops    180일  이동 쌍(경로 합계, 개인 식별자 없음)
  events  180일  반응 이벤트 원본

댓글·반응 집계는 지우지 않는다(콘텐츠이고 공개된 글이다).
매일 auto-improve 워크플로에서 돈다.
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
