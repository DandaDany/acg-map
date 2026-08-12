from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'public' / 'taiwan-exhibition-map.html'
DECISION = ROOT / 'decision.md'
MAP_TEST = ROOT / 'backend' / '_test_map_ux.py'
OLD_TEST = ROOT / 'backend' / '_test_discover_intent_home.py'
NEW_TEST = ROOT / 'backend' / '_test_editorial_c_home.py'

text = HTML.read_text(encoding='utf-8')


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 match, found {count}')
    text = text.replace(old, new, 1)


def sub_once(pattern: str, repl: str, label: str, flags=0) -> None:
    global text
    new_text, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 regex match, found {count}')
    text = new_text


# ---------------------------------------------------------------------------
# Light editorial design system
# ---------------------------------------------------------------------------
replace_once(
    ':root{\n  --bg:#0d1016;--panel:#151a24;--panel-2:#1b2230;--card:#1c2330;--line:#2a3344;\n  --text:#eef2f8;--muted:#98a6ba;--accent:#ff6469;--accent2:#65a2ff;\n  --free:#67e8f9;--paid:#f9a8d4;--ongoing:#6ee7b7;--upcoming:#9ec1ff;\n  --sidebar:316px;--discover:clamp(340px,29vw,460px);--mobile-nav:66px\n}',
    ':root{\n  --bg:#f7f3ed;--panel:#fffaf5;--panel-2:#f4eee7;--card:#ffffff;--line:#e6ddd4;\n  --text:#2c211a;--muted:#776c63;--accent:#f06b52;--accent2:#e65f47;\n  --free:#147d74;--paid:#b44d73;--ongoing:#2e7d5b;--upcoming:#356eaa;\n  --sidebar:316px;--discover:clamp(340px,29vw,460px);--mobile-nav:66px\n}',
    'light theme variables'
)

# Remove the #91 quick-intent styles entirely.
sub_once(
    r'\.discover-intents\{.*?\.intent-count\{[^}]*\}\n',
    '',
    'remove old quick-intent CSS',
    re.S,
)

