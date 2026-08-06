#!/usr/bin/env python3
"""광고·파트너십 문의 페이지 (/advertise/).

포지셔닝: 프리미엄·선별적. "아무나 광고하지 않는다"를 명시하되 문의는 쉽게.
원칙(메모리 soonsal-ad-principles 준수):
  - 구체 수치(구독자수·오픈율·단가) 비공개 → 소개서로 안내
  - 카테고리 독점 약속 금지 → "동일 업종 소수 파트너" / "슬롯 조기 마감"만
  - 브랜딩 매체 프레임 (클릭 유도 매체 아님)
  - 구독자 데이터 제공 불가 명시
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://soonsal.com"
OUT = ROOT / "advertise"
EMAIL = "team@soonsal.com"

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#111;color:#eee;font-family:'DM Sans','Apple SD Gothic Neo','Malgun Gothic',sans-serif;
-webkit-text-size-adjust:100%;line-height:1.7}
.wrap{max-width:720px;margin:0 auto;padding:34px 18px 72px}
a{color:#eee;text-decoration:none}
h1{font-size:1.8rem;letter-spacing:-.03em;margin-bottom:12px;line-height:1.35}
.lede{color:#aaa;font-size:1rem;line-height:1.8;margin-bottom:8px}
.kicker{color:#F07040;font-size:.78rem;font-weight:700;letter-spacing:.12em;margin-bottom:10px}
h2{font-size:1.06rem;margin:0 0 12px;letter-spacing:-.01em}
section{margin:38px 0}
.card{background:#161616;border:1px solid #232323;border-radius:13px;padding:20px 22px}
.card+.card{margin-top:10px}
ul{list-style:none;margin:0}
li{position:relative;padding-left:17px;margin:9px 0;color:#bbb;font-size:.93rem;line-height:1.7}
li:before{content:"";position:absolute;left:0;top:.62em;width:5px;height:5px;border-radius:50%;background:#F07040}
li.no:before{background:#555}
li b{color:#eee;font-weight:600}
.two{display:grid;gap:10px}
@media(min-width:640px){.two{grid-template-columns:1fr 1fr}}
.steps{counter-reset:s}
.steps li{padding-left:34px;margin:14px 0}
.steps li:before{counter-increment:s;content:counter(s);width:22px;height:22px;border-radius:50%;
background:#F0704022;color:#F07040;font-size:.72rem;font-weight:700;display:flex;align-items:center;
justify-content:center;top:.2em;border:1px solid #F0704055}
.note{color:#777;font-size:.85rem;line-height:1.7;margin-top:14px}
.cta{background:linear-gradient(180deg,#1c1a17,#161514);border:1px solid #3a2b20;border-radius:14px;
padding:26px 22px;text-align:center;margin-top:36px}
.cta h2{font-size:1.15rem;margin-bottom:8px}
.cta p{color:#aaa;font-size:.92rem;margin-bottom:18px}
.btn{display:inline-block;background:#E55A00;color:#fff;font-weight:700;padding:14px 30px;
border-radius:9px;font-size:1rem;letter-spacing:-.01em}
.btn:hover{background:#cc4e00}
.mail{display:block;margin-top:12px;color:#F07040;font-size:.9rem}
.tagline{color:#666;font-size:.82rem;margin-top:28px;text-align:center;line-height:1.8}
"""


