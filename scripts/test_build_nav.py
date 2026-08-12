#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

import build_nav


PAGE = '<html><head><style>.nav{overflow-x:auto}</style></head><body><div class="nav"><a href="/">old</a></div></body></html>'


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
                build_nav.ROOT = root
                self.assertEqual(3, build_nav.main())
                self.assertEqual(0, build_nav.main())

                morning = (root / "morning/2026/0812.html").read_text(encoding="utf-8")
                self.assertIn('<nav class="nav" aria-label="주요 메뉴">', morning)
                self.assertNotIn('<a href="/">홈</a>', morning)
                self.assertIn('<a href="/newsletters/">브리핑</a>', morning)
                self.assertIn('<a href="/morning/" class="active">모닝순살</a>', morning)
                self.assertIn('<a href="/topics/">주제별</a>', morning)
                self.assertIn('<details class="nav-more">', morning)
                self.assertIn('grid-template-columns:repeat(4,minmax(0,1fr))', morning)
                self.assertEqual(1, morning.count('id="soonsal-nav-v2"'))

                youtube = (root / "youtube/index.html").read_text(encoding="utf-8")
                self.assertIn('<details class="nav-more active">', youtube)
                self.assertIn('<a href="/youtube/" class="active">YouTube</a>', youtube)
        finally:
            build_nav.ROOT = original_root


if __name__ == "__main__":
    unittest.main()
