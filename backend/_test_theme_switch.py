#!/usr/bin/env python3
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_HTML = os.path.join(ROOT, "public", "taiwan-exhibition-map.html")


class ThemeSwitchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(MAP_HTML, encoding="utf-8") as fh:
            cls.html = fh.read()

    def test_warm_dark_switch_is_available_on_desktop_and_mobile(self):
        self.assertGreaterEqual(self.html.count('data-theme-toggle'), 2)
        self.assertIn('class="theme-switch"', self.html)
        self.assertIn('class="theme-switch mobile-theme-switch"', self.html)
        self.assertIn('aria-pressed="false"', self.html)

    def test_theme_choice_is_persisted(self):
        self.assertIn("const THEME_STORAGE_KEY='acg-map-theme'", self.html)
        self.assertIn('localStorage.setItem(THEME_STORAGE_KEY,value)', self.html)
        self.assertIn('localStorage.getItem("acg-map-theme")', self.html)

    def test_dark_theme_has_explicit_visual_overrides(self):
        self.assertIn('html[data-theme="dark"]{', self.html)
        self.assertIn('--bg:#0d1016', self.html)
        self.assertIn('html[data-theme="dark"] .editorial-home', self.html)
        self.assertIn('html[data-theme="dark"] .results-mode .discover-list', self.html)
        self.assertIn('html[data-theme="dark"] .mobile-top', self.html)

    def test_default_remains_warm(self):
        self.assertIn('<meta name="theme-color" content="#f7f3ed" id="themeColorMeta">', self.html)
        self.assertIn('var theme="warm"', self.html)


if __name__ == '__main__':
    unittest.main()
