#!/usr/bin/env python3
"""C44 — 웹 페이지를 **혼자 서는 파일**로 만들고, 정말 서는지 검사한다.

KD 2026-08-20: *"같은 실수를 11번 반복 하는 건 토큰 낭비 & 너가 일을 제대로
하지 못 하고 있다는 거야."*

## 왜 열한 번 반복됐나

2026-08-20 하루에 같은 결의 사고가 열한 번 났다. 공통점이 하나다 —
**만든 사람이 자기가 만든 조건 하나에서만 확인했다.**

  · 데스크톱에서만 봤다      → 모바일에서 깨졌다 (`<source srcset>` 미치환)
  · 첫 배포만 봤다           → 재배포에서 깨졌다 (목록 그리드 닫는 태그)
  · 내 경로에서만 봤다        → 발행기 경로에서 안 돌았다 (관문 건너뜀)

그리고 이 파일이 있기 전엔 **통짜본 만드는 정규식을 매번 손으로 다시 썼다.**
어제 되던 게 오늘 빠진 이유가 그거다. 손으로 다시 쓰면 매번 다른 걸 빠뜨린다.

## 그래서 두 가지를 한다

  ① **한 자리에서** 심는다 — `src` · `srcset` · CSS `url()` 을 한꺼번에
  ② **심고 나서 검사한다** — 바깥을 가리키는 게 하나라도 남으면 **실패**

검사가 핵심이다. 심는 코드는 언제든 빠뜨릴 수 있지만, 검사가 있으면
빠뜨린 게 **보낸 뒤가 아니라 보내기 전에** 드러난다.

사용:
  python3 scripts/standalone.py <원본.html> <내보낼.html> --assets <자산루트>
  python3 scripts/standalone.py --check <파일.html>      # 검사만
"""

import argparse
import base64
import mimetypes
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ★ 심는 쪽과 검사하는 쪽이 **같은 조각**을 쓴다 (2026-08-20).
#   처음엔 둘을 따로 썼는데 쿼리 문자열(`?v=…`)에서 어긋났다 — 검사는 잡고
#   심기는 못 잡아서, 「검사가 실패하는데 고칠 방법이 없는」 꼴이 됐다.
#   같은 것을 두 번 쓰면 반드시 갈라진다.
_EXT = r"svg|png|jpg|jpeg|gif|webp"
_PATH = rf"/[^\"')\s]+\.(?:{_EXT})(?:\?[^\"')\s]*)?"

LOCAL_REF = re.compile(rf'(?:\b(?:src|srcset|href)="|url\()\s*({_PATH}|/[^"\')\s]+\.(?:css|js))')
ATTR = re.compile(rf'\b(src|srcset|href)="({_PATH})"')
CSSURL = re.compile(rf"url\(\s*['\"]?({_PATH})['\"]?\s*\)")


def _resolve(path: str, roots: list[Path]) -> Path | None:
    """`/chart/assets/x.svg?v=1` 을 실제 파일로."""
    clean = path.split("?")[0].split("#")[0].lstrip("/")
    for r in roots:
        p = r / clean
        if p.is_file():
            return p
    # 마지막 손 — 이름만 같은 파일을 자산 루트에서 찾는다
    name = Path(clean).name
    for r in roots:
        hit = next((q for q in r.rglob(name) if q.is_file()), None)
        if hit:
            return hit
    # ★ 빌드가 쓰는 이름 규칙을 안다 (2026-08-20).
    #   웹에는 `/chart/assets/<날짜>/<슬러그>-diagram[-mobile].svg` 로 나가지만
    #   빌드 산출물은 `diagrams/<슬러그>/web-diagram[-mobile].svg` 다.
    #   사이트에 복사되기 **전**(승인 전) 미리보기를 만들 땐 이 규칙이 필요하다.
    m = re.match(r"(.+?)-diagram(-mobile)?\.svg$", name)
    if m:
        slug, mob = m.group(1), "-mobile" if m.group(2) else ""
        for r in roots:
            q = next((x for x in r.rglob(f"diagrams/{slug}/web-diagram{mob}.svg")
                      if x.is_file()), None)
            if q:
                return q
    return None


