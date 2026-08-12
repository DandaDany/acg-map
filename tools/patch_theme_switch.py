from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'public' / 'taiwan-exhibition-map.html'
MAP_TEST = ROOT / 'backend' / '_test_map_ux.py'
THEME_TEST = ROOT / 'backend' / '_test_theme_switch.py'
DECISION = ROOT / 'decision.md'

text = HTML.read_text(encoding='utf-8')


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 match, found {count}')
    text = text.replace(old, new, 1)


# Apply the saved choice before paint so the page does not flash warm first.
replace_once(
    '<meta name="theme-color" content="#0f141d">',
    '<meta name="theme-color" content="#f7f3ed" id="themeColorMeta">\n'
    '<script id="themeBootstrap">(function(){var theme="warm";try{if(localStorage.getItem("acg-map-theme")==="dark")theme="dark";}catch(e){}document.documentElement.dataset.theme=theme;}());</script>',
    'theme bootstrap',
)

THEME_CSS = r'''
/* ===== Warm / dark theme switch ===== */
.editorial-actions{display:flex;align-items:center;gap:8px}
.theme-switch{position:relative;width:54px;height:30px;flex:none;padding:2px;border:1px solid var(--line);border-radius:999px;background:#fff;color:var(--muted);cursor:pointer;box-shadow:0 5px 16px rgba(70,52,38,.07)}
.theme-switch:focus-visible{outline:2px solid var(--accent2);outline-offset:2px}
.theme-switch-track{display:block;position:relative;width:100%;height:100%;border-radius:999px;background:#f2eae3;transition:background .18s ease}
.theme-switch-icon{position:absolute;z-index:1;top:50%;font-size:12px;line-height:1;transform:translateY(-50%);transition:opacity .18s ease}
.theme-switch-sun{left:6px;color:#c95741;opacity:.95}
.theme-switch-moon{right:6px;color:#6e625a;opacity:.55}
.theme-switch-knob{position:absolute;z-index:2;top:2px;left:2px;width:22px;height:22px;border-radius:50%;background:#fff;box-shadow:0 2px 7px rgba(70,52,38,.2);transition:transform .2s ease,background .2s ease}
html[data-theme="dark"] .theme-switch{border-color:#3a4558;background:#111722;box-shadow:0 5px 16px rgba(0,0,0,.24)}
html[data-theme="dark"] .theme-switch-track{background:#242d3e}
html[data-theme="dark"] .theme-switch-sun{opacity:.45}
html[data-theme="dark"] .theme-switch-moon{color:#dbe6f7;opacity:1}
html[data-theme="dark"] .theme-switch-knob{background:#eef2f8;transform:translateX(24px)}
.mobile-theme-switch{margin-right:1px}

html[data-theme="dark"]{
  --bg:#0d1016;--panel:#151a24;--panel-2:#1b2230;--card:#1c2330;--line:#2a3344;
  --text:#eef2f8;--muted:#98a6ba;--accent:#ff6469;--accent2:#65a2ff;
  --free:#67e8f9;--paid:#f9a8d4;--ongoing:#6ee7b7;--upcoming:#9ec1ff;
  color-scheme:dark
}
html[data-theme="dark"],html[data-theme="dark"] body,html[data-theme="dark"] #app{background:#0d1016;color:var(--text)}
html[data-theme="dark"] .filter-pane,html[data-theme="dark"] .discover-pane{background:var(--panel);border-color:var(--line)}
html[data-theme="dark"] .searchbox{border-color:var(--line);background:#101620;box-shadow:0 8px 26px rgba(0,0,0,.22)}
html[data-theme="dark"] .searchbox input{color:var(--text)}
html[data-theme="dark"] .search-suggestions{border-color:var(--line);background:#131925;box-shadow:0 18px 46px rgba(0,0,0,.38)}
html[data-theme="dark"] .search-option:hover,html[data-theme="dark"] .search-option.active,html[data-theme="dark"] .filter-category:hover,html[data-theme="dark"] .filter-category.open,html[data-theme="dark"] .filter-option:hover:not(:disabled),html[data-theme="dark"] .filter-option.selected{background:#242d3e}
html[data-theme="dark"] .filter-detail{border-color:var(--line);background:#171d28;box-shadow:20px 0 42px rgba(0,0,0,.3)}
html[data-theme="dark"] .filter-back:hover{background:#263044}
html[data-theme="dark"] .pin-legend{border-color:var(--line);background:#111722}
html[data-theme="dark"] .segmented{border-color:var(--line);background:#101620}
html[data-theme="dark"] .segmented button.active{background:#2b3650;color:var(--text)}
html[data-theme="dark"] .event-card{border-color:var(--line);background:var(--card);box-shadow:0 8px 26px rgba(0,0,0,.24)}
html[data-theme="dark"] .event-card.desktop-clickable:hover{border-color:#465674;box-shadow:0 12px 32px rgba(0,0,0,.3)}
html[data-theme="dark"] .media-frame{background:#0e121a}
html[data-theme="dark"] .media-placeholder{color:#596579;background:linear-gradient(145deg,#161d29,#0e121a)}
html[data-theme="dark"] .secondary-btn{border-color:var(--line);background:#151c28;color:var(--text)}
html[data-theme="dark"] .dialog-panel,html[data-theme="dark"] .mobile-filter-sheet,html[data-theme="dark"] .mobile-venue-card{border-color:var(--line);background:var(--panel)}
html[data-theme="dark"] .location-row,html[data-theme="dark"] .mobile-detail .location-row{border-color:var(--line);background:#111722}
html[data-theme="dark"] .action-btn{border-color:var(--line);background:#151d2a}
html[data-theme="dark"] .action-btn.primary{border-color:#3c6da8;background:#203c62;color:#cfe3ff}
html[data-theme="dark"] .popup-arrow{border-color:var(--line);background:#151d2a;color:#aab4c3}
html[data-theme="dark"] .toast{border-color:var(--line);background:#111722;color:var(--text)}
html[data-theme="dark"] .map-marker-toggle{border-color:rgba(255,255,255,.1);background:rgba(16,22,32,.94);box-shadow:0 8px 28px rgba(0,0,0,.28)}
html[data-theme="dark"] .map-marker-toggle button{color:#98a6ba}
html[data-theme="dark"] .map-marker-toggle button.active{background:#2b3650;color:#eef2f8}

html[data-theme="dark"] .editorial-home{background:linear-gradient(180deg,#151a24 0%,#0f141d 100%)}
html[data-theme="dark"] .editorial-brandbar{background:rgba(21,26,36,.94)}
html[data-theme="dark"] .editorial-brand small{color:#8694a8}
html[data-theme="dark"] .editorial-filter-trigger{border-color:var(--line);background:#151a24;color:#dce4ef}
html[data-theme="dark"] .editorial-filter-trigger:hover{border-color:#4d6382;color:#9ec1ff}
html[data-theme="dark"] .home-section{border-color:#2a3344}
html[data-theme="dark"] .home-section-head h1,html[data-theme="dark"] .home-section-head h2{color:#eef2f8}
html[data-theme="dark"] .home-hero-card{background:#111722;box-shadow:0 14px 38px rgba(0,0,0,.28)}
html[data-theme="dark"] .home-hero-card:hover{box-shadow:0 18px 44px rgba(0,0,0,.36)}
html[data-theme="dark"] .home-card-media{background:#111722}
html[data-theme="dark"] .home-placeholder{background:linear-gradient(145deg,#252e3d,#161d29);color:#8592a5}
html[data-theme="dark"] .home-nearby-prompt,html[data-theme="dark"] .home-nearby-row,html[data-theme="dark"] .home-nearby-empty,html[data-theme="dark"] .home-recent-card,html[data-theme="dark"] .home-empty{border-color:#2a3344;background:#171d28;box-shadow:0 8px 24px rgba(0,0,0,.18)}
html[data-theme="dark"] .home-nearby-row:hover,html[data-theme="dark"] .home-recent-card:hover{border-color:#465674;box-shadow:0 10px 28px rgba(0,0,0,.28)}
html[data-theme="dark"] .home-nearby-thumb,html[data-theme="dark"] .home-recent-media{background:#111722}
html[data-theme="dark"] .results-head{border-color:var(--line);background:rgba(21,26,36,.96)}
html[data-theme="dark"] .results-back{border-color:var(--line);background:#151d2a;color:var(--text)}
html[data-theme="dark"] .results-mode .discover-list{background:#0f141d}
html[data-theme="dark"] .results-mode .filter-pane{background:#151a24}
html[data-theme="dark"] .results-mode .discover-pane{background:#0f141d}
html[data-theme="dark"] .results-mode .event-card{border-color:#2a3344}
html[data-theme="dark"] .user-location-dot{border-color:#eef2f8;background:#ff6469}

html[data-theme="dark"] .mobile-top{border-color:#2a3344;background:rgba(21,26,36,.96)}
html[data-theme="dark"] .mobile-top-actions .icon-btn{color:#eef2f8}
html[data-theme="dark"] .mobile-search-panel{border-color:#2a3344;background:#151a24;box-shadow:0 16px 44px rgba(0,0,0,.38)}
html[data-theme="dark"] .mobile-search-close{background:#242d3e;color:#eef2f8}
html[data-theme="dark"] .mobile-tabs{border-color:#2a3344;background:rgba(15,19,27,.98)}
html[data-theme="dark"] .mobile-tab{color:#98a6ba}
html[data-theme="dark"] .mobile-tab.active{color:#ff7b80}
html[data-theme="dark"] .mobile-filter-sheet,html[data-theme="dark"] .mobile-venue-card{background:#151a24}
html[data-theme="dark"] .mobile-category:hover{background:#242d3e}
html[data-theme="dark"] .map-legend{background:rgba(16,22,32,.94)!important}
html[data-theme="dark"] .map-legend-item{color:#e6ecf5!important}
'''