EDITORIAL_CSS = r'''
/* ===== Editorial C home ===== */
.desktop-shell.home-mode{grid-template-columns:minmax(560px,55%) minmax(0,45%)}
.desktop-shell.home-mode>.filter-pane{display:none}
.desktop-shell.home-mode>.discover-pane{grid-column:1}
.desktop-shell.home-mode>.map-pane{grid-column:2}
.home-filter-scrim{display:none;position:fixed;z-index:2040;inset:0;background:rgba(37,27,20,.24);backdrop-filter:blur(2px)}
body.home-filter-open .home-filter-scrim{display:block}
body.home-filter-open .desktop-shell.home-mode>.filter-pane{display:flex;position:fixed;z-index:2050;top:0;bottom:0;left:0;width:var(--sidebar);box-shadow:22px 0 60px rgba(55,40,28,.16)}
.home-filter-close{display:none;margin-left:auto}
body.home-filter-open .home-filter-close{display:grid}
body.home-filter-open .homebtn{display:none}

/* Light surfaces: home + results share one visual family. */
.filter-pane,.discover-pane{background:var(--panel)}
.searchbox{border-color:var(--line);background:rgba(255,255,255,.96);box-shadow:0 8px 26px rgba(70,52,38,.08)}
.searchbox input{color:var(--text)}
.search-suggestions{border-color:var(--line);background:#fff;box-shadow:0 18px 46px rgba(70,52,38,.14)}
.search-option:hover,.search-option.active,.filter-category:hover,.filter-category.open,.filter-option:hover:not(:disabled),.filter-option.selected{background:#f6eee8}
.filter-detail{border-color:var(--line);background:#fff;box-shadow:20px 0 42px rgba(70,52,38,.12)}
.filter-back:hover{background:#f6eee8}
.pin-legend{background:#fff;border-color:var(--line)}
.segmented{border-color:var(--line);background:rgba(255,255,255,.96)}
.segmented button.active{background:#fff0eb;color:var(--accent2);box-shadow:none}
.event-card{background:#fff;box-shadow:0 8px 26px rgba(70,52,38,.08)}
.event-card.desktop-clickable:hover{border-color:#e9b9aa;box-shadow:0 12px 32px rgba(70,52,38,.12)}
.media-frame{background:#f0e9e2}
.media-placeholder{color:#9d8f83;background:linear-gradient(145deg,#f5eee7,#ebe2da)}
.secondary-btn{border-color:var(--line);background:#fff;color:var(--text)}
.primary-btn{background:var(--accent);color:#fff}
.dialog-panel,.mobile-filter-sheet,.mobile-venue-card{background:#fff;border-color:var(--line)}
.location-row{background:#faf6f2;border-color:var(--line)}
.action-btn{background:#fff;border-color:var(--line)}
.action-btn.primary{border-color:#efb09f;background:#fff1ec;color:#b84f39}
.popup-arrow{border-color:var(--line);background:#fff;color:var(--muted)}
.toast{border-color:#ded4ca;background:#34271f;color:#fff}
.map-marker-toggle{border-color:rgba(42,33,26,.12);background:rgba(255,255,255,.96);box-shadow:0 8px 28px rgba(47,39,32,.16)}
.map-marker-toggle button{color:#685e56}
.map-marker-toggle button.active{background:#fff0eb;color:#c95741}

.editorial-home{min-height:0;flex:1;overflow-y:auto;overscroll-behavior:contain;padding:0 28px 48px;background:linear-gradient(180deg,#fffaf5 0%,#f8f3ed 100%);scrollbar-gutter:stable}
.editorial-home[hidden],.results-head[hidden],.discover-list[hidden]{display:none!important}
.editorial-brandbar{display:flex;position:sticky;z-index:30;top:0;align-items:center;justify-content:space-between;margin:0 -28px 16px;padding:22px 28px 14px;background:rgba(255,250,245,.94);backdrop-filter:blur(14px)}
.editorial-brand{color:var(--accent);font-size:24px;font-weight:900;letter-spacing:.6px}
.editorial-brand small{display:block;margin-top:2px;color:#9b8c80;font-size:9px;font-weight:650;letter-spacing:1.4px}
.editorial-filter-trigger{display:inline-flex;min-height:42px;align-items:center;gap:7px;padding:0 13px;border:1px solid var(--line);border-radius:999px;background:#fff;color:#51463e;font-size:12px;font-weight:800;cursor:pointer}
.editorial-filter-trigger:hover{border-color:#ebb5a6;color:var(--accent2)}
.home-section{padding:20px 0 28px;border-bottom:1px solid #eadfd5}
.home-section:last-child{border-bottom:0}
.home-section[hidden]{display:none!important}
.home-section-head{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin-bottom:14px}
.home-section-head h1,.home-section-head h2{margin:0;color:#2d2119;font-weight:900;letter-spacing:-.4px}
.home-section-head h1{font-size:clamp(26px,2.4vw,36px)}
.home-section-head h2{font-size:22px}
.home-section-link{padding:5px 0;border:0;background:transparent;color:var(--accent2);font-size:12px;font-weight:800;cursor:pointer;white-space:nowrap}
.home-section-link:hover{text-decoration:underline}
.home-week-grid{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(170px,.72fr);grid-template-rows:1fr 1fr;gap:12px;min-height:430px}
.home-hero-card{position:relative;min-width:0;padding:0;overflow:hidden;border:0;border-radius:22px;background:#211b17;color:#fff;text-align:left;cursor:pointer;box-shadow:0 14px 38px rgba(62,43,31,.15)}
.home-hero-card:nth-child(1){grid-row:1/3}
.home-hero-card:nth-child(n+4){display:none}
.home-hero-card:hover{transform:translateY(-2px);box-shadow:0 18px 44px rgba(62,43,31,.2)}
.home-card-media{display:block;position:absolute;inset:0;background:#ece5dd}
.home-card-media img{width:100%;height:100%;object-fit:cover;display:block}
.home-card-media::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(18,13,10,0) 32%,rgba(18,13,10,.82) 100%)}
.home-card-copy{display:flex;position:absolute;z-index:2;right:0;bottom:0;left:0;flex-direction:column;gap:5px;padding:18px}
.home-card-title{font-size:20px;font-weight:900;line-height:1.3;text-shadow:0 2px 12px rgba(0,0,0,.3)}
.home-hero-card:not(:first-child) .home-card-title{font-size:14px}
.home-card-meta,.home-card-place{font-size:12px;line-height:1.45;color:rgba(255,255,255,.88)}
.home-card-cta{align-self:flex-start;margin-top:4px;padding:7px 11px;border:1px solid rgba(255,255,255,.35);border-radius:999px;background:rgba(20,14,11,.26);font-size:11px;font-weight:800}
.home-hero-card:not(:first-child) .home-card-cta{display:none}
.home-placeholder{display:grid;position:absolute;inset:0;place-items:center;background:linear-gradient(145deg,#e4d8ce,#cdbdb0);color:#75665c;font-weight:800}
.home-nearby-prompt{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px;border:1px solid #eadfd5;border-radius:18px;background:#fff;box-shadow:0 8px 24px rgba(70,52,38,.06)}
.home-nearby-prompt-copy strong{display:block;font-size:15px}.home-nearby-prompt-copy span{display:block;margin-top:4px;color:var(--muted);font-size:12px}
.home-locate-btn{min-height:42px;padding:0 14px;border:0;border-radius:999px;background:var(--accent);color:#fff;font-size:12px;font-weight:850;cursor:pointer;white-space:nowrap}
.home-nearby-list{display:grid;gap:8px}
.home-nearby-row{display:grid;width:100%;grid-template-columns:76px minmax(0,1fr) auto;align-items:center;gap:12px;padding:8px;border:0;border-radius:16px;background:#fff;color:var(--text);text-align:left;cursor:pointer;box-shadow:0 5px 18px rgba(70,52,38,.055)}
.home-nearby-row:hover{box-shadow:0 8px 26px rgba(70,52,38,.1)}
.home-nearby-thumb{position:relative;overflow:hidden;width:76px;height:62px;border-radius:11px;background:#eee5de}
.home-nearby-thumb img{width:100%;height:100%;object-fit:cover}
.home-nearby-copy{min-width:0}.home-nearby-title{display:block;overflow:hidden;font-size:13px;font-weight:850;text-overflow:ellipsis;white-space:nowrap}.home-nearby-place{display:block;margin-top:4px;color:var(--muted);font-size:11.5px}
.home-nearby-distance{color:var(--accent2);font-size:12px;font-weight:850;white-space:nowrap}
.home-nearby-empty{padding:16px;border:1px solid #eadfd5;border-radius:16px;background:#fff;color:var(--muted);font-size:12px}
.home-recent-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.home-recent-card{display:grid;grid-template-columns:112px minmax(0,1fr);gap:12px;min-height:112px;padding:0;overflow:hidden;border:1px solid #eadfd5;border-radius:17px;background:#fff;color:var(--text);text-align:left;cursor:pointer;box-shadow:0 7px 22px rgba(70,52,38,.055)}
.home-recent-card:hover{border-color:#eab3a4;box-shadow:0 10px 28px rgba(70,52,38,.1)}
.home-recent-media{position:relative;overflow:hidden;background:#eee5de}.home-recent-media img{width:100%;height:100%;object-fit:cover}.home-recent-media .home-placeholder{position:absolute}
.home-recent-copy{min-width:0;padding:13px 13px 13px 0}.home-recent-title{display:-webkit-box;overflow:hidden;font-size:14px;font-weight:850;line-height:1.38;-webkit-box-orient:vertical;-webkit-line-clamp:2}.home-recent-meta,.home-recent-place{display:block;margin-top:5px;color:var(--muted);font-size:11.5px;line-height:1.4}
.home-empty{padding:28px;border:1px solid #eadfd5;border-radius:20px;background:#fff;text-align:center}.home-empty p{margin:0 0 12px;color:var(--muted)}

.results-head{display:flex;align-items:center;gap:12px;padding:15px 18px;border-bottom:1px solid var(--line);background:rgba(255,250,245,.96)}
.results-back{display:grid;width:42px;height:42px;place-items:center;border:1px solid var(--line);border-radius:50%;background:#fff;color:var(--text);font-size:21px;cursor:pointer}
.results-head-copy{min-width:0;flex:1}.results-head h1{margin:0;font-size:21px}.results-head p{margin:3px 0 0;color:var(--muted);font-size:11.5px}
.results-mode .discover-list{background:#f8f3ed}
.results-mode .filter-pane{background:#fffaf5}
.results-mode .discover-pane{background:#f8f3ed}
.results-mode .event-card{border-color:#e7ddd4}

.user-location-icon{background:transparent!important;border:0!important}
.user-location-dot{display:grid;width:28px;height:28px;place-items:center;border:3px solid #fff;border-radius:50%;background:#f06b52;box-shadow:0 3px 12px rgba(64,45,33,.28)}
.user-location-dot::after{content:"";width:8px;height:8px;border-radius:50%;background:#fff}

.mobile-brand,.mobile-top-actions,.mobile-search-panel{display:none}

@media(max-width:1100px) and (min-width:761px){
  .desktop-shell.home-mode{grid-template-columns:minmax(500px,58%) minmax(0,42%)}
  .editorial-home{padding-right:22px;padding-left:22px}.editorial-brandbar{margin-right:-22px;margin-left:-22px;padding-right:22px;padding-left:22px}
  .home-week-grid{grid-template-columns:minmax(0,1.5fr) minmax(150px,.78fr);min-height:390px}
}
@media(max-width:760px){
  :root{--mobile-top:72px;--mobile-nav:68px}
  html,body,#app{background:#f8f3ed;color:var(--text)}
  .desktop-shell.home-mode,.desktop-shell.results-mode{display:block;min-width:0}
  .desktop-shell.home-mode>.filter-pane,.desktop-shell.results-mode>.filter-pane{display:none}
  .discover-pane{background:#f8f3ed}
  .editorial-home{position:fixed;z-index:5;inset:var(--mobile-top) 0 calc(var(--mobile-nav) + env(safe-area-inset-bottom,0px));padding:0 14px 28px;background:linear-gradient(180deg,#fffaf5 0%,#f8f3ed 100%)}
  .editorial-brandbar{display:none}
  .home-section{padding:20px 0 24px}
  .home-section-head{margin-bottom:12px}.home-section-head h1{font-size:28px}.home-section-head h2{font-size:22px}.home-section-link{font-size:12px}
  .home-week-grid{display:flex;min-height:0;gap:10px;overflow-x:auto;margin-right:-14px;padding-right:14px;scroll-snap-type:x mandatory;scrollbar-width:none}
  .home-week-grid::-webkit-scrollbar{display:none}
  .home-hero-card,.home-hero-card:nth-child(1){display:block!important;width:min(82vw,390px);height:330px;flex:0 0 min(82vw,390px);grid-row:auto;scroll-snap-align:start;border-radius:20px}
  .home-hero-card:nth-child(n+6){display:none!important}
  .home-hero-card:not(:first-child) .home-card-title{font-size:19px}.home-hero-card:not(:first-child) .home-card-cta{display:inline-flex}
  .home-card-copy{padding:17px}.home-card-title{font-size:20px}
  .home-nearby-prompt{align-items:flex-start;flex-direction:column}.home-locate-btn{width:100%}
  .home-nearby-row{grid-template-columns:72px minmax(0,1fr) auto}.home-nearby-thumb{width:72px;height:60px}
  .home-recent-grid{display:grid;grid-template-columns:1fr;gap:8px}.home-recent-card{grid-template-columns:96px minmax(0,1fr);min-height:94px}.home-recent-card:nth-child(n+4){display:none}.home-recent-copy{padding:11px 11px 11px 0}
  .results-head{position:fixed;z-index:7;top:var(--mobile-top);right:0;left:0;min-height:62px;padding:8px 12px;background:rgba(255,250,245,.96);backdrop-filter:blur(12px)}
  .results-mode .discover-list{position:fixed;z-index:5;inset:calc(var(--mobile-top) + 62px) 0 calc(var(--mobile-nav) + env(safe-area-inset-bottom,0px));padding:10px 12px 22px;background:#f8f3ed}
  .results-mode .discover-pane{position:static}
  .results-mode .event-card.desktop-clickable{background:#fff;border-color:#e7ddd4}
  .results-mode .event-card.desktop-clickable>.media-frame{max-height:220px}
  .mobile-top{display:flex;position:fixed;z-index:1900;top:0;left:0;right:0;height:var(--mobile-top);align-items:flex-end;justify-content:space-between;padding:calc(8px + env(safe-area-inset-top,0px)) 14px 9px;border-bottom:1px solid rgba(230,221,212,.8);background:rgba(255,250,245,.96);backdrop-filter:blur(14px)}
  .mobile-brand{display:block;color:var(--accent);font-size:24px;font-weight:900;letter-spacing:.5px}
  .mobile-top-actions{display:flex;align-items:center;gap:3px}.mobile-top-actions .icon-btn{display:grid;width:44px;height:44px;border:0;background:transparent;color:#3a2d25}
  .mobile-search-panel{display:none;position:absolute;z-index:2;top:calc(100% + 6px);right:10px;left:10px;align-items:center;gap:7px;padding:8px;border:1px solid var(--line);border-radius:16px;background:#fff;box-shadow:0 16px 44px rgba(70,52,38,.16)}
  .mobile-search-panel.show{display:flex}.mobile-search-panel .search-shell{min-width:0;flex:1}.mobile-search-panel .searchbox{height:44px;box-shadow:none}.mobile-search-close{width:40px;height:40px;border:0;border-radius:50%;background:#f7f0ea;color:#5f5147;font-size:21px;cursor:pointer}
  .mobile-tabs{height:calc(var(--mobile-nav) + env(safe-area-inset-bottom,0px));padding:6px 20px env(safe-area-inset-bottom,0px);border-top:1px solid #e6ddd4;background:rgba(255,250,245,.98)}
  .mobile-tab{color:#756960}.mobile-tab.active{background:transparent;color:var(--accent2)}
  .mobile-filter-sheet{background:#fff;border-color:var(--line)}.mobile-category:hover{background:#f6eee8}.mobile-venue-card{background:#fff}.mobile-detail .location-row{background:#faf6f2}
  .map-marker-toggle{top:10px;right:auto;left:50%;width:148px;transform:translateX(-50%);background:rgba(255,255,255,.96)}
  .map-legend{background:rgba(255,255,255,.94)!important}.map-legend-item{color:#4e443c!important}
  .home-filter-scrim{display:none!important}
}
'''
replace_once(
    '@media(prefers-reduced-motion:reduce){',
    EDITORIAL_CSS + '\n@media(prefers-reduced-motion:reduce){',
    'insert editorial C CSS'
)

