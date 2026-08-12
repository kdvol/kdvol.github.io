#!/usr/bin/env python3
"""순살차트 도식(SVG)을 사양에서 그린다.

어제 것은 손으로 그렸다. 그런데 결과물을 뜯어보니 배치가 완전히 규칙적이다 —
캔버스 1080×860, 노드 높이 118, 한 줄에 1개(760폭) 또는 2개(430폭), 그 사이를
베지어 화살표가 잇고 라벨이 알약으로 얹힌다. 모션은 노드·엣지가 번갈아
0,1,2,3… 스텝을 받는다. 그러면 사람이 정할 건 '무엇이 무엇을 일으키는가'뿐이고
그리는 일은 기계가 하면 된다.

사양(dict):
  rows   [["A"], ["B","C"], ["D"]]   각 줄의 노드 글. 한 줄에 1~2개
  edges  ["라벨", "라벨", …]          줄 사이 화살표 라벨. rows보다 하나 적다
  dashed [2]                          점선으로 그릴 엣지 번호(해석·영향 경로)
  risk   True                         마지막 노드를 위험(주황)으로

가로판(1080)과 모바일판(720)을 같은 사양에서 뽑는다 — 두 벌을 손으로 맞추면
언젠가 한쪽만 고쳐진다.
"""

FONT = "Apple SD Gothic Neo,Malgun Gothic,Arial,sans-serif"
ACCENT = "#F07040"
BG = "#FAFAF7"
NODE_H = 118
STEP_MS = 830          # 스텝 간격. 어제 것과 같은 리듬
ACCENT_MS = 660        # 노드가 강조색을 먹는 시점


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _edge(x1, y1, x2, y2, label, dashed, step):
    """줄과 줄을 잇는 화살표. 라벨은 선 위 알약으로."""
    my = y1 + (y2 - y1) * 0.55
    d = f"M {x1:.1f} {y1:.1f} C {x1:.1f} {my:.1f}, {x2:.1f} {my:.1f}, {x2:.1f} {y2:.1f}"
    dash = ' stroke-dasharray="12 10"' if dashed else ""
    lx, ly = (x1 + x2) / 2, y1 + (y2 - y1) * 0.42
    w = max(144, len(label) * 20)
    return (
        f'<g class="motion-step motion-edge" data-motion-step="{step}"'
        f' style="--motion-delay:{step * STEP_MS - 415}ms">\n'
        f'<path d="{d}" fill="none" stroke="{ACCENT}" stroke-width="4"{dash}'
        f' marker-end="url(#arrow)"/>\n'
        f'<rect x="{lx - w / 2:.1f}" y="{ly:.1f}" width="{w}" height="36" rx="18" fill="{BG}"/>\n'
        f'<text x="{lx:.1f}" y="{ly + 27:.1f}" text-anchor="middle" font-family="{FONT}"'
        f' font-size="18" fill="#8B4B2C">{_esc(label)}</text>\n</g>\n')


def _node(x, y, w, text, step, risk=False):
    fill, stroke = ("#FFF4EF", ACCENT) if risk else ("#FFFFFF", "#E0DDD5")
    cls = "motion-step motion-node" + (" motion-risk" if risk else "")
    # 글이 길면 폰트를 줄인다 — 넘치느니 작은 게 낫다
    fs = 27 if len(text) <= 16 else (24 if len(text) <= 22 else 21)
    return (
        f'<g class="{cls}" data-motion-step="{step}"'
        f' style="--motion-delay:{step * STEP_MS}ms;'
        f'--motion-accent-delay:{step * STEP_MS + ACCENT_MS}ms">\n'
        f'<rect class="motion-node-shape" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}"'
        f' height="{NODE_H}" rx="22" fill="{fill}" stroke="{stroke}" stroke-width="3"'
        f' filter="url(#shadow)"/>\n'
        f'<text x="{x + w / 2:.1f}" y="{y + NODE_H / 2:.1f}" text-anchor="middle"'
        f' dominant-baseline="middle" font-family="{FONT}" font-size="{fs}"'
        f' font-weight="700" fill="#222222">{_esc(text)}</text>\n</g>\n')


def render(spec: dict, width: int = 1080) -> str:
    rows = spec["rows"]
    edges = spec.get("edges", [])
    dashed = set(spec.get("dashed", []))
    risk = spec.get("risk", True)

    height = 860
    pad = 72 if width > 900 else 40
    inner = width - pad * 2
    top, bottom = 70, 808            # 노드가 놓이는 세로 범위
    n = len(rows)
    gap = (bottom - top - NODE_H) / max(1, n - 1) if n > 1 else 0

    parts = []
    # 엣지를 먼저 그린다 — 노드가 위에 얹혀야 그림자가 산다
    for i in range(n - 1):
        y1 = top + gap * i + NODE_H
        y2 = top + gap * (i + 1)
        for a, ax in enumerate(_centers(rows[i], width, inner, pad)):
            for b, bx in enumerate(_centers(rows[i + 1], width, inner, pad)):
                if len(rows[i]) > 1 and len(rows[i + 1]) > 1 and a != b:
                    continue                      # 2:2는 같은 열끼리만
                lab = edges[i] if i < len(edges) else ""
                if isinstance(lab, list):
                    lab = lab[a] if a < len(lab) else lab[-1]
                parts.append(_edge(ax, y1, bx, y2, lab, i in dashed, i * 2 + 1))

    for i, row in enumerate(rows):
        y = top + gap * i
        wide = inner if len(row) == 1 else (inner - 32) / 2
        for j, txt in enumerate(row):
            x = pad if len(row) == 1 else pad + j * (wide + 32)
            is_last = (i == n - 1) and risk
            parts.append(_node(x, y, wide, txt, i * 2, is_last))

    steps = (n - 1) * 2 + 1
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"'
        f' viewBox="0 0 {width} {height}" class="morning-diagram'
        + ('' if width > 900 else ' morning-diagram-mobile')
        + f'" data-motion-orientation="TB" data-motion-steps="{steps}">\n'
        '<defs><filter id="shadow" x="-20%" y="-20%" width="140%" height="160%">'
        '<feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#111111"'
        ' flood-opacity=".09"/></filter>\n'
        f'<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8"'
        f' markerHeight="8" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{ACCENT}"/></marker></defs>\n'
        f'<rect width="{width}" height="{height}" fill="{BG}"/>\n'
        + "".join(parts)
        + f'<line x1="{pad}" y1="812" x2="{width - pad}" y2="812" stroke="#E8E8E0" stroke-width="2"/>\n'
        f'<text x="{pad}" y="842" font-family="{FONT}" font-size="17" fill="#888888">'
        '실선 = 확인된 연결 · 점선 = 해석/영향 경로</text>\n</svg>\n')


def _centers(row, width, inner, pad):
    if len(row) == 1:
        return [width / 2]
    w = (inner - 32) / 2
    return [pad + w / 2, pad + w + 32 + w / 2]
