#!/usr/bin/env python3
"""스토리별 공유 OG 페이지 — /s/{id}.html.

문제: 뉴스레터 페이지엔 OG 태그가 하나뿐이라, #story-N 딥링크를 공유해도 미리보기
(썸네일·제목)가 뉴스레터 전체 것으로 뜨고 그날 카드뉴스(스토리와 무관)가 붙는다.
해결: 스토리마다 자기 OG(제목=스토리 제목, 설명=요약, 이미지=순살 기본)를 가진
작은 페이지를 만들고, 열면 뉴스레터의 해당 스토리로 리다이렉트. 공유는 이 URL로.

- OG 이미지: og-default.png (순살 기본 브랜드 — 스토리별 이미지 매핑 불가라 통일)
- noindex(썸 페이지, 콘텐츠 아님) + canonical은 실제 뉴스레터로
- 유료 서비스 0 · 순수 파이썬 정적 생성

generate_seo가 atomize 이후 호출(아톰 재사용).
"""
import html as _html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://soonsal.com"
OUT = ROOT / "s"
OG_IMG = f"{BASE}/og-default.png"
ATOMS = ROOT / "content" / "story_atoms.json"


def _clean_title(t):
    return re.sub(r"^[^\w<>&\"']{1,4}\s+", "", t or "").strip()


def _summary(body, n=120):
    s = re.sub(r"\s+", " ", (body or "")).strip()
    if len(s) > n:
        s = s[:n].rsplit(" ", 1)[0] + "…"
    return s


def build(atoms=None):
    if atoms is None:
        atoms = json.loads(ATOMS.read_text(encoding="utf-8")) if ATOMS.exists() else []
    OUT.mkdir(exist_ok=True)
    n = 0
    for a in atoms:
        if not a.get("title"):
            continue
        title = _clean_title(a["title"])
        desc = _summary(a.get("body", ""))
        nl_url = a["url"]                       # /newsletters/2026/0710.html#story-5
        shim_url = f"{BASE}/s/{a['id']}.html"
        canonical = f"{BASE}{a['newsletter']}"  # 프래그먼트 없는 실제 페이지
        t, d = _html.escape(title, True), _html.escape(desc, True)
        page = (
            f'<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">'
            f'<meta name="robots" content="noindex,follow">'
            f'<title>{t} — 순살브리핑</title>'
            f'<meta name="description" content="{d}">'
            f'<meta property="og:type" content="article">'
            f'<meta property="og:site_name" content="순살브리핑 Soonsal">'
            f'<meta property="og:title" content="{t}">'
            f'<meta property="og:description" content="{d}">'
            f'<meta property="og:image" content="{OG_IMG}">'
            f'<meta property="og:url" content="{shim_url}">'
            f'<meta property="og:locale" content="ko_KR">'
            f'<meta name="twitter:card" content="summary_large_image">'
            f'<meta name="twitter:title" content="{t}">'
            f'<meta name="twitter:description" content="{d}">'
            f'<meta name="twitter:image" content="{OG_IMG}">'
            f'<link rel="canonical" href="{canonical}">'
            f'<meta http-equiv="refresh" content="0; url={nl_url}">'
            f'</head><body>'
            f'<script>location.replace({json.dumps(nl_url)});</script>'
            f'<a href="{nl_url}">{t} — 순살브리핑에서 보기</a>'
            f'</body></html>'
        )
        (OUT / f"{a['id']}.html").write_text(page, encoding="utf-8")
        n += 1
    print(f"🖼️  sharepages: 스토리별 OG 페이지 {n}개 (/s/)")
    return n


if __name__ == "__main__":
    build()