# ---------------------------------------------------------------------------
# Markup: editorial home + results, filter drawer, mobile app header
# ---------------------------------------------------------------------------
replace_once(
    '<div class="desktop-shell">',
    '<div class="desktop-shell home-mode">',
    'initial home shell class'
)
replace_once(
    '  <aside class="filter-pane" aria-label="活動篩選">',
    '  <aside class="filter-pane" id="filterPane" aria-label="活動篩選">',
    'filter pane id'
)
replace_once(
    '      <button class="icon-btn homebtn" id="homeButton" type="button" title="回到台灣全圖" aria-label="回到台灣全圖">⌂</button>',
    '      <button class="icon-btn homebtn" id="homeButton" type="button" title="回到台灣全圖" aria-label="回到台灣全圖">⌂</button>\n      <button class="icon-btn home-filter-close" id="homeFilterClose" type="button" aria-label="關閉篩選">×</button>',
    'filter drawer close button'
)

DISCOVER_MARKUP = r'''  <section class="discover-pane" id="discoverPane" aria-label="探索活動">
    <section class="editorial-home" id="editorialHome" aria-label="探索首頁">
      <header class="editorial-brandbar">
        <div class="editorial-brand">ACG MAP<small>TAIWAN ACG EVENT MAP</small></div>
        <button class="editorial-filter-trigger" id="homeFilterButton" type="button" aria-label="開啟篩選">⌁ 篩選</button>
      </header>

      <section class="home-section home-week" id="homeWeekSection">
        <div class="home-section-head"><h1>這週想去哪？</h1><button class="home-section-link" type="button" data-home-action="week-results">查看更多 ›</button></div>
        <div class="home-week-grid" id="homeWeekGrid"></div>
      </section>

      <section class="home-section home-nearby" id="homeNearbySection">
        <div class="home-section-head"><h2>附近</h2><button class="home-section-link" id="homeNearbyMap" type="button" data-home-action="nearby-map">看地圖 ›</button></div>
        <div id="homeNearbyContent"></div>
      </section>

      <section class="home-section home-recent" id="homeRecentSection">
        <div class="home-section-head"><h2>最近發現</h2><button class="home-section-link" type="button" data-home-action="latest-results">探索更多 ›</button></div>
        <div class="home-recent-grid" id="homeRecentGrid"></div>
      </section>
      <div class="home-empty" id="homeEditorialEmpty" hidden><p>目前篩選條件下沒有可推薦的活動。</p><button class="primary-btn" id="homeEditorialClear" type="button">清除篩選</button></div>
    </section>

    <header class="discover-head results-head" id="resultsHead" hidden>
      <button class="results-back" id="resultsBack" type="button" aria-label="返回探索首頁">‹</button>
      <div class="results-head-copy"><h1 id="resultsTitle">所有活動</h1><p id="resultsSubtitle">依目前條件瀏覽活動</p></div>
      <span class="discover-count" id="discoverCount"></span>
    </header>
    <div class="discover-list" id="discoverList" hidden></div>
  </section>

'''
sub_once(
    r'  <section class="discover-pane" id="discoverPane".*?</section>\n\n(?=  <section class="map-pane" id="mapPane")',
    DISCOVER_MARKUP,
    'replace discover with editorial home',
    re.S,
)

