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
import json, os, sys, time, subprocess, shutil, re, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(os.environ.get("KDVOL_ROOT", ".")).resolve()   # 러너에선 repo 체크아웃 루트
QUEUE = ROOT / "_queue"
DONE = QUEUE / "done"
DEPLOY = ROOT / "deploy.py"
PY = sys.executable

def log(m): print(f"[queue] {m}", flush=True)

# deploy.py stdout에서 IG 캐러셀 게시 성공 라인("게시 완료 — ID:<미디어ID>")을 잡는 패턴.
IG_MEDIA_ID_RE = re.compile(r"게시 완료\s*[—\-–]\s*ID:\s*(\d+)")

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

def _token():
    igp = Path(os.environ.get("INSTAGRAM_PIPELINE", str(ROOT / "ig_pipeline")))
    conf = igp / "config.env"
    if conf.is_file():
        for l in conf.read_text(encoding="utf-8").splitlines():
            s = l.strip()
            if s.startswith("INSTAGRAM_ACCESS_TOKEN="):
                return s.split("=", 1)[1].strip()
    return os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")

def post_first_comment(stdout, d):
    """deploy 성공 stdout에서 미디어 ID 파싱 → POST.txt [첫 댓글] 게시(해시태그)."""
    pt = d.get("post_txt") or d.get("caption_txt")
    if not pt:
        return
    p = ROOT / pt
    if not p.is_file():
        log(f"POST.txt 없음: {p} — 첫 댓글 스킵"); return
    m = IG_MEDIA_ID_RE.search(stdout)
    if not m:
        log("미디어 ID 파싱 실패 — 첫 댓글 스킵"); return
    mid = m.group(1)
    cm = re.search(r"\[첫 댓글\]\s*\n(.+?)(?:\n\[|\Z)", p.read_text(encoding="utf-8"), re.S)
    tok = _token()
    if not (cm and tok):
        log("첫 댓글 텍스트/토큰 없음 — 스킵"); return
    try:
        data = urllib.parse.urlencode({"message": cm.group(1).strip(), "access_token": tok}).encode()
        with urllib.request.urlopen(f"https://graph.facebook.com/v21.0/{mid}/comments", data=data, timeout=25) as r:
            log(f"첫 댓글 게시 완료: {json.loads(r.read().decode())}")
    except Exception as e:
        log(f"첫 댓글 실패(수동 필요): {e}")

def publish(mf, d, force_dry=False):
    dry = force_dry or d.get("dry_run", False)
    if d.get("type") == "single_video":
        # 단일 세로영상 — IG 릴스 / 유튜브 숏츠 (독립 스위치)
        cmd = [PY, str(ROOT / "ci" / "publish_single_video.py"), "--manifest", str(mf)] \
              + (["--dry-run"] if dry else [])
    elif d.get("type") == "video_carousel":
        # 움직이는 캐러셀(영상 8슬라이드) — 전용 발행자 사용, 성공 라인 포맷은 deploy.py와 동일
        cmd = [PY, str(ROOT / "ci" / "publish_video_carousel.py"), "--manifest", str(mf)] \
              + (["--dry-run"] if dry else [])
    else:
        html = ROOT / d["html"]
        if not html.is_file():
            log(f"❌ HTML 없음: {html}"); return False
        cmd = [PY, str(DEPLOY), str(html)] + (["--no-instagram"] if dry else [])
    log(f"발행 시작: {d.get('name')} ({d.get('date')}) dry={dry}")
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, env=os.environ)
    sys.stdout.write(r.stdout[-4000:]); sys.stderr.write(r.stderr[-2000:])
    if r.returncode != 0:
        log(f"⚠️ 발행 실패(rc={r.returncode}) · 큐 유지 → 다음 스케줄에 재시도")
        return False

    if dry:
        log("✅ dry-run 성공(IG 미게시). 큐 유지.")
        return True

    # ── 실발행: deploy.py 종료코드 0이어도 IG 캐러셀이 실제로 올라갔는지 검증한다.
    #    deploy.py는 IG 단계가 실패해도(PNG 미생성·토큰 오류 등) 종료코드 0으로 끝나므로,
    #    stdout의 "게시 완료 — ID:<미디어ID>" 유무로 실제 게시를 확인한다. 미디어 ID가 없으면
    #    웹은 발행됐어도 IG 미게시로 보고 done 이동을 보류 → 다음 스케줄에 재시도(멱등).
    m = IG_MEDIA_ID_RE.search(r.stdout)
    if not m:
        log("❌ IG 미디어 ID 없음 — 웹은 발행됐어도 IG 캐러셀 미게시로 판단. "
            "done 이동 보류 · 큐 유지 → 다음 스케줄에 재시도 (deploy.py PNG/IG 단계 로그 확인).")
        return False

    log(f"📸 IG 게시 확인 — media ID {m.group(1)}")
    post_first_comment(r.stdout, d)                 # 해시태그 첫 댓글
    DONE.mkdir(parents=True, exist_ok=True)
    shutil.move(str(mf), str(DONE / mf.name))       # 멱등: 큐에서 제거
    log(f"✅ 발행 성공 · 큐 → done/{mf.name}")
    return True

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
