# ACG 地圖產品決策

> 本文件記錄不可在一般功能追加或版面重構時擅自改動的產品行為。若新需求與本文件衝突，必須先向 Daniel 說明影響並取得明確同意，同步更新本文件與測試。

## 地圖背景

- 預設底圖使用 OpenFreeMap Positron 向量樣式：`https://tiles.openfreemap.org/styles/positron`。
- 主要道路與快速道路使用白色內線、淡灰色外框，縮放越近逐步加粗；次要道路於高縮放層級顯示。
- 台灣鄉鎮市區邊界為 `#8fa0b5`、線寬 `0.7`、透明度 `0.5`、不填色。
- 縮放低於 11 顯示縣市名稱；縮放 11 以上顯示鄉鎮市區名稱。
- 地圖縮放範圍為 6–16，初始畫面涵蓋台灣；桌機與手機沿用既有台灣範圍限制。
- 桌機地圖導航控制固定在右上：Home 鍵下方依序為 `+ / -`；手機保留既有右下 Leaflet 縮放控制。
- 不得只因自動驗收環境不支援 WebGL，就把所有使用者的預設底圖改成其他樣式。相容性問題應以不改變正常環境視覺的方式處理，或先取得 Daniel 同意。
- 不支援 WebGL 的環境可自動改用 OpenStreetMap raster 備援；此備援不得改變支援 WebGL 環境的預設 Positron 視覺。

## 圖釘模式

| 活動形式 | 顏色 | 圖案 |
|---|---|---|
| 展覽 | `#3f8ad0` | 畫框／展覽圖片 |
| 快閃店 | `#e05aa0` | 購物袋 |
| 主題餐廳 | `#e08a3c` | 咖啡杯 |
| 體驗活動 | `#8560d8` | 星星 |

- ACG 活動只有上述四種形式，沒有「其他」分類；圖例與篩選皆不列出「其他」。
- 圖釘為白框水滴造型。
- 每個活動各自一個 marker；同場館／同座標的多個活動會聚合。桌機只有 canonical 大型文化園區 destination cluster（華山、松菸、駁二，以及同類花蓮／嘉義文化創意產業園區）在目前篩選後仍含 2 個以上不同活動時，才直接開啟全螢幕 Activity Picker；一般 cluster 必須持續 zoom-to-bounds，最大層級再 spiderfy。若 broad cluster 同時混入園區外 marker，也先 zoom，不能因其中包含園區就提前滿版。手機維持 zoom／最大層級 spiderfy。個別 marker 不顯示數字徽章；聚合徽章顯示該處活動數。
- 每個活動依自身活動形式顯示對應顏色的圖釘。
- 座標不是 `exact` 時，圖釘透明度降為 70%。
- 場館包含七日內即將結束的非常設活動時，顯示紅色提示點。
- 聚合 marker：小群組藍色、中群組橘色、大群組紅色。
- 「圖片模式」顯示活動 KV；新增或修改圖片模式不得改掉上述圖釘模式。
- 圖片 marker 依 KV 實際寬高比顯示為橫式或直式，不得強制裁成單一直式比例。
- 圖片 marker 的 KV 必須置中完整呈現，剩餘空間以同圖模糊背景補齊；活動數徽章固定在圖片右上角、貼齊邊界外緣（手機 App 通知徽章樣式），使用紅底白字。
- Marker 顯示模式切換：桌機放在地圖上方右側；手機 Map 維持上方置中。
- 點擊 marker 顯示該活動資訊；被選取的 marker 放大 30% 並以紅色外框標示（取代原本白框）。關閉 popup 後 active selection 仍清除，但最後看過的 marker 保留紅框；`lastViewedLocationId` 只能控制視覺，不得控制定位、popup、URL、history 或 spiderfy。桌機滑鼠移入水滴與圖片 marker 時放大 30%，只縮放 marker 內層元素，不修改 Leaflet 定位 transform。
- 使用者展開群聚並進入活動資訊後，回到地圖時必須保留該群聚的展開狀態；圖片與圖釘模式行為一致。
- 群聚展開狀態透過 MarkerCluster 的 `spiderfied` / `unspiderfied` 事件追蹤，以展開群聚內子 marker 的 LatLng 作為識別依據（不依賴 venueId）。cluster UI state 與活動 selection state 必須分離。
- `selectedLocationId` 是 map activity selection 的 single source of truth；`selectedEventId`／`selectedVenueId` 只做輔助資料，不可各自決定紅框。
- 紅框優先代表 Map popup 目前正在觀看的 activity marker；沒有 active selection 時代表最後看過的 marker。同時間只顯示一個主要紅框。Discover、Latest、Search、deep link、marker click、Cluster Picker、Nearby Picker 與 popstate 必須共用同一 selection pipeline。Map popup 不提供跨活動 swipe／上一個／下一個 carousel。
- selected marker 被 cluster 包住時，必須使用 MarkerCluster reveal API 自動顯示；同座標仍無法分辨時自動 spiderfy。
- `unspiderfied` 只表示 cluster UI 收合，不表示取消 activity selection，也不得清除 `selectedLocationId`。cluster lifecycle、moveend、zoomend、flyTo、invalidateSize 與 redraw 都不得自行取消 selection。
- 不使用 `setTimeout` 作為群聚恢復或 marker 渲染的修補；使用 `requestAnimationFrame` 搭配 MarkerCluster 實際事件。
- 地圖初始畫面與 Home 鍵使用 `TW_MAIN_BOUNDS`（主島＋澎湖），避免離島拉大視野。`TW_BOUNDS`（含離島）僅用於 maxBounds 平移限制。
- 水滴圖釘模式啟用時，桌機左側篩選面板底部需顯示活動形式的顏色與圖案圖例；圖片模式時隱藏。

