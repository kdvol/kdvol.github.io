"""
post_instagram.py — Instagram Graph API로 캐러셀 포스트 + 릴스 게시

캐러셀 플로우 (Meta Graph API):
    1. 각 이미지를 개별 media container로 생성 (POST /{ig-id}/media)
    2. 캐러셀 container 생성 (POST /{ig-id}/media, children=[...])
    3. 게시 (POST /{ig-id}/media_publish)

릴스 플로우:
    1. 영상 URL로 media container 생성 (media_type=REELS)
    2. 게시 (POST /{ig-id}/media_publish)

사용법:
    from post_instagram import post_carousel, post_reel
    
    # 캐러셀
    post_id = post_carousel(
        image_urls=["https://img.soonsal.com/.../01.png", ...],
        caption="순살브리핑 카드뉴스 2026.03.04\\n\\n#순살브리핑 #금융 #경제"
    )
    
    # 릴스
    reel_id = post_reel(
        video_url="https://img.soonsal.com/.../shorts.mp4",
        caption="순살브리핑 카드뉴스 2026.03.04"
    )

환경변수 필요:
    INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID
"""

import os
import sys
import time
import json

import requests
from dotenv import load_dotenv

load_dotenv("config.env")

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


def _get_config():
    return {
        "access_token": os.environ["INSTAGRAM_ACCESS_TOKEN"],
        "ig_id": os.environ["INSTAGRAM_BUSINESS_ACCOUNT_ID"],
    }


def _api_post(endpoint: str, params: dict) -> dict:
    """Graph API POST 요청 + 에러 핸들링."""
    url = f"{GRAPH_API_BASE}/{endpoint}"
    resp = requests.post(url, json=params, timeout=60)
    data = resp.json()
    
    if "error" in data:
        err = data["error"]
        raise RuntimeError(
            f"Instagram API 에러: [{err.get('code')}] {err.get('message')}"
        )
    return data


def _api_get(endpoint: str, params: dict) -> dict:
    """Graph API GET 요청."""
    url = f"{GRAPH_API_BASE}/{endpoint}"
    resp = requests.get(url, params=params, timeout=60)
    return resp.json()