MOBILE_MARKUP = r'''<div class="home-filter-scrim" id="homeFilterScrim" aria-hidden="true"></div>
<header class="mobile-top">
  <div class="mobile-brand">ACG MAP</div>
  <div class="mobile-top-actions">
    <button class="icon-btn" id="mobileSearchButton" type="button" aria-label="搜尋活動">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="22" height="22" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
    </button>
    <button class="icon-btn mobile-filter-btn" id="mobileFilterButton" type="button" aria-label="開啟篩選"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="21" height="21" aria-hidden="true"><path d="M3 5h18l-7 8v6l-4 2v-8z"/></svg></button>
  </div>
  <div class="mobile-search-panel" id="mobileSearchPanel" aria-hidden="true">
    <div class="search-shell">
      <div class="searchbox">
        <svg viewBox="0 0 24 24" fill="none" stroke="#8d8075" stroke-width="2" width="17" height="17" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
        <input id="mq" placeholder="搜尋作品、活動或地點" aria-label="搜尋作品、活動或地點" role="combobox" aria-autocomplete="list" aria-controls="mobileSearchSuggestions" aria-expanded="false">
      </div>
      <div class="search-suggestions" id="mobileSearchSuggestions" role="listbox"></div>
    </div>
    <button class="mobile-search-close" id="mobileSearchClose" type="button" aria-label="關閉搜尋">×</button>
  </div>
</header>

<nav class="mobile-tabs" aria-label="主要頁籤">
  <button class="mobile-tab active" id="discoverTab" type="button" data-tab="discover" aria-current="page"><span aria-hidden="true">◉</span>探索</button>
  <button class="mobile-tab" id="mapTab" type="button" data-tab="map"><span aria-hidden="true">⌖</span>地圖</button>
</nav>

'''
sub_once(
    r'<header class="mobile-top">.*?</nav>\n\n(?=<div class="mobile-filter-overlay")',
    MOBILE_MARKUP,
    'replace mobile header/nav',
    re.S,
)

# ---------------------------------------------------------------------------
# State and time model
# ---------------------------------------------------------------------------
replace_once(
    "  discoverSort:'default',\n  userLocation:null,\n  markerMode:'pin',",
    "  discoverSort:'default',\n  userLocation:null,\n  exploreView:'home',\n  resultsContext:'all',\n  resultsPreviousTime:null,\n  homeScrollTop:0,\n  markerMode:'pin',",
    'editorial view state'
)
replace_once(
    "    {value:'all',label:'全部時間'},{value:'today',label:'今天'},{value:'weekend',label:'本週末'},\n    {value:'ongoing',label:'進行中'},{value:'upcoming',label:'即將開始'},{value:'ending',label:'即將結束'}]},",
    "    {value:'all',label:'全部時間'},{value:'next7',label:'未來 7 天'},{value:'today',label:'今天'},{value:'weekend',label:'本週末'},\n    {value:'ongoing',label:'進行中'},{value:'upcoming',label:'即將開始'},{value:'ending',label:'即將結束'}]},",
    'next seven days filter'
)
replace_once(
    "function currentWeekendRange(today=taipeiCalendarToday()){\n  const todayDay=calendarDayNumber(today);\n  const weekday=new Date(todayDay*86400000).getUTCDay();\n  const saturday=todayDay+(weekday===0?-1:6-weekday);\n  return {start:saturday,end:saturday+1};\n}",
    "function currentWeekendRange(today=taipeiCalendarToday()){\n  const todayDay=calendarDayNumber(today);\n  const weekday=new Date(todayDay*86400000).getUTCDay();\n  if(weekday===0)return {start:todayDay,end:todayDay};\n  const saturday=todayDay+(weekday===6?0:6-weekday);\n  return {start:saturday,end:saturday+1};\n}",
    'Sunday-safe weekend range'
)
replace_once(
    "function locationMatchesTimeFilter(location,value){\n  if(value==='today'){const day=calendarDayNumber(taipeiCalendarToday());return locationOverlapsCalendarRange(location,day,day)}\n  if(value==='weekend'){const range=currentWeekendRange();return locationOverlapsCalendarRange(location,range.start,range.end)}\n  return location.status.kind===value||(value==='ongoing'&&location.status.kind==='ending');\n}",
    "function locationMatchesTimeFilter(location,value){\n  if(value==='today'){const day=calendarDayNumber(taipeiCalendarToday());return locationOverlapsCalendarRange(location,day,day)}\n  if(value==='next7'){const day=calendarDayNumber(taipeiCalendarToday());return locationOverlapsCalendarRange(location,day,day+6)}\n  if(value==='weekend'){const range=currentWeekendRange();return locationOverlapsCalendarRange(location,range.start,range.end)}\n  return location.status.kind===value||(value==='ongoing'&&location.status.kind==='ending');\n}",
    'next7 match logic'
)

