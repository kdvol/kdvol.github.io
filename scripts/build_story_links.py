#!/usr/bin/env python3
"""뉴스레터 스토리 끝에 「이 이야기에 나온 것 / 같은 흐름」을 붙인다.

재료는 이미 다 있다 — 엔티티 152개, 위키 142장, 스토리 색인 1,022건.
없는 건 연결뿐이다. 0814 한 편에만 엔티티가 24개 나오는데 위키를 가리키는
링크는 1개였다.

**본문 안에 인라인으로 깔지 않는다** (KD 2026-08-15: 가독성 유지).
24개를 문단에 박으면 읽을 수가 없고, 뉴스레터는 이메일 원본이라 링크가
많으면 스팸 판정 위험도 오른다. 나무위키는 찾아보러 온 사람의 구조고
뉴스레터는 읽으러 온 사람이 본다.

그래서 **면책 문구 다음**에 두 줄로 단다. 면책은 본문에 바로 붙고,
부가 링크는 그 뒤다 (KD 2026-08-15).
  이 이야기에 나온 것 →  메타 · 저커버그 · 오픈AI      (최대 5개, 등장 순)
  같은 흐름 →  8/12 「AI 크레딧이 완전 뒤바뀐 거 봤어?」  (최대 2개)

「같은 흐름」이 실은 더 중요하다. 엔티티 페이지보다 **다른 회차로 보내는 것**이
체류를 늘린다. 그게 연재처럼 읽히게 만드는 장치이기도 하다.

사용:
  python3 scripts/build_story_links.py --issue 0814
  python3 scripts/build_story_links.py --all --dry
"""

import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTITIES = ROOT / "scripts" / "entities.json"
TAXONOMY = ROOT / "scripts" / "topics_taxonomy.json"
STORIES = ROOT / "search" / "index.json"

# 기존 면책과 글자 하나까지 같아야 한 벌로 보인다
DISCLAIMER = ('<p style="font-size:11px; color:#aaa; margin:12px 0 0 0;">'
              '매수매도 추천 아님, 순살도 주주 아님</p>')

MAX_ENT = 5
MAX_REL = 2
MAX_TOPIC = 2      # 주제는 둘까지. 셋이 넘으면 분류표가 되고 아무도 안 누른다
MIN_HITS = 2       # 스치듯 한 번 나온 것은 그 글의 주제가 아니다

# ★ 태그가 늘어나지 않게 잡는 선 (KD 2026-08-15)
#   > "이렇게 태그 추가 시작하면 미친듯이 늘어날 수도 있어서 적정 선을 지켜야 함"
#   그래서 **20개 스토리 이상에서 반복되는 주제만** 태그가 된다. 이 숫자는
#   빌드할 때마다 실제 본문에서 다시 센다 — 아래로 떨어진 주제는 스스로 빠진다.
MIN_TOPIC_STORIES = 20

CSS = """
<style id="soonsal-story-links">
/* 스토리 끝 — 다 읽은 사람만 본다. 본문 흐름을 끊지 않는다 */
.story-links{margin:14px 0 0;padding:11px 0 0;border-top:1px solid #ece8e0;
font-size:11.5px;line-height:1.8;color:#9a958a;word-break:keep-all}
.story-links .k{color:#b5b0a4;margin-right:5px}
.story-links a{color:#8a857c;text-decoration:none;border-bottom:1px solid #e6e1d8}
.story-links a:hover{color:#C24A00;border-bottom-color:#C24A00}
.story-links .sep{opacity:.4;margin:0 4px}
/* 주제는 개별 이름이 아니라 묶음이다 — 테두리로 구분한다 */
.story-links a.topic{border-bottom:0;padding:1px 7px;border-radius:999px;
background:#f3efe8;color:#8a857c}
.story-links a.topic:hover{background:#C24A00;color:#fff}
.story-links .row + .row{margin-top:4px}
/* 「같은 흐름」은 제목이 길어 한 줄에 하나씩 세운다. 라벨은 왼쪽에 고정 */
.story-links .flows{display:flex;align-items:flex-start}
.story-links .flow-list{display:flex;flex-direction:column;gap:2px;min-width:0}
.story-links .flow{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.story-links .flow b{font-weight:600;color:#b5b0a4;margin-right:3px}
@media(max-width:560px){.story-links .flows{display:block}
  .story-links .flow-list{margin-top:2px;padding-left:1px}}
</style>
"""


