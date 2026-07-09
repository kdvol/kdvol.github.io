#!/usr/bin/env python3
"""엔티티 자동 발굴 — 사전에 없는 고빈도 고유명사를 상시 관찰·추가.

매 빌드마다 story_atoms.json 을 훑어 현재 entities.json 어디에도 안 걸리는
영어 고유명사(기업·인물·자산·기관 후보)의 등장 빈도를 센다. 임계치를 넘으면:
  - ANTHROPIC_API_KEY 있음(워크플로): LLM이 slug/한글명/type/패턴(한글 별칭 포함)을
    지어 entities.json 에 자동 추가.
  - 키 없음(로컬): entities.json 의 `_pending` 에 후보를 쌓아만 둠(가시화).

사람이 빈도 분석을 수동으로 돌릴 필요가 없도록 하는 것이 목적. auto_evolve(주제)의
엔티티 버전. generate_seo.py 가 atomize 직후 호출.
"""
import json
import os
import re
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENT_PATH = Path(__file__).resolve().parent / "entities.json"
ATOMS_PATH = ROOT / "content" / "story_atoms.json"

DISCOVER_THRESHOLD = 8       # 영어 고유명사: 이 스토리 수 이상이면 후보
KO_THRESHOLD = 5             # 한글 고정밀 신호(이름+역할/영문괄호): 더 낮은 문턱
PROMOTE_MAX = 14             # 1회 빌드당 LLM 승격 상한

# 한글 후보 고정밀 추출 — 동음이의 오탐을 원천 차단하기 위해 강신호만.
# ① 이름+역할어(회장/CEO/창업자/투자자…)  ② 이름+영문괄호(손정의(Masayoshi Son))
_KO_ROLE = re.compile(r"([가-힣]{2,6})\s*(?:회장|대표|CEO|창업자|공동창업자|의장|"
                      r"CFO|CTO|최고경영자|투자자|억만장자|파운더|펀드매니저|매니저|총수)")
_KO_PAREN = re.compile(r"([가-힣]{2,10})\s*\([A-Z][A-Za-z][A-Za-z .·&]{1,}\)")
_KO_STOP = set("""대통령 정부 회사 시장 기업 업계 당국 위원회 부처 은행 증권 투자 자산 펀드
익명 관계자 전문가 애널리스트 임원 직원 고객 주주 소식통 내부자 이사회 경영진 창업 대표이사
미국 중국 일본 한국 유럽 그룹 지주 계열 본사 지사 국내 해외 글로벌 이번 지난 최근 당시 현재
기관 개인 공동 신임 초기 일반 헤지펀드 벤처 전문 기존 최대 유명 대형 소액 기타 외국인 대주주
소액주주 사모 국부 연기금 스타트업 창투 엔젤 전략 신규 주요 복수 다수 일부 전체 양대 국내외
워시 모건 신흥 성장 가치 기술주 성장주 우량 부실 신생 상장 비상장 공모 사내 외부 잠재 실질""".split())
MODEL = "claude-sonnet-5"
API_URL = "https://api.anthropic.com/v1/messages"

_PROPER_RE = re.compile(r"\b[A-Z][A-Za-z0-9][A-Za-z0-9.&-]{1,}\b")
# 고유명사가 아닌 흔한 대문자 토큰·개념어(엔티티 아님) 제외
_STOP = set("""The This That These Those When Where What Which While With Without And But
For Nor Not Neither Either After Before Its Their They Are Was Were Will Would Can Could
Should Has Have Had One Two Three All New Now Get Buy Sell Company Companies Market Markets
Price Model Models Data Fund Funds Corp Inc Ltd You Your His Her She Him Our About Over
Under Into From Than Then More Most Less Least Big Small High Low First Last Next Some
Many Much Very Just Even Open Close Weight Carry Trade Free Tax Dollar Rate Rates Deal
Deals Chief Board CEO CFO CTO COO IPO ETF ETFs GPU CPU AI ML LLM DeFi NFT DAO API SaaS
RWA KYC AML ATH AUM MMF PCE CPI GDP CLARITY GENIUS MiCA Act Bill Fear Greed Digital
Capital World Global Group Holdings Partners Ventures Fund Labs Protocol Network Chain
Coin Token Stable US USA UK EU UAE China Japan Korea Fed SEC IRS DOJ FBI But However
Meanwhile Yet Still Also Both Each Other Another Such Same Own Here There Where Why How
Q1 Q2 Q3 Q4 January February March April May June July August September October November
December Monday Tuesday Wednesday Thursday Friday
Strategy Clarity Financial American Liberty Extreme Truth Blue Asset Morgan Mythos HBM
YTD NAV EPS B2B LNG DRAM Swift IBIT BUIDL FBTC Brent Bitcoin Ethereum Solana Riot
Nigel Vanguard Wyoming Texas Europe Asia Africa India Taiwan Hormuz Series Vol Reserve
Treasury Street Wall Point Points Index Fear Greed Onchain Layer Mainnet Testnet""".split())


def _load_ent():
    return json.loads(ENT_PATH.read_text(encoding="utf-8"))


def _save_ent(ent):
    ent = {k: v for k, v in ent.items() if not k.startswith("_rx")}
    for e in ent["entities"]:
        e.pop("_rx", None)
    ENT_PATH.write_text(json.dumps(ent, ensure_ascii=False, indent=2), encoding="utf-8")