## Discover、篩選與活動詳情

- 探索首頁採 Editorial C：首頁直接呈現「這週想去哪？／附近／最近發現」，不顯示 `Discover / Latest` switch；Latest 的資料定義保留，並由「最近發現」與其完整 Collection view 使用。
- Latest 是最近 7 個 Asia/Taipei 日曆日內第一次加入 ACG Map 的活動（包含今天），不得使用活動開始日、公告日、KV 日期、`DATA.updated` 或 Git 最新 commit 代替。
- 加入日期使用 stable event ID 對應的 persistent `data/event_first_seen.json`；既有 ID 保留原日期，新 ID 才登記台北當日，無法可靠回填時使用 `null`。
- Latest 共用 city、time、form、fee、multi 與 search，只改 Discover list，不得改 marker dataset、selection、popup、filters 或 map viewport；Discover 與 Latest 分別保存 scroll position。
- 點擊 Discover 活動卡時，地圖同步移動至該活動的代表地點；手機版接著切至 Map 並開啟該地點資訊卡。
- 一般篩選下 Discover 維持一活動一卡；只有選定特定「多店活動」時，改為逐門市列出同一活動。
- 多店活動篩選選項的數字代表目前其他篩選條件下的可見門市數，不是活動群組數。
- 活動 popup 只顯示目前定位的主要地點，不再列出其他活動地點。
- Map popup 不提供跨活動上一個／下一個、`1 / N`、桌機方向鍵切換或手機左右 swipe。使用者要看另一活動時直接點另一 marker；同園區大量活動使用 Fullscreen Activity Picker，附近探索使用 Nearby Picker，大量瀏覽使用 Collection。底層距離清單只可作為 Nearby 計算，不得再暴露成 popup carousel。
- 桌機與手機活動 popup 共用橫式卡片資訊結構：左 KV、右資訊。手機高度約螢幕 1/3；桌機使用地圖內底部 docked card，不使用阻斷探索的全螢幕 event modal。桌機 card 應盡量使用地圖寬度、以內容撐高並一次顯示核心資訊，不提供 card 內垂直捲動。大型文化園區 destination 的多活動 cluster 才使用 Fullscreen Activity Picker。
- Popup 的閱讀順序固定為活動名稱 → 目前地點／導航 → 目前 location 日期 → `#縣市`／`#付費狀態` → 官方資訊／分享；IP、主辦與授權商都不進 compact popup。浮動活動仍顯示「請至官方網站查詢地點」。Nearby CTA 屬 secondary interaction，可保留在主要資訊之後。
- Popup 以目前 location 為中心顯示 2 公里內其他活動的 Nearby CTA。Nearby 尊重所有 active filters、排除目前 event、包含同場館的其他 event，並以 event 去重及最近 occurrence 作為目標。
- Nearby CTA 與大型文化園區 destination cluster／需要明確選活動的 venue selection 共用 Fullscreen Activity Picker。Picker 是 transient UI，不寫入核心 selection 或 history；一般多地點 Cluster 不得開 Picker。Nearby Picker 關閉後保留底層 popup，點卡片後一律關閉 Picker再呼叫 `selectLocation()`。
- 桌機與手機活動 popup 皆保留純文字 tertiary context：`#縣市` 與 `#付費狀態`（例：`#台北市 #免費`）；不擴張成活動形式／IP 等大量 chips。
- 地點列只保留無外框的「導航」文字連結，不顯示 Threads 圖示；手機橫式卡的場館列本身即為導航連結。
- 「分享活動」一律直接複製目前活動的深連結，成功後顯示「成功複製連結」；Open Graph 連結預覽留待後續設計。
- 公開顯示值若含「需人工確認」，整個值留白；後台原始稽核資料可保留該文字。
- Mobile popup 只能存在於 Map；Map → Discover 必須 close popup 並 clear active map selection，但保留合法的 last-viewed 紅框供回到 Map 時恢復。若 filter 或 rerender 已排除該 location，才清除 last viewed。
- 手機 Map hidden 時不得執行或保存 user viewport。首次進 Map 且無 explicit target 時顯示 `TW_MAIN_BOUNDS`；後續回 Map 恢復離開前真正的 user viewport。
- viewport 優先序固定為 activity target > city target > user map view > Taiwan default。

