#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_private_rules.py — **비공개 규칙이 공개 레포로 새는 걸 막는다.**

> KD 2026-08-20: *"이 규칙들은 전부 비공개에 회사 비밀자산이라, 혹시라도
> GitHub 에서 public하게 유출되면 절대 안 되는 거 명심해."*

이 레포(`kdvol.github.io`)는 **GitHub Pages 라 공개**다. 반면 규칙 원본은
`~/soonsal-build`(비공개)에 산다. 둘 사이에 사람이 파일을 옮기다 실수하면
되돌릴 수 없다 — 공개 레포는 푸시 순간 인덱싱된다.

**막는 것** — 규칙 원본 파일명, 규칙 원장·컴파일 산출물, 판례 ID 뭉치.
**안 막는 것** — 발행되는 뉴스레터 본문. 그건 원래 공개다.

    python3 scripts/check_private_rules.py --staged
"""
import re, subprocess, sys

# 파일명 자체가 금지 — 규칙 원본·원장·컴파일 산출물
BAD_PATH = re.compile(
    r"(tone_casebook|soonsal_tone_guide|editorial_memory|common_review"
    r"|briefing_rules|rules?/compiled/|rules?/_incoming/|rules?/registry/"
    r"|rule_cardnews|rule_zzal|rule_briefing_crypto|audit_practice)", re.I)

# 내용 지문 — 판례 ID 가 여러 개 몰려 있으면 규칙 문서다
CASE_ID = re.compile(r"(?<![A-Za-z0-9])(?:C\d{1,2}|X\d{2}|P-\d{1,2}|U-\d{1,2}|Y-\d{1,2})(?![A-Za-z0-9])")
CASE_MIN = 8          # 한 파일에 8개 이상 몰리면 규칙 문서로 본다

# 발행물은 예외 — 뉴스레터·카드뉴스 본문은 원래 공개다
EXEMPT = re.compile(r"(^newsletters/|^chart/|^cardnews/|^_publish/|^s/|^2026/|\.html$)")


def staged() -> list[str]:
    r = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                       capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l.strip()]


def main() -> int:
    hits = []
    for p in staged():
        if EXEMPT.search(p):
            continue
        if BAD_PATH.search(p):
            hits.append((p, "파일명이 비공개 규칙을 가리킨다"))
            continue
        try:
            body = subprocess.run(["git", "show", f":{p}"], capture_output=True,
                                  text=True).stdout
        except Exception:
            continue
        n = len(set(CASE_ID.findall(body)))
        if n >= CASE_MIN:
            hits.append((p, f"판례 ID {n}종이 몰려 있다 — 규칙 문서로 보인다"))

    if hits:
        print("⛔ 커밋 중단 — 이 레포는 **공개**다 (GitHub Pages)\n")
        for p, why in hits:
            print(f"   {p}\n      └ {why}")
        print("\n   규칙 원본은 ~/soonsal-build (비공개) 에만 둔다.")
        print("   정말 공개해야 하면: git commit --no-verify (되돌릴 수 없음)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