def build():
    import build_nav
    OUT.mkdir(exist_ok=True)
    canonical = f"{BASE}/advertise/"
    subject = "%5B%EA%B4%91%EA%B3%A0%20%EB%AC%B8%EC%9D%98%5D%20"      # [광고 문의]
    body = (
        "%EB%B8%8C%EB%9E%9C%EB%93%9C%2F%ED%9A%8C%EC%82%AC%3A%0A"        # 브랜드/회사:
        "%EB%8B%B4%EB%8B%B9%EC%9E%90%3A%0A"                            # 담당자:
        "%ED%9D%AC%EB%A7%9D%20%EC%8B%9C%EA%B8%B0%3A%0A"                # 희망 시기:
        "%EB%AA%A9%ED%91%9C%2F%ED%95%98%EA%B3%A0%20%EC%8B%B6%EC%9D%80%20%EC%9D%B4%EC%95%BC%EA%B8%B0%3A%0A"
    )
    mailto = f"mailto:{EMAIL}?subject={subject}&body={body}"

    desc = ("순살브리핑 광고·파트너십 문의. 매일 아침 금융·경제·크립토를 읽는 독자에게 "
            "브랜드를 각인시키는 브랜딩 매체. 스폰서 스토리·로고 노출·AI 검색까지 함께 설계합니다.")

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>광고·파트너십 문의 — 순살브리핑</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}"><meta name="robots" content="index, follow">
<meta property="og:type" content="website"><meta property="og:site_name" content="순살브리핑 Soonsal">
<meta property="og:title" content="광고·파트너십 문의 — 순살브리핑">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE}/og-cover-v2.png">
<meta property="og:locale" content="ko_KR">
<meta name="twitter:card" content="summary_large_image">
{build_nav.FONT_LINK}
<style>{CSS}{build_nav.HEADER_CSS}</style></head><body>
{build_nav.header_html(None)}
<div class="wrap">

<div class="kicker">PARTNERSHIP</div>
<h1>순살에서 브랜드는<br>광고가 아니라 이야기가 됩니다</h1>
<p class="lede">순살브리핑은 매일 아침, 글로벌 금융·경제·크립토를 순살만 발라 전합니다.
스폰서 스토리도 같은 자리에 같은 문체로 <b style="color:#ddd">한 바닥</b>을 씁니다 —
독자가 건너뛰지 않고 끝까지 읽도록.</p>

<section>
<h2>순살은 이런 매체입니다</h2>
<div class="card"><ul>
<li><b>브랜딩 매체입니다.</b> 클릭을 파는 곳이 아니라, 브랜드가 기억되는 곳입니다.
당장의 전환율보다 "이 브랜드 순살에서 봤다"는 인식을 만듭니다.</li>
<li><b>독자는 업계 사람들입니다.</b> 금융·투자·테크 업계의 실무자와 의사결정권자가
매일 아침 같은 시간에 읽습니다.</li>
<li><b>원고는 순살이 씁니다.</b> 브랜드가 하고 싶은 이야기를 순살 문체로 한 바닥 풀어드리고,
초안은 함께 다듬습니다. 배너를 붙이는 것보다 손이 더 가지만, 그만큼 읽힙니다.</li>
</ul></div>
</section>

<section>
<h2>숫자 대신, 이렇게 말씀드립니다</h2>
<div class="card"><ul>
<li><b>같은 규모의 금융 뉴스레터 평균 오픈율의 4배</b>가 매일 아침 열립니다.
(구체 수치는 소개서에서 기준·구간과 함께 투명하게 공개합니다)</li>
<li><b>매일 같은 시간, 약 10분.</b> 스크롤하며 스쳐 가는 매체가 아니라
정해진 시간에 자리 잡고 읽는 매체입니다.</li>
<li><b>읽는 사람이 다릅니다.</b> 금융·투자·테크 업계의 실무자와 의사결정권자가
주 독자층입니다.</li>
</ul></div>
</section>

<section>
<h2>최근 집행 사례</h2>
<div class="card"><ul>
<li><b>Salesforce — 스폰서 스토리</b><br>
금융권 망분리 규제 완화라는 시의성 있는 주제를 잡아, 브랜드가 말하고 싶은 메시지를
순살 톤의 한 바닥으로 풀었습니다.<br>
<a href="/newsletters/2026/0805.html#story-2" style="color:#F07040">실제 발행분 보기 →</a></li>
</ul></div>
<p class="note" style="margin-bottom:10px">실제 제작물로 톤과 형식을 확인하실 수 있습니다.</p>
<div class="card"><ul>
<li><b>뉴스레터 스토리 샘플</b><br>
<a href="/partners/salesforce/NewsletterSample.html" style="color:#F07040">Salesforce →</a></li>
</ul></div>
<p class="note">스폰서 스토리는 일반 스토리와 같은 자리, 같은 문체로 실립니다.
상단에 스폰서 표기를 분명히 하되, 읽는 흐름을 끊지 않습니다.</p>
</section>