## 變更規則

- 地圖框架、底圖、圖釘分類視覺或資料粒度的重構，必須先逐項列出保留／改動內容。
- 相關決策必須同時落在程式碼測試中；只測「功能存在」不足以保護既有視覺規則。
- 任何刻意改動本文件內容的 PR，需在 PR 說明中明列差異與 Daniel 的確認依據。

最後更新：2026-08-10（Asia/Taipei）

## 2026-08-12 — Editorial C 探索首頁（取代同日舊 Quick Intent 版）

- 探索首頁不是 Filter/List 工具首頁；第一層固定為「這週想去哪？／附近／最近發現」三個 editorial sections。首頁不得顯示 Today／Weekend 數字 chip、活動總數 badge、`Discover / Latest` switch 或排名數字。
- 「這週想去哪？」實際範圍為 Asia/Taipei 今天起未來 7 個日曆日；手機最多 5 張橫向 Hero cards，桌機只呈現前 3 張（1 大 2 小）。首頁 selection 使用可解釋規則：快結束 → 7 日內新開始 → first_seen 最近 → 其他有效活動，並做 IP／活動形式多樣化；沒有可用 KV 的活動不進 Hero，但仍可出現在完整 Results。
- 「這週想去哪？」的「查看全部」進入 Weekly Collection：桌機以 2 欄等權 KV cards＋右側 persistent Map 呈現，手機以單欄 image-first cards 呈現；首批直接增加可瀏覽的 KV 數量，之後可用「載入更多」續載。不得因查看全部而切回舊 Filter/List/Map 三欄工具版。
- 「附近」是首頁內容 section，不是 quick-sort pill。未授權時只顯示「使用目前位置」CTA；必須由使用者點擊後才呼叫 geolocation。授權後首頁顯示 20 公里內最近 3 個不同 event，多店活動只取最近 eligible location；「查看更多」進入距離排序的 Nearby Collection，「地圖查看」才主動調整 map viewport。兩者都沿用同一 location target 與 `selectLocation()`。
- 「最近發現」沿用 first_seen / Latest 最近 7 日定義；手機最多 3 筆 compact rows，桌機最多 4 張 2×2 cards。它可避開已出現在「這週想去哪？」的 event；Nearby 不為視覺去重而犧牲真實距離排序。
- Desktop Home 與 Collection 都維持 `Editorial content × persistent map` 兩欄；Filter sidebar 不常駐，只有使用者主動點「篩選」才以 drawer overlay 開啟。搜尋固定放在右側地圖上方，Marker 圖釘／圖片切換放右上。Collection 不得切回舊三欄工具架構。
- Desktop Home card hover 只 highlight 對應 marker，不 flyTo；click 才走既有 `selectLocation()` / reveal / popup pipeline。
- Mobile Home 頂部是 `ACG MAP` brand + search icon + filter icon；底部只有「探索／地圖」。首頁不把 search input 常駐成工具列；搜尋 icon 展開搜尋面板，輸入後進 image-first Search Collection。
- Home 與所有 Collection 共用同一套 light/dark editorial consumer-product visual system；首頁 teaser 可用不對稱 hierarchy，Collection 為方便比較改用規律 grid，但 KV 尺寸不得因「查看更多」反而縮成工具型小縮圖。Positron 地圖與既有 pin 類型配色不變。Filter facet counts、日期、距離、Map cluster counts 屬功能性資訊，可保留；禁止的是把首頁做成統計儀表板。
- `selectLocation()`、Nearby popup、Popup carousel、lastViewed、Activity Picker、MarkerCluster/spiderfy、selectedLocationId SSOT、deep link、popstate 與 first_seen 定義不得因本次首頁重排而重構。

