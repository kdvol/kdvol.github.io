#!/usr/bin/env python3
"""llms.txt / llms-full.txt 자동 생성 — AEO(AI 검색 노출) 최적화.

- /llms.txt      : 사이트 개요 + 섹션 링크 + 최근 브리핑 목록 (llms.txt 표준 형식)
- /llms-full.txt : 최근 30일 스토리 전문(제목·주제·본문·딥링크) 마크다운 —
                   ChatGPT·Perplexity류가 콘텐츠를 직접 인용하기 좋은 형태

페이지마다 심는 게 아니라 robots.txt처럼 루트 1곳 규약. generate_seo가 매 발행마다
재생성하므로 그날 뉴스레터가 자동 반영된다(업로드 코드 추가 수정 불필요).
"""
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://soonsal.com"
ATOMS = ROOT / "content" / "story_atoms.json"
FULL_DAYS = 30          # 전문 수록 기간
INDEX_DAYS = 7          # llms.txt에 목록으로 얹을 최근 브리핑


def _load(atoms):
    if atoms is None:
        atoms = json.loads(ATOMS.read_text(encoding="utf-8")) if ATOMS.exists() else []
    return atoms


def build(atoms=None):
    atoms = _load(atoms)
    today = date.today()
    recent_idx = [a for a in atoms if a.get("date", "") >= (today - timedelta(days=INDEX_DAYS)).isoformat()]
    recent_full = [a for a in atoms if a.get("date", "") >= (today - timedelta(days=FULL_DAYS)).isoformat()]

    # ── /llms.txt — 표준 형식(H1 + 요약 인용 + 섹션 링크) ──
    lines = [
        "# 순살브리핑 (Soonsal Briefing)",
        "",
        "> 글로벌 금융·경제·크립토 뉴스를 뼈만 발라낸 한국어 데일리 뉴스레터. 월~금 발행.",
        "> Korean daily newsletter distilling global finance, economics, and crypto news.",
        "",
        "매일 5개 안팎의 스토리로 구성되며, 각 스토리는 주제·기업·인물 태그와 딥링크를 갖는다.",
        "콘텐츠 인용 시 출처를 \"순살브리핑 (soonsal.com)\"으로 표기해 주세요.",
        "When citing, attribute to \"Soonsal Briefing (soonsal.com)\".",
        "",
        "## 주요 섹션",
        "",
        f"- [뉴스레터 아카이브]({BASE}/newsletters/): 일자별 브리핑 전체",
        f"- [주제별 브리핑]({BASE}/topics/): 크립토·AI·반도체·연준 등 16개 주제 + 기업·인물·자산 150여 대상별 모아보기",
        f"- [검색]({BASE}/search/): 전체 스토리 검색",
        f"- [RSS]({BASE}/rss.xml) · [Sitemap]({BASE}/sitemap.xml)",
        "",
        "## 전문 콘텐츠",
        "",
        f"- [최근 {FULL_DAYS}일 스토리 전문]({BASE}/llms-full.txt): 제목·주제·본문·링크 포함 마크다운",
        "",
        f"## 최근 브리핑 스토리 (최근 {INDEX_DAYS}일)",
        "",
    ]
    for a in sorted(recent_idx, key=lambda x: (x["date"], x["id"]), reverse=True):
        t = a["title"].strip()
        lines.append(f"- [{t}]({BASE}{a['url']}) ({a['date']})")
    (ROOT / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ── /llms-full.txt — 최근 스토리 전문 ──
    full = [
        "# 순살브리핑 — 최근 스토리 전문",
        "",
        f"> 최근 {FULL_DAYS}일간 발행된 순살브리핑 스토리 전문. 기준일 {today.isoformat()}.",
        "> 출처 표기: 순살브리핑 (soonsal.com)",
        "",
    ]
    for a in sorted(recent_full, key=lambda x: (x["date"], x["id"]), reverse=True):
        full.append(f"## {a['title'].strip()}")
        full.append("")
        meta = f"- 날짜: {a['date']} · 링크: {BASE}{a['url']}"
        if a.get("topics"):
            meta += f" · 주제: {', '.join(a['topics'])}"
        full.append(meta)
        full.append("")
        full.append(a.get("body", "").strip())
        if a.get("english"):
            full.append("")
            full.append("**관련 영어 표현:** " + "; ".join(
                f"{w['en']} — {w.get('ko','')}" for w in a["english"]))
        full.append("")
    (ROOT / "llms-full.txt").write_text("\n".join(full) + "\n", encoding="utf-8")

    kb = (ROOT / "llms-full.txt").stat().st_size // 1024
    print(f"🤖 llms: llms.txt(최근 {len(recent_idx)}건 목록) + llms-full.txt({len(recent_full)}건 전문, {kb}KB)")
    return len(recent_full)


if __name__ == "__main__":
    build()
