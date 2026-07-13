#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""발행 큐 지연 감시 — GitHub Actions 마지막 스텝에서 실행 (if: always()).
_queue/에 발행 예정 시각을 30분 넘긴 항목이 남아 있으면 GitHub 이슈로 알림(중복 생성 없음),
큐가 정상화되면 열린 알림 이슈를 자동으로 닫는다. 새 시크릿 불필요(GH_TOKEN).
알림 경로: GitHub 이슈 → KD의 GitHub 알림(메일/폰) — 맥/앱 꺼져 있어도 도달."""
import json, time, subprocess, pathlib, datetime, sys

TITLE = "🚨 카드뉴스 자동발행 지연/실패"
GRACE_SEC = 1800  # 예정 시각 + 30분까지는 정상 재시도로 간주


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def main():
    now = time.time()
    kst = datetime.timezone(datetime.timedelta(hours=9))
    stuck = []
    for mf in sorted(pathlib.Path("_queue").glob("*.json")):
        try:
            d = json.loads(mf.read_text(encoding="utf-8"))
        except Exception:
            stuck.append(f"- **{mf.name}** — 매니페스트 파싱 불가(손상?)")
            continue
        overdue = now - d.get("target_epoch", 0)
        if overdue > GRACE_SEC:
            when = datetime.datetime.fromtimestamp(d["target_epoch"], kst)
            stuck.append(f"- **{d.get('name')}** ({d.get('date')}) — 예정 {when:%m-%d %H:%M} KST, {int(overdue // 60)}분 경과")

    r = gh("issue", "list", "--search", f'"{TITLE}" in:title', "--state", "open", "--json", "number")
    try:
        open_issues = json.loads(r.stdout or "[]")
    except Exception:
        open_issues = []

    if stuck:
        body = ("자동발행이 지연되고 있습니다. 큐에 남은 항목:\n\n" + "\n".join(stuck)
                + "\n\n크론이 15분마다 재시도 중(멱등 — 중복 발행 없음). 계속 실패하면 "
                + "최신 publish-cardnews 런 로그를 확인하세요.")
        if open_issues:
            gh("issue", "comment", str(open_issues[0]["number"]), "--body", body)
        else:
            gh("issue", "create", "--title", TITLE, "--body", body)
        print(f"⚠️ 지연 {len(stuck)}건 — 이슈 알림 발송")
    elif open_issues:
        gh("issue", "close", str(open_issues[0]["number"]),
           "--comment", "✅ 큐 정상화(지연 항목 없음). 자동 종료.")
        print("✅ 정상화 — 알림 이슈 자동 닫음")
    else:
        print("✅ 지연 항목 없음")
    return 0  # 알림 실패가 발행을 실패시키지 않도록 항상 0


if __name__ == "__main__":
    sys.exit(main())