# ---------------------------------------------------------------------------
# Editorial selectors + rendering (replaces #91 quick intent renderer)
# ---------------------------------------------------------------------------
HOME_FUNCTIONS = r'''const HOME_NEARBY_MAX_M=20000;
function homeImageHtml(group,className='home-card-media'){
  const src=safeUrl(group.image,true);
  if(!src)return '<span class="'+className+'"><span class="home-placeholder">主視覺敬請期待</span></span>';
  return '<span class="'+className+'"><img src="'+esc(src)+'" alt="" loading="lazy" decoding="async"></span>';
}
function homeVisibleLocations(group){
  return group.locations.filter(location=>occurrenceVisible(location,uiState.filters));
}
function homeWeekLocations(group,startDay,endDay){
  return homeVisibleLocations(group).filter(location=>locationOverlapsCalendarRange(location,startDay,endDay));
}
function homeEditorialRank(group,todayDay){
  const locations=homeWeekLocations(group,todayDay,todayDay+6);
  const endDays=locations.map(location=>eventCalendarDayNumber(location.end)).filter(Number.isFinite).filter(day=>day>=todayDay);
  const nearestEnd=endDays.length?Math.min(...endDays):Infinity;
  if(nearestEnd<=todayDay+3)return [0,nearestEnd];
  const startDays=locations.map(location=>eventCalendarDayNumber(location.start)).filter(Number.isFinite).filter(day=>day>=todayDay&&day<=todayDay+6);
  if(startDays.length)return [1,Math.min(...startDays)];
  if(isLatestGroup(group))return [2,-calendarDayNumber(String(group.firstSeen||''))];
  return [3,nearestEnd];
}
function pickEditorialDiverse(groups,limit){
  const selected=[],selectedIds=new Set(),seenIp=new Set(),seenForm=new Set();
  const add=(group)=>{selected.push(group);selectedIds.add(group.id);if(group.ip)seenIp.add(normalizeText(group.ip));if(group.form)seenForm.add(group.form)};
  [0,1,2].some(pass=>{
    groups.forEach(group=>{
      if(selected.length>=limit||selectedIds.has(group.id))return;
      const ipKey=group.ip?normalizeText(group.ip):'';
      const newIp=!ipKey||!seenIp.has(ipKey),newForm=!group.form||!seenForm.has(group.form);
      if((pass===0&&newIp&&newForm)||(pass===1&&newIp)||pass===2)add(group);
    });
    return selected.length>=limit;
  });
  return selected;
}
function getHomeWeekGroups(){
  const todayDay=calendarDayNumber(taipeiCalendarToday());
  const groups=getFilteredActivityGroups().filter(group=>safeUrl(group.image,true)&&homeWeekLocations(group,todayDay,todayDay+6).length);
  groups.sort((a,b)=>{
    const ra=homeEditorialRank(a,todayDay),rb=homeEditorialRank(b,todayDay);
    return ra[0]-rb[0]||ra[1]-rb[1]||a.title.localeCompare(b.title,'zh-Hant')||a.id.localeCompare(b.id);
  });
  return pickEditorialDiverse(groups,5);
}
function homeRepresentativeLocation(group){
  const visible=homeVisibleLocations(group);
  return visible[0]||group.locations[0];
}
function homeDateLabel(group){
  const todayDay=calendarDayNumber(taipeiCalendarToday());
  const start=group.overallStart?Date.UTC(group.overallStart.getFullYear(),group.overallStart.getMonth(),group.overallStart.getDate())/86400000:NaN;
  const end=group.overallEnd?Date.UTC(group.overallEnd.getFullYear(),group.overallEnd.getMonth(),group.overallEnd.getDate())/86400000:NaN;
  if(Number.isFinite(start)&&start>todayDay&&start<=todayDay+6)return formatMonthDay(start)+' 開始';
  if(Number.isFinite(end)&&end>=todayDay)return '至 '+formatMonthDay(end);
  return '進行中';
}
function homeHeroCardHtml(group,index){
  const location=homeRepresentativeLocation(group);
  if(!location)return '';
  const meta=[homeDateLabel(group),group.fee].filter(Boolean).join(' · ');
  const place=[location.city,location.venueName].filter(Boolean).join(' · ');
  return '<button class="home-hero-card home-event-target" type="button" data-home-location-id="'+esc(location.id)+'">'
    +homeImageHtml(group)
    +'<span class="home-card-copy"><span class="home-card-title">'+esc(group.title)+'</span>'
    +(meta?'<span class="home-card-meta">'+esc(meta)+'</span>':'')
    +(place?'<span class="home-card-place">⌖ '+esc(place)+'</span>':'')
    +'<span class="home-card-cta">查看活動 →</span></span></button>';
}
function homeNearbyItems(){
  if(!uiState.userLocation)return [];
  const items=[];
  getFilteredActivityGroups().forEach(group=>{
    const info=nearestLocationForGroup(group);
    if(info&&info.distanceMeters<=HOME_NEARBY_MAX_M)items.push({group,location:info.location,distanceMeters:info.distanceMeters});
  });
  return items.sort((a,b)=>a.distanceMeters-b.distanceMeters||a.group.title.localeCompare(b.group.title,'zh-Hant')||a.group.id.localeCompare(b.group.id)).slice(0,3);
}
function homeNearbyRowHtml(item){
  const group=item.group,location=item.location;
  return '<button class="home-nearby-row home-event-target" type="button" data-home-location-id="'+esc(location.id)+'">'
    +homeImageHtml(group,'home-nearby-thumb')
    +'<span class="home-nearby-copy"><span class="home-nearby-title">'+esc(group.title)+'</span><span class="home-nearby-place">'+esc(location.venueName||location.city||'')+'</span></span>'
    +'<span class="home-nearby-distance">'+esc(formatDistance(item.distanceMeters))+'</span></button>';
}
function getHomeRecentGroups(excludedIds){
  return getLatestActivityGroups().filter(group=>!excludedIds.has(group.id)&&safeUrl(group.image,true)).slice(0,4);
}
function homeRecentCardHtml(group){
  const location=homeRepresentativeLocation(group);if(!location)return '';
  const meta=[group.form,group.fee].filter(Boolean).join(' · ');
  const place=[location.city,location.venueName].filter(Boolean).join(' · ');
  return '<button class="home-recent-card home-event-target" type="button" data-home-location-id="'+esc(location.id)+'">'
    +homeImageHtml(group,'home-recent-media')
    +'<span class="home-recent-copy"><span class="home-recent-title">'+esc(group.title)+'</span>'
    +(meta?'<span class="home-recent-meta">'+esc(meta)+'</span>':'')
    +(place?'<span class="home-recent-place">⌖ '+esc(place)+'</span>':'')+'</span></button>';
}
function renderEditorialHome(){
  const week=getHomeWeekGroups();
  const weekSection=document.getElementById('homeWeekSection'),weekGrid=document.getElementById('homeWeekGrid');
  weekSection.hidden=!week.length;weekGrid.innerHTML=week.map(homeHeroCardHtml).join('');

  const nearbySection=document.getElementById('homeNearbySection'),nearbyContent=document.getElementById('homeNearbyContent'),nearbyMap=document.getElementById('homeNearbyMap');
  nearbySection.hidden=false;nearbyMap.hidden=!uiState.userLocation;
  if(!uiState.userLocation){
    nearbyContent.innerHTML='<div class="home-nearby-prompt"><div class="home-nearby-prompt-copy"><strong>看看你附近有哪些 ACG 活動</strong><span>只有在你主動開啟後才會使用目前位置。</span></div><button class="home-locate-btn" type="button" data-home-action="locate">使用目前位置</button></div>';
  }else{
    const items=homeNearbyItems();
    nearbyContent.innerHTML=items.length?'<div class="home-nearby-list">'+items.map(homeNearbyRowHtml).join('')+'</div>':'<div class="home-nearby-empty">20 公里內目前沒有符合條件的活動。</div>';
  }

  const recent=getHomeRecentGroups(new Set(week.map(group=>group.id)));
  const recentSection=document.getElementById('homeRecentSection'),recentGrid=document.getElementById('homeRecentGrid');
  recentSection.hidden=!recent.length;recentGrid.innerHTML=recent.map(homeRecentCardHtml).join('');

  const empty=document.getElementById('homeEditorialEmpty');
  empty.hidden=!!(week.length||recent.length||!uiState.userLocation||homeNearbyItems().length);
}
function requestHomeLocation(button,onReady=null){
  if(uiState.userLocation){if(onReady)onReady();return}
  if(!navigator.geolocation){showToast('此瀏覽器不支援定位功能');return}
  if(button){button.disabled=true;button.setAttribute('aria-busy','true')}
  navigator.geolocation.getCurrentPosition(position=>{
    if(button){button.disabled=false;button.removeAttribute('aria-busy')}
    const lat=Number(position.coords.latitude),lng=Number(position.coords.longitude);
    if(!Number.isFinite(lat)||!Number.isFinite(lng)){showToast('無法取得目前位置');return}
    uiState.userLocation={lat,lng};renderUserLocationMarker();renderEditorialHome();if(onReady)onReady();
  },error=>{
    if(button){button.disabled=false;button.removeAttribute('aria-busy')}
    showToast(error&&error.code===1?'未取得定位權限，請允許瀏覽器使用位置':'定位失敗，請稍後再試');
  },{enableHighAccuracy:false,timeout:10000,maximumAge:300000});
}
function openHomeNearbyMap(){
  const run=()=>{
    const items=homeNearbyItems();
    if(MOBILE_QUERY.matches)setTab('map',{explicitTarget:true});
    requestAnimationFrame(()=>{
      map.invalidateSize();renderUserLocationMarker();
      const points=[[uiState.userLocation.lat,uiState.userLocation.lng],...items.map(item=>[item.location.lat,item.location.lng])];
      if(points.length>1)map.fitBounds(points,{padding:[48,48],maxZoom:14});else map.setView(points[0],13);
      uiState.mapHasVisibleView=true;
    });
  };
  if(uiState.userLocation)run();else requestHomeLocation(document.querySelector('[data-home-action="locate"]'),run);
}
function closeHomeFilterDrawer(){document.body.classList.remove('home-filter-open');document.getElementById('homeFilterScrim').setAttribute('aria-hidden','true')}
function openHomeFilterDrawer(){if(MOBILE_QUERY.matches){openMobileFilters();return}document.body.classList.add('home-filter-open');document.getElementById('homeFilterScrim').setAttribute('aria-hidden','false')}
function updateResultsHeader(){
  const title=document.getElementById('resultsTitle'),subtitle=document.getElementById('resultsSubtitle');
  if(uiState.resultsContext==='week'){title.textContent='這週想去哪？';subtitle.textContent='未來 7 天可以參加的活動'}
  else if(uiState.resultsContext==='latest'){title.textContent='最近發現';subtitle.textContent='最近 7 天加入 ACG Map 的活動'}
  else if(uiState.resultsContext==='search'){title.textContent='搜尋結果';subtitle.textContent=uiState.query?'「'+uiState.query+'」':'依目前條件瀏覽活動'}
  else{title.textContent='所有活動';subtitle.textContent='依目前條件瀏覽活動'}
}
function updateExploreViewUI(){
  const home=uiState.exploreView==='home';
  const shell=document.querySelector('.desktop-shell');shell.classList.toggle('home-mode',home);shell.classList.toggle('results-mode',!home);
  document.body.classList.toggle('editorial-home-active',home);
  document.getElementById('editorialHome').hidden=!home;document.getElementById('resultsHead').hidden=home;document.getElementById('discoverList').hidden=home;
  if(!home)updateResultsHeader();
  requestAnimationFrame(()=>{map.invalidateSize();if(home){document.getElementById('editorialHome').scrollTop=uiState.homeScrollTop||0}});
}
function enterResults(context='all'){
  if(uiState.exploreView==='home')uiState.homeScrollTop=document.getElementById('editorialHome').scrollTop;
  uiState.resultsContext=context;uiState.resultsPreviousTime=null;
  if(context==='week'){uiState.resultsPreviousTime=uiState.filters.time;uiState.filters.time='next7';uiState.discoverMode='discover'}
  else if(context==='latest'){uiState.discoverMode='latest'}
  else uiState.discoverMode='discover';
  uiState.exploreView='results';closeHomeFilterDrawer();updateExploreViewUI();
  if(context==='latest'){
    renderDiscover(getDiscoverModeGroups());updateFilterUI();updateStat(getFilteredActivityGroups());
  }else renderAll();
}
function returnEditorialHome(){
  if(uiState.resultsContext==='week'&&uiState.filters.time==='next7')uiState.filters.time=uiState.resultsPreviousTime||'all';
  if(uiState.resultsContext==='search'){
    uiState.query='';document.getElementById('q').value='';document.getElementById('mq').value='';hideSearchSuggestions();
  }
  uiState.discoverMode='discover';uiState.resultsContext='all';uiState.resultsPreviousTime=null;uiState.exploreView='home';
  renderAll();updateExploreViewUI();
}
function setHomeMarkerHover(locationId,hovered){
  if(MOBILE_QUERY.matches)return;
  const marker=markers.find(item=>item.locationId===locationId);if(!marker)return;
  marker.isHovered=hovered;applyMarkerVisualState(marker);
}
'''
sub_once(
    r'function getIntentCount\(value\)\{.*?\nfunction popupNavigationHtml\(\)\{',
    HOME_FUNCTIONS + '\nfunction popupNavigationHtml(){',
    'replace quick intent renderer with editorial home',
    re.S,
)

