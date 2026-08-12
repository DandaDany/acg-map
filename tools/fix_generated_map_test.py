from pathlib import Path

path=Path('backend/_test_map_ux.py')
text=path.read_text(encoding='utf-8')
old='        desktop_css = self.html[self.html.index(".desktop-map-card{"):self.html.index("html[data-theme="dark"] .home-filter-close")]\n'
new='        desktop_css = self.html[self.html.index(".desktop-map-card{"):self.html.index(\'html[data-theme="dark"] .home-filter-close\')]\n'
if text.count(old)!=1:
    raise RuntimeError(f'generated desktop css test line: expected 1 match, found {text.count(old)}')
path.write_text(text.replace(old,new,1),encoding='utf-8')
