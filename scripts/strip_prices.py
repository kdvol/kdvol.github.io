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
    # "연 4,160만원 (주 1회 기준)" → "주 1회 기준"
    (r"연\s*[\d,]+\s*만원\s*\(([^)]*)\)", r"\1"),
    (r"연\s*[\d,]+\s*만원", "연간 계약"),
    (r"상장\s*1건\s*[\d,]+\s*만원", "상장 1건 단위"),
    (r"건당\s*[\d,]+\s*만원", "건당 단위"),
    (r"편당\s*[\d,]+\s*만원", "편당 단위"),
    (r"월\s*[\d,]+\s*만원\s*~?", "월 단위"),
    # "단가 : 테마·심층 콘텐츠 건당 800,000원 — 주 1회 기준" → 앞머리 제거
    (r"단가\s*[:：]\s*", ""),
    (r"[\d,]{4,}\s*원", ""),
    (r"₩\s?[\d,]{4,}", ""),
    (r"[\d,]+\s*만원", ""),
    (r"[\d,]+\s*백만원", ""),
]

NOTE = ("<p style=\"margin-top:26px;padding-top:20px;border-top:1px solid #2a2a2a;"
        "color:#888;font-size:14px;line-height:1.9;\">"
        "빈도·분량·기간이 정해지면 견적을 드립니다. "
        "<a href=\"mailto:team@soonsal.com\" style=\"color:#F38C61;\">team@soonsal.com</a></p>")


def strip(html: str) -> tuple:
    before = re.findall(r"₩?[\d,]{3,}\s*(?:만원|백만원|원)", html)
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