- 2026-08-12：Editorial C 介面提供暖白／黑色小型主題 switch。暖白為預設；使用者手動選擇會以 `localStorage` 的 `acg-map-theme` 保存。主題切換只改 UI visual chrome，不改活動資料、filter、selection、popup、cluster 或 map viewport state。


## 2026-08-12 — Collection Page UX

- 首頁 section CTA 的語意固定：`查看全部／查看更多／探索更多` 代表進入同主題的完整 Collection，必須增加同類內容供瀏覽；不得讓 Filter sidebar 自動出現、不得把 KV 卡縮成舊工具 List，也不得改成不同視覺系統。
- Weekly／Nearby／Recent Collection 共用同一套 image-first Collection template；桌機 2 欄 cards＋persistent Map，手機單欄 cards。Search results 也使用相同 Collection card system。
- Collection 首批桌機顯示 8 張、手機顯示 6 張；若仍有內容，底部「載入更多」以同樣卡片規格追加下一批。
- Filter 與「查看更多」是不同 intent：Filter 只有使用者主動點擊才開 drawer，套用後只改 Collection 內容，不改版型。
- Nearby 同時提供「查看更多」與「地圖查看」：前者維持內容瀏覽，後者才切換／調整空間視角。

## 2026-08-12 — Map exploration / Filter 微調

- 篩選的「活動時段」只保留 `不限／進行中／即將開始／即將結束`，不再提供「今天／週末／未來 7 天」preset；`進行中` 與 `即將結束` 為互斥狀態。
- 「活動時段」下方提供月曆。點單一日期代表 `event.start <= selected_date <= event.end`；日期選擇與狀態選擇互斥，選其中一種會取代另一種。月曆只以小點提示當天有符合其他 active filters 的活動，不在日期格顯示活動數。
- 「最近發現」Collection 的母集合固定為 `first_seen` 最近 7 個 Asia/Taipei 日曆日；進入這頁後仍可篩選，但所有 facet count、disabled 狀態與摘要統計都必須先限制在這個 7 日母集合，再套 city／time／form／fee／multi／query。
- 暖白模式的 Filter 關閉 X 使用 warm semantic surface／text token，不得維持黑底高對比；dark mode 使用對應深色 surface。
- 使用者自己的位置 marker 使用鮮紅實心圓＋白色 halo＋淡紅外圈；活動 selected marker 仍用原 marker shape 的紅色 outline，兩者不得混為同一語意。

## 2026-08-12 — Desktop Map controls / Destination cluster / City viewport 微調

- Desktop `Home / + / -` 為同一組 map navigation utility，固定在右上垂直排列；移開右下縮放控制是為了釋放 bottom card 空間，手機仍保留原生右下縮放。
- Desktop activity card 使用更寬、內容撐高的 bottom dock，一次顯示活動名稱、地點／導航、日期、`#縣市 #付費狀態`、官方資訊／分享與 Nearby；card 本身不得上下捲動。
- Map popup 不再提供跨活動 carousel：沒有 `1 / N`、左右箭頭、桌機方向鍵或手機左右 swipe。另一個活動由 marker、Destination Picker、Nearby Picker 或 Collection 進入。
- 大型文化園區以 UI 靜態 canonical destination config 判定，不寫入每日活動資料。現階段包含華山1914、松山文創園區、駁二藝術特區（含官方／既有別名）、花蓮文化創意產業園區、嘉義文化創意產業園區。只有 cluster 的所有目前可見子活動都屬於同一 destination 且至少有 2 個不同活動時才直接 Fullscreen；混合一般地點的 cluster 先 zoom／spiderfy。
- Desktop 選定縣市 Filter 後立即 `fitCityView(city)`；選全台灣回 `fitTaiwanView()`。此 viewport side effect 不得選活動、開 popup 或改寫 selection。Mobile 若正在 Map 則立即 fit；若仍在 Explore，只記錄 pending city target，下一次使用者自行進 Map 時優先顯示該縣市，不可自動切 tab。

