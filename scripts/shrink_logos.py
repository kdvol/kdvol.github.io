#!/usr/bin/env python3
"""뉴스레터 인라인 로고를 표시 크기에 맞게 줄인다.

원본이 700x745인데 헤더는 36px, 푸터는 24px로 표시된다. base64로 박혀 있어
회차당 50KB, 전체 파일의 절반을 잡아먹었다. Gmail은 102KB가 넘으면 본문을
잘라내므로(0805 회차 116KB → 실제로 잘림) 여유가 3KB밖에 없었다.

레티나 2배 크기로 다시 인코딩한다. 외부 URL로 빼지 않는 이유는 이미지 차단
설정에서도 로고가 그대로 보여야 하기 때문.

사용: python3 scripts/shrink_logos.py newsletters/2026/0811.html
"""
import base64
import io
import re
import sys
from pathlib import Path

from PIL import Image

# 표시 높이(px) → 레티나 2배로 저장
DISPLAY_H = {"header": 36, "footer": 24}


def shrink(b64: str, target_h: int) -> tuple[str, int, int]:
    raw = base64.b64decode(b64)
    im = Image.open(io.BytesIO(raw))
    if im.mode not in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
    w = round(im.width * target_h / im.height)
    im = im.resize((w, target_h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode(), len(raw), len(buf.getvalue())


def main(path: str) -> int:
    p = Path(path)
    t = p.read_text(encoding="utf-8")
    hits = list(re.finditer(r"data:image/png;base64,([A-Za-z0-9+/=]+)", t))
    if not hits:
        print("인라인 PNG 없음")
        return 0

    before = len(t.encode())
    out, last, saved = [], 0, 0
    for i, m in enumerate(hits):
        # 첫 번째 = 헤더, 마지막 = 푸터 (그 사이 이미지는 헤더 규격으로)
        slot = "footer" if i == len(hits) - 1 else "header"
        new_b64, orig, new = shrink(m.group(1), DISPLAY_H[slot] * 2)
        out.append(t[last:m.start(1)] + new_b64)
        last = m.end(1)
        saved += orig - new
        print(f"  {slot}: {orig/1024:.1f}KB → {new/1024:.1f}KB")
    out.append(t[last:])
    t2 = "".join(out)
    p.write_text(t2, encoding="utf-8")

    after = len(t2.encode())
    print(f"파일: {before/1024:.1f}KB → {after/1024:.1f}KB "
          f"(Gmail 102KB 한도까지 여유 {(102*1024-after)/1024:.1f}KB)")
    return 1


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1]) else 1)