<section>
<h2>이렇게 함께할 수 있습니다</h2>
<div class="two">
<div class="card"><ul>
<li><b>스토리 스폰서십</b><br>브리핑 안에 순살 톤으로 쓰는 한 바닥</li>
<li><b>시리즈 편성</b><br>여러 회차에 걸쳐 쌓는 브랜딩</li>
<li><b>브랜드 로고 노출</b><br>해당 회차 뉴스레터 안에 로고를 함께 배치</li>
</ul></div>
<div class="card"><ul>
<li><b>카드뉴스·인스타그램</b><br>뉴스레터와 소셜 채널 연계</li>
<li><b>AI 검색 노출</b><br>순살은 AI 검색엔진이 읽어가기 좋은 구조로 발행합니다.
스폰서 스토리도 같은 구조로 실려, 관련 주제를 물었을 때 함께 인용될 수 있습니다</li>
<li><b>웹 아카이브</b><br>메일은 하루지만 웹은 계속입니다. 발행 후에도 주제별·검색·
기업별 페이지에서 계속 읽힙니다</li>
</ul></div>
</div>
<p class="note">패키지 구성과 단가는 문의 주시면 <b style="color:#bbb">소개서</b>로 안내드립니다.
같은 업종에서는 소수 파트너와만 함께해 브랜드가 묻히지 않도록 하고 있어, 월 편성 슬롯이
조기에 마감될 수 있습니다.</p>
</section>

<section>
<h2>이것만 미리 말씀드립니다</h2>
<div class="card">
<p style="color:#aaa;font-size:.9rem;line-height:1.75;margin-bottom:12px">
독자의 신뢰가 곧 광고 효과라고 믿습니다. 그래서 아래 경우에는 아쉽지만
함께하기 어렵습니다 — 브랜드를 가리려는 게 아니라, 실었을 때 서로에게
결과가 좋지 않기 때문입니다.</p>
<ul>
<li class="no">원금·수익 보장을 내세운 투자 권유, 리딩방·유사수신성 서비스</li>
<li class="no">독자 데이터(이메일·개인정보) 제공이 필요한 형태 —
순살은 <b>어떤 경우에도 구독자 데이터를 제공하지 않습니다</b></li>
<li class="no">사실 확인이 어려운 표현이 꼭 들어가야 하는 콘텐츠</li>
</ul></div>
</section>

<section>
<h2>진행은 이렇게</h2>
<div class="card"><ul class="steps">
<li>문의 주시면 영업일 기준 2일 안에 회신드립니다</li>
<li><b>핏 리뷰</b> — 브랜드가 가장 잘 드러날 각도를 먼저 함께 찾습니다.
지금 타이밍이 아니라고 판단되면 솔직하게 말씀드립니다</li>
<li>소개서·제안서와 편성 일정 협의</li>
<li>원고는 순살이 쓰고, <b>초안은 발행 전에 확인</b>하실 수 있습니다</li>
<li>발행 후 성과 리포트 (콘텐츠가 충분히 소비된 뒤 정리해 드립니다)</li>
</ul></div>
</section>

<div class="cta">
<h2>가볍게 물어보셔도 됩니다</h2>
<p>예산이나 시기가 아직 정해지지 않았어도 괜찮습니다.<br>
브랜드와 하고 싶은 이야기만 알려주시면, 어떤 방식이 맞을지 함께 찾아드릴게요.</p>
<a class="btn" href="{mailto}">광고 문의 메일 보내기</a>
<a class="mail" href="mailto:{EMAIL}">{EMAIL}</a>
</div>

<p class="tagline">순살브리핑 · 글로벌 금융경제 살코기<br>
매일 아침, 순살만 발라낸 금융·경제 브리핑</p>

</div></body></html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print("📣 advertise: /advertise/ 광고·파트너십 문의 페이지")
    return 1


if __name__ == "__main__":
    build()