## 2026-08-18 — 場館資料生命週期與 geocode SSOT

- `data/manual/venue_geocodes.json`、`venue_address_overrides.json` 等人工場館修正是**持久的人工決策層**。已驗證的地址、座標與精度必須保留，供目前與未來活動重用；它們不是「目前必須出現在地圖上的場館清單」。
- `public/venues.json` 是**依當期有效活動動態產生的衍生輸出**，不是場館或 geocode 的 SSOT。只有至少一筆活動通過日期、分類、審核與 metadata 門檻的場館才應出現在公開地圖。
- 場館的最後一筆活動到期、被拒絕或因資料不完整而隔離後，該場館應自然退出 `public/venues.json`；這不等於人工座標遺失。日後同一正規化場館名稱出現新活動時，管線必須重新套用既有人工地址與 geocode，不得要求空場館永久留在公開輸出。
- 測試必須分開保護兩種不同生命週期：
  1. **持久決策完整性**：已確認的人工 geocode 記錄仍存在，且地址、座標與精度未被自動流程覆寫。
  2. **當期輸出正確性**：目前有公開活動的已驗證場館，其公開地址、座標與精度必須與人工決策一致。
- 不得把某日快照中的場館數、場館名單或精度統計，直接寫成未來每次 `public/venues.json` 都必須維持的永久不變量。2026-08-09 的「65 筆、54 exact／11 building」只代表該批人工 geocode 決策的完整性，不代表公開地圖必須永久顯示 65 個場館。
- 不得為通過測試而延長已到期活動、製造空白活動、保留空場館，或針對單一到期場館寫例外。若仍有有效且資料完整的活動卻整個場館消失，才屬資料管線 regression，必須另行阻擋並查明原因。

## 2026-08-19 — 六館官網日期品質與官方 ACG 重疊模型

- 六館官網資料的日期必須先通過格式與生命週期檢查，才可進入 `data/generated/venue_extra.json` 與公開輸出。完整日期只接受可解析的西元 `YYYY/MM/DD`；民國年必須明確落在合理範圍後換算。像 `11/8-9` 這種月／日區間不得把尾端的 `9` 誤認為年份並產生 `11/08/09`。
- 對會保留歷史頁面的官方來源（目前包含嘉義文化創意產業園區、圓山花博），若活動開始日已過且官方沒有可驗證的結束日，必須先隔離，不得無限期留在公開地圖；未來開始、但尚未公布結束日的活動可保留。松山文創園區原始資料已提供完整起訖日，仍須通過同一公開輸出日期驗證門檻。
- 日期品質採兩層防線：`collect_venues.py` 在擷取時拒絕不合法／過期且無結束日的資料，`refresh_venues.py` 在合併公開輸出時再次驗證。只從某日的 generated 或 public JSON 刪除壞資料屬一次性清理，不算完成修正。
- `data/generated/venue_extra.json` 是六館完整爬蟲與稽核層，可保留日期有效但尚未判定為 ACG 的官方活動；`public/venues.json` 是 ACG 地圖產品輸出，只能包含 `c=ACG` 且通過完整欄位門檻的活動。不得把非 ACG 活動交給前端再隱藏；過濾後沒有 ACG 活動的場館必須退出公開輸出。
- 官方六館來源若已存在同一活動，該官方紀錄仍是活動名稱、日期、地點、連結與 KV 的自動資料來源；人工 ACG 層只以標題重疊紀錄與 overrides 補上分類、形式、費用、主辦、授權／權利方及查證 provenance，不得再建立第二個重複公開活動。
- 自動來源中的 ACG 活動也必須通過與人工活動相同的公開欄位門檻：`c=ACG`、四種允許形式之一、免費／付費、主辦、授權／權利方、HTTPS 合格活動連結與 repository 內可用 KV。若官方未公開主辦，使用「活動官方未公開」並保存查證來源；不得猜測。
- 「偶像夢幻祭 2 聚光舞台主題快閃店 台北場」是此模型的回歸案例：松山官網資料提供日期、地點、免費資訊、活動連結與官方 KV；人工 overrides 補為 ACG／快閃店、主辦「活動官方未公開」、權利方 `Happy Elements K.K.`。測試需同時確認公開資料完整、ID 穩定、KV 已落地，以及 manual decision/provenance 仍存在。
