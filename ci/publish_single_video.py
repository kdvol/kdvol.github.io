#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""단일 세로영상 발행 — IG 릴스 + / 또는 유튜브 숏츠. 클라우드 큐 소비용.

publish_from_queue.py가 manifest {"type":"single_video"}일 때 호출.
IG 릴스와 유튜브를 독립 스위치로 제어 → "IG만" / "유튜브만" / "둘 다" 모두 가능.
성공 시 stdout에 "게시 완료 — ID:<미디어ID>" (큐의 첫 댓글·멱등 로직이 이 라인을 파싱).

manifest 스키마:
{
  "type": "single_video",
  "video": "_publish/sv/<name>/reel.mp4",     # repo 상대경로 (BGM 베이킹 완료본)
  "caption_txt": "_publish/sv/<name>/POST.txt",  # [첫 댓글] 앞 = 캡션
  "prefix": "sv/2026/0717_loop",              # R2 경로 (재발행 시 반드시 변경)
  "instagram": true,                           # IG 릴스 게시 여부
  "youtube": true,                             # 유튜브 숏츠 게시 여부
  "youtube_title": "...",                     # 없으면 캡션 첫 줄
  "name": "loop", "target_epoch": ..., "dry_run": false
}
※ 유튜브만 발행(instagram:false)이면 IG 미디어ID가 없으므로, 유튜브 성공을 성공 라인으로 출력한다.
"""
import argparse
import json
import mimetypes
import os
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("KDVOL_ROOT", ".")).resolve()
GRAPH = "https://graph.facebook.com/v21.0"


def log(m):
    print(f"[sv] {m}", flush=True)


def load_ig_config():
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
        sys.exit("❌ IG 토큰/계정ID 없음")
    return tok, igid


def api(endpoint, params, method="POST"):
    url = f"{GRAPH}/{endpoint}"
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode())
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def upload_r2(path: Path, prefix: str) -> str:
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
    key = f"{prefix}/{path.name}"
    cli.upload_file(str(path), os.environ["R2_BUCKET_NAME"], key,
                    ExtraArgs={"ContentType": mimetypes.guess_type(path.name)[0] or "video/mp4"})
    url = f"{os.environ['R2_PUBLIC_URL'].rstrip('/')}/{key}"
    log(f"R2 업로드: {key}")
    return url


def wait_container(cid, tok, max_wait=600):
    t0 = time.time()
    while time.time() - t0 < max_wait:
        st = api(cid, {"fields": "status_code", "access_token": tok}, "GET")
        code = st.get("status_code")
        if code == "FINISHED":
            return True
        if code == "ERROR":
            log(f"❌ 릴스 컨테이너 처리 실패: {st}")
            return False
        time.sleep(8)
    log("❌ 릴스 컨테이너 타임아웃")
    return False


def post_ig_reel(video_url, caption):
    tok, igid = load_ig_config()
    res = api(f"{igid}/media", {"media_type": "REELS", "video_url": video_url,
                                "caption": caption, "share_to_feed": "true",
                                "access_token": tok})
    cid = res["id"]
    log(f"릴스 컨테이너: {cid}")
    if not wait_container(cid, tok):
        return None
    pub = api(f"{igid}/media_publish", {"creation_id": cid, "access_token": tok})
    return pub["id"]


def upload_youtube(video_path, title, description):
    """유튜브 숏츠. 실패해도 예외 던지지 않음(IG 성공 무효화 방지)."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        log("⚠️ 유튜브 라이브러리 없음 — 스킵")
        return None
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    tok_json = os.environ.get("YOUTUBE_TOKEN_JSON", "")
    if tok_json:
        tf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        tf.write(tok_json)
        tf.close()
        tok_path = tf.name
    else:
        tok_path = os.path.expanduser("~/soonsal-reels/youtube_token.json")
    if not Path(tok_path).is_file():
        log("⚠️ 유튜브 토큰 없음 — 스킵")
        return None
    try:
        creds = Credentials.from_authorized_user_file(tok_path, SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        yt = build("youtube", "v3", credentials=creds)
        title = title if "#Shorts" in title else f"{title} #Shorts"
        body = {
            "snippet": {"title": title[:100], "description": description,
                        "categoryId": "25", "defaultLanguage": "ko",
                        "tags": ["순살", "주식", "투자", "개미", "Shorts", "밈", "경제"]},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
        }
        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
        resp = None
        while resp is None:
            _, resp = req.next_chunk()
        vid = resp.get("id")
        log(f"📺 유튜브 숏츠 게시 완료 — https://youtube.com/shorts/{vid}")
        return vid
    except Exception as e:  # noqa: BLE001
        log(f"⚠️ 유튜브 업로드 실패(무시): {type(e).__name__}: {str(e)[:200]}")
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    d = json.loads(Path(a.manifest).read_text(encoding="utf-8"))

    video = ROOT / d["video"]
    if not video.is_file():
        sys.exit(f"❌ 영상 없음: {video}")
    cap_path = ROOT / d["caption_txt"]
    caption = cap_path.read_text(encoding="utf-8").split("[첫 댓글]")[0].strip() \
        if cap_path.is_file() else ""
    want_ig = bool(d.get("instagram", True))
    want_yt = bool(d.get("youtube", False))
    log(f"{d.get('name')} · IG={want_ig} · YT={want_yt} · 캡션 {len(caption)}자")

    if a.dry_run or d.get("dry_run"):
        if want_ig:
            log(f"dry-run: R2 업로드만 → {upload_r2(video, d['prefix'])}")
        log("✅ dry-run 완료 (게시 없음)")
        return

    ig_id = None
    if want_ig:
        url = upload_r2(video, d["prefix"])
        ig_id = post_ig_reel(url, caption)
        if not ig_id:
            sys.exit(1)          # 큐 유지 → 재시도
        print(f"게시 완료 — ID:{ig_id}")

    if want_yt:
        yt_id = upload_youtube(str(video), d.get("youtube_title") or caption.split("\n")[0],
                               caption)
        # 유튜브 전용 발행이면 유튜브 성공을 성공 라인으로 (큐 done 이동 조건 충족용)
        if not want_ig:
            if not yt_id:
                sys.exit(1)
            print(f"게시 완료 — ID:{yt_id}")


if __name__ == "__main__":
    main()