DIV_RE = re.compile(r"<(/?)div\b[^>]*>", re.I)


def story_close(src: str, sid: str) -> int | None:
    """`id="story-N"` 스토리 상자가 **닫히는 자리**의 시작 인덱스.

    ★ 「`</p>` 뒤 `</div></div>`」로 자리를 잡던 것을 버렸다 (KD 2026-08-21:
      *"0622 스토리2 는 웹사이트에서 양식들 더하다가 css가 깨져버렸어"*).

      0622 2번은 마지막 불릿이 이렇게 끝난다 —

        <div class="bullet">…<p>…한 주</p>
        </div>   ← 불릿
        </div>   ← story-body
        </div>   ← story

      옛 정규식은 `</p>` 바로 뒤에서 멈추고, 뒤따르는 `</div></div>` 를
      「본문과 스토리」로 착각했다. 실제로는 **불릿과 story-body** 였다.
      그래서 면책과 링크 줄이 **불릿 안**에 들어갔고, 불릿은 아이콘 옆
      좁은 칸이라 글자가 세로로 한 줄씩 쌓였다.

      태그를 세는 수밖에 없다. 여는 `div` 마다 +1, 닫는 `div` 마다 -1 해서
      0 으로 돌아오는 자리가 그 스토리의 끝이다. **깊이를 세면 마크업이
      어떻게 생겼든 안 틀린다** — 옛 회차마다 본문 끝 태그가 다르다는 게
      이 함수가 있는 이유다.
    """
    m = re.search(r'<div[^>]*id="' + re.escape(sid) + r'"[^>]*>', src)
    if not m:
        return None
    depth, pos = 1, m.end()
    for t in DIV_RE.finditer(src, m.end()):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return t.start()
        pos = t.end()
    return None                                   # 안 닫혔다 — 손대지 않는다


def misplaced_stories(src: str) -> list[str]:
    """면책·링크 줄이 **불릿 안**에 들어간 스토리 번호.

    고치는 쪽과 검사하는 쪽이 **같은 파일**에 있어야 갈라지지 않는다
    (2026-08-20 `standalone.py` 에서 정규식을 두 벌 쓰다 겪었다).
    """
    bad = []
    for m in re.finditer(r'<div class="bullet"[^>]*>((?:(?!<div class="bullet")[\s\S])*?)</div>',
                         src):
        if "story-links" in m.group(1) or "매수매도 추천 아님" in m.group(1):
            head = src[:m.start()]
            sid = (re.findall(r'id="(story-\d+)"', head) or ["?"])[-1]
            if sid not in bad:
                bad.append(sid)
    return bad


def heal(src: str) -> tuple[str, int]:
    """이미 **불릿 안**에 들어가 버린 면책을 걷어낸다.

    링크 줄(`story-links`)은 `process()` 가 어차피 걷었다 다시 단다. 면책은
    안 걷는다 — 제자리에 있는 것과 글자가 똑같아 구분할 수가 없다. 그래서
    **불릿 안에 있다**는 위치로만 가려낸다. 걷어내면 그 스토리는 「면책 없음」
    이 되고, 다음 단계가 제자리에 다시 붙인다.
    """
    n = 0

    def one(m):
        nonlocal n
        inner = m.group(1)
        if DISCLAIMER not in inner:
            return m.group(0)
        n += 1
        return m.group(0).replace(DISCLAIMER, "")

    out = re.sub(r'<div class="bullet"[^>]*>((?:(?!<div class="bullet")[\s\S])*?)</div>',
                 one, src)
    return out, n


def entities() -> list[dict]:
    if not ENTITIES.is_file():
        return []
    d = json.loads(ENTITIES.read_text(encoding="utf-8"))
    return d.get("entities", d) if isinstance(d, dict) else d


