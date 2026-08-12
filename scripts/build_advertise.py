#!/usr/bin/env python3
"""협업 문의 페이지 (/advertise/).

광고 하나가 아니라 협업 여섯 갈래를 늘어놓는다 — 채널 광고·라이선싱·런칭
패키지·아카이브 스폰서십·공동 리포트·채널 운영. 각 항목에 고를 수 있는
범위를 붙여 "얼마예요"가 아니라 "우린 이만큼 필요해요"로 대화가 시작되게 한다.

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
/* 협업 스코프 — 광고 하나가 아니라 여러 갈래임이 한눈에 보여야 한다.
   카드마다 번호·제목·설명·범위. 범위가 있어야 "얼마예요"가 아니라
   "우린 이만큼 필요해요"로 대화가 시작된다. */
.lead{color:#9a948a;font-size:.92rem;line-height:1.8;margin:0 0 20px}
.scopes{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.scope{background:#161616;border:1px solid #242424;border-radius:12px;padding:18px 18px 16px;
position:relative;transition:border-color .18s}
.scope:hover{border-color:#3a3a3a}
.scope .sn{font-size:.68rem;font-weight:800;letter-spacing:.1em;color:#F07040;margin-bottom:9px}
.scope h3{font-size:1.02rem;font-weight:800;letter-spacing:-.02em;color:#f2efe8;margin:0 0 7px}
.scope p{color:#8b8578;font-size:.86rem;line-height:1.7;margin:0 0 13px}
.scope .rng{font-size:.75rem;color:#c9c4ba;background:#1e1e1e;border:1px solid #2a2a2a;
border-radius:6px;padding:6px 10px;display:inline-block}
@media(max-width:560px){.scopes{grid-template-columns:1fr}}
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
.hl{color:#F07040;font-weight:700}
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
    subject = "%5B%ED%98%91%EC%97%85%20%EB%AC%B8%EC%9D%98%5D%20"  # [협업 문의]
    body = (
        "%EB%B8%8C%EB%9E%9C%EB%93%9C%2F%ED%9A%8C%EC%82%AC%3A%0A"        # 브랜드/회사:
        "%EB%8B%B4%EB%8B%B9%EC%9E%90%3A%0A"                            # 담당자:
        "%ED%9D%AC%EB%A7%9D%20%EC%8B%9C%EA%B8%B0%3A%0A"                # 희망 시기:
        "%EB%AA%A9%ED%91%9C%2F%ED%95%98%EA%B3%A0%20%EC%8B%B6%EC%9D%80%20%EC%9D%B4%EC%95%BC%EA%B8%B0%3A%0A"
    )
    mailto = f"mailto:{EMAIL}?subject={subject}&body={body}"

    desc = ("순살브리핑 협업 문의. 매일 아침 금융·경제·크립토를 읽는 독자에게 "
            "브랜드를 각인시키는 브랜딩 매체. 스폰서 스토리·로고 노출·AI 검색까지 함께 설계합니다.")

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>협업 문의 — 순살브리핑</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}"><meta name="robots" content="index, follow">
<meta property="og:type" content="website"><meta property="og:site_name" content="순살브리핑 Soonsal">
<meta property="og:title" content="협업 문의 — 순살브리핑">
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
스폰서 스토리도 같은 자리에 같은 문체로 <span class="hl">한 바닥</span>을 씁니다.
독자는 건너뛰지 않고 끝까지 읽게 됩니다.</p>

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
<li><span class="hl">비슷한 규모의 금융 뉴스레터 평균 오픈율 대비 4배</span>가 매일 아침 열립니다.
(구체적 수치는, 소개서에서 디테일하게 설명 드립니다)</li>
<li><span class="hl">매일 같은 시간, 약 10분.</span> 스크롤하며 스쳐 가는 매체가 아니라
정해진 시간에 자리 잡고 읽는 매체입니다.</li>
<li><span class="hl">읽는 사람이 다릅니다.</span> 금융·투자·테크 업계의 실무자와 의사결정권자가
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
<div class="two">
<div class="card"><ul>
<li><b>뉴스레터 스토리</b><br>
<a href="/partners/salesforce/NewsletterSample.html" style="color:#F07040">Salesforce 샘플 →</a></li>
</ul></div>
<div class="card"><ul>
<li><b>카드뉴스</b><br>
<a href="/cardnews/2026/0806.html" style="color:#F07040">AI에게 아이를 빼앗김 →</a><br>
<a href="/cardnews/2026/0804.html" style="color:#F07040">미국은 6배를 열었고 →</a></li>
</ul></div>
</div>
<p class="note" style="margin-top:10px">카드뉴스는 인스타그램 피드에 맞춘 정사각 포맷으로,
브랜드 콘텐츠도 동일한 제작 프로세스를 거칩니다.</p>
<p class="note">스폰서 스토리는 일반 스토리와 같은 자리, 같은 문체로 실립니다.
상단에 스폰서 표기를 분명히 하되, 읽는 흐름을 끊지 않습니다.</p>
</section>

<section>
<h2>이렇게 함께할 수 있습니다</h2>
<p class="lead">광고 한 가지가 아닙니다. 순살이 매일 만드는 것(콘텐츠·채널·독자)을
어느 쪽으로 쓰실지에 따라 형태가 달라집니다. <b style="color:#ccc">아래에서 고르시면
그에 맞춰 견적을 드립니다.</b></p>

<div class="scopes">
<div class="scope"><div class="sn">01</div>
<h3>순살 채널 광고</h3>
<p>순살브리핑·인스타그램에 브랜드 기획으로 발행합니다.
브랜디드 스토리 · 카드뉴스 · 릴스 · 배너 전 포맷.</p>
<div class="rng">포맷·횟수 선택 · 건별 또는 연 단위</div></div>

<div class="scope"><div class="sn">02</div>
<h3>콘텐츠 라이선싱</h3>
<p>순살 에디토리얼을 브랜드 채널 전용 편집본으로 제작·납품합니다.
채널은 이미 있고 채울 콘텐츠만 필요한 경우.</p>
<div class="rng">주 1~5회 중 선택 · 연 단위</div></div>

<div class="scope"><div class="sn">03</div>
<h3>런칭 패키지</h3>
<p>신상품·신규 상장 일정에 맞춰 한 세트로 묶습니다.
D-3 티저 → 당일 스토리 → D+7 카드뉴스.</p>
<div class="rng">건별 · 연 1~4건</div></div>

<div class="scope"><div class="sn">04</div>
<h3>아카이브 스폰서십</h3>
<p>「브랜드와 함께 만드는 ○○ 사전」. 검색으로 계속 유입되는 자산이라
시간이 지날수록 가치가 올라갑니다.</p>
<div class="rng">연 단위 · 항목 수 협의</div></div>

<div class="scope"><div class="sn">05</div>
<h3>공동 리포트</h3>
<p>순살 독자 설문을 <b style="color:#b8b2a8">집계 결과로만</b> 정리해 공동 리포트로
발간하고 언론에 배포합니다. 개별 응답이나 구독자 명단은 넘기지 않습니다.</p>
<div class="rng">연 1~2회 중 선택</div></div>

<div class="scope"><div class="sn">06</div>
<h3>채널 운영 대행</h3>
<p>콘텐츠 제작을 넘어 채널 기획·편성·운영까지.
위 항목이 자리를 잡은 뒤 확장하는 것을 권합니다.</p>
<div class="rng">월 단위 · 범위에 따라</div></div>
</div>

<p class="note">어떤 형태든 <span class="hl">원고는 순살이 씁니다.</span>
발행 후에는 주제별·기업별 페이지에 남아 계속 읽히고, AI 검색이 읽어가기 좋은
구조로 실립니다. 같은 업종에서는 소수 파트너와만 함께해
<span class="hl">브랜드 차별화</span>를 강조합니다 — 월 편성 슬롯이 조기에
마감될 수 있습니다.</p>
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
순살은 <span class="hl">어떤 경우에도 구독자 데이터를 제공하지 않습니다</span></li>
<li class="no">사실 확인이 어려운 표현이 꼭 들어가야 하는 콘텐츠</li>
</ul></div>
</section>

<section>
<h2>진행은 이렇게</h2>
<div class="card"><ul class="steps">
<li>문의 주시면 영업일 기준 2일 안에 회신드립니다</li>
<li><span class="hl">핏 리뷰</span> — 브랜드가 가장 잘 드러날 각도를 먼저 함께 찾습니다.
지금 타이밍이 아니라고 판단되면 솔직하게 말씀드립니다</li>
<li>소개서·제안서와 편성 일정 협의</li>
<li>원고는 순살이 쓰고, <span class="hl">초안은 발행 전에 확인</span>하실 수 있습니다</li>
<li>발행 후 성과 리포트 (콘텐츠가 충분히 소비된 뒤 정리해 드립니다)</li>
</ul></div>
</section>

<div class="cta">
<h2>가볍게 물어보셔도 됩니다</h2>
<p>예산이나 시기가 아직 정해지지 않았어도 괜찮습니다.<br>
브랜드와 하고 싶은 이야기만 알려주시면, 어떤 방식이 맞을지 함께 찾아드릴게요.</p>
<a class="btn" href="{mailto}">협업 문의 메일 보내기</a>
<a class="mail" href="mailto:{EMAIL}">{EMAIL}</a>
</div>

<p class="tagline">순살브리핑 · 글로벌 금융경제 살코기<br>
매일 아침, 순살만 발라낸 금융·경제 브리핑</p>

</div></body></html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print("📣 advertise: /advertise/ 협업 문의 페이지")
    return 1


if __name__ == "__main__":
    build()
