#!/usr/bin/env python3
"""보류된 코멘트를 LLM이 직접 판정한다 — 사람이 큐를 보지 않는다.

Worker의 정규식 필터는 링크·리딩방·전화번호처럼 '형태'만 잡는다. 그 그물에 걸린 글
중에는 정상 글도 섞이는데(뉴스 링크를 붙인 독자 등), 이걸 사람이 풀어주지 않으면
선의의 글이 영구히 묻힌다. 반대로 그물을 성기게 하면 사기 링크가 뚫린다.

그래서 판정만 LLM에 맡긴다. 운영자는 아무것도 하지 않는다.
  Worker 정규식(형태) → 보류 → 이 스크립트(맥락) → 공개 / 숨김 / 스팸+차단

ANTHROPIC_API_KEY 와 SOONSAL_ADMIN_KEY 가 둘 다 있어야 동작하고, 없으면 조용히
넘어간다(로컬·PR 빌드에서 깨지지 않게). GitHub Actions에서 하루 단위로 돈다.

단독 실행:  python3 scripts/moderate_comments.py
"""
import json
import os
import re
import urllib.error
import urllib.request

WORKER = os.environ.get("SOONSAL_WORKER", "https://soonsal-react.kd-d0a.workers.dev")
MODEL = "claude-sonnet-5"
API_URL = "https://api.anthropic.com/v1/messages"
BATCH = 40          # 한 번에 판정할 최대 건수

# LLM이 못 돌 때(키 없음·장애) 최소한의 자동 처리.
# 사기·리딩방 유인은 애매할 게 없으므로 사람 없이도 바로 내린다.
HARD_SPAM = re.compile(
    r"리딩\s?방|원금\s?보장|수익률\s?보장|무료\s?체험|카톡\s?아이디|open\.kakao|"
    r"01[016-9][-. ]?\d{3,4}[-. ]?\d{4}"
)

PROMPT = """너는 한국 금융 뉴스레터 '순살브리핑' 웹사이트의 코멘트 검수자다.
정규식 필터에 걸려 보류된 독자 코멘트를 판정한다. 사람이 다시 보지 않으니 네 판정이 최종이다.

판정 기준:
- show: 정상. 링크가 있어도 언론사·공시·기업 IR 등 출처가 분명하고 맥락에 맞으면 공개.
  비판·반대 의견·거친 표현은 그 자체로 내리지 않는다. 토론은 커뮤니티의 목적이다.
- hide: 맥락 없는 광고, 특정인 비방·모욕, 개인정보 노출, 무관한 도배.
- spam: 리딩방·오픈채팅 유인, 사기 의심 링크, 수익 보장 문구, 연락처 유도.
  spam은 작성자를 자동 차단하므로 확신이 있을 때만 쓴다.

애매하면 show 쪽으로 기운다 — 정상 글을 묻는 비용이 스팸 하나를 놓치는 비용보다 크다.
단, 금전 피해로 이어질 수 있는 것(사기 링크·리딩방)은 애매해도 spam.

아래 JSON 배열의 각 코멘트를 판정하라. 출력은 JSON 배열만:
[{"id":123,"act":"show|hide|spam","why":"20자 이내 한글 사유"}]

코멘트:
"""


def _req(path, method="GET", body=None, admin=None, timeout=30):
    data = json.dumps(body).encode() if body is not None else None
    # 기본 Python-urllib UA는 Cloudflare가 403으로 막는다
    headers = {"content-type": "application/json", "Origin": "https://soonsal.com",
               "user-agent": "soonsal-moderator/1.0"}
    if admin:
        headers["x-admin-key"] = admin
    req = urllib.request.Request(WORKER.rstrip("/") + path, data=data,
                                 headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return json.loads(raw) if raw else {}


def _judge(items):
    """LLM 판정. 키가 없거나 실패하면 None → 호출부가 폴백."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    payload = [{"id": i["id"], "hold": i.get("hold"), "nick": i["nick"],
                "body": i["body"]} for i in items]
    body = json.dumps({
        "model": MODEL, "max_tokens": 2048,
        "messages": [{"role": "user",
                      "content": PROMPT + json.dumps(payload, ensure_ascii=False)}],
    }).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "content-type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        text = "".join(b.get("text", "") for b in data.get("content", []))
        m = re.search(r"\[.*\]", text, re.S)
        return json.loads(m.group(0)) if m else []
    except Exception as e:
        print(f"⚠️ 모더레이션 LLM 실패(폴백으로 진행): {type(e).__name__}")
        return None


def _fallback(items):
    """LLM 없이: 명백한 것만 내리고 나머지는 보류로 남긴다(임의 공개 금지)."""
    out = []
    for i in items:
        if HARD_SPAM.search(i["body"]):
            out.append({"id": i["id"], "act": "spam", "why": "규칙 기반 명백 스팸"})
    return out


ACT = {"show": (1, False), "hide": (-1, False), "spam": (-2, True)}


def main():
    admin = os.environ.get("SOONSAL_ADMIN_KEY")
    if not admin:
        print("ℹ️ moderate: SOONSAL_ADMIN_KEY 없음 — 건너뜀")
        return 0
    try:
        held = _req("/mod?state=0", admin=admin).get("items", [])
    except urllib.error.HTTPError as e:
        print(f"⚠️ moderate: 보류 큐 조회 실패 HTTP {e.code}")
        return 0
    except Exception as e:
        print(f"⚠️ moderate: 보류 큐 조회 실패 {type(e).__name__}")
        return 0

    if not held:
        print("✅ moderate: 보류 0건")
        return 0

    items = held[:BATCH]
    verdicts = _judge(items)
    mode = "LLM"
    if verdicts is None:
        verdicts, mode = _fallback(items), "규칙 폴백"

    by_id = {i["id"]: i for i in items}
    done = {"show": 0, "hide": 0, "spam": 0}
    for v in verdicts:
        act = v.get("act")
        if act not in ACT or v.get("id") not in by_id:
            continue
        state, block = ACT[act]
        try:
            _req("/mod", "POST", {"id": v["id"], "state": state,
                                  "block": block, "judge": v.get("why", "")[:120]},
                 admin=admin)
            done[act] += 1
        except Exception as e:
            print(f"⚠️ #{v['id']} 반영 실패: {type(e).__name__}")

    left = len(items) - sum(done.values())
    print(f"🛡️ moderate({mode}): 보류 {len(held)}건 중 "
          f"공개 {done['show']} · 숨김 {done['hide']} · 스팸 {done['spam']}"
          + (f" · 판정 보류 {left}" if left else ""))
    return sum(done.values())


if __name__ == "__main__":
    main()
