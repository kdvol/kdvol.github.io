#!/usr/bin/env python3
"""하루 한 번, 어제 무슨 일이 있었는지 텔레그램으로 보낸다.

/stats/ 는 열어야만 알 수 있는 화면이라 결국 안 보게 된다. 그래서 지표를 사람에게
찾아가게 만든다. 아무 일도 없었던 날은 보내지 않는다 — 매일 오는 빈 알림은 곧
읽지 않는 알림이 된다.

TG_TOKEN / TG_CHAT 이 없으면 조용히 넘어간다. auto-improve 워크플로에서 실행.
"""
import json
import os
from datetime import datetime, timedelta, timezone
import urllib.error
import urllib.parse
import urllib.request

WORKER = os.environ.get("SOONSAL_WORKER", "https://soonsal-react.kd-d0a.workers.dev")
TG_API = "https://api.telegram.org"
DAYS = 7          # 집계 창. 하루 수치와 섞이지 않게 표기에 기간을 밝힌다


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


BOT_FILTER_FROM = "2026-08-18"


def _has_prebot(days: int) -> bool:
    """집계 창이 봇 필터 시행일 이전을 물고 있나."""
    kst = timezone(timedelta(hours=9))
    start = (datetime.now(kst) - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    return start < BOT_FILTER_FROM



def main():
    token, chat = os.environ.get("TG_TOKEN"), os.environ.get("TG_CHAT")
    if not (token and chat):
        print("ℹ️ digest: 텔레그램 토큰 없음 — 건너뜀")
        return 0

    # ── **어제 하루**를 본다 (KD 2026-08-20) ──────────────────────────
    #   이 요약은 05:30 KST 에 돈다. 그런데 워커의 「오늘」은 KST 기준 오늘이라,
    #   `visitors.today` 와 `daily[-1]` 이 **오늘 00:00~05:30, 다섯 시간 반치**를
    #   가리켰다. 그걸 「하루 요약 · 방문 38명 · 56뷰」로 보냈다.
    #   숫자가 작은 게 아니라 **하루가 아니었다.**
    #   `?day=` 를 주면 그 날짜로 범위가 좁혀지고, `visitors.active` 가 그날
    #   방문자가 된다. 어제를 명시해 부른다.
    kst = timezone(timedelta(hours=9))
    yday = (datetime.now(kst) - timedelta(days=1)).strftime("%Y-%m-%d")
    admin_key = os.environ.get("SOONSAL_ADMIN_KEY")
    try:
        # /insights는 관리자 키가 필요하다 — 없으면 401로 요약이 통째로 실패한다
        one = _get(f"/insights?days=1&day={yday}", admin=admin_key)
        ins = _get(f"/insights?days={DAYS}", admin=admin_key)
    except Exception as e:
        print(f"⚠️ digest: 집계 조회 실패 {type(e).__name__}")
        return 0

    daily = one.get("daily", [])
    today = daily[-1] if daily else {"hits": 0, "uniq": 0}
    vis = ins.get("visitors", {}) or {}          # 누적·재방문은 창 전체가 맞다
    yvis = one.get("visitors", {}) or {}         # 어제 방문자
    eng = {}
    for e in one.get("engage", []):
        eng[e["kind"]] = eng.get(e["kind"], 0) + e["n"]

    # ★ **하루 요약은 하루치만 쓴다** (KD 2026-08-15)
    #   /insights?days=7 은 창(窓) 합계를 준다. 그걸 그대로 쓰면 하루 요약에
    #   7일 합계가 섞인다 — 실제로 "방문 17명 · 34뷰" 옆에 "유입 직접 4683"이
    #   찍혔다. 방문은 하루, 유입은 7일 합계였다. 같은 블록에 다른 기간을
    #   섞으면 어느 쪽도 못 믿는다.
    #   그래서 일자별 배열은 **마지막 날만** 꺼내고, 창 전체 합계인 refs 는
    #   기간을 명시해 따로 적는다.
    day = today.get("day") or ""

    def _one_day(rows, *keys):
        """일자별 배열에서 마지막 날 것만. 그 날 기록이 없으면 0."""
        if not rows:
            return [0] * len(keys)
        last = rows[-1]
        if day and last.get("day") and last["day"] != day:
            return [0] * len(keys)
        return [last.get(k, 0) for k in keys]

    people = yvis.get("active") or 0
    cd = one.get("commentsDaily") or []
    comments, readers = _one_day(cd, "n", "readers")
    if not cd:                                              # 예전 워커면 이벤트로
        comments, readers = eng.get("comment", 0), 0
    rd = one.get("reactsDaily") or []
    reacts, undo = _one_day(rd, "up", "undo")
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
        f"🐟 <b>순살 웹사이트 · {yday[5:].replace('-', '/')} 하루</b>",
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
        # refs 는 창 전체 합계다. 하루 수치 옆에 그냥 두면 같은 기간으로 읽힌다.
        ko = {"direct": "직접", "telegram": "텔레그램", "instagram": "인스타",
              "search": "검색", "mail": "뉴스레터", "other": "기타"}
        top = ", ".join(f"{ko.get(r['src'], r['src'])} {r['n']}" for r in refs[:3])
        # ★ 이 합계엔 **봇 필터 이전 기록이 섞여 있다** (필터는 2026-08-18 12:49 부터).
        #   그래서 하루 숫자와 나란히 놓으면 자릿수가 안 맞는다 —
        #   「방문 38명」 옆에 「직접 5,402」가 찍혀 오류처럼 보였다.
        #   창이 8/18 이후로만 채워지면 이 주석과 꼬리표를 뺀다.
        tail = " <i>(8/18 이전은 봇 포함)</i>" if _has_prebot(DAYS) else ""
        lines.append(f"<i>최근 {DAYS}일 유입</i> {top}{tail}")
    if held:
        lines.append(f"\n⏳ 검토 중 댓글 {held}건 — 다음 자동 판정에서 처리됩니다")
    lines.append('\n<a href="https://soonsal.com/stats/">자세히 보기</a>')

    ok = send(token, chat, "\n".join(lines))
    print(f"📨 digest: 발송 {'성공' if ok else '실패'} (방문 {people} · 댓글 {comments})")
    return 1 if ok else 0


if __name__ == "__main__":
    main()