def discover(ent):
    """미등록 고유명사 후보를 {token: {count, examples}} 로 반환."""
    if not ATOMS_PATH.exists():
        return {}
    atoms = json.loads(ATOMS_PATH.read_text(encoding="utf-8"))
    patterns = [re.compile(e["pattern"]) for e in ent["entities"]]
    cand_docs = Counter()
    examples = {}
    is_ko = {}

    def add(key, disp, title, korean):
        cand_docs[key] += 1
        examples.setdefault(key, (disp, title))
        is_ko[key] = korean

    for a in atoms:
        text = f"{a['title']} {a['body']}"
        seen = set()
        # 영어 고유명사
        for m in _PROPER_RE.finditer(text):
            w = m.group(0)
            if w in _STOP or w.lower() in seen or len(w) < 3:
                continue
            if any(rx.search(w) for rx in patterns):
                continue
            seen.add(w.lower())
            add(w.lower(), w, a["title"], False)
        # 한글 고정밀 후보(이름+역할, 이름+영문괄호)
        for rx in (_KO_ROLE, _KO_PAREN):
            for m in rx.finditer(text):
                name = m.group(1).strip()
                if len(name) < 2 or name in _KO_STOP or ("ko:" + name) in seen:
                    continue
                if any(p.search(name) for p in patterns):
                    continue
                seen.add("ko:" + name)
                add("ko:" + name, name, a["title"], True)

    out = {}
    for tok, n in cand_docs.items():
        th = KO_THRESHOLD if is_ko[tok] else DISCOVER_THRESHOLD
        if n >= th:
            disp, ex = examples[tok]
            out[disp] = {"count": n, "example": ex, "ko": is_ko[tok]}
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["count"]))


def _promote_llm(cands, existing_slugs):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    lines = [f"- '{k}' (스토리 {v['count']}건, 예: {v['example']})" for k, v in cands.items()]
    prompt = (
        "한국 금융 뉴스레터에서 자주 등장하는데 엔티티 사전에 없는 고유명사 후보다(영어+한글 혼재). "
        "각각이 페이지를 만들 가치가 있는 실제 대상인지 판단하라. **기업뿐 아니라 유명 투자자·"
        "경영자·정치인 등 인물(person)도 반드시 포함**하라. 일반 개념어·약어·지명·직책은 제외.\n\n"
        f"기존 slug(중복 금지): {sorted(existing_slugs)}\n\n"
        f"후보:\n" + "\n".join(lines) + "\n\n"
        "JSON 배열만 출력. 각 원소: "
        '{"slug":"영문-kebab","name":"한글명","type":"company|person|asset|institution",'
        '"pattern":"한글|영문 별칭 정규식(|)"}. \n'
        "★패턴 주의: 한글 이름이 흔한 단어와 겹치면 반드시 정밀하게. 예) '버리'는 동사 '버리다'와 "
        "겹치므로 '마이클\\\\s?버리|Burry'처럼, '우드'는 'wood'와 겹치므로 '캐시\\\\s?우드|Cathie Wood'처럼 "
        "성+이름 전체나 영문을 써라. 성씨/약어 단독 매칭 금지. "
        "실제 대상이 아니면 제외. 없으면 []."
    )
    body = json.dumps({"model": MODEL, "max_tokens": 1500,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "content-type": "application/json", "x-api-key": key,
        "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=50) as r:
            data = json.loads(r.read())
        text = "".join(b.get("text", "") for b in data.get("content", []))
        m = re.search(r"\[.*\]", text, re.S)
        return json.loads(m.group(0)) if m else []
    except Exception as e:
        print(f"⚠️ entity_discovery LLM 실패(무시): {type(e).__name__}")
        return None


def main():
    ent = _load_ent()
    cands = discover(ent)
    ent["_pending"] = cands                      # 항상 최신 후보 가시화
    if not cands:
        _save_ent(ent)
        return 0
    existing = {e["slug"] for e in ent["entities"]}
    top = dict(list(cands.items())[:PROMOTE_MAX])
    proposals = _promote_llm(top, existing)
    if not proposals:
        _save_ent(ent)                            # 키 없음 → 후보만 축적
        print(f"ℹ️ entity_discovery: 미등록 고빈도 후보 {len(cands)}건 대기(_pending)")
        return 0
    added = []
    for p in proposals:
        if not all(k in p for k in ("slug", "name", "type", "pattern")):
            continue
        if p["slug"] in existing:
            continue
        try:
            re.compile(p["pattern"])
        except re.error:
            continue
        ent["entities"].append({"slug": p["slug"], "name": p["name"],
                                "type": p["type"], "pattern": p["pattern"]})
        existing.add(p["slug"])
        added.append(p["name"])
    # 승격된 것은 후보에서 제거
    for p in proposals:
        rx = None
        try:
            rx = re.compile(p.get("pattern", "(?!)"))
        except re.error:
            continue
        for k in list(ent["_pending"]):
            if rx.search(k):
                ent["_pending"].pop(k, None)
    _save_ent(ent)
    if added:
        print(f"🌱 entity_discovery: 새 엔티티 {len(added)}개 자동 추가 — {', '.join(added)}")
    return len(added)


if __name__ == "__main__":
    main()
