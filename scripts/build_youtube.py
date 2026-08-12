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
.yt{max-width:900px;margin:0 auto;padding:30px 16px 70px}

/* 페이지 머리 — nav와 붙지 않게 여백을 두고, 배경은 사이트와 같은 #111 */
.ph{margin-bottom:30px}
.ph .ey{font-size:.72rem;font-weight:700;letter-spacing:.09em;color:#F07040;
text-transform:uppercase;margin-bottom:9px}
.ph h1{font-size:1.72rem;font-weight:800;letter-spacing:-.03em;margin:0 0 9px;
line-height:1.28;color:#f0ede6}
.ph p{margin:0;color:#8b8578;font-size:.93rem;line-height:1.7;max-width:52ch}
.ph .go{display:inline-block;margin-top:15px;border:1px solid #333;border-radius:9px;
padding:9px 16px;font-size:.84rem;font-weight:700;color:#eee;transition:.15s}
.ph .go:hover{border-color:#F07040;color:#F07040}

h2{font-size:1.02rem;font-weight:800;letter-spacing:-.01em;margin:40px 0 3px;color:#f0ede6}
h2 .n{color:#666;font-weight:400;font-size:.76rem;margin-left:8px}
.lead{color:#8b8578;font-size:.84rem;margin:0 0 16px;line-height:1.6}

/* 히어로 영상 — 한 편을 크게. 숏츠에 묻히면 안 되는 콘텐츠다 */
.hero{display:block;border:1px solid #262626;border-radius:16px;overflow:hidden;
background:#161616;transition:border-color .15s}
.hero:hover{border-color:#3a3a3a}
.hv{position:relative;aspect-ratio:16/9;background:#000;cursor:pointer;display:block}
.hv img{width:100%;height:100%;object-fit:cover;display:block;opacity:.82;transition:opacity .25s}
.hero:hover .hv img{opacity:1}
.hv iframe{width:100%;height:100%;border:0;display:block}
.hv .pl{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
width:62px;height:62px;border-radius:50%;background:rgba(0,0,0,.55);
border:1.5px solid rgba(255,255,255,.55);color:#fff;display:flex;align-items:center;
justify-content:center;font-size:19px;padding-left:4px;backdrop-filter:blur(3px)}
.hb{padding:17px 19px}
.hb .t{font-size:1.04rem;font-weight:800;letter-spacing:-.02em;line-height:1.42;color:#f0ede6}
.hb .d{color:#8b8578;font-size:.85rem;margin-top:6px;line-height:1.6}
.hb .lk{display:inline-block;margin-top:11px;color:#F07040;font-size:.83rem;font-weight:700}

/* 위클리 — 가로 카드 */
.wk{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:15px}
.wc{display:block;border:1px solid #232323;border-radius:13px;overflow:hidden;
background:#161616;transition:border-color .15s}
.wc:hover{border-color:#3a3a3a}
.wc .th{position:relative;aspect-ratio:16/9;background:#000}
.wc .th img{width:100%;height:100%;object-fit:cover;display:block;opacity:.82;transition:opacity .25s}
.wc:hover .th img{opacity:1}
.wc .th .pl{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
width:40px;height:40px;border-radius:50%;background:rgba(0,0,0,.55);color:#fff;
display:flex;align-items:center;justify-content:center;font-size:13px;padding-left:2px}
.wc .tt{padding:12px 13px;font-size:.86rem;font-weight:700;line-height:1.5;color:#e8e4dc;
display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}

/* 숏츠 — 작게, 많이 */
.sh{display:grid;grid-template-columns:repeat(auto-fill,minmax(124px,1fr));gap:12px}
.sc{display:block}
.sc .th{position:relative;border-radius:10px;overflow:hidden;background:#000;aspect-ratio:9/16}
.sc .th img{width:100%;height:100%;object-fit:cover;display:block;opacity:.85;transition:.25s}
.sc:hover .th img{opacity:1;transform:scale(1.03)}
.sc .tt{margin-top:7px;font-size:.76rem;font-weight:600;line-height:1.45;color:#c9c4ba;
display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.sc .dd{font-size:.68rem;color:#5f5a52;margin-top:3px}

/* 클래스로 잇는 자리 */
.bridge{margin-top:44px;border:1px solid #262626;border-radius:16px;padding:24px 22px;
background:linear-gradient(160deg,#17181a,#141414)}
.bridge .ey{font-size:.7rem;font-weight:700;letter-spacing:.08em;color:#F07040;
text-transform:uppercase;margin-bottom:8px}
.bridge h3{font-size:1.14rem;font-weight:800;letter-spacing:-.02em;margin:0 0 8px;color:#f0ede6}
.bridge p{margin:0 0 15px;color:#8b8578;font-size:.88rem;line-height:1.7}
.bridge a.b{display:inline-block;background:#E55A00;color:#fff;border-radius:9px;
padding:11px 19px;font-size:.86rem;font-weight:700}
.bridge a.b:hover{background:#F07040}

.more{display:block;text-align:center;margin-top:26px;color:#7a756c;
font-size:.85rem;border:1px solid #262626;border-radius:11px;padding:13px;transition:.15s}
.more:hover{color:#F07040;border-color:#F07040}
@media(max-width:560px){
 .yt{padding:24px 15px 60px}
 .ph h1{font-size:1.42rem}
 .sh{grid-template-columns:repeat(auto-fill,minmax(104px,1fr));gap:10px}
}
"""



HERO = ROOT / "content/youtube_hero.json"
CLASS = "https://soonsal.liveklass.com/classes/"


def short(v):
    return f"""<a class="sc" href="https://www.youtube.com/shorts/{v['id']}" target="_blank" rel="noopener">
<span class="th"><img src="https://i.ytimg.com/vi/{v['id']}/hqdefault.jpg"
 alt="{H.escape(v['t'])}" loading="lazy" width="270" height="480"/></span>
<span class="tt">{H.escape(v['t'])}</span>
<span class="dd">{v['d'][5:].replace('-', '.')}{' · ' + f"{v['v']:,}" if v['v'] else ''}</span></a>"""


def weekly(v):
    return f"""<a class="wc" href="https://www.youtube.com/watch?v={v['id']}" target="_blank" rel="noopener">
<span class="th"><img src="https://i.ytimg.com/vi/{v['id']}/hqdefault.jpg"
 alt="{H.escape(v['t'])}" loading="lazy" width="480" height="270"/><span class="pl">▶</span></span>
<span class="tt">{H.escape(v['t'])}</span></a>"""


def hero_block(h):
    """한 편을 크게 건다. 클릭해야 재생하고, 클래스로 이어지는 줄을 붙인다."""
    return f"""<div class="hero">
<span class="hv" data-v="{h['id']}">
<img src="https://i.ytimg.com/vi/{h['id']}/maxresdefault.jpg"
 onerror="this.src='https://i.ytimg.com/vi/{h['id']}/hqdefault.jpg'"
 alt="{H.escape(h['t'])}" width="1280" height="720"/><span class="pl">▶</span></span>
<div class="hb"><div class="t">{H.escape(h['t'])}</div>
<div class="d">{H.escape(h['d'])}</div>
<a class="lk" href="/school/">이어지는 클래스 보기 →</a></div>
</div>"""


def video_ld(vids, hero):
    """영상 목록을 VideoObject로 표시한다. 썸네일·업로드일·URL만 쓴다 —
    조회수는 RSS 값이 실시간이 아니라 넣지 않는다(틀린 숫자를 심는 게 더 나쁘다)."""
    items, seen = [], set()
    pool = []
    for k in ("career",):
        if hero.get(k):
            pool.append((hero[k], False))
    for k in ("teasers", "weekly"):
        for v in hero.get(k) or []:
            pool.append((v, False))
    for v in vids[:12]:
        pool.append((v, True))

    for v, is_short in pool:
        vid = v.get("id")
        if not vid or vid in seen:
            continue
        seen.add(vid)
        node = {
            "@type": "VideoObject",
            "name": v.get("t") or "순살브리핑",
            "thumbnailUrl": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            "contentUrl": (f"https://www.youtube.com/shorts/{vid}" if is_short
                           else f"https://www.youtube.com/watch?v={vid}"),
            "embedUrl": f"https://www.youtube-nocookie.com/embed/{vid}",
            "inLanguage": "ko",
            "publisher": {"@type": "Organization", "name": "순살브리핑",
                          "url": "https://soonsal.com/"},
        }
        if v.get("d"):
            node["uploadDate"] = v["d"]
        if v.get("dsc") or v.get("d0"):
            node["description"] = v.get("dsc") or v.get("d0")
        items.append({"@type": "ListItem", "position": len(items) + 1, "item": node})

    return {"@context": "https://schema.org", "@type": "ItemList",
            "name": "순살브리핑 영상", "itemListElement": items}


def build(nav_html=None):
    if nav_html is None:
        try:
            import build_nav
            nav_html = ("<style>" + build_nav.HEADER_CSS + "</style>"
                        + build_nav.header_html("/youtube/"))
        except Exception:
            nav_html = ""

    vids = fetch()
    hero = json.loads(HERO.read_text(encoding="utf-8")) if HERO.exists() else {}
    OUT.mkdir(exist_ok=True)

    body = """<div class="ph">
<div class="ey">순살 YouTube</div>
<h1>보면서 이해하는<br>글로벌 금융</h1>
<p>매일 1분 숏츠로 오늘의 시장을, 긴 영상으로는 커리어와 산업의 맥락을 다룹니다.</p>
<a class="go" href="https://www.youtube.com/@soonsal?sub_confirmation=1"
 target="_blank" rel="noopener">채널 구독하기</a>
</div>"""

    # 1) 커리어 영상 — 숏츠에 묻히면 안 되는 콘텐츠라 맨 위에 크게
    c = hero.get("career")
    if c:
        body += ('<h2>커리어 이야기</h2>'
                 '<p class="lead">금융권에서 일한다는 게 실제로 어떤 것인지.</p>'
                 + hero_block(c))

    # 2) 클래스 맛보기 — 커리어 영상과 같은 줄기다
    tz = hero.get("teasers") or []
    if tz:
        body += ('<h2>클래스 맛보기<span class="n">순살 스쿨</span></h2>'
                 '<p class="lead">현직자가 여는 클래스의 첫 1분.</p>'
                 f'<div class="wk">{"".join(weekly(v) for v in tz)}</div>')

    # 3) 위클리 롱폼
    wk = hero.get("weekly") or []
    if wk:
        body += ('<h2>순살 위클리</h2>'
                 '<p class="lead">한 주의 흐름을 길게 짚습니다.</p>'
                 f'<div class="wk">{"".join(weekly(v) for v in wk)}</div>')

    # 4) 숏츠 — 자동 갱신되는 자리
    if vids:
        body += (f'<h2>매일 올라오는 숏츠<span class="n">{vids[0]["d"].replace("-", ".")} 기준</span></h2>'
                 f'<div class="sh">{"".join(short(v) for v in vids[:12])}</div>'
                 '<a class="more" href="https://www.youtube.com/@soonsal/shorts"'
                 ' target="_blank" rel="noopener">채널에서 전체 보기 →</a>')

    body += """<div class="bridge">
<div class="ey">Soonsal School</div>
<h3>영상으로 궁금해졌다면, 다음은 클래스</h3>
<p>홍콩·한국의 투자은행과 헤지펀드에서 지금도 일하는 사람들이
IBD·M&amp;A·바이사이드·퀀트를 직접 풀어드립니다.</p>
<a class="b" href="/school/">순살 스쿨 보기 →</a>
</div>"""

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YouTube | 순살브리핑</title>
<meta name="description" content="순살브리핑 유튜브 — 1분 숏츠로 오늘의 시장, 긴 영상으로 금융 커리어와 산업의 맥락. 매일 새 영상."/>
<link rel="canonical" href="https://soonsal.com/youtube/"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="순살브리핑 YouTube — 보면서 이해하는 글로벌 금융"/>
<meta property="og:description" content="1분 숏츠로 오늘의 시장, 긴 영상으로 커리어와 산업의 맥락."/>
<meta property="og:url" content="https://soonsal.com/youtube/"/>
<meta name="twitter:card" content="summary_large_image"/>
<script type="application/ld+json">{json.dumps(video_ld(vids, hero), ensure_ascii=False)}</script>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;800&display=swap" rel="stylesheet"/>
<script src="/ss-config.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#111;color:#eee;font-family:'DM Sans','Apple SD Gothic Neo',sans-serif;
min-height:100vh;-webkit-text-size-adjust:100%;-webkit-font-smoothing:antialiased}}
a{{color:#eee;text-decoration:none}}
{CSS}
</style></head><body>
{nav_html}
<div class="yt">{body}</div>
<script src="/soonsal.js" defer></script>
<script>
// 영상은 누를 때만 불러온다 — 썸네일 12장에 iframe을 미리 심으면 페이지가 무거워진다
document.querySelectorAll('.hv[data-v]').forEach(function (b) {{
  b.addEventListener('click', function () {{
    var v = b.getAttribute('data-v');
    b.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + v +
      '?autoplay=1&rel=0" allow="autoplay; encrypted-media" allowfullscreen></iframe>';
    b.removeAttribute('data-v');
  }});
}});
</script>
</body></html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"▶ youtube: 숏츠 {len(vids)} · 위클리 {len(wk)} · 티저 {len(tz)}")


if __name__ == "__main__":
    build()
