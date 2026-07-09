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


def extract_entities(story, ent):
    """스토리 제목+본문에서 통제 어휘 엔티티를 균일 추출 → 일관된 태그."""
    hay = f"{story['title']} {story['body']}"
    return [e["slug"] for e in ent["entities"] if e["_rx"].search(hay)]


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


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


def link_english(stories, words):
    """각 word-item을 같은 호 스토리 중 토큰 겹침이 가장 큰 곳에 붙인다."""
    if not stories or not words:
        return
    story_tokens = [_tokens(s["title"], s["body"]) for s in stories]
    for w in words:
        wt = _tokens(w["en"], w["ko"], w["example"])
        best, best_score = -1, 0
        for i, st in enumerate(story_tokens):
            score = len(wt & st)
            if score > best_score:
                best, best_score = i, score
        if best >= 0 and best_score >= 1:
            stories[best]["english"].append(w)


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
    atoms = []
    files = sorted(p for p in NL_DIR.glob("*.html") if p.name != "index.html")
    anchored = 0
    for p in files:
        stories, words = parse_newsletter(p)
        if not stories:
            continue
        link_english(stories, words)
        for s in stories:
            s["topics"] = classify(s, tax)
            s["entities"] = extract_entities(s, ent)
            if not s["topics"]:
                note_pending(s, tax)
        atoms.extend(stories)
        if inject_anchors(p):
            anchored += 1

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
