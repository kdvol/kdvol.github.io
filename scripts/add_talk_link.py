#!/usr/bin/env python3
"""뉴스레터 푸터에 /talk/ 링크를 박아 넣는다.

soonsal.js가 넣는 링크는 웹사이트에서만 보인다. 이메일 클라이언트는 자바스크립트를
실행하지 않으므로, 정작 구독자 대부분이 보는 화면(메일)에는 한마디로 가는 길이
없었다. 발행되는 HTML 자체에 넣어야 메일에서도 살아남는다.

  - 절대 주소를 쓴다. 메일에서는 /talk/ 같은 상대 경로가 열리지 않는다
  - footer-links 줄에 붙인다 — 이미 soonsal.com·구독하기가 있는 자리다
  - 이미 있으면 건너뛴다(매 빌드마다 중복으로 쌓이면 안 된다)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = '<a href="https://soonsal.com/talk/">💬 순살톡</a>'
ANCHOR = '<a href="https://subscribe.soonsal.com/subscribe">구독하기</a>'


def patch(p: Path) -> bool:
    t = p.read_text(encoding="utf-8")
    if "soonsal.com/talk/" in t:
        return False
    if ANCHOR not in t:
        return False
    p.write_text(t.replace(ANCHOR, ANCHOR + " · " + LINK, 1), encoding="utf-8")
    return True


def main(dirs=None):
    targets = dirs or ["newsletters", "english", "morning"]
    n = 0
    for d in targets:
        base = ROOT / d
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.html")):
            n += patch(p)
    print(f"💬 talk 링크: {n}개 뉴스레터 푸터에 추가")
    return n


if __name__ == "__main__":
    main(sys.argv[1:] or None)
