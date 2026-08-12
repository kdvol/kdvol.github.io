#!/usr/bin/env python3
"""순살 팀 이름으로 회차별 질문을 남긴다.

빈 댓글창에는 아무도 안 쓴다. 그래서 먼저 말을 거는데, 그 발신자를 숨기지
않는다 — '순살 에디터'로 올라가고 화면에는 '순살 팀' 배지가 붙는다.
독자인 척하는 것과는 다르다. 읽는 사람이 누가 쓴 글인지 바로 안다.

관리자 키가 있어야 op=1이 붙고, 그 키가 있어야 '순살 에디터'라는 이름도
쓸 수 있다(NICK_BAN 예외). 키 없이 같은 이름을 쓰면 400이다.

사용:
  SOONSAL_ADMIN_KEY=... python3 scripts/post_prompts.py            # 안 올린 것 1개
  SOONSAL_ADMIN_KEY=... python3 scripts/post_prompts.py --all      # 남은 것 전부
  SOONSAL_ADMIN_KEY=... python3 scripts/post_prompts.py --dry      # 미리보기

한 번에 쏟아붓지 않는다. 같은 시각에 14개가 한꺼번에 붙으면 그것대로
사람이 쓴 것처럼 보이지 않는다. 기본은 한 번에 하나씩이다.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "content/talk_prompts.json"
STATE = ROOT / "content/talk_prompts_done.json"
WORKER = os.environ.get("SOONSAL_WORKER", "https://soonsal-react.kd-d0a.workers.dev")
# 두 발신자를 쓴다. 어느 쪽이든 화면에 정체를 밝힌다 — 사람인 척하는 계정은 없다.
#   순살 에디터 : 사람이 쓰는 글 (op=1, '순살 팀' 배지)
#   순살 질문봇 : 자동으로 올라오는 질문 (op=2, '🤖 봇' 배지)
SENDERS = {
    "team": {"nick": "순살 에디터", "vid": "soonsal-editor-01", "as": None},
    "bot": {"nick": "순살 질문봇", "vid": "soonsal-askbot-01", "as": "bot"},
}


def _post(admin, story, body, who="bot"):
    s = SENDERS[who]
    payload = {"story": story, "v": s["vid"], "nick": s["nick"], "body": body}
    if s["as"]:
        payload["as"] = s["as"]
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        WORKER.rstrip("/") + "/comment", data=data,
        headers={"content-type": "application/json", "x-admin-key": admin,
                 "Origin": "https://soonsal.com", "user-agent": "soonsal-editor/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main():
    dry = "--dry" in sys.argv
    every = "--all" in sys.argv
    admin = os.environ.get("SOONSAL_ADMIN_KEY")
    if not admin and not dry:
        print("ℹ️ 관리자 키 없음 — 건너뜀")
        return 0

    items = json.loads(PROMPTS.read_text(encoding="utf-8"))
    done = set(json.loads(STATE.read_text(encoding="utf-8"))) if STATE.exists() else set()
    todo = [x for x in items if x["story"] not in done]
    if not todo:
        print("💬 남은 질문 없음")
        return 0

    picked = todo if every else todo[:1]
    n = 0
    for x in picked:
        if dry:
            print(f"  [미리보기] {x['story']}: {x['body']}")
            continue
        try:
            res = _post(admin, x["story"], x["body"], x.get("who", "bot"))
        except urllib.error.HTTPError as e:
            print(f"  ⚠️ {x['story']} 실패 {e.code} {e.read()[:80].decode(errors='replace')}")
            continue
        except Exception as e:
            print(f"  ⚠️ {x['story']} 실패 {type(e).__name__}")
            continue
        if res.get("ok"):
            done.add(x["story"])
            n += 1
            print(f"  💬 {x['story']} (id={res.get('id')})")
        else:
            print(f"  ⚠️ {x['story']} 거절: {res}")

    if n and not dry:
        STATE.write_text(json.dumps(sorted(done), ensure_ascii=False, indent=1),
                         encoding="utf-8")
    print(f"💬 질문 {n}개 게시 · 남은 {len(todo) - n}개")
    return n


if __name__ == "__main__":
    main()
