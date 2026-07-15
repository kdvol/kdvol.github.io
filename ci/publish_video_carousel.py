#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""영상 캐러셀(움직이는 캐러셀) IG 자동 발행 — 클라우드 큐 소비용.

publish_from_queue.py가 manifest {"type":"video_carousel"}일 때 이 스크립트를 호출한다.
동작: mp4들을 R2 업로드 → IG 영상 자식 컨테이너 생성/처리대기 → CAROUSEL 컨테이너 → 게시.
성공 시 stdout에 "게시 완료 — ID:<미디어ID>" 출력 (큐의 첫 댓글 로직이 이 라인을 파싱).

manifest 스키마:
{
  "type": "video_carousel",
  "videos": ["_publish/vc/<name>/v1.mp4", ...],   # repo 상대경로, 슬라이드 순서
  "caption_txt": "_publish/vc/<name>/POST.txt",   # [첫 댓글] 앞부분 = 캡션
  "prefix": "vc/2026/0716_rollercoaster",         # R2 경로 (재발행 시 캐시버스팅 위해 변경)
  "name": "rollercoaster", "target_epoch": ..., "dry_run": false
}
사용: python ci/publish_video_carousel.py --manifest _queue/<name>.json [--dry-run]
환경: R2_* 환경변수(워크플로 시크릿), INSTAGRAM_PIPELINE(config.env 위치) 또는 IG 토큰 env.
"""
import argparse
import json
import mimetypes
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("KDVOL_ROOT", ".")).resolve()
GRAPH = "https://graph.facebook.com/v21.0"


def log(m):
    print(f"[vc] {m}", flush=True)


def load_ig_config():
    """토큰/계정ID: env 우선, 없으면 INSTAGRAM_PIPELINE/config.env 파싱."""
    tok = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
    igid = os.environ.get("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
    conf = Path(os.environ.get("INSTAGRAM_PIPELINE", str(ROOT / "ig_pipeline"))) / "config.env"
    if conf.is_file():
        for line in conf.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("INSTAGRAM_ACCESS_TOKEN=") and not tok:
                tok = s.split("=", 1)[1].strip()
            if s.startswith("INSTAGRAM_BUSINESS_ACCOUNT_ID=") and not igid:
                igid = s.split("=", 1)[1].strip()
    if not (tok and igid):
        sys.exit("❌ IG 토큰/계정ID 없음 (env 또는 config.env)")
    return tok, igid


def api(endpoint, params, method="POST"):
    data = urllib.parse.urlencode(params).encode()
    url = f"{GRAPH}/{endpoint}"
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def upload_r2(paths, prefix):
    import boto3
    conf = Path(os.environ.get("INSTAGRAM_PIPELINE", str(ROOT / "ig_pipeline"))) / "config.env"
    if conf.is_file():
        try:
            from dotenv import load_dotenv
            load_dotenv(conf)
        except ImportError:
            pass
    cli = boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto")
    bucket = os.environ["R2_BUCKET_NAME"]
    public = os.environ["R2_PUBLIC_URL"].rstrip("/")
    urls = []
    for p in paths:
        key = f"{prefix}/{p.name}"
        ct = mimetypes.guess_type(p.name)[0] or "video/mp4"
        cli.upload_file(str(p), bucket, key, ExtraArgs={"ContentType": ct})
        urls.append(f"{public}/{key}")
        log(f"R2 업로드: {key}")
    return urls


def wait_container(cid, tok, label, max_wait=420):
    t0 = time.time()
    while time.time() - t0 < max_wait:
        st = api(cid, {"fields": "status_code", "access_token": tok}, "GET")
        code = st.get("status_code")
        if code == "FINISHED":
            return True
        if code == "ERROR":
            log(f"❌ 컨테이너 처리 실패({label}): {st}")
            return False
        time.sleep(8)
    log(f"❌ 컨테이너 처리 타임아웃({label})")
    return False


def caption_from(post_path):
    txt = post_path.read_text(encoding="utf-8")
    return txt.split("[첫 댓글]")[0].strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    d = json.loads(Path(a.manifest).read_text(encoding="utf-8"))

    videos = [ROOT / v for v in d["videos"]]
    missing = [str(v) for v in videos if not v.is_file()]
    if missing:
        sys.exit(f"❌ 영상 없음: {missing}")
    cap_path = ROOT / d["caption_txt"]
    caption = caption_from(cap_path) if cap_path.is_file() else ""
    if not caption:
        sys.exit(f"❌ 캡션 없음: {cap_path}")
    log(f"영상 {len(videos)}개 · 캡션 {len(caption)}자 · prefix {d['prefix']}")

    urls = upload_r2(videos, d["prefix"])

    if a.dry_run or d.get("dry_run"):
        log("✅ dry-run: R2 업로드까지만 수행 (IG 미게시)")
        for u in urls:
            log(f"  {u}")
        return

    tok, igid = load_ig_config()
    children = []
    for i, u in enumerate(urls, 1):
        res = api(f"{igid}/media", {
            "media_type": "VIDEO", "video_url": u,
            "is_carousel_item": "true", "access_token": tok})
        cid = res["id"]
        log(f"자식 컨테이너 {i}/{len(urls)}: {cid}")
        if not wait_container(cid, tok, f"v{i}"):
            sys.exit(1)
        children.append(cid)

    car = api(f"{igid}/media", {
        "media_type": "CAROUSEL", "children": ",".join(children),
        "caption": caption, "access_token": tok})
    car_id = car["id"]
    log(f"캐러셀 컨테이너: {car_id}")
    if not wait_container(car_id, tok, "carousel"):
        sys.exit(1)

    pub = api(f"{igid}/media_publish", {"creation_id": car_id, "access_token": tok})
    media_id = pub["id"]
    print(f"게시 완료 — ID:{media_id}")


if __name__ == "__main__":
    main()
