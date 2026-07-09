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
body{background:#111;color:#eee;font-family:'DM Sans','Apple SD Gothic Neo','Malgun Gothic',sans-serif;-webkit-text-size-adjust:100%}
.wrap{max-width:720px;margin:0 auto;padding:24px 16px 60px}
a{color:#eee;text-decoration:none}
.home{color:#F07040;font-size:.88rem;display:inline-block;margin-bottom:16px}
h1{font-size:1.5rem;margin-bottom:6px;letter-spacing:-.02em}
.sub{color:#888;font-size:.9rem;margin-bottom:24px;line-height:1.65}
.card{background:#161616;border:1px solid #222;border-radius:14px;padding:22px;margin:16px 0}
.card h2{font-size:1.08rem;margin-bottom:8px;letter-spacing:-.01em}
.card p{color:#999;font-size:.9rem;line-height:1.65;margin-bottom:16px}
.btn{display:inline-flex;align-items:center;gap:8px;background:#E55A00;color:#fff;font-weight:700;
  padding:12px 22px;border-radius:8px;font-size:.95rem;transition:background .2s}
.btn:hover{background:#cc4e00}
.social-row{display:flex;gap:14px;margin-top:16px}
.social-icon{display:flex;align-items:center;justify-content:center;width:38px;height:38px;border-radius:50%;
  background:rgba(255,255,255,.06);transition:background .2s,transform .15s}
.social-icon:hover{background:rgba(255,255,255,.14);transform:scale(1.08)}
.social-icon svg{width:16px;height:16px;fill:#777;transition:fill .2s}
.social-icon:hover svg{fill:#fff}
.live{display:inline-block;width:7px;height:7px;background:#2ecc71;border-radius:50%;margin-right:7px;vertical-align:middle;
  box-shadow:0 0 0 0 #2ecc7180;animation:p 2s infinite}
@keyframes p{0%{box-shadow:0 0 0 0 #2ecc7180}70%{box-shadow:0 0 0 7px #2ecc7100}100%{box-shadow:0 0 0 0 #2ecc7100}}
.note{color:#555;font-size:.78rem;margin-top:12px;line-height:1.55}
.giscus{margin-top:8px}
@media(min-width:640px){.wrap{padding:32px 20px 60px}}
</style></head><body><div class="wrap">
<a class="home" href="/">← 순살 홈</a>
<h1>순살 커뮤니티</h1>
<p class="sub">시장은 혼자 보는 것보다 같이 볼 때 덜 무섭습니다. 실시간 대화는 텔레그램에서,
브리핑을 두고 찬찬히 나누는 토론은 아래 게시판에서.</p>

<div class="card">
<h2><span class="live"></span>실시간 대화 · 텔레그램</h2>
<p>장 흐름, 속보 반응, 서로의 포지션 — 실시간 대화는 텔레그램 채널에서 오갑니다. 지금 참여하세요.</p>
<a class="btn" href="https://t.me/__TG__" target="_blank" rel="noopener">텔레그램 대화 참여 →</a>
<div class="social-row">
<a class="social-icon" href="https://t.me/__TG__" target="_blank" rel="noopener" title="Telegram @__TG__"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0M8.287 5.906q-1.168.486-4.666 2.01-.567.225-.595.442c-.03.243.275.339.69.47l.175.055c.408.133.958.288 1.243.294q.39.01.868-.32 3.269-2.206 3.374-2.23c.05-.012.12-.026.166.016s.042.12.037.141c-.03.129-1.227 1.241-1.846 1.817-.193.18-.33.307-.358.336a8 8 0 0 1-.188.186c-.38.366-.664.64.015 1.088.327.216.589.393.85.571.284.194.568.387.936.629q.14.092.27.187c.331.236.63.448.997.414.214-.02.435-.22.547-.82.265-1.417.786-4.486.906-5.751a1.4 1.4 0 0 0-.013-.315.34.34 0 0 0-.114-.217.53.53 0 0 0-.31-.093c-.3.005-.763.166-2.984 1.09"/></svg></a>
<a class="social-icon" href="https://instagram.com/__IG__" target="_blank" rel="noopener" title="Instagram @__IG__"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="M8 0C5.829 0 5.556.01 4.703.048 3.85.088 3.269.222 2.76.42a3.9 3.9 0 0 0-1.417.923A3.9 3.9 0 0 0 .42 2.76C.222 3.268.087 3.85.048 4.7.01 5.555 0 5.827 0 8.001c0 2.172.01 2.444.048 3.297.04.852.174 1.433.372 1.942.205.526.478.972.923 1.417.444.445.89.719 1.416.923.51.198 1.09.333 1.942.372C5.555 15.99 5.827 16 8 16s2.444-.01 3.298-.048c.851-.04 1.434-.174 1.943-.372a3.9 3.9 0 0 0 1.416-.923c.445-.445.718-.891.923-1.417.197-.509.332-1.09.372-1.942C15.99 10.445 16 10.173 16 8s-.01-2.445-.048-3.299c-.04-.851-.175-1.433-.372-1.941a3.9 3.9 0 0 0-.923-1.417A3.9 3.9 0 0 0 13.24.42c-.51-.198-1.092-.333-1.943-.372C10.443.01 10.172 0 7.998 0zm-.717 1.442h.718c2.136 0 2.389.007 3.232.046.78.035 1.204.166 1.486.275.373.145.64.319.92.599s.453.546.598.92c.11.281.24.705.275 1.485.039.843.047 1.096.047 3.231s-.008 2.389-.047 3.232c-.035.78-.166 1.203-.275 1.485a2.5 2.5 0 0 1-.599.919c-.28.28-.546.453-.92.598-.28.11-.704.24-1.485.276-.843.038-1.096.047-3.232.047s-2.39-.009-3.233-.047c-.78-.036-1.203-.166-1.485-.276a2.5 2.5 0 0 1-.92-.598 2.5 2.5 0 0 1-.6-.92c-.109-.281-.24-.705-.275-1.485-.038-.843-.046-1.096-.046-3.233s.008-2.388.046-3.231c.036-.78.166-1.204.276-1.486.145-.373.319-.64.599-.92s.546-.453.92-.598c.282-.11.705-.24 1.485-.276.738-.034 1.024-.044 2.515-.045zm4.988 1.328a.96.96 0 1 0 0 1.92.96.96 0 0 0 0-1.92m-4.27 1.122a4.109 4.109 0 1 0 0 8.217 4.109 4.109 0 0 0 0-8.217m0 1.441a2.667 2.667 0 1 1 0 5.334 2.667 2.667 0 0 1 0-5.334"/></svg></a>
<a class="social-icon" href="https://youtube.com/@__TG__" target="_blank" rel="noopener" title="YouTube"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="M8.051 1.999h.089c.822.003 4.987.033 6.11.335a2.01 2.01 0 0 1 1.415 1.42c.101.38.172.883.22 1.402l.01.104.022.26.008.104c.065.914.073 1.77.074 1.957v.075c-.001.194-.01 1.108-.082 2.06l-.008.105-.009.104c-.05.572-.124 1.14-.235 1.558a2.01 2.01 0 0 1-1.415 1.42c-1.16.312-5.569.334-6.18.335h-.142c-.309 0-1.587-.006-2.927-.052l-.17-.006-.087-.004-.171-.007-.171-.007c-1.11-.049-2.167-.128-2.654-.26a2.01 2.01 0 0 1-1.415-1.419c-.111-.417-.185-.986-.235-1.558L.09 9.82l-.008-.104A31 31 0 0 1 0 7.68v-.123c.002-.215.01-.958.064-1.778l.007-.103.003-.052.008-.104.022-.26.01-.104c.048-.519.119-1.023.22-1.402a2.01 2.01 0 0 1 1.415-1.42c.487-.13 1.544-.21 2.654-.26l.17-.007.172-.006.086-.003.171-.007A100 100 0 0 1 7.858 2zM6.4 5.209v4.818l4.157-2.408z"/></svg></a>
</div>
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
