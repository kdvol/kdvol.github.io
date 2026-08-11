#!/usr/bin/env python3
"""방문·참여 데이터를 읽어 사이트를 스스로 고친다 — 사람이 대시보드를 안 봐도 되게.

/stats/ 는 "보면 알 수 있는" 화면이지 "보지 않아도 되는" 장치가 아니다. KD가 매일
대시보드를 열어 판단할 시간이 없으므로, 데이터가 곧바로 사이트에 반영되는 경로를 만든다.

이 스크립트가 실제로 바꾸는 것:
  1. content/signals.json     — 실제 조회·반응·읽음 기준의 인기/부진 신호 (아래 2·3의 입력)
  2. api/signals.json         — 챗(claude.ai 프로젝트)이 web_fetch로 읽는 공개 신호.
                                다음 뉴스레터 주제 선택에 데이터가 자동으로 흘러든다
  3. sitemap.xml 우선순위     — generate_seo.py가 signals.json을 읽어 적용
                                (sitemap은 매 빌드 새로 쓰이므로 밖에서 고치면 날아간다)
  4. docs/AUTO_IMPROVE.md     — 무엇을 왜 바꿨는지 누적 기록(사람이 나중에 훑어볼 용도)

의도적으로 하지 않는 것: 본문·제목 수정. 편집물의 문장은 사람이 쓴다. 자동화는
'무엇을 앞에 둘지'와 '무엇을 다음에 다룰지'까지만 관여한다.

키가 없으면 조용히 넘어간다. GitHub Actions에서 하루 1회 실행.
"""
import json
import os
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKER = os.environ.get("SOONSAL_WORKER", "https://soonsal-react.kd-d0a.workers.dev")
ATOMS = ROOT / "content" / "story_atoms.json"
SIGNALS = ROOT / "content" / "signals.json"
API_SIGNALS = ROOT / "api" / "signals.json"
LOG = ROOT / "docs" / "AUTO_IMPROVE.md"
KST = timezone(timedelta(hours=9))


