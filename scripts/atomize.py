#!/usr/bin/env python3
"""뉴스레터 → 스토리 아톰화 (plantree 방식).

각 뉴스레터를 5개 내외 스토리로 쪼개 개별 라벨링하고, 같은 호에 실린
영어 표현(word-item)을 내용 유사도로 해당 스토리에 연결한다.

산출:
  - content/story_atoms.json  : 스토리 아톰 배열 (build_topics.py 소비)
  - 각 뉴스레터 <div class="story"> 에 id="story-N" 앵커 주입 (멱등, 딥링크용)
  - topics_taxonomy.json 의 _pending 에 미매칭 라벨 누적 (자동 진화 입력)

분류 우선순위: story-label(작성자 섹션, 고정밀) → 제목+본문(재현율).
사전 파일 존재 여부를 사람이 신경 쓸 필요 없음 — 없으면 만들고, 미매칭은 쌓인다.
"""
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NL_DIR = ROOT / "newsletters" / "2026"
TAX_PATH = Path(__file__).resolve().parent / "topics_taxonomy.json"
ENT_PATH = Path(__file__).resolve().parent / "entities.json"
ATOMS_PATH = ROOT / "content" / "story_atoms.json"

DEFAULT_TAX = {"version": 2, "min_stories_per_topic": 3, "topics": [], "_pending": {}}


def load_tax():
    if TAX_PATH.exists():
        return json.loads(TAX_PATH.read_text(encoding="utf-8"))
    return dict(DEFAULT_TAX)


def save_tax(tax):
    TAX_PATH.write_text(json.dumps(tax, ensure_ascii=False, indent=2), encoding="utf-8")


def load_entities():
    if not ENT_PATH.exists():
        return {"entities": [], "types": {}, "min_stories": 3}
    ent = json.loads(ENT_PATH.read_text(encoding="utf-8"))
    for e in ent["entities"]:
        e["_rx"] = re.compile(e["pattern"])
    return ent


def _entity_slugs(text, ent):
    return [e["slug"] for e in ent["entities"] if e["_rx"].search(text)]


def trending_entities(atoms, days=14, size=10, n_top=5, min_recent=3):
    """'지금 뜨는' 엔티티 — 최근 N일 건수 상위(상시 강자) + 급부상(최근 비중) 혼합.
    순수 계산·LLM 0. 뉴스 사이클 따라 매일 바뀌는 압축 탐색층의 원천."""
    from collections import Counter
    from datetime import timedelta
    cut = (date.today() - timedelta(days=days)).isoformat()
    total = Counter(s for a in atoms for s in a["entities"])
    recent = Counter(s for a in atoms if a["date"] >= cut for s in a["entities"])
    if not recent:
        return [s for s, _ in total.most_common(size)]
    top = [s for s, _ in recent.most_common(size)]
    surge = sorted((s for s, c in recent.items() if c >= min_recent),
                   key=lambda s: -(recent[s] / total[s]))
    picks = list(top[:n_top])
    for s in surge:                       # 급부상으로 나머지 채움
        if s not in picks:
            picks.append(s)
        if len(picks) >= size:
            break
    for s in top:                         # 급부상 부족 시 상시 강자로 보충
        if len(picks) >= size:
            break
        if s not in picks:
            picks.append(s)
    return picks[:size]


def extract_entities(story, ent):
    """스토리 제목+본문에서 통제 어휘 엔티티를 균일 추출 → 일관된 태그."""
    return _entity_slugs(f"{story['title']} {story['body']}", ent)


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def english_html(english):
    """word-item을 전체(용어 + 전체 뜻 + 예문) HTML로 렌더. 잘림 없음.
    build_topics/build_wiki가 공용으로 사용해 표현이 항상 동일하도록."""
    from html import escape as esc
    out = []
    for w in english:
        parts = [f'<div class="eng-t">{esc(w["en"])}</div>',
                 f'<div class="eng-k">{esc(w.get("ko", ""))}</div>']
        ex = (w.get("example") or "").strip()
        if ex:
            seg = ex.split('"')                    # {한글 라벨}"{영어 예문}"
            label, sent = seg[0].strip(), (seg[1].strip() if len(seg) > 1 else "")
            if sent:
                inner = (f'<span class="eng-xl">{esc(label)}</span> ' if label else "") + \
                        f'&ldquo;{esc(sent)}&rdquo;'
            else:
                inner = esc(ex)
            parts.append(f'<div class="eng-x">{inner}</div>')
        out.append("".join(parts))
    return "".join(out)


STORY_RE = re.compile(r'<div class="story"(?:\s[^>]*)?>(.*?)(?=<div class="story"[\s>]|<div class="word|'
                      r'<div class="section-title"|<!-- ?WORD|<div class="headline|</body>)', re.S)
