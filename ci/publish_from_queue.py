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
MAX_LATE_H = 12      # 발행 시각을 이만큼 넘겨 밀린 항목은 자동 발행 안 함 (무한 재발행 방지)
MAX_ATTEMPTS = 4     # 같은 항목 연속 실패 상한
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
        # ── 지각 상한 (2026-08-03 추가): 발행 시각을 MAX_LATE_H 넘겨 밀린 항목은 자동 발행하지 않는다.
        #    예전엔 상한이 없어, done 이동에 실패한 항목이 크론마다(15분) 무한 재발행됐다.
        #    시의성도 이미 죽은 항목이므로 사람이 보고 결정하게 남긴다(stuck-queue 알림이 잡음).
        late_h = (now - d.get("target_epoch", 0)) / 3600
        if not only and late_h > MAX_LATE_H:
            log(f"⏸ {mf.stem}: 발행 시각 {late_h:.1f}h 경과 — 자동 발행 보류(재개는 --only {mf.stem})")
            continue
        # ── 재시도 상한: 같은 항목이 계속 실패하면 멈춘다(무한 루프 2차 방어).
        if not only and int(d.get("attempts", 0)) >= MAX_ATTEMPTS:
            log(f"⏸ {mf.stem}: 재시도 {d.get('attempts')}회 초과 — 보류(원인 확인 후 attempts 리셋)")
            continue
        # ── ★ 이미 나간 것인가 (2026-08-11 중복 발행 사고 · 2차 방어)
        #    멱등 마커는 「큐 파일이 done/ 으로 옮겨졌는가」 하나뿐이다. 그런데 낡은 트리를
        #    체크아웃하면 **큐에도 있고 done 에도 있는** 상태가 보인다. 그때 발행하면 두 번 나간다.
        #    (근본 원인은 워크플로의 Sync 스텝에서 막지만, 여기서도 한 번 더 본다 —
        #     같은 영상이 두 번 올라가는 사고는 되돌릴 수가 없다.)
        # ── ★ 사람이 봤다는 기록이 매니페스트에 있나 (KD 2026-08-13 「검수 관문 필요해」)
        #    예약 스크립트의 관문은 **새 예약만** 막는다. 이미 큐에 앉은 것은 그대로 나간다.
        #    실제로 승인 기록 없는 카드뉴스 3건(agegap·bucees·flock)이 큐에 있었다 —
        #    릴스에는 그 관문이 있었는데 카드뉴스 경로에만 없었다.
        #    `review_log.jsonl` 은 빌드 레포에만 있어 러너가 못 읽으므로,
        #    예약 시점에 매니페스트에 새겨 두고 여기서 그걸 확인한다.
        #    ★ --only 로도 못 뚫는다. 우회로를 하나 남기면 반드시 거기로 샌다.
        if not (d.get("reviewed") or {}).get("by"):
            log(f"⛔ {mf.stem}: 검수 기록이 매니페스트에 없다 — **발행하지 않는다.**\n"
                f"   빌드 레포에서: python3 scripts/review_log.py approve {mf.stem} --verbatim \"...\"\n"
                f"   그 뒤 재예약하거나 scripts/stamp_reviewed.py 로 새길 것")
            continue

        if (DONE / mf.name).exists():
            log(f"⛔ {mf.stem}: done/ 에 이미 있다 — **발행하지 않는다**(중복 방어). "
                f"큐 파일을 지우고 원인을 확인할 것")
            continue
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
        # 실패 횟수를 매니페스트에 누적 → MAX_ATTEMPTS 초과 시 due_items가 걸러낸다
        try:
            d["attempts"] = int(d.get("attempts", 0)) + 1
            mf.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception as e:
            log(f"attempts 기록 실패: {e}")
        log(f"⚠️ 발행 실패(rc={r.returncode}) · 시도 {d.get('attempts')}회 "
            f"· 큐 유지 → 다음 스케줄에 재시도")
        return False

    if dry:
        log("✅ dry-run 성공(IG 미게시). 큐 유지.")
        return True

    # ── single_video 발행자는 IG/YT 실패 시 자체적으로 exit(1)을 낸다(deploy.py와 다름).
    #    따라서 returncode(위에서 0 확인됨)로 성공 판정한다. IG 미디어ID(숫자) 정규식으로
    #    판정하면 YT 전용(영숫자 ID) 발행이 매번 done 이동 실패 → 크론마다 중복 발행되는 버그가
    #    있었음(2026-07-20 yt_korea 2회 중복). 첫 댓글은 IG 미디어ID가 있을 때만.
    if d.get("type") == "single_video":
        m = IG_MEDIA_ID_RE.search(r.stdout)
        if m:
            log(f"📸 IG 릴스 게시 확인 — media ID {m.group(1)}")
            post_first_comment(r.stdout, d)
        else:
            log("📺 게시 확인 (YT 전용 등, IG 미디어ID 없음) — exit 0 이므로 정상 완료 처리")
        DONE.mkdir(parents=True, exist_ok=True)
        shutil.move(str(mf), str(DONE / mf.name))
        log(f"✅ 발행 성공 · 큐 → done/{mf.name}")
        return True

    # ── 실발행: deploy.py 종료코드 0이어도 IG 캐러셀이 실제로 올라갔는지 검증한다.
    #    deploy.py는 IG 단계가 실패해도(PNG 미생성·토큰 오류 등) 종료코드 0으로 끝나므로,
    #    stdout의 "게시 완료 — ID:<미디어ID>" 유무로 실제 게시를 확인한다. 미디어 ID가 없으면
    #    웹은 발행됐어도 IG 미게시로 보고 done 이동을 보류 → 다음 스케줄에 재시도(멱등).
    #    (video_carousel은 항상 IG 캐러셀을 게시하므로 숫자 미디어ID가 나옴 → 이 경로로 정상.)
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
