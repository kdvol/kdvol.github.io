#!/usr/bin/env python3
"""단가 없는 제안서 변형본을 만든다.

첫 미팅에 단가표를 들고 가면 대화가 "얼마예요"로 시작하고 거기서 끝난다.
스코프를 먼저 합의하고 견적을 내려면, 무엇을 할 수 있는지만 보여주는 판이 필요하다.

원본(partners/index.html)에서 금액이 든 두 섹션만 들어낸다:
  03  광고 상품 구성 — 단가(회당) 열
  04  연간 리테이너 패키지 — 연 단가

들어낸 자리에는 "스코프를 정한 뒤 견적" 한 장을 넣는다. 나머지(채널 소개·독자
구성·실제 발행 사례)는 그대로 둔다 — 그게 미팅에서 실제로 필요한 부분이다.

원본은 건드리지 않는다. 단가 있는 판은 그대로 살아 있어야 한다.

사용:
  python3 scripts/build_partner_variant.py KIWOOM "키움투자자산운용"
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "partners/index.html"

# 걷어낼 섹션의 제목 표식. 원본 h2가 "03광고 상품 구성" 형태로 붙어 있다.
DROP_HEADINGS = ["광고 상품 구성", "연간 리테이너 패키지"]

SCOPE_PAGE = """
<div class="page">
  <div class="section-num">03</div>
  <h2>협업 범위</h2>
  <p style="color:#555;line-height:1.9;margin:18px 0 26px;font-size:15px;">
    순살은 광고 지면을 파는 매체가 아니라, 에디토리얼 팀이 직접 기획·제작합니다.
    그래서 형태와 분량이 정해지면 그에 맞춰 견적을 드립니다.
  </p>
  <ul style="list-style:none;padding:0;margin:0;line-height:2.1;color:#333;font-size:15px;">
    <li>· <b>뉴스레터 브랜디드 스토리</b> — 에디토리얼과 같은 톤의 네이티브 콘텐츠</li>
    <li>· <b>상단 배너</b> — 로고 + 한 줄 카피, 스토리와 같은 회차</li>
    <li>· <b>인스타그램 카드뉴스</b> — 순살 포맷으로 제작·발행</li>
    <li>· <b>인앱 콘텐츠 공급</b> — 파트너 앱에 정기 공급 (BC카드 페이북 사례)</li>
    <li>· <b>딥다이브 리포트</b> — 주제 하나를 길게, 단독 발행</li>
    <li>· <b>연간 리테이너</b> — 위 조합을 연 단위로 묶어 운영</li>
  </ul>
  <p style="color:#777;line-height:1.9;margin-top:30px;font-size:14px;
            border-top:1px solid #eee;padding-top:22px;">
    빈도·분량·기간이 정해지면 견적을 드립니다.<br>
    문의 <a href="mailto:team@soonsal.com" style="color:#E55A00;">team@soonsal.com</a>
  </p>
</div>
"""


def drop_sections(html: str) -> tuple:
    """h2 제목으로 페이지 블록을 찾아 통째로 들어낸다.

    원본은 <div class="page">…<h2>…</h2>…</div> 구조다. h2 위치에서 바깥
    page 블록의 시작·끝을 div 깊이로 찾는다 — 정규식으로 닫는 태그를 잡으면
    중첩 때문에 어긋난다.
    """
    dropped = []
    for label in DROP_HEADINGS:
        while True:
            # h2 안에 <span class="num">03</span> 같은 태그가 끼어 있다
            m = re.search(rf'<h2[^>]*>(?:(?!</h2>).)*?{re.escape(label)}', html, re.S)
            if not m:
                break
            start = html.rfind('<div class="page', 0, m.start())
            if start < 0:
                break
            depth, pos = 0, start
            tag = re.compile(r"</?div\b", re.I)
            end = None
            while True:
                x = tag.search(html, pos)
                if not x:
                    break
                depth += -1 if x.group(0).startswith("</") else 1
                pos = x.end()
                if depth == 0:
                    end = pos
                    break
            if end is None:
                break
            dropped.append(label)
            html = html[:start] + html[end:]
    return html, dropped


def build(slug: str, name: str):
    if not SRC.exists():
        print(f"  ⚠️ 원본 없음: {SRC}")
        return 0
    t = SRC.read_text(encoding="utf-8")
    if "soonsal:locked" in t:
        print("  ⚠️ 원본이 잠겨 있다. 백업본에서 만들어야 한다")
        return 0

    t, dropped = drop_sections(t)
    if not dropped:
        print("  ⚠️ 걷어낼 섹션을 못 찾음 — 원본 구조가 바뀌었는지 확인")
        return 0

    # 섹션을 들어내도 노출 예시 안에 '단가: ₩1,500,000 /회'가 남는다.
    # 금액만 지우고 빈도는 살린다 — 빈도는 스코프 대화에 필요한 정보다.
    t = re.sub(r"단가\s*:\s*₩[\d,]+\s*/\s*회\s*(·\s*)?", "", t)
    t = re.sub(r"₩\s?[\d,]{4,}", "", t)
    t = re.sub(r"[\d,]+\s*백만원\s*/\s*연간", "", t)

    left = re.findall(r"₩[\d,]+|[\d,]{3,}\s*(?:만원|백만원)", t)
    if left:
        print(f"  ⚠️ 금액이 남았다: {left[:5]} — 확인 필요")

    # 들어낸 자리에 스코프 장을 넣는다(04 다음 섹션 앞)
    m = re.search(r'<div class="page">\s*<div class="section-num">0[45]', t)
    t = (t[:m.start()] + SCOPE_PAGE + t[m.start():]) if m else t + SCOPE_PAGE

    t = t.replace("순살 파트너십 제안서", f"순살 × {name} 제안서", 1)
    t = re.sub(r"<title>[^<]*</title>",
               f"<title>순살 × {name} — 파트너십 제안서</title>", t, count=1)

    out = ROOT / "partners" / slug
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(t, encoding="utf-8")
    print(f"  📄 partners/{slug}/ — 걷어낸 섹션: {', '.join(dropped)} · {len(t):,} bytes")
    return 1


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용: build_partner_variant.py <SLUG> <표시이름>")
        raise SystemExit(1)
    build(sys.argv[1], sys.argv[2])
