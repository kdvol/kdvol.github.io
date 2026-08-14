#!/usr/bin/env python3
"""카드뉴스 상세 페이지를 가볍게 바꾸고 인스타로 보낸다.

지금 카드뉴스 폴더는 556MB다. 카드 이미지를 base64로 HTML에 통째로 박아 넣어서
한 페이지가 평균 2.6MB, 최대 27.6MB다. 폰에서 27MB짜리 페이지는 열리지 않는다.
데이터 요금도 그렇고, GitHub Pages 용량 한도도 그렇다.

카드뉴스의 목적지는 인스타여야 한다 — 거기서 저장·공유·팔로우가 일어난다.
사이트는 표지 한 장으로 궁금하게 만들고 넘겨주면 된다.

  표지  가장 큰 이미지 1장만 뽑아 1080px JPEG로 저장 (원본 대비 ~97% 감소)
  본문  나머지 카드는 페이지에서 뺀다. 인스타에 있다
  CTA   @soonsal.brief로 보내는 버튼

되돌리려면 git 히스토리에 원본이 그대로 있다.
"""

import base64
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "cardnews/2026"
IMGDIR = ROOT / "assets/cardnews"
IG = "https://www.instagram.com/soonsal.brief/"
MARK = "<!-- soonsal:cardnews-light -->"
MAX_W = 1080


def cover_of(html: str):
    """가장 큰 base64 이미지를 표지로 본다 — 표지가 늘 제일 크다."""
    best, best_n = None, 0
    for m in re.finditer(r'data:image/(\w+);base64,([A-Za-z0-9+/=]+)', html):
        n = len(m.group(2))
        if n > best_n:
            best, best_n = m.group(2), n
    return best


def save_cover(b64: str, out: Path) -> int:
    from PIL import Image
    im = Image.open(io.BytesIO(base64.b64decode(b64)))
    if im.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    if im.width > MAX_W:
        im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "JPEG", quality=82, optimize=True, progressive=True)
    return out.stat().st_size


def meta_of(html: str):
    t = re.search(r"<title>([^<]*)</title>", html)
    title = (t.group(1) if t else "").split("|")[0].strip()
    d = re.search(r"(\d{4})[.-](\d{2})[.-](\d{2})", html)
    date = f"{d.group(1)}.{d.group(2)}.{d.group(3)}" if d else ""
    return title, date


PAGE = """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | 순살 카드뉴스</title>
<meta name="description" content="{title} — 순살브리핑 카드뉴스. 전체는 인스타그램에서 보실 수 있어요."/>
<meta property="og:title" content="{title}"/>
<meta property="og:image" content="https://soonsal.com{img}"/>
<meta property="og:type" content="article"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;800&display=swap" rel="stylesheet"/>
<script src="/ss-config.js"></script>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#faf8f3;color:#2b2b2b;
font-family:'DM Sans',-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;
-webkit-font-smoothing:antialiased}}
.w{{max-width:520px;margin:0 auto;padding:24px 16px 60px}}
.bk{{display:inline-block;color:#8a8578;text-decoration:none;font-size:.82rem;margin-bottom:16px}}
.bk:hover{{color:#E55A00}}
.dt{{color:#a8a294;font-size:.78rem;margin:0 0 6px}}
h1{{font-size:1.32rem;font-weight:800;line-height:1.42;margin:0 0 18px;letter-spacing:-.02em}}
.cv{{width:100%;border-radius:12px;display:block;background:#eee}}
.cta{{margin-top:20px;background:#fff;border:1px solid #ece8de;border-radius:12px;padding:18px 17px}}
.cta p{{margin:0 0 13px;font-size:.9rem;line-height:1.65;color:#5f5a50}}
.cta b{{color:#2b2b2b}}
.go{{display:block;text-align:center;background:linear-gradient(93deg,#F07040,#E55A00);
color:#fff;text-decoration:none;font-weight:700;font-size:.95rem;border-radius:12px;padding:14px}}
.go:hover{{filter:brightness(1.05)}}
.sub{{display:block;text-align:center;color:#8a8578;text-decoration:none;font-size:.82rem;margin-top:12px}}
.sub:hover{{color:#E55A00}}
</style></head><body>
<div class="w">
<a class="bk" href="/cardnews/">← 카드뉴스 전체</a>
<p class="dt">{date}</p>
<h1>{title}</h1>
<img class="cv" src="{img}" alt="{title}" width="1080" loading="eager"/>
<div class="cta">
<p><b>나머지 장은 인스타에 있어요.</b><br>저장해두고 나중에 다시 보거나, 친구에게 넘기기 편해요.</p>
<a class="go" href="{ig}" target="_blank" rel="noopener">인스타그램에서 전체 보기 →</a>
<a class="sub" href="/">오늘 브리핑 읽으러 가기</a>
</div>
</div>
<script src="/soonsal.js" defer></script>
{mark}
</body></html>
"""


def convert(p: Path) -> tuple:
    html = p.read_text(encoding="utf-8")
    if MARK in html:
        return 0, 0
    before = len(html.encode())
    b64 = cover_of(html)
    if not b64:
        return 0, 0
    title, date = meta_of(html)
    img_rel = f"/assets/cardnews/{p.stem}.jpg"
    save_cover(b64, IMGDIR / f"{p.stem}.jpg")
    p.write_text(PAGE.format(title=title or "순살 카드뉴스", date=date,
                             img=img_rel, ig=IG, mark=MARK), encoding="utf-8")
    return before, p.stat().st_size


def main():
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    files = [SRC / f"{x}.html" for x in only] if only else sorted(SRC.glob("*.html"))
    tb = ta = n = 0
    for p in files:
        if not p.exists():
            continue
        b, a = convert(p)
        if b:
            n += 1
            tb += b
            ta += a
    img = sum(f.stat().st_size for f in IMGDIR.glob("*.jpg")) if IMGDIR.exists() else 0
    print(f"🎴 cardnews: {n}개 경량화 — HTML {tb/1048576:.0f}MB → {ta/1048576:.1f}MB"
          f" · 표지 이미지 {img/1048576:.0f}MB")


if __name__ == "__main__":
    main()
