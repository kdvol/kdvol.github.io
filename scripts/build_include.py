#!/usr/bin/env python3
"""공용 위젯 스크립트 태그를 전 페이지에 1회 보장 — 재주입 비용 제거.

기존엔 FAB·공유 버튼 HTML을 페이지마다 통째로 심어서, 바꿀 때마다 전 페이지를
다시 건드려야 했다. 이제는 로직을 /soonsal.js 로 빼고 각 페이지엔 안 바뀌는
<script src="/soonsal.js" defer> 한 줄만 둔다. 동작 변경은 그 파일만 고치면 끝.

이 스텝은: ① 과거 인라인 FAB/공유 코드 제거 ② 스크립트 태그 보장(멱등, 자가치유).
generate_seo가 모든 페이지 생성 후 마지막에 호출.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAG = '<script src="/soonsal.js" defer></script>'
BODY_RE = re.compile(r"</body>", re.I)

# 과거 방식으로 인라인 주입됐던 것들 제거
STRIP = [
    re.compile(r'<a\b[^>]*class="ss-fab".*?</a>', re.S),        # 옛 FAB(인라인 style 포함)
    re.compile(r'<button class="ss-share"[^>]*>.*?</button>', re.S),  # 옛 공유 버튼
    re.compile(r'<style>\s*\.ss-share.*?</style>', re.S),        # 옛 공유 CSS
    re.compile(r'<script>\s*function ssToast.*?</script>', re.S),  # 옛 공유 JS
]

GLOBS = ["index.html", "newsletters/2026/*.html", "cardnews/2026/*.html",
         "english/2026/*.html", "financial-english/*.html", "special/*.html",
         "topics/*.html", "wiki/*.html", "search/index.html",
         "newsletters/index.html", "cardnews/index.html", "english/index.html",
         "school/index.html", "youtube/index.html"]


def main():
    n = 0
    seen = set()
    for g in GLOBS:
        for p in ROOT.glob(g):
            if p in seen:
                continue
            seen.add(p)
            html = p.read_text(encoding="utf-8", errors="replace")
            if p.name == "index.html" and p.parent.name == "wiki":
                continue                                  # /wiki/ 리다이렉트 스텁
            if 'http-equiv="refresh"' in html:
                continue
            orig = html
            for rx in STRIP:                              # 옛 인라인 제거
                html = rx.sub("", html)
            if TAG not in html and BODY_RE.search(html):  # 스크립트 태그 보장
                html = BODY_RE.sub(TAG + "</body>", html, count=1)
            if html != orig:
                p.write_text(html, encoding="utf-8")
                n += 1
    print(f"🧩 include: /soonsal.js 태그 보장 {n}개 페이지")
    return n


if __name__ == "__main__":
    main()
