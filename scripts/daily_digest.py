#!/usr/bin/env python3
"""하루 한 번, 어제 무슨 일이 있었는지 텔레그램으로 보낸다.

/stats/ 는 열어야만 알 수 있는 화면이라 결국 안 보게 된다. 그래서 지표를 사람에게
찾아가게 만든다. 아무 일도 없었던 날은 보내지 않는다 — 매일 오는 빈 알림은 곧
읽지 않는 알림이 된다.

TG_TOKEN / TG_CHAT 이 없으면 조용히 넘어간다. auto-improve 워크플로에서 실행.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

WORKER = os.environ.get("SOONSAL_WORKER", "https://soonsal-react.kd-d0a.workers.dev")
TG_API = "https://api.telegram.org"


def _get(path, admin=None, timeout=30):
    h = {"Origin": "https://soonsal.com", "user-agent": "soonsal-digest/1.0"}
    if admin:
        h["x-admin-key"] = admin
    req = urllib.request.Request(WORKER.rstrip("/") + path, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def send(token, chat, text):
    """알림 실패가 워크플로를 죽이면 안 된다 — 예외를 삼키고 False만 돌려준다."""
    body = urllib.parse.urlencode({
        "chat_id": chat, "text": text,
        "parse_mode": "HTML", "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(f"{TG_API}/bot{token}/sendMessage", data=body)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read()).get("ok", False)
    except urllib.error.HTTPError as e:
        print(f"⚠️ digest: 텔레그램 거부 HTTP {e.code} (토큰·chat_id 확인)")
    except Exception as e:
        print(f"⚠️ digest: 발송 실패 {type(e).__name__}")
    return False


def main():
    token, chat = os.environ.get("TG_TOKEN"), os.environ.get("TG_CHAT")
    if not (token and chat):
        print("ℹ️ digest: 텔레그램 토큰 없음 — 건너뜀")
        return 0

    try:
        # /insights는 관리자 키가 필요하다 — 없으면 401로 요약이 통째로 실패한다
        ins = _get("/insights?days=7", admin=os.environ.get("SOONSAL_ADMIN_KEY"))
    except Exception as e:
        print(f"⚠️ digest: 집계 조회 실패 {type(e).__name__}")
        return 0

    daily = ins.get("daily", [])
    today = daily[-1] if daily else {"hits": 0, "uniq": 0}
    vis = ins.get("visitors", {}) or {}
    eng = {}
    for e in ins.get("engage", []):
        eng[e["kind"]] = eng.get(e["kind"], 0) + e["n"]

    people = vis.get("today") or 0
    cd = ins.get("commentsDaily") or []
    comments = sum(r.get("n", 0) for r in cd)
    readers = sum(r.get("readers", 0) for r in cd)          # 순살 팀·봇을 뺀 수
    if not cd:                                              # 예전 워커면 이벤트로
        comments = eng.get("comment", 0)
        readers = 0
    rd = ins.get("reactsDaily") or []
    reacts = sum(r.get("up", 0) for r in rd)
    undo = sum(r.get("undo", 0) for r in rd)
    if not rd:
        reacts, undo = eng.get("react", 0), 0

    # 아무 일도 없었으면 침묵한다
    if not (people or comments or reacts):
        print("🔕 digest: 어제 활동 없음 — 발송 안 함")
        return 0

    held = 0
    admin = os.environ.get("SOONSAL_ADMIN_KEY")
    if admin:
        try:
            held = len(_get("/mod?state=0", admin=admin).get("items", []))
        except Exception:
            pass

    lines = [
        "🐟 <b>순살 웹사이트 하루 요약</b>",
        "",
        f"방문 <b>{people}명</b> · {today.get('hits', 0)}뷰",
        f"반응 {reacts}건" + (f" (취소 {undo})" if undo else "") + f" · 댓글 {comments}건"
        + (f" (순살러 {readers}건)" if comments and readers else ""),
    ]
    if vis.get("total"):
        rate = round((vis.get("repeat_v", 0) / vis["total"]) * 100)
        lines.append(f"재방문율 {rate}%  <i>(누적 {vis['total']}명 중 {vis.get('repeat_v', 0)}명)</i>")
    refs = ins.get("refs", [])
    if refs:
        ko = {"direct": "직접", "telegram": "텔레그램", "instagram": "인스타",
              "search": "검색", "mail": "뉴스레터", "other": "기타"}
        top = ", ".join(f"{ko.get(r['src'], r['src'])} {r['n']}" for r in refs[:3])
        lines.append(f"유입 {top}")
    if held:
        lines.append(f"\n⏳ 검토 중 댓글 {held}건 — 다음 자동 판정에서 처리됩니다")
    lines.append('\n<a href="https://soonsal.com/stats/">자세히 보기</a>')

    ok = send(token, chat, "\n".join(lines))
    print(f"📨 digest: 발송 {'성공' if ok else '실패'} (방문 {people} · 댓글 {comments})")
    return 1 if ok else 0


if __name__ == "__main__":
    main()