# ---------------------------------------------------------------------------
# User location marker on the persistent map
# ---------------------------------------------------------------------------
replace_once(
    "const map=L.map('map',{zoomControl:true,minZoom:6,maxZoom:16,attributionControl:false,maxBoundsViscosity:1.0,closePopupOnClick:false});\nmap.zoomControl.setPosition('bottomright');",
    "const map=L.map('map',{zoomControl:true,minZoom:6,maxZoom:16,attributionControl:false,maxBoundsViscosity:1.0,closePopupOnClick:false});\nmap.zoomControl.setPosition('bottomright');\nlet userLocationMarker=null;\nfunction renderUserLocationMarker(){\n  if(userLocationMarker){map.removeLayer(userLocationMarker);userLocationMarker=null}\n  if(!uiState.userLocation)return;\n  userLocationMarker=L.marker([uiState.userLocation.lat,uiState.userLocation.lng],{interactive:false,zIndexOffset:2600,icon:L.divIcon({className:'user-location-icon',html:'<div class=\"user-location-dot\" aria-label=\"你的位置\"></div>',iconSize:[28,28],iconAnchor:[14,14]})}).addTo(map);\n}",
    'user location marker'
)
replace_once(
    '  cluster.addLayers(markers);\n  requestAnimationFrame(wireClusterKeyboard);',
    '  cluster.addLayers(markers);\n  renderUserLocationMarker();\n  requestAnimationFrame(wireClusterKeyboard);',
    'render user location after markers'
)

# ---------------------------------------------------------------------------
# Results/home rendering, tab scroll behavior, search transition
# ---------------------------------------------------------------------------
replace_once(
    "function renderAll(){\n  const groups=getFilteredActivityGroups();\n  renderDiscover(getDiscoverModeGroups());renderDiscoverIntents();renderMapMarkers();renderFloatingEvents();updateFilterUI();updateMarkerToggles();updateStat(groups);\n}",
    "function renderAll(){\n  const groups=getFilteredActivityGroups();\n  if(uiState.exploreView==='home')renderEditorialHome();else renderDiscover(getDiscoverModeGroups());\n  renderMapMarkers();renderFloatingEvents();updateFilterUI();updateMarkerToggles();updateStat(groups);updateExploreViewUI();\n}",
    'render home or results'
)

# Filter city changes should not yank the persistent home map viewport.
replace_once(
    "  const key=openFilterKey,value=button.dataset.value;uiState.filters[key]=value;closeFilterDetail();renderAll();if(key==='city')fitCityView(value);",
    "  const key=openFilterKey,value=button.dataset.value;uiState.filters[key]=value;closeFilterDetail();renderAll();if(key==='city'&&uiState.exploreView==='results')fitCityView(value);",
    'home filter viewport safety'
)

# Replace setTab to restore the correct surface scroll state.
sub_once(
    r'function setTab\(tab,options=\{\}\)\{.*?\n\}\n\nlet searchTimer=null;',
    r'''function setTab(tab,options={}){
  if(!['discover','map'].includes(tab)) return;
  const list=document.getElementById('discoverList'),home=document.getElementById('editorialHome');
  if(uiState.tab==='discover'){
    if(uiState.exploreView==='home')uiState.homeScrollTop=home.scrollTop;
    else uiState.discoverScrollTop[uiState.discoverMode]=list.scrollTop;
  }
  const leavingMap=uiState.tab==='map'&&tab==='discover';
  uiState.tab=tab;
  document.body.classList.toggle('mobile-map',tab==='map');
  document.querySelectorAll('.mobile-tab').forEach(button=>{
    const active=button.dataset.tab===tab;button.classList.toggle('active',active);
    if(active) button.setAttribute('aria-current','page'); else button.removeAttribute('aria-current');
  });
  if(tab==='discover'){
    if(leavingMap)closeActiveMapPopup({clearSelection:true});
    requestAnimationFrame(()=>{if(uiState.exploreView==='home')home.scrollTop=uiState.homeScrollTop||0;else list.scrollTop=uiState.discoverScrollTop[uiState.discoverMode]||0});
  }else requestAnimationFrame(()=>{
    map.invalidateSize();
    if(options.explicitTarget)return;
    if(uiState.mapHasVisibleView&&uiState.mapView)map.setView(uiState.mapView.center,uiState.mapView.zoom,{animate:false});
    else{fitTaiwanView();uiState.mapHasVisibleView=true}
    restoreExpandedCluster();
  });
}

let searchTimer=null;''',
    'editorial-aware setTab',
    re.S,
)

replace_once(
    "    searchTimer=setTimeout(()=>{uiState.query=input.value.trim();renderAll()},180);",
    "    searchTimer=setTimeout(()=>{\n      uiState.query=input.value.trim();\n      if(uiState.query&&uiState.exploreView==='home'){uiState.homeScrollTop=document.getElementById('editorialHome').scrollTop;uiState.exploreView='results';uiState.resultsContext='search';uiState.discoverMode='discover';updateExploreViewUI()}\n      renderAll();\n    },180);",
    'search opens results'
)

# Search suggestions should close the mobile search panel after choosing.
replace_once(
    "function chooseSuggestion(item){\n  if(!item) return;\n  hideSearchSuggestions();",
    "function chooseSuggestion(item){\n  if(!item) return;\n  hideSearchSuggestions();closeMobileSearchPanel();",
    'close search panel after selection'
)

