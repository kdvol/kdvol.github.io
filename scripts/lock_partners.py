#!/usr/bin/env python3
"""거래처 제안서를 진짜로 잠근다.

기존 게이트는 겉치레였다 — 액세스 코드가 소스에 평문으로 박혀 있고(ACCESS_CODE),
제안서 본문도 같은 파일에 그대로 들어 있었다. 주소만 알면 curl 한 번으로
거래처별 단가가 전부 읽혔다. 다른 거래처의 단가를 서로 볼 수 있는 상태였다.

GitHub Pages는 정적 호스팅이라 서버 인증을 붙일 수 없다. 대신 본문 자체를
AES-256-GCM으로 암호화해 둔다. 코드를 모르면 페이지에 남는 건 의미 없는
바이트뿐이고, 복호화 실패는 GCM 인증 태그가 잡는다.

  키 유도: PBKDF2-SHA256, 210,000회 (OWASP 2023 권고치)
  암호화 : AES-256-GCM (96bit IV, 128bit 태그)
  페이지 : salt + iv + ciphertext(base64)만 남고 코드는 어디에도 없다

사용:
  python3 scripts/lock_partners.py                # 전체 재잠금
  python3 scripts/lock_partners.py partners/KIM   # 하나만
"""

import base64
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITERATIONS = 210_000
MARK = "<!-- soonsal:locked -->"

# 잠글 대상과 실제 액세스 코드(원본 페이지에 박혀 있던 값 그대로).
# 코드는 결과물에 들어가지 않는다 — 여기서 키만 만들고 버린다.
# 한 페이지에 코드가 여러 개면 전부 적는다. 내용은 한 번만 암호화하고 코드별로
# 그 키를 감싸므로(키 래핑) 코드가 늘어도 파일이 커지지 않는다.
TARGETS = {
    "partners/index.html": ["soonsal2026", "soonsalbiz26"],
    "partners/salesforce/index.html": ["salesforceads2026"],
    "partners/KIM/index.html": ["soonsal2026"],
}


def _derive(code: str, salt: bytes) -> bytes:
    import hashlib
    return hashlib.pbkdf2_hmac("sha256", code.encode(), salt, ITERATIONS, dklen=32)


