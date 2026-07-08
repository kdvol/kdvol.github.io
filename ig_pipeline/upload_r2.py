"""
upload_r2.py — PNG 파일들을 Cloudflare R2에 업로드

사용법:
    from upload_r2 import upload_pngs_to_r2
    urls = upload_pngs_to_r2(
        png_paths=["./output_png/card_01.png", ...],
        r2_prefix="cardnews/2026/0304"
    )
    # → ["https://img.soonsal.com/cardnews/2026/0304/card_01.png", ...]

단독 실행:
    python upload_r2.py ./output_png/순살카드뉴스_20260304_*.png

환경변수 필요:
    R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
    R2_BUCKET_NAME, R2_PUBLIC_URL
"""

import sys
import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

# config.env는 항상 이 스크립트 옆에 있음 — CWD 무관 절대경로로 로드
# (deploy.py가 ~/kdvol.github.io에서 호출 시 상대경로 "config.env"는 못 찾음)
load_dotenv(Path(__file__).resolve().parent / "config.env")


def _get_r2_client():
    """Cloudflare R2 S3 호환 클라이언트 생성."""
    account_id = os.environ["R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def upload_pngs_to_r2(
    png_paths: list[str],
    r2_prefix: str = "cardnews",
) -> list[str]:
    """
    PNG 파일들을 R2 버킷에 업로드하고 public URL을 반환.

    Args:
        png_paths: 업로드할 PNG 파일 경로 리스트
        r2_prefix: R2 내 경로 prefix (예: "cardnews/2026/0304")

    Returns:
        public URL 리스트 (순서 동일)
    """
    client = _get_r2_client()
    bucket = os.environ["R2_BUCKET_NAME"]
    public_url = os.environ["R2_PUBLIC_URL"].rstrip("/")

    urls = []

    for png_path in png_paths:
        png_path = Path(png_path)
        if not png_path.exists():
            raise FileNotFoundError(f"PNG 파일 없음: {png_path}")

        # R2 key를 영문으로 변환 (Instagram API가 한글 URL 처리 불가)
        # 순살카드뉴스_20260304_01.png → 01.png
        import re
        num_match = re.search(r"_(\d{2})\.png$", png_path.name)
        r2_filename = f"{num_match.group(1)}.png" if num_match else png_path.name
        r2_key = f"{r2_prefix}/{r2_filename}"

        print(f"[upload_r2] 업로드: {png_path.name} → s3://{bucket}/{r2_key}")

        client.upload_file(
            str(png_path),
            bucket,
            r2_key,
            ExtraArgs={
                "ContentType": "image/png",
                "CacheControl": "public, max-age=31536000",  # 1년 캐시
            },
        )

        url = f"{public_url}/{r2_key}"
        urls.append(url)

    print(f"[upload_r2] 완료 — {len(urls)}장 업로드")
    return urls


def derive_r2_prefix(html_filename: str) -> str:
    """
    HTML 파일명에서 R2 prefix를 자동 생성.
    
    예: "순살카드뉴스_20260304.html"
        → "cardnews/2026/0304"
    예: "순살크립토카드뉴스_20260304.html"
        → "cardnews/2026/0304-crypto"
    """
    stem = Path(html_filename).stem
    
    # 날짜 추출 (YYYYMMDD)
    import re
    m = re.search(r"(\d{8})", stem)
    if not m:
        raise ValueError(f"파일명에서 날짜를 찾을 수 없음: {stem}")
    
    date_str = m.group(1)
    yyyy = date_str[:4]
    mmdd = date_str[4:]
    
    # 크립토 여부
    suffix = "-crypto" if "크립토" in stem else ""
    
    return f"cardnews/{yyyy}/{mmdd}{suffix}"


if __name__ == "__main__":
    import glob

    if len(sys.argv) < 2:
        print("Usage: python upload_r2.py <png_glob_pattern>")
        print("  예: python upload_r2.py './output_png/순살카드뉴스_20260304_*.png'")
        sys.exit(1)

    pattern = sys.argv[1]
    files = sorted(glob.glob(pattern))
    
    if not files:
        print(f"매칭 파일 없음: {pattern}")
        sys.exit(1)

    # prefix 자동 추출
    prefix = derive_r2_prefix(files[0])
    print(f"[upload_r2] R2 prefix: {prefix}")

    urls = upload_pngs_to_r2(files, r2_prefix=prefix)
    for url in urls:
        print(url)
