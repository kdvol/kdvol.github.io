#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""(B) 클라우드 발행 — GitHub Actions 러너에서 발행 큐를 소비.
로컬 맥/인터넷과 무관하게 GitHub 서버가 예약대로 발행한다.

동작:
  - _queue/<slug>.json 매니페스트들을 읽어, 발행 시각(target)이 지났고 아직 미발행인 항목을 찾는다.
  - 각 항목의 HTML로 deploy.py를 실행(웹+R2+IG 전부 deploy.py가 처리).
  - 성공 시 매니페스트를 _queue/done/으로 이동(= 멱등 마커). 실패 시 남겨 다음 스케줄에 재시도.
매니페스트 스키마: {"html": "cardnews/2026/0708-2.html", "date": "20260708_2", "name": "index",
                   "target_epoch": 1783499000, "dry_run": false}
사용: python ci/publish_from_queue.py [--only <slug>] [--dry-run]
환경: 러너에서 config.env는 시크릿으로 미리 생성됨(워크플로가 처리). deploy.py는 CWD=repo 루트에서 실행.
"""
import json, os, sys, time, subprocess, shutil
from pathlib import Path

ROOT = Path(os.environ.get("KDVOL_ROOT", ".")).resolve()   # 러너에선 repo 체크아웃 루트
QUEUE = ROOT / "_queue"
DONE = QUEUE / "done"
DEPLOY = ROOT / "deploy.py"
PY = sys.executable

def log(m): print(f"[queue] {m}", flush=True)

def due_items(only=None):
    now = time.time()
    items = []
    for mf in sorted(QUEUE.glob("*.json")):
        try:
            d = json.loads(mf.read_text(encoding="utf-8"))
        except Exception as e:
            log(f"매니페스트 파싱 실패 {mf.name}: {e}"); continue
        if only and mf.stem != only:
            continue
        if not only and now < d.get("target_epoch", 0):
            continue  # 아직 발행 시각 전
        items.append((mf, d))
    return items

def publish(mf, d, force_dry=False):
    html = ROOT / d["html"]
    if not html.is_file():
        log(f"❌ HTML 없음: {html}"); return False
    dry = force_dry or d.get("dry_run", False)
    cmd = [PY, str(DEPLOY), str(html)] + (["--no-instagram"] if dry else [])
    log(f"발행 시작: {d.get('name')} ({d.get('date')}) dry={dry}")
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, env=os.environ)
    sys.stdout.write(r.stdout[-4000:]); sys.stderr.write(r.stderr[-2000:])
    ok = r.returncode == 0
    if ok and not dry:
        DONE.mkdir(parents=True, exist_ok=True)
        shutil.move(str(mf), str(DONE / mf.name))       # 멱등: 큐에서 제거
        log(f"✅ 발행 성공 · 큐 → done/{mf.name}")
    elif ok and dry:
        log("✅ dry-run 성공(IG 미게시). 큐 유지.")
    else:
        log(f"⚠️ 발행 실패(rc={r.returncode}) · 큐 유지 → 다음 스케줄에 재시도")
    return ok

def selftest():
    """무발행 검증: 벤더 모듈 임포트 + 필수 시크릿 존재만 확인."""
    igp = os.environ.get("INSTAGRAM_PIPELINE", str(ROOT / "ig_pipeline"))
    sys.path.insert(0, igp)
    try:
        import post_instagram, upload_r2  # noqa
        log(f"✅ 모듈 임포트 OK (post_instagram, upload_r2) @ {igp}")
    except Exception as e:
        log(f"❌ 모듈 임포트 실패: {e}"); return 1
    need=["INSTAGRAM_ACCESS_TOKEN","INSTAGRAM_BUSINESS_ACCOUNT_ID","R2_ACCESS_KEY_ID",
          "R2_SECRET_ACCESS_KEY","R2_ACCOUNT_ID","R2_BUCKET_NAME","R2_PUBLIC_URL"]
    miss=[k for k in need if not os.environ.get(k)]
    if miss: log(f"❌ 누락 시크릿: {miss}"); return 1
    log(f"✅ 필수 시크릿 {len(need)}종 전부 존재. deploy.py CWD={ROOT}, exists={DEPLOY.is_file()}")
    log("🟢 셀프테스트 통과 — 하네스 정상(무발행).")
    return 0

def main():
    if "--selftest" in sys.argv: return selftest()
    only = None; dry = "--dry-run" in sys.argv
    if "--only" in sys.argv: only = sys.argv[sys.argv.index("--only") + 1]
    items = due_items(only)
    if not items:
        log("발행 예정 항목 없음."); return 0
    fails = 0
    for mf, d in items:
        if not publish(mf, d, force_dry=dry): fails += 1
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
