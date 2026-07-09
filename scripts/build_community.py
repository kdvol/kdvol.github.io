#!/usr/bin/env python3
"""커뮤니티 페이지(A+B) — Giscus 토론 + 텔레그램 실시간.

정적 사이트라 자체 백엔드/DB 없이 커뮤니티를 붙인다:
  A. Giscus — GitHub Discussions 기반 토론 게시판(로그인은 GitHub OAuth에 위임,
     우리가 비밀번호를 다루지 않음). data-mapping=pathname → 페이지별 스레드.
  B. 텔레그램 — 실시간 대화는 기존 채널(t.me/soonsal)에서. 웹에서 진입 CTA.

CONFIG의 giscus 값은 실제 repo/카테고리 ID. 남은 사용자 작업: giscus GitHub App을
repo에 설치(github.com/apps/giscus) — 이건 웹 UI라 코드로 못 함. 설치 전엔 위젯이
'giscus is not installed' 안내를 띄운다.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://soonsal.com"
OUT = ROOT / "community"

CONFIG = {
    "giscus_repo": "kdvol/kdvol.github.io",
    "giscus_repo_id": "R_kgDORavtPg",
    "giscus_category": "General",
    "giscus_category_id": "DIC_kwDORavtPs4DA0PT",
    "telegram": "soonsal",
    "instagram": "soonsal.brief",
}

PAGE = """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>커뮤니티 — 순살브리핑</title>
<meta name="description" content="순살브리핑 커뮤니티. 텔레그램에서 실시간으로 시장을 이야기하고, 게시판에서 브리핑을 두고 토론하세요.">
<link rel="canonical" href="__BASE__/community/"><meta name="robots" content="index, follow">
<meta property="og:title" content="커뮤니티 — 순살브리핑"><meta property="og:type" content="website">
<meta property="og:locale" content="ko_KR"><meta property="og:url" content="__BASE__/community/">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#111;color:#eee;font-family:'DM Sans','Apple SD Gothic Neo',sans-serif;-webkit-text-size-adjust:100%}
.wrap{max-width:760px;margin:0 auto;padding:24px 16px 60px}
a{color:#eee;text-decoration:none}
.home{color:#F07040;font-size:.88rem;display:inline-block;margin-bottom:14px}
h1{font-size:1.5rem;margin-bottom:6px;letter-spacing:-.02em}
.sub{color:#888;font-size:.9rem;margin-bottom:24px;line-height:1.6}
.card{background:#161616;border:1px solid #242424;border-radius:14px;padding:20px;margin:16px 0}
.card h2{font-size:1.1rem;margin-bottom:6px}
.card p{color:#9aa;font-size:.9rem;line-height:1.6;margin-bottom:14px}
.btn{display:inline-flex;align-items:center;gap:8px;background:#229ED9;color:#fff;font-weight:700;
  padding:12px 22px;border-radius:10px;font-size:.98rem}
.btn.ig{background:linear-gradient(45deg,#f09433,#dc2743,#bc1888)}
.btn+.btn{margin-left:10px}
.live{display:inline-block;width:8px;height:8px;background:#2ecc71;border-radius:50%;margin-right:6px;
  box-shadow:0 0 0 0 #2ecc7188;animation:p 2s infinite}
@keyframes p{0%{box-shadow:0 0 0 0 #2ecc7188}70%{box-shadow:0 0 0 8px #2ecc7100}100%{box-shadow:0 0 0 0 #2ecc7100}}
.note{color:#666;font-size:.8rem;margin-top:10px;line-height:1.55}
.giscus{margin-top:8px}
@media(min-width:640px){.wrap{padding:32px 20px 60px}}
</style></head><body><div class="wrap">
<a class="home" href="/">← 순살 홈</a>
<h1>순살 커뮤니티</h1>
<p class="sub">시장은 혼자 보는 것보다 같이 볼 때 덜 무섭습니다. 실시간 대화는 텔레그램에서,
브리핑을 두고 찬찬히 나누는 토론은 아래 게시판에서.</p>

<div class="card">
<h2><span class="live"></span>실시간 대화 · 텔레그램</h2>
<p>장 열리는 시간의 흐름, 속보에 대한 반응, 서로의 포지션 — 실시간은 텔레그램 채널에서 오갑니다.
지금 바로 참여하세요.</p>
<a class="btn" href="https://t.me/__TG__" target="_blank" rel="noopener">✈️ 텔레그램 참여</a>
<a class="btn ig" href="https://instagram.com/__IG__" target="_blank" rel="noopener">📸 인스타그램</a>
</div>

<div class="card">
<h2>💬 토론 게시판</h2>
<p>브리핑에 대한 생각, 종목·시장 이야기, 질문과 반박 — 자유롭게 남겨보세요.
로그인은 GitHub 계정으로 안전하게 처리됩니다(순살은 비밀번호를 저장하지 않습니다).</p>
<div class="giscus"></div>
<script src="https://giscus.app/client.js"
  data-repo="__REPO__" data-repo-id="__REPO_ID__"
  data-category="__CAT__" data-category-id="__CAT_ID__"
  data-mapping="pathname" data-strict="0" data-reactions-enabled="1"
  data-emit-metadata="0" data-input-position="top" data-theme="dark_dimmed"
  data-lang="ko" data-loading="lazy" crossorigin="anonymous" async>
</script>
<p class="note">게시판이 안 보이면 아직 설정 마무리 전입니다(관리자: giscus 앱 설치 필요).</p>
</div>
</div></body></html>"""


def build():
    OUT.mkdir(exist_ok=True)
    html = (PAGE.replace("__BASE__", BASE)
            .replace("__TG__", CONFIG["telegram"])
            .replace("__IG__", CONFIG["instagram"])
            .replace("__REPO__", CONFIG["giscus_repo"])
            .replace("__REPO_ID__", CONFIG["giscus_repo_id"])
            .replace("__CAT__", CONFIG["giscus_category"])
            .replace("__CAT_ID__", CONFIG["giscus_category_id"]))
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print("💬 community: /community/ (Giscus 토론 + 텔레그램)")


if __name__ == "__main__":
    build()