replace_once(
    '\n@media(prefers-reduced-motion:reduce){',
    '\n' + THEME_CSS + '\n@media(prefers-reduced-motion:reduce){',
    'theme CSS insertion',
)

# Desktop: compact switch immediately beside Filter.
replace_once(
    '        <button class="editorial-filter-trigger" id="homeFilterButton" type="button" aria-label="開啟篩選">⌁ 篩選</button>',
    '        <div class="editorial-actions">\n'
    '          <button class="theme-switch" type="button" data-theme-toggle aria-pressed="false" aria-label="切換成黑色主題" title="切換成黑色主題"><span class="theme-switch-track" aria-hidden="true"><span class="theme-switch-icon theme-switch-sun">☀</span><span class="theme-switch-icon theme-switch-moon">☾</span><span class="theme-switch-knob"></span></span></button>\n'
    '          <button class="editorial-filter-trigger" id="homeFilterButton" type="button" aria-label="開啟篩選">⌁ 篩選</button>\n'
    '        </div>',
    'desktop theme switch',
)

# Mobile: same compact control sits with search/filter actions.
replace_once(
    '  <div class="mobile-top-actions">\n',
    '  <div class="mobile-top-actions">\n'
    '    <button class="theme-switch mobile-theme-switch" type="button" data-theme-toggle aria-pressed="false" aria-label="切換成黑色主題" title="切換成黑色主題"><span class="theme-switch-track" aria-hidden="true"><span class="theme-switch-icon theme-switch-sun">☀</span><span class="theme-switch-icon theme-switch-moon">☾</span><span class="theme-switch-knob"></span></span></button>\n',
    'mobile theme switch',
)