def stories() -> list[dict]:
    return json.loads(STORIES.read_text(encoding="utf-8")) if STORIES.is_file() else []


def topics() -> list[dict]:
    """주제 분류표. content_pattern 이 이미 있어 그대로 쓴다."""
    if not TAXONOMY.is_file():
        return []
    d = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    out = []
    for t in d.get("topics", []):
        pat = t.get("content_pattern")
        if not pat or not (ROOT / "topics" / f"{t['slug']}.html").is_file():
            continue
        try:
            t = {**t, "re": re.compile(pat)}
        except re.error:
            continue
        out.append(t)
    return out


def live_topics(tops: list[dict], bodies: list[str]) -> list[dict]:
    """20개 스토리에 못 미치는 주제는 태그로 쓰지 않는다."""
    keep = []
    for t in tops:
        n = sum(1 for b in bodies if t["re"].search(b))
        if n >= MIN_TOPIC_STORIES:
            keep.append(t)
    return keep


def topics_in(text: str, tops: list[dict], title: str = "") -> list[dict]:
    """등장 순이 아니라 **얼마나 나왔나** 순. 등장 순으로 고르면 스치듯 한 번
    나온 주제가 그 글의 중심 주제를 밀어낸다 — 염소 산불 글에서 「보험」이
    「트럼프·정책」에 밀려 빠졌다 (KD 2026-08-15)."""
    hits = []
    for t in tops:
        n = len(t["re"].findall(text))
        # 제목에 있으면 두 번 친다. 「크립토 연방 은행」 기사에 「크립토」가
        # 안 붙었던 건 본문 언급 수로만 셌기 때문이다.
        if title and t["re"].search(title):
            n += 2
        if n:
            hits.append((n, -text.index(t["re"].search(text).group(0)), t))
    hits.sort(key=lambda x: (-x[0], -x[1]))
    # 두 번은 나와야 주제로 친다. 비만약 기사에 「에너지·원자재」가 붙은 건
    # `골드만삭스`의 '골드' 한 번 때문이었다. 다만 그렇게 걸러 하나도 안 남으면
    # 가장 많이 나온 것 하나는 살린다 — 태그가 통째로 사라지는 게 더 나쁘다.
    strong = [h for h in hits if h[0] >= MIN_HITS]
    if not strong and hits:
        strong = hits[:1]
    return [t for _, _, t in strong[:MAX_TOPIC]]


def wiki_exists(slug: str) -> bool:
    return (ROOT / "wiki" / f"{slug}.html").is_file()


def found_in(text: str, ents: list[dict]) -> list[tuple[int, dict]]:
    """본문에 나온 엔티티를 등장 순으로. 위키 페이지가 있는 것만.

    이름으로 부분일치를 하면 오탐이 난다 — `금지`에서 `금`(gold)이 잡혔다.
    entities.json 의 pattern 이 그 문제를 이미 풀어 뒀다(`금값|금 선물|온스당`).
    """
    hits = []
    for e in ents:
        if not wiki_exists(e["slug"]):
            continue
        pat = e.get("pattern") or re.escape(e.get("name") or "")
        if not pat:
            continue
        try:
            m = re.search(pat, text)
        except re.error:
            continue
        if m:
            hits.append((m.start(), e))
    hits.sort(key=lambda x: x[0])
    return hits[:MAX_ENT]


def related(title: str, issue: str, all_stories: list[dict]) -> list[dict]:
    """같은 흐름 — 제목이 겹치는 지난 스토리. 같은 회차는 뺀다."""
    def bg(t):
        t = "".join(c for c in t if c.isalnum())
        return {t[i:i + 2] for i in range(len(t) - 1)}
    want = bg(title)
    if not want:
        return []
    scored = []
    for s in all_stories:
        if issue in s.get("u", ""):
            continue
        have = bg(s.get("t", ""))
        if not have:
            continue
        score = len(want & have) / min(len(want), len(have))
        if score >= 0.30:
            scored.append((score, s))
    scored.sort(key=lambda x: (-x[0], x[1].get("d", "")))
    return [s for _, s in scored[:MAX_REL]]


