#!/usr/bin/env python3
"""2월 이관 전 옛 URL을 현재 주소로 잇는다.

원래 리포 루트의 `_redirects`(Netlify 형식)가 담당하던 일인데, 사이트가 GitHub
Pages라 그 파일은 읽히지 않았고 해당 URL들은 이관 이후 계속 404였다. Netlify
letters 프로젝트 정리하면서 `_redirects`를 지웠고, 의도했던 연결을 여기서 실제로
동작하는 형태(meta refresh + JS)로 되살린다.

GitHub Pages는 확장자 없는 요청(`/2026/0227/crypto`)에도 `crypto.html`을 내주므로
파일 하나가 `.html` 있는 주소와 없는 주소를 함께 커버한다.

/s/ 공유 스텁과 같은 방식: noindex,follow + canonical로 원본에 신호를 몰아준다.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://soonsal.com"

# 옛 경로(파일) → 현재 주소
MAP = {
    "2026/0227/index.html": "/newsletters/2026/0227.html",
    "2026/0227/crypto.html": "/newsletters/2026/0227-crypto.html",
    "2026/0227/publish.html": "/english/2026/0227.html",
    "2026/0228/index.html": "/newsletters/2026/0228.html",
    "2026/0228/crypto.html": "/newsletters/2026/0228-crypto.html",
    # 0228 영문판은 발행되지 않았다 → 영어 허브로 보낸다(404보다 낫다)
    "2026/0228/publish.html": "/english/",
}


def _page(dest):
    return (
        '<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">'
        '<meta name="robots" content="noindex,follow">'
        '<title>이동합니다 — 순살브리핑</title>'
        f'<link rel="canonical" href="{BASE}{dest}">'
        f'<meta http-equiv="refresh" content="0; url={dest}">'
        f'</head><body><script>location.replace("{dest}");</script>'
        f'<a href="{dest}">순살브리핑에서 보기</a></body></html>\n'
    )


def build():
    n = 0
    for rel, dest in MAP.items():
        target = ROOT / dest.lstrip("/")
        # 목적지가 디렉터리 주소면 index.html 존재로 확인
        probe = target / "index.html" if dest.endswith("/") else target
        if not probe.exists():
            print(f"⚠️ legacy: 목적지 없음, 건너뜀 — {dest}")
            continue
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(_page(dest), encoding="utf-8")
        n += 1
    print(f"↪️  legacy: 옛 URL {n}개 연결 (2월 이관 전 주소)")
    return n


if __name__ == "__main__":
    build()