LABEL_RE = re.compile(r'<(\w+) class="story-label"[^>]*>(.*?)</\1>', re.S)
TITLE_RE = re.compile(r'<(\w+) class="story-title"[^>]*>(.*?)</\1>', re.S)
BODY_RE = re.compile(r'<div class="story-body"[^>]*>(.*)$', re.S)
WORD_RE = re.compile(
    r'<div class="word-en">(.*?)</div>\s*<div class="word-ko">(.*?)</div>'
    r'(?:\s*<div class="word-example">(.*?)</div>)?', re.S)
FNAME_RE = re.compile(r"^(\d{2})(\d{2})(?:-(crypto))?\.html$")


def parse_newsletter(path):
    """→ (stories[], words[]) . stories: dict, words: dict."""
    fn = path.name
    fm = FNAME_RE.match(fn)
    if not fm:
        return [], []
    mm, dd, crypto = fm.group(1), fm.group(2), bool(fm.group(3))
    try:
        d = date(2026, int(mm), int(dd))
    except ValueError:
        return [], []
    html = path.read_text(encoding="utf-8", errors="replace")
    base_id = f"{mm}{dd}{'c' if crypto else ''}"

    stories = []
    for i, sm in enumerate(STORY_RE.finditer(html), 1):
        seg = sm.group(1)
        lm = LABEL_RE.search(seg)
        tm = TITLE_RE.search(seg)
        if not tm:
            continue
        bm = BODY_RE.search(seg)
        title = strip_tags(tm.group(2))
        label = strip_tags(lm.group(2)) if lm else ""
        body = strip_tags(bm.group(1)) if bm else ""
        stories.append({
            "id": f"{base_id}-{i}",
            "n": i,
            "date": d.isoformat(),
            "crypto": crypto,
            "url": f"/newsletters/2026/{fn}#story-{i}",
            "newsletter": f"/newsletters/2026/{fn}",
            "label": label,
            "title": title,
            "body": body,
            "topics": [],
            "entities": [],
            "english": [],
        })

    words = []
    for wm in WORD_RE.finditer(html):
        en = strip_tags(wm.group(1))
        ko = strip_tags(wm.group(2))
        ex = strip_tags(wm.group(3)) if wm.group(3) else ""
        if en:
            words.append({"en": en, "ko": ko, "example": ex})
    return stories, words


# ── 분류 ───────────────────────────────────────────────────────────
def classify(story, tax, max_topics=3):
    """작성자 섹션라벨을 1순위 신호로. 라벨 매칭이 하나라도 있으면 그것만 쓰고
    (작성자 의도 = 고정밀), 전무할 때만 본문 키워드로 폴백(재현율). 최대 3개."""
    label = story["label"].upper()
    hay = f"{story['title']} {story['body']}"
    label_hits, content_hits = [], []
    for t in tax["topics"]:
        if t.get("label_pattern") and re.search(t["label_pattern"], label, re.I):
            label_hits.append(t["slug"])
        elif t.get("content_pattern") and re.search(t["content_pattern"], hay, re.I):
            content_hits.append(t["slug"])
    topics = label_hits if label_hits else content_hits
    if story["crypto"] and "crypto" not in topics:
        topics = ["crypto"] + topics
    return topics[:max_topics]


def note_pending(story, tax):
    """어떤 토픽에도 안 걸린 스토리의 라벨을 _pending에 축적(자동 진화 입력)."""
    label = story["label"].strip()
    if not label:
        return
    key = label.upper()
    pend = tax.setdefault("_pending", {})
    rec = pend.setdefault(key, {"count": 0, "examples": []})
    rec["count"] += 1
    if len(rec["examples"]) < 3 and story["title"] not in rec["examples"]:
        rec["examples"].append(story["title"])


# ── 영어 표현 → 스토리 연결 (내용 유사도) ──────────────────────────
_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]{2,}|[가-힣]{2,}")
_STOP = set("그리고 하지만 그러나 때문 이것 저것 그것 대한 위해 관련 통해 라는 이는 있다 없다 된다 한다 "
            "the and for that with from this have been will企業 및 등 약 것 수 더 이 그".split())


def _tokens(*parts):
    toks = set()
    for p in parts:
        for m in _TOKEN.finditer((p or "").lower()):
            w = m.group(0)
            if w not in _STOP and len(w) >= 2:
                toks.add(w)
    return toks