def _encrypt(plain: str, codes):
    """내용은 임의 키로 한 번 암호화하고, 그 키를 코드마다 따로 감싼다(키 래핑).

    코드별로 본문을 통째로 다시 암호화하면 220KB짜리가 코드 수만큼 늘어난다.
    래핑하면 코드가 몇 개든 늘어나는 건 한 줄(76바이트)뿐이다.
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    b64 = lambda b: base64.b64encode(b).decode()

    ckey, iv = AESGCM.generate_key(bit_length=256), os.urandom(12)
    ct = AESGCM(ckey).encrypt(iv, plain.encode(), None)

    keys = []
    for code in codes:
        salt, kiv = os.urandom(16), os.urandom(12)
        wrapped = AESGCM(_derive(code, salt)).encrypt(kiv, ckey, None)
        keys.append({"s": b64(salt), "i": b64(kiv), "k": b64(wrapped)})
    return {"i": b64(iv), "c": b64(ct), "n": ITERATIONS, "keys": keys}


UNLOCK_JS = """
<script>
// 본문은 암호화돼 있다. 코드가 맞아야 복호화되고, 틀리면 GCM 인증 태그에서 걸린다.
// 페이지 어디에도 코드는 없다 — 무차별 대입 말고는 열 방법이 없고, PBKDF2 210,000회가
// 그 비용을 올린다.
(function () {
  var P = %%PAYLOAD%%;
  var b2a = function (s) { return Uint8Array.from(atob(s), function (c) { return c.charCodeAt(0); }); };

  async function unlock(code) {
    var enc = new TextEncoder();
    var base = await crypto.subtle.importKey('raw', enc.encode(code), 'PBKDF2', false, ['deriveKey']);
    // 코드가 여러 개일 수 있다 — 맞는 것 하나가 내용 키를 풀어준다
    for (var j = 0; j < P.keys.length; j++) {
      var e = P.keys[j];
      try {
        var kek = await crypto.subtle.deriveKey(
          { name: 'PBKDF2', salt: b2a(e.s), iterations: P.n, hash: 'SHA-256' },
          base, { name: 'AES-GCM', length: 256 }, false, ['decrypt']);
        var raw = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: b2a(e.i) }, kek, b2a(e.k));
        var ck = await crypto.subtle.importKey('raw', raw, 'AES-GCM', false, ['decrypt']);
        var plain = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: b2a(P.i) }, ck, b2a(P.c));
        return { html: new TextDecoder().decode(plain), idx: j };
      } catch (err) { /* 다음 코드 */ }
    }
    throw new Error('bad code');
  }

  function reveal() {
    // 페이지마다 공개 방식이 다르다(style.display / classList) — 양쪽 다 맞춘다
    var d = document.getElementById('deck'), g = document.getElementById('gate');
    if (d) { d.style.display = ''; d.classList.add('visible'); }
    if (g) { g.classList.add('hidden'); g.style.display = 'none'; }
  }

  window.ssUnlock = async function (code, onOk, onFail) {
    try {
      var r = await unlock((code || '').trim());
      document.getElementById('deck').innerHTML = r.html;
      window.ssCodeIdx = r.idx;        // 유입 경로 라벨용(어느 코드로 열었는지)
      reveal();
      try { sessionStorage.setItem('ss_pk', (code || '').trim()); } catch (e) {}
      if (onOk) onOk();
    } catch (e) { if (onFail) onFail(); }
  };

  // 게이트의 열람 버튼을 가로챈다. 원래 checkAccess는 평문 코드를 비교했다.
  window.addEventListener('DOMContentLoaded', function () {
    var err = document.getElementById('gate-error');
    window.checkAccess = function () {
      var el = document.getElementById('gate-password');
      var pw = el ? el.value : '';
      window.ssUnlock(pw, null, function () {
        if (err) { err.textContent = '액세스 코드가 올바르지 않습니다.'; err.style.display = 'block'; }
      });
    };
  });

  // 같은 탭에서는 다시 묻지 않는다(sessionStorage — 탭을 닫으면 사라진다)
  try {
    var saved = sessionStorage.getItem('ss_pk');
    if (saved) window.addEventListener('DOMContentLoaded', function () {
      window.ssUnlock(saved, null, function () { sessionStorage.removeItem('ss_pk'); });
    });
  } catch (e) {}
})();
</script>
"""


def _deck_span(html: str):
    """#deck 여는 태그 끝 위치와 짝이 맞는 닫는 태그 시작 위치."""
    m = re.search(r'<div[^>]*id="deck"[^>]*>', html)
    if not m:
        return None
    depth, pos = 1, m.end()
    tag = re.compile(r'</?div\b', re.I)
    while depth:
        t = tag.search(html, pos)
        if not t:
            return None
        depth += -1 if t.group(0).startswith('</') else 1
        pos = t.end()
        if depth == 0:
            return m.end(), t.start()
    return None


def lock_file(rel: str, codes) -> bool:
    path = ROOT / rel
    if not path.exists():
        print(f"  ⚠️ 없음: {rel}")
        return False
    html = path.read_text(encoding="utf-8")
    if MARK in html:
        print(f"  · 이미 잠김: {rel}")
        return False

    # 본문(#deck) 안쪽만 뽑아 암호화한다. 껍데기(헤드·스타일·게이트 UI)는 남긴다.
    # 정규식으로 닫는 태그를 찾으면 파일마다 구조가 달라 어긋난다 — div 깊이를 센다.
    span = _deck_span(html)
    if not span:
        print(f"  ⚠️ 본문 영역을 못 찾음: {rel}")
        return False
    open_end, close_start = span
    inner = html[open_end:close_start]
    payload = _encrypt(inner, codes)

    # 껍데기에서 본문을 들어내고, 평문 코드 검사를 암호화 해제로 바꾼다
    shell = html[:open_end] + html[close_start:]
    # 평문 코드를 전부 들어낸다 — 단수형·복수형 맵 양쪽 다
    shell = re.sub(r"const ACCESS_CODES?\s*=\s*\{.*?\}", "const ACCESS_CODES = {}", shell, flags=re.S)
    shell = re.sub(r"const ACCESS_CODE\s*=\s*'[^']*'", "const ACCESS_CODE = ''", shell)

    js = UNLOCK_JS.replace("%%PAYLOAD%%", json.dumps(payload))
    shell = shell.replace("</body>", MARK + "\n" + js + "\n</body>", 1)
    path.write_text(shell, encoding="utf-8")
    print(f"  🔒 {rel} — 본문 {len(inner):,}자, 코드 {len(codes)}개")
    return True


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    print("🔐 lock_partners: 제안서 본문 암호화")
    n = 0
    for rel, codes in TARGETS.items():
        if only and not rel.startswith(only.rstrip("/")):
            continue
        n += lock_file(rel, codes)
    print(f"   {n}개 처리")


if __name__ == "__main__":
    main()
