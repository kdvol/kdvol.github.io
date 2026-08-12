#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

import build_nav


PAGE = '<html><head><style>.nav{overflow-x:auto}</style></head><body><div class="nav"><a href="/">old</a></div></body></html>'
PRESTYLED_PAGE = '<html><head><style>.nav-more>summary{display:flex}</style></head><body><div class="nav"><a href="/">old</a></div></body></html>'


class BuildNavTest(unittest.TestCase):
    def test_sitewide_nav_is_compact_mobile_safe_and_idempotent(self):
        original_root = build_nav.ROOT
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                for rel in ("index.html", "morning/2026/0812.html", "youtube/index.html"):
                    path = root / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(PAGE, encoding="utf-8")
                topics = root / "topics/index.html"
                topics.parent.mkdir(parents=True, exist_ok=True)
                topics.write_text(PRESTYLED_PAGE, encoding="utf-8")
                build_nav.ROOT = root
                self.assertEqual(4, build_nav.main())
                self.assertEqual(0, build_nav.main())

                morning = (root / "morning/2026/0812.html").read_text(encoding="utf-8")
                self.assertIn('<nav class="nav" aria-label="주요 메뉴">', morning)
                self.assertNotIn('<a href="/">홈</a>', morning)
                self.assertIn('<a href="/newsletters/">브리핑</a>', morning)
                self.assertIn('<a href="/morning/" class="active">모닝순살</a>', morning)
                self.assertIn('<a href="/topics/">주제별</a>', morning)
                self.assertIn('<a href="/school/" class="nav-desktop-link">스쿨</a>', morning)
                self.assertIn('<a href="/advertise/" class="nav-desktop-link biz">광고 문의</a>', morning)
                self.assertIn('<details class="nav-more">', morning)
                self.assertIn('<section class="nav-menu" aria-label="추가 메뉴"><a href="/cardnews/">카드뉴스</a>', morning)
                self.assertIn('<a href="/talk/">순살톡</a>', morning)
                self.assertIn('<a href="/school/" class="nav-mobile-only">스쿨</a>', morning)
                self.assertIn('<a href="/advertise/" class="nav-mobile-only biz">광고 문의</a>', morning)
                self.assertIn('grid-template-columns:repeat(5,minmax(0,1fr))', morning)
                self.assertIn('.nav>a.nav-desktop-link{display:none}', morning)
                self.assertEqual(1, morning.count('id="soonsal-nav-v2"'))
                self.assertEqual(1, morning.count('id="soonsal-nav-visibility-v3"'))

                topics_html = topics.read_text(encoding="utf-8")
                self.assertNotIn('id="soonsal-nav-v2"', topics_html)
                self.assertEqual(1, topics_html.count('id="soonsal-nav-visibility-v3"'))
                self.assertGreaterEqual(topics_html.count('.nav-more>summary'), 1)

                youtube = (root / "youtube/index.html").read_text(encoding="utf-8")
                self.assertIn('<details class="nav-more active">', youtube)
                self.assertIn('<a href="/youtube/" class="active">YouTube</a>', youtube)

                talk = root / "talk/index.html"
                talk.parent.mkdir(parents=True, exist_ok=True)
                talk.write_text(PAGE, encoding="utf-8")
                self.assertEqual(1, build_nav.main())
                talk_html = talk.read_text(encoding="utf-8")
                self.assertIn('<details class="nav-more">', talk_html)
                self.assertIn('<a href="/talk/" class="active">순살톡</a>', talk_html)

                school = root / "school/index.html"
                school.parent.mkdir(parents=True, exist_ok=True)
                school.write_text(PAGE, encoding="utf-8")
                self.assertEqual(1, build_nav.main())
                school_html = school.read_text(encoding="utf-8")
                self.assertIn('<a href="/school/" class="nav-desktop-link active">스쿨</a>', school_html)
                self.assertIn('<details class="nav-more mobile-active">', school_html)
                self.assertIn('<a href="/school/" class="nav-mobile-only active">스쿨</a>', school_html)
                self.assertEqual(0, build_nav.main())
        finally:
            build_nav.ROOT = original_root


if __name__ == "__main__":
    unittest.main()
