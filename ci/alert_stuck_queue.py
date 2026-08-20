#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""발행 큐 지연 감시 — GitHub Actions 에서 **발행보다 먼저** 실행 (if: always()).
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
        # ★★ 큐가 가리키는 **본문 파일이 실제로 있는지** 먼저 본다 (KD 2026-08-20).
        #
        #   2026-08-20 에 0821·0822 두 편이 **큐 JSON 만 원격에 있고 `_publish/*.html` 은
        #   없는 채로** 앉아 있었다. 예약 스크립트가 git push 에 막혀 API 로 우회했는데,
        #   그 우회가 큐 파일 하나만 올렸기 때문이다. 「등록 완료」는 찍혔고,
        #   발행 시각이 되면 러너가 집을 본문이 없어 **조용히 실패**했을 것이다.
        #
        #   지연은 시각이 지나야 알 수 있지만 **파일 누락은 지금 당장 알 수 있다.**
        #   그래서 예정 시각과 무관하게 매번 본다 — 발행 전에 고칠 시간을 번다.
        for key in ("html", "post_txt"):
            ref = d.get(key)
            if ref and not pathlib.Path(ref).is_file():
                stuck.append(f"- **{d.get('name')}** ({d.get('date')}) — "
                             f"⛔ 큐가 가리키는 파일이 원격에 없다: `{ref}` "
                             f"(예약 스크립트가 큐만 올리고 본문을 빠뜨린 경우)")

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
                + "\n\n크론이 30분마다 재시도 중(멱등 — 중복 발행 없음). 계속 실패하면 "
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