def block(ents: list[tuple[int, dict]], rel: list[dict],
          tops: list[dict] | None = None) -> str:
    rows = []
    parts = [f'<a href="/wiki/{e["slug"]}.html">{html.escape(e.get("name",""))}</a>'
             for _, e in ents]
    # 주제는 인물·기업 뒤에 온다. 레이커스 얘기에 「스포츠 비즈니스」가 없어서
    # 걸 데가 하나도 없던 게 이걸 붙이는 이유다 (KD 2026-08-15).
    parts += [f'<a class="topic" href="/topics/{t["slug"]}.html">'
              f'{html.escape(t["name"])}</a>' for t in (tops or [])]
    if parts:
        links = '<span class="sep">·</span>'.join(parts)
        rows.append(f'<div class="row"><span class="k">이 이야기에 나온 것</span>{links}</div>')
    if rel:
        # 회차 제목은 길다. 가운뎃점으로 이으면 아무 데서나 접혀 덩어리가 된다.
        # 한 줄에 하나씩 세운다 (KD 2026-08-15: 줄별로 정돈).
        links = "".join(
            f'<span class="flow"><a href="{html.escape(s["u"])}">'
            f'<b>{html.escape(s.get("d","")[5:])}</b> '
            f'{html.escape(s.get("t",""))[:30]}</a></span>' for s in rel)
        rows.append(f'<div class="row flows"><span class="k">같은 흐름</span>'
                    f'<span class="flow-list">{links}</span></div>')
    return f'<div class="story-links">{"".join(rows)}</div>' if rows else ""


