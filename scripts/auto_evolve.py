#!/usr/bin/env python3
"""주제 분류 사전 자동 진화.

atomize가 축적한 `_pending`(어떤 주제에도 안 걸린 스토리 라벨)을 검사해,
같은 성격의 라벨이 임계치 이상 반복되면 새 주제로 승격한다. 승격 판단·네이밍·
패턴 생성은 LLM 1회 호출(ANTHROPIC_API_KEY, 워크플로에 존재). 키가 없으면
아무 것도 하지 않고 조용히 넘어간다 — 로컬에서도 빌드가 깨지지 않음.

사람이 topics_taxonomy.json 을 직접 만질 필요가 전혀 없도록 하는 것이 목적.
generate_seo.py 가 atomize 다음, build_topics 앞에서 호출.
"""
import json
import os
import re
import urllib.request
from pathlib import Path

TAX_PATH = Path(__file__).resolve().parent / "topics_taxonomy.json"
PROMOTE_THRESHOLD = 4          # 미매칭 라벨이 이 횟수 이상 쌓이면 승격 후보
MODEL = "claude-sonnet-5"
API_URL = "https://api.anthropic.com/v1/messages"


def _load():
    return json.loads(TAX_PATH.read_text(encoding="utf-8"))


def _save(tax):
    TAX_PATH.write_text(json.dumps(tax, ensure_ascii=False, indent=2), encoding="utf-8")


def _candidates(tax):
    return {k: v for k, v in tax.get("_pending", {}).items()
            if v.get("count", 0) >= PROMOTE_THRESHOLD}


def _call_llm(cands, existing_slugs):
    """LLM에 승격 후보를 주고 새 주제 정의(JSON 배열)를 받는다."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    lines = [f"- 라벨 '{k}' (스토리 {v['count']}건): 예시 {v.get('examples', [])}"
             for k, v in cands.items()]
    prompt = (
        "너는 한국 금융 뉴스레터의 주제 분류 체계를 관리한다. 아래는 기존 주제 어디에도 "
        "속하지 않아 누적된 스토리 섹션 라벨들이다. 이 중 하나의 일관된 주제로 묶을 만한 것이 "
        "있으면 새 주제를 정의하라.\n\n"
        f"기존 주제 slug(중복 금지): {sorted(existing_slugs)}\n\n"
        f"누적 라벨:\n" + "\n".join(lines) + "\n\n"
        "JSON 배열만 출력. 각 원소: "
        '{"slug":"영문-kebab", "name":"한글명", "emoji":"1글자", '
        '"label_pattern":"대문자 정규식 대안(|)", "content_pattern":"한글 키워드 정규식(|)"}. '
        "승격할 게 없으면 빈 배열 []. 억지로 만들지 말 것 — 진짜 반복되는 뚜렷한 주제만."
    )
    body = json.dumps({
        "model": MODEL, "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "content-type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
    })
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            data = json.loads(r.read())
        text = "".join(b.get("text", "") for b in data.get("content", []))
        m = re.search(r"\[.*\]", text, re.S)
        return json.loads(m.group(0)) if m else []
    except Exception as e:
        print(f"⚠️ auto_evolve LLM 호출 실패(무시): {type(e).__name__}")
        return None


def main():
    tax = _load()
    cands = _candidates(tax)
    if not cands:
        return 0
    existing = {t["slug"] for t in tax["topics"]}
    proposals = _call_llm(cands, existing)
    if not proposals:                       # 키 없음 or 승격 없음 → 조용히 유지
        if proposals is None:
            print(f"ℹ️ auto_evolve: 승격 후보 {len(cands)}건 대기(키 없음, 사전 유지)")
        return 0
    added = []
    for p in proposals:
        if not all(k in p for k in ("slug", "name", "emoji")):
            continue
        if p["slug"] in existing:
            continue
        tax["topics"].append({
            "slug": p["slug"], "name": p["name"], "emoji": p["emoji"],
            "label_pattern": p.get("label_pattern", ""),
            "content_pattern": p.get("content_pattern", ""),
        })
        existing.add(p["slug"])
        added.append(p["name"])
        # 승격된 라벨은 _pending에서 제거
        for k in list(tax.get("_pending", {})):
            if p.get("label_pattern") and re.search(p["label_pattern"], k, re.I):
                tax["_pending"].pop(k, None)
    if added:
        _save(tax)
        print(f"🌱 auto_evolve: 새 주제 {len(added)}개 자동 추가 — {', '.join(added)}")
    return len(added)


if __name__ == "__main__":
    main()
