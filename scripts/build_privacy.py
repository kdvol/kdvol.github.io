#!/usr/bin/env python3
"""수집 안내 페이지 (/privacy/).

쿠키를 쓰지 않아 동의 배너 의무는 없지만, 코멘트를 열면서 닉네임과 본문이라는 실제
이용자 입력을 저장하게 됐다. 무엇을 받고 무엇을 안 받는지 한 페이지에 적어둔다.

nav에는 넣지 않는다 — 푸터 안내 줄(soonsal.js의 mountNotice)에서만 닿게.
헤더는 build_nav의 것을 재사용해 다른 생성 페이지와 톤을 맞춘다.
"""
from pathlib import Path

import build_nav

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "privacy"
BASE = "https://soonsal.com"

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#fff;color:#222;-webkit-text-size-adjust:100%;
font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif}
.wrap{max-width:720px;margin:0 auto;padding:26px 18px 70px}
h1{font-size:1.45rem;letter-spacing:-.02em;margin-bottom:8px}
.lead{color:#77726a;font-size:.92rem;line-height:1.75;margin-bottom:26px}
h2{font-size:1rem;margin:26px 0 9px;color:#111}
h2:first-of-type{margin-top:6px}
p,li{font-size:.93rem;line-height:1.85;color:#3a3a3a}
ul{margin:0 0 0 18px}
li{margin-bottom:3px}
.box{border:1px solid #e8e8e0;background:#fafaf7;border-radius:10px;padding:16px 18px;margin:12px 0}
.box.no{border-color:#e8e0d8}
.hl{color:#E55A00;font-weight:700}
.upd{color:#a5a099;font-size:.8rem;margin-top:30px}
a{color:#E55A00}
"""

BODY = """
<h1>수집 안내</h1>
<p class="lead">순살브리핑 웹사이트가 무엇을 받고 무엇을 받지 않는지 적어둡니다.
어려운 말 없이 쓰겠습니다.</p>

<h2>받지 않는 것</h2>
<div class="box no">
<ul>
<li><span class="hl">쿠키를 쓰지 않습니다.</span> 그래서 동의 배너도 없습니다</li>
<li>IP 주소, 브라우저 정보(User-Agent)를 저장하지 않습니다</li>
<li>이름·이메일·전화번호 같은 개인정보를 웹사이트에서 받지 않습니다
<br>(뉴스레터 구독은 별도 서비스에서 처리되며 이 페이지와 무관합니다)</li>
<li>광고·분석 목적으로 제3자에게 넘기는 데이터가 없습니다</li>
</ul>
</div>

<h2>받는 것</h2>
<div class="box">
<ul>
<li><b>익명 번호</b> — 브라우저에 무작위로 만든 번호 하나를 저장해, 같은 사람이 다시
왔는지만 구분합니다. 누구인지는 알 수 없고 알아낼 방법도 없습니다</li>
<li><b>어떤 페이지를 봤는지</b>와 <b>어디서 들어왔는지</b>(검색·텔레그램·인스타그램 등)</li>
<li><b>버튼 반응</b> — 👍 좋았음 / 🤔 글쎄 / 🔥 중요함, 공유·코멘트 클릭</li>
<li><b>코멘트를 남기면</b> 그 닉네임과 본문</li>
</ul>
</div>

<h2>어떻게 보관하나요</h2>
<p>개별 기록을 쌓아두지 않고 <b>날짜별 합계</b>만 남깁니다. "8월 11일에 몇 명이 왔고
몇 번 눌렸다" 수준이지, "누가 무엇을 봤다"는 기록은 만들지 않습니다.
저장 위치는 Cloudflare D1이며, 이 사이트 운영 외의 용도로 쓰지 않습니다.</p>

<h2>코멘트 운영</h2>
<p>남긴 글의 책임은 작성자에게 있습니다. 아래에 해당하면 사전 통보 없이 숨겨집니다.</p>
<ul>
<li>투자 권유, 리딩방·오픈채팅 유인, 수익 보장 문구, 연락처 유도</li>
<li>맥락 없는 광고, 특정인 비방·모욕, 개인정보 노출, 도배</li>
</ul>
<p>링크나 위 문구가 포함된 글은 자동으로 검토 대기로 넘어가며, 검토 후 공개되거나
숨겨집니다. 비판이나 반대 의견은 그 자체로 숨기지 않습니다.
신고가 여러 건 쌓인 글도 검토 대기로 넘어갑니다.</p>

<h2>삭제·문의</h2>
<p>브라우저의 사이트 데이터를 지우면 익명 번호가 사라져 이전 기록과의 연결이 끊깁니다.
남긴 코멘트 삭제나 그 밖의 문의는
<a href="mailto:team@soonsal.com">team@soonsal.com</a> 으로 알려주세요.</p>

<p class="upd">최종 갱신 2026-08-11</p>
"""


def build():
    OUT.mkdir(exist_ok=True)
    html = (
        '<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>수집 안내 — 순살브리핑</title>\n"
        f'<link rel="canonical" href="{BASE}/privacy/"/>\n'
        '<meta name="description" content="순살브리핑 웹사이트가 받는 것과 받지 않는 것. '
        '쿠키를 쓰지 않습니다."/>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com"/>\n'
        '<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;800&display=swap" '
        'rel="stylesheet"/>\n'
        f"<style>{build_nav.HEADER_CSS}{CSS}</style></head><body>\n"
        f"{build_nav.header_html(None)}\n"
        f'<div class="wrap">{BODY}</div>\n'
        '<script src="/ss-config.js"></script><script src="/soonsal.js" defer></script>\n'
        "</body></html>\n"
    )
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print("🔒 privacy: /privacy/ 수집 안내")
    return 1


if __name__ == "__main__":
    build()
