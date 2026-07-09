#!/usr/bin/env python3
"""플로팅 커뮤니티 버튼(FAB) — 전 페이지 우하단에 상시 표시.

커뮤니티를 nav 탭으로 빼는 대신, 어느 페이지에서든 한 번에 닿는 플로팅 버튼으로.
</body> 직전에 주입(멱등). generate_seo가 모든 페이지 생성 후 마지막에 호출하므로
뉴스레터·주제별·위키·검색 등 전부 커버되고, 새 페이지에도 자동 적용.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FAB = ('<a href="/community/" class="ss-fab" aria-label="커뮤니티 참여" title="커뮤니티">💬'
       '<style>.ss-fab{position:fixed;right:16px;bottom:16px;z-index:9999;width:54px;height:54px;'
       'border-radius:50%;background:#F07040;box-shadow:0 4px 14px rgba(0,0,0,.35);display:flex;'
       'align-items:center;justify-content:center;text-decoration:none;font-size:26px;line-height:1;'
       'transition:transform .15s}.ss-fab:active,.ss-fab:hover{transform:scale(1.08)}'
       '@media(min-width:640px){.ss-fab{width:58px;height:58px;right:24px;bottom:24px;font-size:28px}}'
       '</style></a>')

# FAB를 넣을 페이지: 콘텐츠·탐색 페이지 전부. 커뮤니티 자신·리다이렉트 스텁은 제외.
GLOBS = ["index.html", "newsletters/2026/*.html", "cardnews/2026/*.html",
         "english/2026/*.html", "financial-english/*.html", "special/*.html",
         "topics/*.html", "wiki/*.html", "search/index.html",
         "newsletters/index.html", "cardnews/index.html", "english/index.html",
         "school/index.html", "youtube/index.html"]

BODY_RE = re.compile(r"</body>", re.I)


def _skip(p, html):
    if "ss-fab" in html:                         # 이미 있음(멱등)
        return True
    if p.name == "index.html" and p.parent.name == "wiki":
        return True                              # /wiki/ 는 리다이렉트 스텁
    if "http-equiv=\"refresh\"" in html:
        return True
    return False


def main():
    n = 0
    seen = set()
    for g in GLOBS:
        for p in ROOT.glob(g):
            if p in seen:
                continue
            seen.add(p)
            html = p.read_text(encoding="utf-8", errors="replace")
            if _skip(p, html) or not BODY_RE.search(html):
                continue
            new = BODY_RE.sub(FAB + "</body>", html, count=1)
            p.write_text(new, encoding="utf-8")
            n += 1
    print(f"💬 fab: 플로팅 커뮤니티 버튼 주입 {n}개 페이지")
    return n


if __name__ == "__main__":
    main()