def _get(path, timeout=30):
    req = urllib.request.Request(
        WORKER.rstrip("/") + path,
        headers={"Origin": "https://soonsal.com", "user-agent": "soonsal-improver/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def collect():
    """Worker에서 원자료를 모은다. 실패하면 None — 호출부가 조용히 종료."""
    try:
        return {
            "insights": _get("/insights?days=30"),
            "counts": _get("/counts"),
            "activity": _get("/activity"),
        }
    except Exception as e:
        print(f"⚠️ auto_improve: 데이터 수집 실패({type(e).__name__}) — 건너뜀")
        return None


def analyse(raw, atoms):
    """원자료 → 신호. 여기서 '무엇이 잘 읽혔나'를 스토리·주제·엔티티 단위로 환산."""
    ins = raw["insights"]
    views = {r["path"]: r["hits"] for r in ins.get("top", [])}
    total_views = sum(views.values()) or 1

    # 스토리별 반응 합
    react = {s: sum(v.values()) for s, v in (raw["counts"] or {}).items()}

    # 회차(=페이지) 단위 조회수를 그 회차의 스토리들에 배분하고,
    # 반응은 스토리에 직접 붙는다. 둘을 합쳐 '주목도'로 본다.
    by_story = {}
    for a in atoms:
        url = a.get("url", "")
        page = url.split("#")[0].replace("https://soonsal.com", "")
        v = views.get(page, 0)
        by_story[a["id"]] = {
            "title": a["title"], "date": a["date"], "url": url,
            "views": v, "react": react.get(a["id"], 0),
            "topics": a.get("topics", []), "entities": a.get("entities", []),
        }

    def score(s):
        # 반응은 조회보다 귀한 신호라 가중치를 크게 준다
        return s["views"] + s["react"] * 20

    ranked = sorted(by_story.values(), key=score, reverse=True)
    hot = [s for s in ranked if score(s) > 0][:12]

    # 주제·엔티티 단위 집계 — 다음 회차 주제 선택에 쓰는 신호
    topic_w, ent_w = defaultdict(int), defaultdict(int)
    for s in by_story.values():
        w = score(s)
        if not w:
            continue
        for t in s["topics"]:
            topic_w[t] += w
        for e in s["entities"]:
            ent_w[e] += w

    eng = defaultdict(int)
    for e in ins.get("engage", []):
        eng[e["kind"]] += e["n"]
    vis = ins.get("visitors", {}) or {}
    uniq = sum(d["uniq"] for d in ins.get("daily", [])) or 1

    return {
        "generated": datetime.now(KST).isoformat(timespec="seconds"),
        "window_days": ins.get("days", 30),
        "traffic": {
            "views_30d": total_views,
            "people_7d": vis.get("active7", 0),
            "repeat_rate": round((vis.get("repeat_v", 0) / (vis.get("total") or 1)) * 100),
            "read_rate": round(eng["read"] / uniq * 100),
            "react_rate": round(eng["react"] / uniq * 100),
            "comment": eng.get("comment", 0),
        },
        "hot_stories": [{"id": next(k for k, v in by_story.items() if v is s),
                         "title": s["title"], "date": s["date"], "url": s["url"],
                         "views": s["views"], "react": s["react"]} for s in hot],
        "hot_topics": sorted(topic_w, key=topic_w.get, reverse=True)[:6],
        "hot_entities": sorted(ent_w, key=ent_w.get, reverse=True)[:10],
        "refs": {r["src"]: r["n"] for r in ins.get("refs", [])},
        "top_paths": [{"path": r["path"], "hits": r["hits"]} for r in ins.get("top", [])[:12]],
    }


def write_api(sig, atoms):
    """챗이 읽는 공개 신호. 다음 브리핑 주제 선택에 데이터가 흘러들게 하는 통로."""
    names = {}
    ents = json.loads((ROOT / "scripts" / "entities.json").read_text(encoding="utf-8"))
    for e in ents["entities"]:
        names[e["slug"]] = e["name"]

    out = {
        "generated": sig["generated"][:10],
        "usage": (
            "순살브리핑 독자 반응 신호. 다음 회차 주제를 고를 때 참고한다. "
            "hot_entities/hot_topics는 최근 30일 실제 조회·반응 기준으로 독자가 반응한 "
            "대상이다. 이미 다룬 걸 반복하라는 뜻이 아니라, 후속·심화가 먹힐 영역이라는 뜻. "
            "cold는 최근 노출 대비 반응이 약했던 주제 — 같은 각도로 또 쓰지 말 것."
        ),
        "traffic": sig["traffic"],
        "hot_entities": [{"slug": s, "name": names.get(s, s)} for s in sig["hot_entities"]],
        "hot_topics": sig["hot_topics"],
        "hot_stories": [{"title": h["title"], "url": h["url"], "react": h["react"]}
                        for h in sig["hot_stories"][:6]],
        "refs": sig["refs"],
    }
    API_SIGNALS.parent.mkdir(exist_ok=True)
    API_SIGNALS.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")),
                           encoding="utf-8")
    return out


def append_log(sig, api):
    LOG.parent.mkdir(exist_ok=True)
    if not LOG.exists():
        LOG.write_text(
            "# 자동 개선 기록\n\n"
            "`scripts/auto_improve.py`가 방문·반응 데이터를 읽고 매일 남기는 기록.\n"
            "사람이 대시보드를 열지 않아도 되도록, 무엇을 왜 바꿨는지 여기에 쌓인다.\n"
            "본문·제목은 자동으로 고치지 않는다 — 노출 순서와 다음 주제 신호까지만.\n",
            encoding="utf-8")
    t = sig["traffic"]
    ents = ", ".join(e["name"] for e in api["hot_entities"][:5]) or "—"
    top = sig["hot_stories"][0]["title"][:40] if sig["hot_stories"] else "—"
    LOG.write_text(
        LOG.read_text(encoding="utf-8") +
        f"\n## {sig['generated'][:10]}\n\n"
        f"- 7일 방문 {t['people_7d']}명 · 재방문 {t['repeat_rate']}% · "
        f"읽음 {t['read_rate']}% · 반응 {t['react_rate']}% · 코멘트 {t['comment']}건\n"
        f"- 반응 몰린 스토리: {top}\n"
        f"- 다음 회차 신호(hot): {ents}\n",
        encoding="utf-8")


def main():
    raw = collect()
    if not raw:
        return 0
    atoms = json.loads(ATOMS.read_text(encoding="utf-8")) if ATOMS.exists() else []
    if not atoms:
        return 0

    sig = analyse(raw, atoms)
    SIGNALS.parent.mkdir(exist_ok=True)
    SIGNALS.write_text(json.dumps(sig, ensure_ascii=False, indent=1), encoding="utf-8")
    api = write_api(sig, atoms)
    append_log(sig, api)

    t = sig["traffic"]
    print(f"📈 auto_improve: 7일 {t['people_7d']}명 · 재방문 {t['repeat_rate']}% · "
          f"읽음 {t['read_rate']}% · hot {len(sig['hot_entities'])}개 → "
          f"signals.json (sitemap은 다음 빌드에 반영)")
    return 1


if __name__ == "__main__":
    main()