def process(page: Path, ents: list[dict], all_stories: list[dict],
            tops: list[dict], dry: bool) -> int:
    src = page.read_text(encoding="utf-8", errors="ignore")
    # ★ 걷어낼 때 남의 </div> 를 먹지 않는다.
    #   예전 정규식은 `...</div>\s*</div>` 를 지우고 `</div>` 하나를 도로 넣었다.
    #   블록 자체가 `<div class="story-links">…</div>` 로 이미 닫혀 있어서,
    #   그 뒤 스토리의 닫는 태그까지 먹고 하나만 돌려준 셈이다. 재실행할 때마다
    #   `</div>` 가 하나씩 늘어, 0814 는 20개가 남아 2번 스토리부터 컨테이너
    #   밖으로 튀어나왔다. 블록 구조를 그대로 적어 정확히 그것만 지운다.
    src = re.sub(r'<div class="story-links">'
                 r'(?:<div class="row[^"]*">[\s\S]*?</div>)+'
                 r'</div>', "", src)
    src = re.sub(r'<style id="soonsal-story-links">.*?</style>\s*', "", src, flags=re.S)
    # ★ 지난 판이 불릿 안에 박아 둔 면책을 먼저 걷는다. 안 걷으면 「면책이
    #   이미 있다」로 읽혀 그 자리에 그대로 남는다 — 고친 코드로 다시 돌려도
    #   깨진 페이지가 안 낫는다. 고치는 도구는 **이미 망가진 것도** 고쳐야 한다.
    src, healed = heal(src)
    if healed:
        print(f"   🩹 {page.name} — 불릿 안 면책 {healed}곳 걷어냄")
    issue = f"/{page.parent.name}/{page.stem}."
    mine = [s for s in all_stories if issue in s.get("u", "")]
    if not mine:
        return 0

    added = 0
    out = src
    for s in mine:
        anchor = re.search(r"#(story-\d+)", s.get("u", ""))
        if not anchor:
            continue
        # 면책 문구 바로 뒤에 끼운다. 면책이 없는 스토리는 마지막 문단 뒤.
        # 스토리 경계를 넘지 않는다. `.*?` 만 쓰면 면책이 없는 스토리에서 다음
        # 스토리의 면책까지 훑어가, 한 자리에 블록이 두 개 붙었다(0317).
        inner = r'(?:(?!id="story-)[\s\S])*?'
        m = re.search(r'(id="' + anchor.group(1) + r'"' + inner + r')'
                      r'(<p style="font-size:11px[^>]*>매수매도 추천 아님[^<]*</p>)', out)
        made_disclaimer = False
        at = None
        if not m:
            # 면책이 없는 스토리 — 절반(512/1,022)이 그렇다. 면책은 모든
            # 스토리에 붙어야 하므로(KD 2026-08-15) 여기서 만들어 넣는다.
            # ★ 자리는 **스토리 상자가 닫히기 직전**이다. 태그로 짐작하지
            #   않는다 — 회차마다 본문 끝 태그가 다르고, 짐작하면 불릿 안으로
            #   들어간다(0622 2번). `story_close` 가 깊이를 세서 잡아 준다.
            at = story_close(out, anchor.group(1))
            if at is None:
                continue
            head = out[:at]
            i = head.rfind(f'id="{anchor.group(1)}"')
            m = re.match(r"[\s\S]*", head[i:])       # 본문 = 스토리 안 전체
            body_src = head[i:]
            made_disclaimer = True
        body = re.sub(r"<[^>]+>", " ", body_src if made_disclaimer else m.group(1))
        blk = block(found_in(body, ents),
                    related(s.get("t", ""), issue, all_stories),
                    topics_in(body, tops, s.get("t", "")))
        if not blk and not made_disclaimer:
            continue          # 걸 링크도 없고 면책도 이미 있다 — 건드릴 게 없다
        # 면책은 본문에 **바로 붙어야** 한다 (KD 2026-08-15). 부가 링크가
        # 사이에 끼면 면책이 본문에서 떨어져 나와 딴 얘기처럼 읽힌다.
        # 그래서 링크 줄은 면책 **뒤**로 간다.
        if made_disclaimer:
            # 스토리 상자가 닫히기 직전 — 면책이 먼저, 링크 줄이 그 뒤
            out = out[:at] + DISCLAIMER + blk + out[at:]
        else:
            out = out[:m.end(2)] + blk + out[m.end(2):]
        added += 1

    if added and "soonsal-story-links" not in out and "</head>" in out:
        out = out.replace("</head>", CSS + "</head>", 1)
    if added and not dry:
        page.write_text(out, encoding="utf-8")
    return added


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue", help="MMDD")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    ents, all_stories = entities(), stories()
    # 주제 태그의 문턱을 실제 본문에서 잰다. 링크 블록은 빼고 센다 —
    # 「같은 흐름」에 걸린 남의 제목이 본문으로 잡히면 숫자가 부풀려진다.
    corpus = []
    for q in sorted((ROOT / "newsletters" / "2026").glob("[0-9][0-9][0-9][0-9]*.html")):
        raw = re.sub(r'<div class="story-links">[\s\S]*?</div></div>', " ",
                     q.read_text(encoding="utf-8", errors="ignore"))
        corpus.append(re.sub(r"<[^>]+>", " ", raw))
    tops = live_topics(topics(), corpus)
    print(f"  주제 태그 {len(tops)}개 "
          f"({MIN_TOPIC_STORIES}개 회차 이상): "
          + " · ".join(t["name"] for t in tops))
    if not ents or not all_stories:
        print("  엔티티나 스토리 색인이 없다")
        return 1

    pages = []
    if a.issue:
        pages = [ROOT / "newsletters" / "2026" / f"{a.issue}.html"]
    elif a.all:
        pages = sorted((ROOT / "newsletters" / "2026")
                       .glob("[0-9][0-9][0-9][0-9]*.html"))   # -crypto 회차 포함
    else:
        print("  --issue MMDD 또는 --all")
        return 1

    total = 0
    for p in pages:
        if not p.is_file():
            continue
        n = process(p, ents, all_stories, tops, a.dry)
        if n:
            print(f"  {p.name}  스토리 {n}개")
            total += n
    print(f"\n  {total}개 스토리에 링크 줄 추가" + ("  (dry)" if a.dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
