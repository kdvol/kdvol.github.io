#!/usr/bin/env python3
"""제안서에서 단가만 걷어낸 판을 만든다.

첫 미팅에 단가표를 들고 가면 대화가 "얼마예요"로 시작해 거기서 끝난다.
무엇을 할 수 있는지 먼저 합의하고, 스코프가 정해지면 그때 견적을 낸다.

단가 있는 원본은 그대로 둔다 — 두 판이 각자 살아 있어야 한다.

지우는 것은 금액뿐이다. 빈도·분량·구성은 남긴다. 그게 스코프 대화의 재료다.
  "연 4,160만원 (주 1회 기준)"  → "주 1회 기준"
  "상장 1건 1,900만원"          → "상장 1건 단위"
  "19,000,000원"                → (지움)

사용:
  python3 scripts/strip_prices.py <입력.html> <출력경로>
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 금액 표현. 앞뒤 맥락을 살려 지운다 — 숫자만 지우면 "연  (주 1회 기준)"이 남는다.
RULES = [
    # 단가를 지우는 게 목적이 아니다. 스코프를 고르게 만드는 게 목적이라
    # 고정값을 지우고 그 자리에 '선택 가능한 범위'를 넣는다.
    #   "연 4,160만원 (주 1회 기준)"  → "주 1~5회 중 선택"
    #   "상장 1건 1,900만원"          → "상장 건별 · 연 1~4건"
    # 범위는 순살이 실제로 감당할 수 있는 폭이어야 한다. 늘려 적으면
    # 미팅에서 못 한다고 물러야 하고, 그게 더 나쁘다.
    (r"연\s*[\d,]+\s*만원\s*\(\s*주\s*1회\s*기준\s*\)", "주 1~5회 중 선택 · 연 단위"),
    (r"상장\s*1건\s*[\d,]+\s*만원", "상장 건별 · 연 1~4건"),
    (r"연\s*[\d,]+\s*만원", "연 단위 · 항목 수 협의"),
    (r"건당\s*[\d,]+\s*만원", "연 1~2회 중 선택"),
    (r"편당\s*[\d,]+\s*만원", "월 1~4편 중 선택"),
    (r"월\s*[\d,]+\s*만원\s*~?", "월 단위 · 채널·편성 범위에 따라"),
    # 상품 표의 '단가 :' 열과 패키지 3종 금액
    (r"단가\s*[:：]\s*", "구성 : "),
    (r"건당\s*[\d,]{4,}\s*원\s*—\s*주\s*1회\s*기준", "테마·심층 콘텐츠 · 주 1~5회 중 선택"),
    (r"[\d,]{4,}\s*원", ""),
    (r"₩\s?[\d,]{4,}", ""),
    (r"[\d,]+\s*만원", ""),
    (r"[\d,]+\s*백만원", ""),
    # 태그가 끼어 위 복합 규칙이 못 잡은 잔여 — 금액만 빠지고 "건당 — 주 1회 기준"이 남는다
    (r"건당\s*(?:</?[a-z][^>]*>\s*)*—\s*주\s*1회\s*기준", "주 1~5회 중 선택"),
    (r"건당\s*—\s*주\s*1회\s*기준", "주 1~5회 중 선택"),
    # 단가 없는 판에 '단가는 정가 기준' 문구가 남으면 앞뒤가 안 맞는다
]


def _tolerant(sentence: str) -> str:
    """문장을 태그가 끼어도 잡히는 정규식으로 바꾼다.

    원본은 <strong>정가 기준</strong> 처럼 문장 중간에 태그가 들어 있다.
    평문 기준으로 규칙을 쓰면 하나도 안 잡힌다. 토큰 사이에 태그·공백을
    허용해 두면 마크업이 바뀌어도 계속 잡힌다.
    """
    toks = [re.escape(x) for x in sentence.split()]
    return r"(?:<[^>]+>|\s)*".join(toks)


# 문장 단위 치환 — 지우지 않고 뜻을 바꾼다. 단가 없는 판에 '정가·단가'가
# 남으면 앞뒤가 안 맞고, 문장을 통째로 지우면 조건이 사라진다.
SENTENCES = [
    ("※ 모든 금액은 정가 기준 입니다. 예산에 맞추실 때는 단가를 낮추는 대신 물량과 범위를 조정 합니다",
     "※ 위 범위 안에서 물량·주기를 고르시면 그에 맞춰 견적을 드립니다"),
    ("단가는 정가 기준이며, 예산에 맞추실 때는 구성 단계를 조정 합니다",
     "예산 범위를 알려주시면 구성 단계를 맞춰 드립니다"),
    ("모든 콘텐츠는 준법 검수 대응을 포함한 단가입니다",
     "모든 콘텐츠는 준법 검수 대응을 포함합니다"),
    ("상장 1건당 구성 (정가)", "상장 1건당 구성"),
]

NOTE = ("<p style=\"margin-top:26px;padding-top:20px;border-top:1px solid #2a2a2a;"
        "color:#888;font-size:14px;line-height:1.9;\">"
        "빈도·분량·기간이 정해지면 견적을 드립니다. "
        "<a href=\"mailto:team@soonsal.com\" style=\"color:#F38C61;\">team@soonsal.com</a></p>")


def strip(html: str) -> tuple:
    before = re.findall(r"₩?[\d,]{3,}\s*(?:만원|백만원|원)", html)
    # 문장부터 — 금액을 지운 뒤엔 문장이 깨져 못 잡는다
    for sent, rep in SENTENCES:
        html = re.sub(_tolerant(sent), rep, html)
    for pat, rep in RULES:
        html = re.sub(pat, rep, html)
    # 금액을 지우고 남은 찌꺼기 정리
    html = re.sub(r"\(\s*\)", "", html)
    html = re.sub(r"—\s*(?=<)", "", html)
    html = re.sub(r"[ \t]{2,}", " ", html)
    after = re.findall(r"₩?[\d,]{3,}\s*(?:만원|백만원|원)", html)
    return html, before, after


def main():
    if len(sys.argv) < 3:
        print("사용: strip_prices.py <입력.html> <출력경로>")
        return 0
    src, dst = Path(sys.argv[1]), ROOT / sys.argv[2]
    t = src.read_text(encoding="utf-8")
    out, before, after = strip(t)

    # 마지막 섹션 끝에 안내 한 줄
    i = out.rfind("</div>")
    if i > 0:
        out = out[:i] + NOTE + out[i:]

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(out, encoding="utf-8")
    try:
        shown = dst.relative_to(ROOT)
    except ValueError:
        shown = dst
    print(f"  📄 {shown} — 지운 금액 {len(before)}개")
    if after:
        print(f"  ⚠️ 남은 금액 표현: {after[:5]}")
    return 1


if __name__ == "__main__":
    main()