def _wait_for_media_ready(container_id: str, access_token: str, max_wait: int = 120):
    """
    미디어 컨테이너가 FINISHED 상태가 될 때까지 폴링.
    릴스 업로드 등 시간이 걸리는 경우에 사용.
    """
    for i in range(max_wait // 5):
        data = _api_get(container_id, {
            "fields": "status_code",
            "access_token": access_token,
        })
        status = data.get("status_code")
        if status == "FINISHED":
            return True
        elif status == "ERROR":
            raise RuntimeError(f"미디어 처리 실패: {data}")
        print(f"  [wait] 상태: {status} ({(i+1)*5}s)")
        time.sleep(5)
    
    raise TimeoutError(f"미디어 처리 타임아웃 ({max_wait}s)")


# ─── 캐러셀 포스트 ───────────────────────────────────────────

def post_carousel(
    image_urls: list[str],
    caption: str,
    ig_account_id: str = None,
) -> str:
    """
    캐러셀 포스트 게시 (이미지 최대 20장).
    
    Args:
        image_urls: public 이미지 URL 리스트 (순서대로)
        caption: 포스트 캡션 (해시태그 포함)
        ig_account_id: Instagram account ID 오버라이드 (None이면 환경변수 사용)
    
    Returns:
        게시된 포스트 ID
    """
    cfg = _get_config()
    ig_id = ig_account_id or cfg["ig_id"]
    token = cfg["access_token"]

    if len(image_urls) < 2:
        raise ValueError("캐러셀은 최소 2장 필요")
    if len(image_urls) > 20:
        raise ValueError("캐러셀은 최대 20장")

    # Step 1: 각 이미지를 개별 container로 생성
    child_ids = []
    for i, url in enumerate(image_urls, 1):
        print(f"[instagram] 이미지 컨테이너 생성 [{i}/{len(image_urls)}]")
        data = _api_post(f"{ig_id}/media", {
            "image_url": url,
            "is_carousel_item": True,
            "access_token": token,
        })
        child_ids.append(data["id"])
        time.sleep(1)  # rate limit 방지

    # Step 2: 캐러셀 container 생성
    print(f"[instagram] 캐러셀 컨테이너 생성 ({len(child_ids)}장)")
    carousel_data = _api_post(f"{ig_id}/media", {
        "media_type": "CAROUSEL",
        "children": ",".join(child_ids),
        "caption": caption,
        "access_token": token,
    })
    carousel_id = carousel_data["id"]

    # Step 3: 게시
    print(f"[instagram] 게시 중...")
    time.sleep(3)  # 처리 대기
    publish_data = _api_post(f"{ig_id}/media_publish", {
        "creation_id": carousel_id,
        "access_token": token,
    })

    post_id = publish_data["id"]
    print(f"[instagram] ✅ 캐러셀 게시 완료 — ID: {post_id}")
    return post_id


# ─── 릴스 ────────────────────────────────────────────────────

def post_reel(
    video_url: str,
    caption: str,
    cover_url: str = None,
    share_to_feed: bool = True,
) -> str:
    """
    릴스 게시.
    
    Args:
        video_url: public 영상 URL (.mp4)
        caption: 릴스 캡션
        cover_url: 커버 이미지 URL (선택)
        share_to_feed: 피드에도 공유 여부
    
    Returns:
        게시된 릴스 ID
    """
    cfg = _get_config()
    ig_id = cfg["ig_id"]
    token = cfg["access_token"]

    # Step 1: 릴스 container 생성
    print(f"[instagram] 릴스 컨테이너 생성...")
    params = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": share_to_feed,
        "access_token": token,
    }
    if cover_url:
        params["cover_url"] = cover_url

    data = _api_post(f"{ig_id}/media", params)
    container_id = data["id"]

    # Step 2: 업로드 완료 대기
    print(f"[instagram] 영상 처리 대기 중...")
    _wait_for_media_ready(container_id, token)

    # Step 3: 게시
    print(f"[instagram] 릴스 게시 중...")
    publish_data = _api_post(f"{ig_id}/media_publish", {
        "creation_id": container_id,
        "access_token": token,
    })

    reel_id = publish_data["id"]
    print(f"[instagram] ✅ 릴스 게시 완료 — ID: {reel_id}")
    return reel_id


# ─── 캡션 생성 헬퍼 ──────────────────────────────────────────

def make_caption(html_filename: str) -> str:
    """
    HTML 파일명에서 캡션 + 해시태그 자동 생성.
    
    예: "순살카드뉴스_20260304.html"
        → "순살브리핑 카드뉴스 2026.03.04\n\n#순살브리핑 #금융 #경제뉴스 #투자"
    예: "순살크립토카드뉴스_20260304.html"
        → "순살크립토 카드뉴스 2026.03.04\n\n#순살크립토 #비트코인 #크립토 #블록체인"
    """
    from pathlib import Path
    import re

    stem = Path(html_filename).stem
    m = re.search(r"(\d{8})", stem)
    date_str = m.group(1) if m else "unknown"
    formatted_date = f"{date_str[:4]}.{date_str[4:6]}.{date_str[6:]}"

    is_crypto = "크립토" in stem

    if is_crypto:
        brand = "순살크립토"
        tags = "#순살크립토 #비트코인 #크립토 #블록체인 #Web3 #금융 #투자"
    else:
        brand = "순살브리핑"
        tags = "#순살브리핑 #금융 #경제 #투자 #주식 #시장분석"

    return f"{brand} 카드뉴스 {formatted_date}\n\n{tags}"


# ─── CLI ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print("이 모듈은 cardnews_publish.py에서 호출됩니다.")
    print("단독 테스트:")
    print("  python -c \"from post_instagram import make_caption; print(make_caption('순살카드뉴스_20260304.html'))\"")
