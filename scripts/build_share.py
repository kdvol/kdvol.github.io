#!/usr/bin/env python3
"""스토리 단위 공유 버튼 — plantree식 콘텐츠 세분화 공유.

각 뉴스레터 스토리(#story-N)에 그 스토리 딥링크를 공유하는 버튼을 붙인다.
모바일은 네이티브 공유 시트(카카오톡·메시지 등 설치앱 전부)를, 데스크톱은
링크 복사를 쓴다 — 앱 키·백엔드 불필요. 미디어 사이트의 확산(MAU) 장치.

generate_seo가 호출(멱등). story-title 뒤에 버튼을, </body> 앞에 JS/CSS를 1회 주입.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NL = ROOT / "newsletters" / "2026"

BTN = ('<button class="ss-share" type="button" onclick="ssShare(this)" '
       'aria-label="이 스토리 공유">🔗 공유</button>')

# story-title(태그 무관) 바로 뒤에 버튼 삽입
TITLE_RE = re.compile(r'(<(\w+) class="story-title"[^>]*>.*?</\2>)', re.S)

ASSETS = """<style>
.ss-share{float:right;margin:2px 0 0 8px;background:transparent;border:1px solid #d8d4c8;
color:#8a8578;font-size:11px;font-weight:600;padding:3px 10px;border-radius:14px;cursor:pointer;
line-height:1.4;transition:all .15s;font-family:inherit}
.ss-share:hover{border-color:#F07040;color:#F07040}
.ss-toast{position:fixed;left:50%;bottom:28px;transform:translateX(-50%);background:#222;color:#fff;
font-size:13px;padding:10px 18px;border-radius:8px;z-index:99999;box-shadow:0 4px 14px rgba(0,0,0,.3)}
</style><script>
function ssToast(m){var d=document.createElement('div');d.className='ss-toast';d.textContent=m;
document.body.appendChild(d);setTimeout(function(){d.remove();},1800);}
function ssShare(b){var s=b.closest('.story');if(!s)return;
var url=location.origin+location.pathname+(s.id?'#'+s.id:'');
var el=s.querySelector('.story-title');var t=(el?el.textContent:document.title).trim();
if(navigator.share){navigator.share({title:t,text:t,url:url}).catch(function(){});}
else if(navigator.clipboard){navigator.clipboard.writeText(url).then(function(){ssToast('링크가 복사됐어요');});}
else{ssToast(url);}}
</script>"""

BODY_RE = re.compile(r"</body>", re.I)


def main():
    n = 0
    for p in sorted(NL.glob("*.html")):
        if p.name == "index.html":
            continue
        html = p.read_text(encoding="utf-8", errors="replace")
        if "ss-share" in html:                       # 멱등
            continue
        new, cnt = TITLE_RE.subn(lambda m: m.group(1) + BTN, html)
        if cnt == 0:
            continue
        if BODY_RE.search(new):
            new = BODY_RE.sub(ASSETS + "</body>", new, count=1)
        else:
            new += ASSETS
        p.write_text(new, encoding="utf-8")
        n += 1
    print(f"🔗 share: 스토리 공유 버튼 주입 {n}개 뉴스레터")
    return n


if __name__ == "__main__":
    main()