def _uri(p: Path) -> str:
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def inline(html: str, roots: list[Path]) -> tuple[str, int, list[str]]:
    """바깥 자산을 파일 안으로 심는다. (결과, 심은 수, 못 찾은 것)"""
    got, missed = 0, []

    def one(path: str) -> str | None:
        nonlocal got
        f = _resolve(path, roots)
        if not f:
            missed.append(path)
            return None
        got += 1
        return _uri(f)

    def attr(m):
        u = one(m.group(2))
        return m.group(0) if u is None else f'{m.group(1)}="{u}"'

    def css(m):
        u = one(m.group(1))
        return m.group(0) if u is None else f'url("{u}")'

    html = ATTR.sub(attr, html)
    html = CSSURL.sub(css, html)
    return html, got, missed


def check(html: str) -> list[str]:
    """바깥을 가리키는 게 남았나. 남으면 그 파일은 혼자 못 선다."""
    left = []
    for m in LOCAL_REF.finditer(html):
        ref = m.group(1)
        # 사이트 안쪽 문서 링크는 괜찮다 — 이미지·스타일·스크립트만 본다
        left.append(ref)
    return sorted(set(left))


def strip_for_artifact(html: str, title: str) -> str:
    """아티팩트로 올릴 꼴 — 바깥 폰트를 걷고 골격을 벗긴다.

    아티팩트는 외부 호스트를 막는다. 폰트 링크를 그대로 두면 **조용히**
    다른 글꼴로 떨어진다 — 조용한 폴백은 금지다(21-12).
    """
    html = re.sub(r'<link[^>]+fonts\.(googleapis|gstatic)[^>]*>', "", html)
    # 사이트 스크립트(집계·설정)는 아티팩트에서 **어차피 못 뜬다.**
    #   그냥 두면 죽은 참조가 남아 검사가 늘 빨간불이 된다. 걷어낸다 —
    #   화면에 보이는 것과 무관하고, 남겨 두면 「왜 늘 실패하지」로 무뎌진다.
    html = re.sub(r'<script[^>]+src="/[^"]+"[^>]*>\s*</script>', "", html)
    m = re.search(r"<head[^>]*>(.*?)</head>.*?<body[^>]*>(.*)</body>", html, re.S)
    head, body = (m.group(1), m.group(2)) if m else ("", html)
    head = re.sub(r"<title>.*?</title>", "", head, flags=re.S)
    return f"<title>{title}</title>\n{head}{body}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path)
    ap.add_argument("out", type=Path, nargs="?")
    ap.add_argument("--assets", type=Path, action="append", default=[],
                    help="자산을 찾을 루트. 여러 번 줄 수 있다")
    ap.add_argument("--check", action="store_true", help="검사만 한다")
    ap.add_argument("--title", default="", help="아티팩트용 제목 — 주면 골격을 벗긴다")
    ARGS = ap.parse_args()

    html = ARGS.src.read_text(encoding="utf-8")

    if ARGS.check:
        left = check(html)
        if left:
            print(f"⛔ 바깥을 가리키는 게 {len(left)}개 남았다 — 혼자 못 선다")
            for r in left[:8]:
                print(f"   · {r}")
            return 1
        print("✅ 혼자 선다 — 바깥을 가리키는 게 없다")
        return 0

    if not ARGS.out:
        print("⛔ 내보낼 경로가 없다")
        return 2
    roots = [p.resolve() for p in (ARGS.assets or [ROOT])]
    html, got, missed = inline(html, roots)
    if ARGS.title:
        html = strip_for_artifact(html, ARGS.title)

    left = check(html)
    print(f"  심은 것 {got}개")
    if missed:
        print(f"  ⚠️ 못 찾은 것 {len(missed)}개: {', '.join(missed[:3])}")
    if left:
        # ★ 여기서 막는다. 보낸 뒤에 「안 보임」을 듣는 게 제일 비싸다.
        print(f"⛔ 바깥을 가리키는 게 {len(left)}개 남았다 — 안 내보낸다")
        for r in left[:8]:
            print(f"   · {r}")
        return 1
    ARGS.out.write_text(html, encoding="utf-8")
    print(f"✅ {ARGS.out} — 혼자 선다 ({len(html):,}자)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
