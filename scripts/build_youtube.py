#!/usr/bin/env python3
"""/youtube/ — 최근 숏츠가 매일 갱신되는 화면.

지금 유튜브 페이지는 hero 하나에 영상 링크가 0개다. 숏츠를 다시 발행하는데
사이트는 그걸 모른다. 죽어 있는 화면이다.

채널 RSS(공개, 키 불필요)를 빌드할 때 읽어 최근 15개를 심는다. 매일 도는
워크플로가 페이지를 다시 만들므로 발행하면 알아서 올라온다.

  https://www.youtube.com/feeds/videos.xml?channel_id=...

썸네일은 i.ytimg.com을 그대로 건다 — 리포에 이미지를 쌓지 않는다.
"""

import html as H
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "youtube"
CHANNEL_ID = "UCAlHlhp6Ug62sP8C6akctmQ"
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
CACHE = ROOT / "content/youtube_feed.json"


def fetch():
    """RSS를 읽는다. 실패하면 지난번 캐시로 페이지를 만든다 —
    유튜브가 잠깐 안 될 때 화면이 통째로 비어버리면 안 된다."""
    try:
        req = urllib.request.Request(FEED, headers={"user-agent": "soonsal-site/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            xml = r.read().decode("utf-8", "replace")
    except Exception as e:
        print(f"  ⚠️ RSS 실패({type(e).__name__}) — 캐시 사용")
        return json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else []

    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.S)
    out = []
    for e in entries:
        def g(tag, attr=None):
            if attr:
                m = re.search(rf'<{tag}[^>]*{attr}="([^"]*)"', e)
            else:
                m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", e, re.S)
            return H.unescape(m.group(1)).strip() if m else ""

        vid = g("yt:videoId")
        if not vid:
            continue
        views = g("media:statistics", "views")
        out.append({
            "id": vid,
            "t": re.sub(r"\s*#\w+\s*$", "", g("media:title")).strip(),
            "d": g("published")[:10],
            "v": int(views) if views.isdigit() else 0,
        })
    out.sort(key=lambda x: x["d"], reverse=True)
    if out:
        CACHE.parent.mkdir(exist_ok=True)
        CACHE.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


CSS = """
*{box-sizing:border-box}
.yt-wrap{max-width:900px;margin:0 auto;padding:0 16px 60px}
.yt-hero{background:linear-gradient(135deg,#1c1c1c,#2b2b2b);border-radius:18px;
padding:30px 26px;color:#f5f2ea;margin-bottom:26px}
.yt-hero .badge{display:inline-block;background:rgba(240,112,64,.18);color:#F5A481;
font-size:.72rem;font-weight:700;border-radius:20px;padding:4px 11px;margin-bottom:12px}
.yt-hero h1{font-size:1.5rem;font-weight:800;margin:0 0 8px;letter-spacing:-.02em;line-height:1.35}
.yt-hero p{margin:0 0 18px;color:#b8b3a8;font-size:.9rem;line-height:1.6}
.yt-sub{display:inline-block;background:#FF0000;color:#fff;text-decoration:none;
font-weight:700;font-size:.9rem;border-radius:10px;padding:11px 20px}
.yt-sub:hover{filter:brightness(1.08)}
.yt-h2{font-size:1.05rem;font-weight:800;margin:26px 0 4px;letter-spacing:-.01em}
.yt-h2 small{font-weight:400;color:#a8a294;font-size:.76rem;margin-left:7px}
.yt-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:14px;margin-top:14px}
.yt-card{text-decoration:none;color:inherit;display:block}
.yt-thumb{position:relative;border-radius:12px;overflow:hidden;background:#eceae2;
aspect-ratio:9/16;display:block}
.yt-thumb img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .25s}
.yt-card:hover .yt-thumb img{transform:scale(1.04)}
.yt-play{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
width:38px;height:38px;border-radius:50%;background:rgba(0,0,0,.55);color:#fff;
display:flex;align-items:center;justify-content:center;font-size:13px;padding-left:2px}
.yt-meta{margin-top:8px}
.yt-t{font-size:.83rem;font-weight:700;line-height:1.45;color:#2b2b2b;
display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.yt-d{font-size:.72rem;color:#a8a294;margin-top:4px}
.yt-more{display:block;text-align:center;margin-top:26px;color:#8a8578;text-decoration:none;
font-size:.87rem;border:1px solid #e6e1d5;border-radius:11px;padding:13px}
.yt-more:hover{color:#E55A00;border-color:#E55A00}
@media(max-width:560px){.yt-grid{grid-template-columns:repeat(auto-fill,minmax(132px,1fr));gap:11px}}
"""


def card(v):
    return f"""<a class="yt-card" href="https://www.youtube.com/shorts/{v['id']}" target="_blank" rel="noopener">
<span class="yt-thumb"><img src="https://i.ytimg.com/vi/{v['id']}/hqdefault.jpg"
 alt="{H.escape(v['t'])}" loading="lazy" width="270" height="480"/>
<span class="yt-play">▶</span></span>
<span class="yt-meta"><span class="yt-t">{H.escape(v['t'])}</span>
<span class="yt-d">{v['d'][5:].replace('-', '.')}{' · 조회 ' + f"{v['v']:,}" if v['v'] else ''}</span></span></a>"""


def build(nav_html=None):
    if nav_html is None:
        try:
            import build_nav
            nav_html = ("<style>" + build_nav.HEADER_CSS + "</style>"
                        + build_nav.header_html("/youtube/"))
        except Exception:
            nav_html = ""

    vids = fetch()
    OUT.mkdir(exist_ok=True)
    latest = vids[0] if vids else None

    body = f"""<div class="yt-hero">
<span class="badge">▶ YouTube</span>
<h1>순살브리핑 숏츠</h1>
<p>글로벌 금융·경제·크립토를 1분 안에. 매일 새 영상이 올라옵니다.</p>
<a class="yt-sub" href="https://www.youtube.com/@soonsal?sub_confirmation=1"
 target="_blank" rel="noopener">채널 구독하기</a>
</div>"""

    if vids:
        body += f"""<h2 class="yt-h2">최근 영상<small>{latest['d'].replace('-', '.')} 업데이트</small></h2>
<div class="yt-grid">{''.join(card(v) for v in vids[:15])}</div>
<a class="yt-more" href="https://www.youtube.com/@soonsal/shorts" target="_blank" rel="noopener">
채널에서 전체 보기 →</a>"""
    else:
        body += """<p style="color:#a8a294;text-align:center;padding:40px 0">
영상을 불러오지 못했어요. <a href="https://www.youtube.com/@soonsal" style="color:#E55A00">채널에서 보기 →</a></p>"""

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YouTube | 순살브리핑</title>
<meta name="description" content="순살브리핑 유튜브 숏츠 — 글로벌 금융·경제·크립토를 1분 안에."/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;800&display=swap" rel="stylesheet"/>
<script src="/ss-config.js"></script>
<style>
body{{margin:0;background:#faf8f3;color:#2b2b2b;
font-family:'DM Sans',-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;
-webkit-font-smoothing:antialiased}}
{CSS}
</style></head><body>
{nav_html}
<div class="yt-wrap">{body}</div>
<script src="/soonsal.js" defer></script>
</body></html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"▶ youtube: 최근 영상 {len(vids)}개 (RSS)")


if __name__ == "__main__":
    build()