# ---------------------------------------------------------------------------
# Event wiring: remove Discover/Latest switch + quick pills, add editorial events
# ---------------------------------------------------------------------------
sub_once(
    r"document\.getElementById\('discoverMode'\)\.addEventListener\('click',event=>\{.*?\n\}\);\ndocument\.getElementById\('discoverIntents'\)\.addEventListener\('click',event=>\{.*?\n\}\);\n",
    r'''document.getElementById('resultsBack').addEventListener('click',returnEditorialHome);
document.getElementById('homeFilterButton').addEventListener('click',openHomeFilterDrawer);
document.getElementById('homeFilterClose').addEventListener('click',closeHomeFilterDrawer);
document.getElementById('homeFilterScrim').addEventListener('click',closeHomeFilterDrawer);
document.getElementById('homeEditorialClear').addEventListener('click',clearAllFilters);
document.getElementById('editorialHome').addEventListener('click',event=>{
  const action=event.target.closest('[data-home-action]');
  if(action){
    if(action.dataset.homeAction==='week-results')enterResults('week');
    else if(action.dataset.homeAction==='latest-results')enterResults('latest');
    else if(action.dataset.homeAction==='nearby-map')openHomeNearbyMap();
    else if(action.dataset.homeAction==='locate')requestHomeLocation(action);
    return;
  }
  const target=event.target.closest('[data-home-location-id]');if(target)selectLocation(target.dataset.homeLocationId,{updateHistory:true});
});
document.getElementById('editorialHome').addEventListener('pointerover',event=>{const target=event.target.closest('[data-home-location-id]');if(target)setHomeMarkerHover(target.dataset.homeLocationId,true)});
document.getElementById('editorialHome').addEventListener('pointerout',event=>{const target=event.target.closest('[data-home-location-id]');if(target&&!target.contains(event.relatedTarget))setHomeMarkerHover(target.dataset.homeLocationId,false)});
''',
    'editorial home event wiring',
    re.S,
)

# Mobile search icon/panel.
replace_once(
    "document.getElementById('mobileFilterButton').addEventListener('click',openMobileFilters);",
    "function openMobileSearchPanel(){const panel=document.getElementById('mobileSearchPanel');panel.classList.add('show');panel.setAttribute('aria-hidden','false');requestAnimationFrame(()=>document.getElementById('mq').focus())}\nfunction closeMobileSearchPanel(){const panel=document.getElementById('mobileSearchPanel');if(!panel)return;panel.classList.remove('show');panel.setAttribute('aria-hidden','true')}\ndocument.getElementById('mobileSearchButton').addEventListener('click',openMobileSearchPanel);\ndocument.getElementById('mobileSearchClose').addEventListener('click',closeMobileSearchPanel);\ndocument.getElementById('mobileFilterButton').addEventListener('click',openMobileFilters);",
    'mobile search icon behavior'
)

# Clear filters should keep the user on the editorial home if that is the current surface.
# Existing function already renders through renderAll; only remove stale quick-sort visual concerns by keeping discoverSort reset.

# ---------------------------------------------------------------------------
# Final start state
# ---------------------------------------------------------------------------
replace_once(
    "  renderAll();\n  if(!MOBILE_QUERY.matches){fitTaiwanView();uiState.mapHasVisibleView=true}\n  setTab('discover');handleDeepLink();",
    "  renderAll();\n  if(!MOBILE_QUERY.matches){fitTaiwanView();uiState.mapHasVisibleView=true}\n  updateExploreViewUI();setTab('discover');handleDeepLink();",
    'start in editorial home'
)

HTML.write_text(text, encoding='utf-8')

# ---------------------------------------------------------------------------
# decision.md: replace superseded #91 decision and correct marker placement
# ---------------------------------------------------------------------------
decision = DECISION.read_text(encoding='utf-8')
decision = decision.replace(
    '- Marker 顯示模式切換固定放在地圖上方正中央。',
    '- Marker 顯示模式切換：桌機放在地圖上方右側；手機 Map 維持上方置中。'
)
decision = decision.replace(
    '- Discover panel 內有 `Discover / Latest` switch；它不是 mobile bottom nav 的第三個 tab。',
    '- 探索首頁採 Editorial C：首頁直接呈現「這週想去哪？／附近／最近發現」，不顯示 `Discover / Latest` switch；Latest 的資料定義保留，並由「最近發現」與其完整 Results view 使用。'
)
old_section = '''## 2026-08-12 — Discover 情境入口與桌機地圖搜尋

- Discover / Latest 仍是內容模式，不新增第三種 mode。
- 「今天」與「本週末」是既有時間 Filter 的正式 preset；兩者共用 `uiState.filters.time`，互斥且同步桌機／手機 Filter。日期以 Asia/Taipei 日曆日判斷。
- 「離我最近」是 Discover 清單排序，不是半徑 Filter；只在使用者點擊後要求 geolocation，不得自動定位，也不得改 Map viewport。
- 多店活動在距離排序時以目前條件下最近的可用分店作為卡片目標，仍走既有 `selectLocation()` flow。
- 桌機搜尋移到地圖上方，圖釘／圖片切換靠右；手機保留頂部搜尋與原本 Map 切換位置。
- Quick intent 只保留高頻情境（今天／週末／離我最近），完整條件仍由 Filter 負責。'''
new_section = '''## 2026-08-12 — Editorial C 探索首頁（取代同日舊 Quick Intent 版）

- 探索首頁不是 Filter/List 工具首頁；第一層固定為「這週想去哪？／附近／最近發現」三個 editorial sections。首頁不得顯示 Today／Weekend 數字 chip、活動總數 badge、`Discover / Latest` switch 或排名數字。
- 「這週想去哪？」實際範圍為 Asia/Taipei 今天起未來 7 個日曆日；手機最多 5 張橫向 Hero cards，桌機只呈現前 3 張（1 大 2 小）。首頁 selection 使用可解釋規則：快結束 → 7 日內新開始 → first_seen 最近 → 其他有效活動，並做 IP／活動形式多樣化；沒有可用 KV 的活動不進 Hero，但仍可出現在完整 Results。
- 「查看更多」進入完整 Results mode，使用既有 Filter/List/Map 架構，並將 `未來 7 天` 作為正式 time filter preset；返回首頁時只撤回這個 route 注入的 time preset，不清除使用者在 Results 中主動修改的其他 Filter。
- 「附近」是首頁內容 section，不是 quick-sort pill。未授權時只顯示「使用目前位置」CTA；必須由使用者點擊後才呼叫 geolocation。授權後顯示 20 公里內最近 3 個不同 event，多店活動只取最近 eligible location；點卡片仍走 `selectLocation()`。使用者位置以獨立 marker 顯示；只有點「看地圖」才可主動調整 map viewport。
- 「最近發現」沿用 first_seen / Latest 最近 7 日定義；手機最多 3 筆 compact rows，桌機最多 4 張 2×2 cards。它可避開已出現在「這週想去哪？」的 event；Nearby 不為視覺去重而犧牲真實距離排序。
- Desktop Home 為 `Editorial content × persistent map` 兩欄；Filter sidebar 在 Home 隱藏，Filter 由 trigger 開啟 drawer。搜尋固定放在右側地圖上方，Marker 圖釘／圖片切換放右上。只有 Results mode 才恢復 Filter / List / Map 三欄工具架構。
- Desktop Home card hover 只 highlight 對應 marker，不 flyTo；click 才走既有 `selectLocation()` / reveal / popup pipeline。
- Mobile Home 頂部是 `ACG MAP` brand + search icon + filter icon；底部只有「探索／地圖」。首頁不把 search input 常駐成工具列；搜尋 icon 展開搜尋面板，輸入後進 Results mode。
- Home 與 Results 共用 light editorial consumer-product visual system；Positron 地圖與既有 pin 類型配色不變。Filter facet counts、日期、距離、Map cluster counts 屬功能性資訊，可保留；禁止的是把首頁做成統計儀表板。
- `selectLocation()`、Nearby popup、Popup carousel、lastViewed、Activity Picker、MarkerCluster/spiderfy、selectedLocationId SSOT、deep link、popstate 與 first_seen 定義不得因本次首頁重排而重構。'''
if old_section not in decision:
    raise RuntimeError('decision.md old quick-intent section not found')