# 고유명사 키 추출 — 링킹의 신호는 '영어 고유명사 + 엔티티'뿐(일반어 배제).
_PROPER_RE = re.compile(r"\b[A-Z][A-Za-z0-9]{2,}\b")
_EN_COMMON = set("""The This That These Those When Where What Which While With Without
And But For Nor Not Neither Either After Before Its Their They Are Was Were Will Would
Can Could Should Has Have Had One Two All New Now Get Buy Sell Company Companies Market
Markets Price Model Models Data Fund Funds Corp Inc Ltd You Your His Her She Him Our
About Over Under Into From Than Then They CEO CFO IPO ETF GPU But However Meanwhile
More Most Less Least Big Small High Low First Last Next Some Many Much Very Just Even
Open Close Weight Carry Trade Free Tax Dollar Rate Rates Deal Deals Chief Board""".split())


def _proper_keys(text, ent):
    """텍스트에서 영어 고유명사(대문자 시작) + 사전 엔티티 슬러그를 키로 추출."""
    keys = set(_entity_slugs(text, ent))
    for m in _PROPER_RE.finditer(text):
        w = m.group(0)
        if w not in _EN_COMMON:
            keys.add("en:" + w.lower())
    return keys


def link_english(stories, words, ent):
    """word-item을 같은 호 스토리 중 '고유명사/엔티티'를 공유하는 곳에 붙인다.
    ko+example의 Zhipu·Comcast·eBay 같은 고유명사가 스토리 본문과 겹칠 때만 연결.
    일반어(신뢰할·가장·하나)는 키가 아니므로 우연 일치가 원천 차단됨.
    공유 고유명사가 없으면(헤드라인 등 다른 출처의 표현) 연결하지 않음."""
    if not stories or not words:
        return
    story_keys = [_proper_keys(f"{s['title']} {s['body']}", ent) for s in stories]
    for w in words:
        wk = _proper_keys(f"{w['ko']} {w['example']}", ent)   # en 용어 자체는 제외(일반적)
        if not wk:
            continue
        scored = sorted(((len(wk & sk), i) for i, sk in enumerate(story_keys)), reverse=True)
        best_n, best_i = scored[0]
        second = scored[1][0] if len(scored) > 1 else 0
        if best_n >= 1 and best_n > second:          # 고유명사 최소 1개 공유 + 유일 최다
            stories[best_i]["english"].append(w)


# ── 앵커 주입 (멱등) ──────────────────────────────────────────────
def inject_anchors(path):
    """모든 <div class="story" ...> 에 위치기반 id="story-N" 주입(멱등).
    이미 id가 있으면 보존, style 등 다른 속성이 있어도 처리."""
    html = path.read_text(encoding="utf-8", errors="replace")
    counter = {"n": 0}

    def repl(m):
        counter["n"] += 1
        attrs = m.group(1)                              # '' 또는 ' style="..."' 등
        if "id=" in attrs:
            return m.group(0)                           # 기존 id(위치기반) 보존
        return f'<div class="story"{attrs} id="story-{counter["n"]}">'

    new = re.sub(r'<div class="story"([^>]*)>', repl, html)
    if new == html:
        return False
    path.write_text(new, encoding="utf-8")
    return True


# ── 빌드 ──────────────────────────────────────────────────────────
def build():
    tax = load_tax()
    ent = load_entities()
    tax["_pending"] = {}                            # 매 실행 재계산
    files = sorted(p for p in NL_DIR.glob("*.html") if p.name != "index.html")
    anchored = 0

    # 1차: 전 파일 파싱 → 전역 토큰 문서빈도(df) 계산 (링킹 변별력의 기준)
    parsed = []
    for p in files:
        stories, words = parse_newsletter(p)
        if not stories:
            continue
        parsed.append((p, stories, words))
        if inject_anchors(p):
            anchored += 1
    # 2차: 고유명사 기반 영어연결 + 분류 + 엔티티추출
    atoms = []
    for p, stories, words in parsed:
        link_english(stories, words, ent)
        for s in stories:
            s["topics"] = classify(s, tax)
            s["entities"] = extract_entities(s, ent)
            if not s["topics"]:
                note_pending(s, tax)
        atoms.extend(stories)

    atoms.sort(key=lambda s: (s["date"], s["id"]), reverse=True)
    ATOMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ATOMS_PATH.write_text(json.dumps(atoms, ensure_ascii=False, indent=1), encoding="utf-8")
    save_tax(tax)

    n_eng = sum(len(s["english"]) for s in atoms)
    n_untagged = sum(1 for s in atoms if not s["topics"])
    n_ent = sum(len(s["entities"]) for s in atoms)
    print(f"⚛️  atomize: 스토리 {len(atoms)} · 영어연결 {n_eng} · 엔티티태그 {n_ent} · "
          f"미분류 {n_untagged} · 앵커주입 {anchored}파일 · pending라벨 {len(tax['_pending'])}")
    return atoms


if __name__ == "__main__":
    build()
