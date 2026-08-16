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
.box{border:1px solid #e8e8e0;background:#fafaf7;border-radius:12px;padding:16px 18px;margin:12px 0}
.uses{margin:10px 0 0;padding-left:22px}
.uses li{margin:5px 0;line-height:1.75}
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
<li>웹사이트에서 이름·이메일·전화번호를 묻지 않습니다. 계정도 로그인도 없습니다</li>
<li>운영자와 개발·검증용 브라우저의 접속은 집계에서 뺍니다. 방문자 수는 읽는 분들만
센 숫자입니다</li>
<li>광고·분석 목적으로 제3자에게 넘기는 데이터가 없습니다</li>
</ul>
</div>

<h2>받는 것</h2>
<div class="box">
<ul>
<li><b>익명 번호</b> — 브라우저에 무작위로 만든 번호 하나를 저장해, 같은 사람이 다시
왔는지만 구분합니다. 이 번호만으로는 누구인지 알 수 없습니다</li>
<li><b>뉴스레터에서 넘어오셨다면 구독자 표시</b> — 메일 안의 링크에는 회차 번호와
<b>되돌릴 수 없게 처리한 구독자 표시</b>가 붙어 있습니다. 이걸로 "이 회차를 읽은
구독자가 몇 명인지", "지난주에도 읽으셨는지"를 셉니다.
<br>표시값은 구독자 번호를 <b>일방향 함수로 바꾼 값</b>이라 그 자체로는 이메일을
되돌릴 수 없고, 되돌리는 열쇠는 발송 시스템에만 있고 <b>분석 저장소에는 없습니다</b>.
다만 저희가 그 열쇠를 갖고 있으므로 <b>익명이 아니라 가명 처리된 정보</b>로 봅니다.
<br>이 표시를 붙이지 않으려면 아래 <b>연결 끄기</b>를 쓰시면 됩니다</li>
<li><b>어떤 페이지를 봤는지</b>와 <b>어디서 들어왔는지</b>(검색·텔레그램·인스타그램 등)</li>
<li><b>어떤 글에서 어떤 글로 넘어갔는지</b> — 경로 쌍의 횟수만 셉니다.
"이 글 다음에 저 글을 본 사람이 7명"까지가 전부이고, <b>누가 그랬는지는 남기지 않습니다</b></li>
<li><b>버튼 반응</b> — 👍 좋았음 / 🤔 글쎄 / 🔥 중요함, 공유·코멘트 클릭</li>
<li><b>코멘트 좋아요</b> — 어떤 코멘트에 익명 번호가 눌렀는지(취소하면 지워집니다)</li>
<li><b>코멘트를 남기면</b> 그 닉네임과 본문. 닉네임을 비워두면 익명 번호에서
자동으로 하나 지어 드립니다</li>
<li><b>프로필을 채우면</b>(선택) 업종. 직장은 <b>'함께 표시'를 켠 경우에만</b> 전송되며,
꺼두면 이 브라우저 밖으로 나가지 않습니다. 둘 다 본인이 적은 내용이고 확인된
소속이 아닙니다 — 코멘트 옆에 그대로 공개됩니다</li>
</ul>
</div>

<h2>왜 구독자 표시를 붙이나요</h2>
<div class="box">
<p>순살브리핑 웹은 대부분 <b>메일 안의 링크</b>로 들어오십니다. 그런데 메일 앱 안에서
열면 브라우저 저장소가 매번 비워져, <b>같은 분이 매일 새 사람으로 잡힙니다</b>.
그래서 "몇 명이 읽는가"를 저희도 못 세고 있었습니다.</p>
<p><b>쓰는 곳은 아래 일곱 가지입니다.</b> 여기 없는 용도로는 쓰지 않습니다.</p>
<ol class="uses">
<li>회차별로 몇 명이 읽었는지, 다시 오셨는지 세는 것</li>
<li>어떤 글·주제가 읽히는지 보고 다음 뉴스레터에 반영하는 것</li>
<li>구독자군별 열람 경향 — 가입 시점, 본인이 고르신 관심분야 같은 <b>집단 단위</b>
분석 (개인을 짚지 않습니다)</li>
<li>안 읽으신 지 오래된 분께 다시 안내드릴지 판단하는 것</li>
<li>서비스 전체의 <b>집계 통계</b>를 만드는 것 — 개인을 알아볼 수 있는 정보는
포함하지 않습니다</li>
<li>오류나 부정 이용을 확인하는 것</li>
<li>위 분석에 따라 뉴스레터 구성이나 보내는 시각을 조정하는 것</li>
</ol>
<p><b>하지 않는 것</b> — 제3자에게 개인정보를 제공하거나 팔지 않습니다.
외부 광고 플랫폼으로 식별자를 보내지 않습니다.</p>
</div>

<h2>민감한 정보는 다루지 않습니다</h2>
<div class="box no">
<p>순살은 <b>경제 매체</b>입니다. 제약·바이오 기사를 쓰더라도 산업과 투자의
관점이고, <b>약을 권하거나 건강 정보를 안내하지 않습니다.</b> 그래서 어떤 글을
읽으셨다는 사실에서 건강 상태 같은 민감한 정보를 알 수 있는 구조가 아닙니다.</p>
<p>다만 앞으로 환자 관점의 글처럼 <b>읽은 사실만으로 개인의 상태가 드러날 수 있는
내용</b>을 싣게 되면, 그 페이지는 구독자 표시와 함께 기록하지 않고 날짜별 합계로만
세겠습니다. 그럴 수 있는 장치를 미리 만들어 두었습니다.</p>
</div>

<h2>어디에 저장되나요 (국외 이전)</h2>
<div class="box">
<p>저장소는 <b>Cloudflare</b>(미국 소재 회사)의 D1 데이터베이스이며, 데이터가
<b>대한민국 밖 서버에 저장될 수 있습니다.</b></p>
<ul>
<li><b>이전받는 곳</b> — Cloudflare, Inc. (미국)</li>
<li><b>이전 항목</b> — 이 페이지에 적은 방문·반응·코멘트·구독자 표시</li>
<li><b>이전 목적</b> — 이 사이트를 돌리고 위 분석을 하기 위한 저장·처리</li>
<li><b>보유 기간</b> — 아래 「어떻게 보관하나요」와 같습니다</li>
</ul>
<p>원하지 않으시면 아래 <b>연결 끄기</b>를 쓰시면 됩니다. 구독은 유지됩니다.</p>
</div>

<h2>구독자의 권리</h2>
<div class="box">
<p>언제든 아래를 요구하실 수 있습니다. <b>team@soonsal.com</b> 으로 알려주시면
지체 없이 처리합니다.</p>
<ul>
<li><b>열람</b> — 어떤 기록이 남아 있는지 확인</li>
<li><b>정정·삭제</b> — 틀린 것을 고치거나 지우기</li>
<li><b>처리정지</b> — 이후 수집을 멈추기 (아래 연결 끄기와 같습니다)</li>
</ul>
<p>요구하셨다는 이유로 불이익을 드리지 않습니다.</p>
</div>

<h2>어떻게 보관하나요</h2>
<p><b>웹에서 직접 오신 방문과 버튼 반응</b>은 개별 기록을 쌓아두지 않고
<b>날짜별 합계</b>만 남깁니다. "8월 11일에 몇 명이 왔고 몇 번 눌렸다" 수준이지,
"누가 무엇을 봤다"는 기록은 만들지 않습니다.</p>
<p><b>뉴스레터 링크로 오신 경우는 다릅니다.</b> 구독자 표시와 함께 <b>어느 회차의
어떤 글을 언제 열었는지</b>가 낱개로 남습니다. 사람 수를 세려면 그 줄이 필요합니다.
<b>90일이 지나면 낱개 줄을 지우고</b> 날짜별 합계만 남깁니다.</p>
<p><b>코멘트는 성격이 다릅니다.</b> 공개해서 함께 읽는 글이라 글 단위로 남습니다 —
닉네임·본문·작성 시각·익명 번호, 답글이라면 그 대상, 그리고 적으셨다면 업종·직장.
지우기 전까지 보관됩니다.</p>
<p>코멘트 좋아요는 "어떤 코멘트에 어떤 익명 번호가 눌렀는지"를 한 줄로 남깁니다.
같은 사람이 두 번 누르는 걸 막으려면 그 한 줄이 필요합니다. 다시 누르면 지워집니다.</p>
<p>저장 위치는 Cloudflare D1이며, 이 사이트 운영 외의 용도로 쓰지 않습니다.</p>

<h2>집계에서 빼는 방법</h2>
<p><a href="/stats/">/stats/</a> 맨 아래 버튼을 누르면 이 브라우저는 방문 집계에서
영구히 빠지고, 그동안 쌓인 이 브라우저의 방문자 기록도 지워집니다. 다만 페이지뷰
합계는 경로별로만 세기 때문에 개인 몫을 되돌릴 수 없습니다 — 누가 무엇을 봤는지
남기지 않는 대신 치르는 비용입니다.</p>

<h2>코멘트 운영</h2>
<p>남긴 글의 책임은 작성자에게 있습니다. 아래에 해당하면 사전 통보 없이 숨겨집니다.</p>
<ul>
<li>투자 권유, 리딩방·오픈채팅 유인, 수익 보장 문구, 연락처 유도</li>
<li>맥락 없는 광고, 특정인 비방·모욕, 개인정보 노출, 도배</li>
</ul>
<p>링크나 위 문구가 포함된 글은 자동으로 검토 대기로 넘어가며, 검토 후 공개되거나
숨겨집니다. 비판이나 반대 의견은 그 자체로 숨기지 않습니다.
신고가 여러 건 쌓인 글도 검토 대기로 넘어갑니다.</p>

<h2>연결 끄기</h2>
<div class="box">
<p>구독자 표시를 붙이지 않기를 원하시면 <b>team@soonsal.com</b> 으로 알려주세요.
그 뒤로 보내는 메일의 링크에는 표시가 붙지 않고, 이미 쌓인 그 표시의 기록도
지워 드립니다. <b>뉴스레터 구독은 그대로 유지됩니다.</b></p>
<p>브라우저 쪽 집계만 끄고 싶으시면 <a href="/stats/">/stats/</a> 맨 아래 버튼을
쓰시면 됩니다.</p>
</div>

<h2>보관 기간</h2>
<div class="box">
<p>구독자 표시가 붙은 <b>낱개 열람 기록은 90일까지</b>만 두고, 그 뒤에는 날짜별
합계만 남기고 지웁니다. 합계에는 개인을 가리키는 값이 없습니다.</p>
<p>구독을 해지하시면 그 표시의 기록도 함께 지웁니다.</p>
</div>

<h2>삭제·문의</h2>
<p>브라우저의 사이트 데이터를 지우면 익명 번호가 사라져 이전 기록과의 연결이 끊깁니다.
남긴 코멘트 삭제나 그 밖의 문의는
<a href="mailto:team@soonsal.com">team@soonsal.com</a> 으로 알려주세요.</p>

<p class="upd">최종 갱신 2026-08-16 — 구독자 표시, 이용 목적 7가지, 민감 주제 제외, 국외 이전, 구독자의 권리를 더했습니다</p>
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