THEME_JS = r'''
const THEME_STORAGE_KEY='acg-map-theme';
function themeChoice(){return document.documentElement.dataset.theme==='dark'?'dark':'warm'}
function syncThemeControls(){
  const dark=themeChoice()==='dark';
  document.querySelectorAll('[data-theme-toggle]').forEach(button=>{
    button.setAttribute('aria-pressed',dark?'true':'false');
    const label=dark?'切換成暖白主題':'切換成黑色主題';
    button.setAttribute('aria-label',label);button.title=label;
  });
}
function applyThemeChoice(theme,persist=true){
  const value=theme==='dark'?'dark':'warm';
  document.documentElement.dataset.theme=value;
  const meta=document.getElementById('themeColorMeta');if(meta)meta.content=value==='dark'?'#0d1016':'#f7f3ed';
  if(persist){try{localStorage.setItem(THEME_STORAGE_KEY,value)}catch(error){}}
  syncThemeControls();
}
function toggleTheme(){applyThemeChoice(themeChoice()==='dark'?'warm':'dark')}
'''

replace_once(
    "let mobileVenueStartY=0;\n\nconst uiState={",
    "let mobileVenueStartY=0;\n\n" + THEME_JS + "\nconst uiState={",
    'theme JS helpers',
)

replace_once(
    '/* ===== Event wiring ===== */\n',
    "/* ===== Event wiring ===== */\n"
    "document.querySelectorAll('[data-theme-toggle]').forEach(button=>button.addEventListener('click',toggleTheme));\n"
    "applyThemeChoice(themeChoice(),false);\n",
    'theme event wiring',
)

HTML.write_text(text, encoding='utf-8')

# The old regression was intended to prevent a Save/Wishlist tab. Generic Chinese
# copy and generic storage assertions now conflict with the editorial heading and
# the theme preference, so keep the test scoped to the actual navigation feature.
map_test = MAP_TEST.read_text(encoding='utf-8')
old = '''        self.assertNotIn('>Save<', ui_html)\n        self.assertNotIn("想去", ui_html)\n        self.assertNotIn("收藏", ui_html)\n        self.assertNotIn("localStorage", ui_html)\n        self.assertNotIn("sessionStorage", ui_html)\n'''
new = '''        self.assertNotIn('>Save<', ui_html)\n        self.assertNotIn('data-tab="save"', ui_html)\n        self.assertNotIn('id="saveTab"', ui_html)\n        self.assertNotIn("收藏", ui_html)\n'''
if old not in map_test:
    raise RuntimeError('map UX regression block not found')
MAP_TEST.write_text(map_test.replace(old, new, 1), encoding='utf-8')

THEME_TEST.write_text(r'''#!/usr/bin/env python3
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
''', encoding='utf-8')

decision = DECISION.read_text(encoding='utf-8') if DECISION.exists() else ''
note = '''\n- 2026-08-12：Editorial C 介面提供暖白／黑色小型主題 switch。暖白為預設；使用者手動選擇會以 `localStorage` 的 `acg-map-theme` 保存。主題切換只改 UI visual chrome，不改活動資料、filter、selection、popup、cluster 或 map viewport state。\n'''
if 'acg-map-theme' not in decision:
    DECISION.write_text(decision.rstrip() + '\n' + note, encoding='utf-8')

print('Warm/dark theme switch patch applied')