decision = decision.replace(old_section, new_section, 1)
DECISION.write_text(decision, encoding='utf-8')

# ---------------------------------------------------------------------------
# Tests: update legacy expectations and add editorial regression
# ---------------------------------------------------------------------------
map_test = MAP_TEST.read_text(encoding='utf-8')
map_test = re.sub(
    r'    def test_desktop_three_column_shell_exists\(self\):.*?\n    def test_mobile_has_only_discover_and_map_tabs',
    '''    def test_desktop_home_and_results_shells_exist(self):
        self.assertIn('class="desktop-shell home-mode"', self.html)
        self.assertIn('class="filter-pane"', self.html)
        self.assertIn('class="discover-pane"', self.html)
        self.assertIn('class="map-pane"', self.html)
        self.assertIn("grid-template-columns:var(--sidebar) var(--discover) minmax(0,1fr)", self.html)
        self.assertIn(".desktop-shell.home-mode{grid-template-columns:minmax(560px,55%) minmax(0,45%)}", self.html)
        self.assertIn(".desktop-shell.home-mode>.filter-pane{display:none}", self.html)

    def test_mobile_has_only_discover_and_map_tabs''',
    map_test,
    count=1,
    flags=re.S,
)
map_test = re.sub(
    r'    def test_marker_toggle_is_centered_over_map\(self\):.*?\n    def test_map_restores_original_positron_visuals',
    '''    def test_marker_toggle_is_right_on_desktop_and_centered_on_mobile(self):
        self.assertIn('class="segmented map-marker-toggle marker-toggle"', self.html)
        self.assertIn(".map-marker-toggle{position:absolute;z-index:1000;top:14px;right:14px", self.html)
        self.assertIn(".map-marker-toggle{top:10px;right:auto;left:50%;width:148px;transform:translateX(-50%);background:rgba(255,255,255,.96)}", self.html)
        self.assertNotIn('class="marker-setting"', self.html)

    def test_map_restores_original_positron_visuals''',
    map_test,
    count=1,
    flags=re.S,
)
map_test = re.sub(
    r'    def test_latest_switch_first_seen_and_separate_scroll\(self\):.*?\n    def test_mobile_viewport_only_saves_visible_initialized_map',
    '''    def test_latest_is_editorial_recent_discovery_and_keeps_first_seen(self):
        self.assertIn('id="homeRecentSection"', self.html)
        self.assertIn('data-home-action="latest-results"', self.html)
        self.assertNotIn('id="discoverMode"', self.html)
        self.assertNotIn('data-discover-mode="discover"', self.html)
        self.assertNotIn('data-discover-mode="latest"', self.html)
        self.assertIn("discoverMode:'discover'", self.html)
        self.assertIn("firstSeen:chooseValue(items,'first_seen')||null", self.html)
        self.assertIn("days>=0&&days<=6", self.html)
        self.assertIn("function getHomeRecentGroups(excludedIds)", self.html)
        self.assertIn("getLatestActivityGroups().filter(group=>!excludedIds.has(group.id)", self.html)
        self.assertIn("discoverScrollTop:{discover:0,latest:0}", self.html)

    def test_latest_results_do_not_change_marker_dataset(self):
        enter = self.html[self.html.index("function enterResults(context='all')"):self.html.index("function returnEditorialHome")]
        self.assertIn("if(context==='latest')", enter)
        latest_branch = enter[enter.index("if(context==='latest')"):]
        self.assertIn("renderDiscover(getDiscoverModeGroups())", latest_branch)
        self.assertNotIn("renderMapMarkers", latest_branch.split("else renderAll()",1)[0])
        self.assertNotIn("fitTaiwanView", latest_branch.split("else renderAll()",1)[0])

    def test_mobile_viewport_only_saves_visible_initialized_map''',
    map_test,
    count=1,
    flags=re.S,
)
MAP_TEST.write_text(map_test, encoding='utf-8')

if OLD_TEST.exists():
    OLD_TEST.unlink()

NEW_TEST.write_text(r'''from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / "public" / "taiwan-exhibition-map.html"
DECISION = Path(__file__).resolve().parents[1] / "decision.md"
text = HTML.read_text(encoding="utf-8")
decision = DECISION.read_text(encoding="utf-8")

# True C information architecture, not #91 pills.
assert 'id="editorialHome"' in text
assert '>這週想去哪？<' in text
assert '>附近<' in text
assert '>最近發現<' in text
assert 'id="discoverIntents"' not in text
assert 'todayIntentCount' not in text
assert 'weekendIntentCount' not in text
assert 'intent-count' not in text
assert 'id="discoverMode"' not in text
assert 'data-discover-mode=' not in text

# Week = rolling seven days; home has editorial ranking/diversity and real Results route.
assert "if(value==='next7')" in text
assert "day,day+6" in text
assert 'function homeEditorialRank' in text
assert 'function pickEditorialDiverse' in text
assert "safeUrl(group.image,true)&&homeWeekLocations" in text
assert "enterResults('week')" in text
assert "uiState.filters.time='next7'" in text

# Nearby is a location section, opt-in only, max 20 km / 3 events, no automatic fit.
assert 'const HOME_NEARBY_MAX_M=20000' in text
assert '使用目前位置' in text
assert 'navigator.geolocation.getCurrentPosition' in text
assert '.slice(0,3)' in text
request_block = text[text.index('function requestHomeLocation'):text.index('function openHomeNearbyMap')]
assert 'fitBounds' not in request_block and 'flyTo' not in request_block and 'setView' not in request_block
assert 'function openHomeNearbyMap' in text and 'map.fitBounds' in text[text.index('function openHomeNearbyMap'):text.index('function closeHomeFilterDrawer')]
assert 'user-location-dot' in text

# Desktop: editorial content + persistent map; tool sidebar only in Results.
assert '.desktop-shell.home-mode{grid-template-columns:minmax(560px,55%) minmax(0,45%)}' in text
assert '.desktop-shell.home-mode>.filter-pane{display:none}' in text
assert 'id="homeFilterButton"' in text
assert 'id="homeFilterScrim"' in text
assert '.desktop-map-search{position:absolute' in text
assert '.map-marker-toggle{position:absolute;z-index:1000;top:14px;right:14px' in text
assert 'function setHomeMarkerHover' in text
assert 'marker.isHovered=hovered' in text

# Mobile: brand + icons, no permanent search bar, only Explore/Map navigation.
assert '<div class="mobile-brand">ACG MAP</div>' in text
assert 'id="mobileSearchButton"' in text
assert 'id="mobileSearchPanel"' in text
assert '>探索</button>' in text
assert '>地圖</button>' in text

# Light editorial system and existing map selection architecture coexist.
assert '--bg:#f7f3ed' in text
assert 'function selectLocation(locationId,options={})' in text
assert 'function buildNearbyActivities(originLocation)' in text
assert 'cluster.zoomToShowLayer(marker' in text
assert "firstSeen:chooseValue(items,'first_seen')||null" in text
assert 'Editorial C 探索首頁' in decision
print('editorial C home UX: PASS')
''', encoding='utf-8')

print('Editorial C patch applied')
