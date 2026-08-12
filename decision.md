# ACG 地圖產品決策

> 本文件記錄不可在一般功能追加或版面重構時擅自改動的產品行為。若新需求與本文件衝突，必須先向 Daniel 說明影響並取得明確同意，同步更新本文件與測試。

## 地圖背景

- 預設底圖使用 OpenFreeMap Positron 向量樣式：`https://tiles.openfreemap.org/styles/positron`。
- 主要道路與快速道路使用白色內線、淡灰色外框，縮放越近逐步加粗；次要道路於高縮放層級顯示。
- 台灣鄉鎮市區邊界為 `#8fa0b5`、線寬 `0.7`、透明度 `0.5`、不填色。
- 縮放低於 11 顯示縣市名稱；縮放 11 以上顯示鄉鎮市區名稱。
- 地圖縮放範圍為 6–16，初始畫面涵蓋台灣；桌機與手機沿用既有台灣範圍限制。
- 縮放控制位於右下角。
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
- 每個活動各自一個 marker；同場館／同座標的多個活動會聚合。桌機點擊聚合開啟共用的全螢幕 Activity Picker，不同步縮放；手機維持 zoom／最大層級 spiderfy。個別 marker 不顯示數字徽章；聚合徽章顯示該處活動數。
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
- 紅框優先代表 Map popup 目前正在觀看的 activity marker；沒有 active selection 時代表最後看過的 marker。同時間只顯示一個主要紅框。Discover、Latest、Search、deep link、marker click、popup swipe／arrow、Cluster Picker、Nearby Picker 與 popstate 必須共用同一 selection pipeline。
- selected marker 被 cluster 包住時，必須使用 MarkerCluster reveal API 自動顯示；同座標仍無法分辨時自動 spiderfy。
- `unspiderfied` 只表示 cluster UI 收合，不表示取消 activity selection，也不得清除 `selectedLocationId`。cluster lifecycle、moveend、zoomend、flyTo、invalidateSize 與 redraw 都不得自行取消 selection。
- 不使用 `setTimeout` 作為群聚恢復或 marker 渲染的修補；使用 `requestAnimationFrame` 搭配 MarkerCluster 實際事件。
- 地圖初始畫面與 Home 鍵使用 `TW_MAIN_BOUNDS`（主島＋澎湖），避免離島拉大視野。`TW_BOUNDS`（含離島）僅用於 maxBounds 平移限制。
- 水滴圖釘模式啟用時，桌機左側篩選面板底部需顯示活動形式的顏色與圖案圖例；圖片模式時隱藏。

## Discover、篩選與活動詳情

- 探索首頁採 Editorial C：首頁直接呈現「這週想去哪？／附近／最近發現」，不顯示 `Discover / Latest` switch；Latest 的資料定義保留，並由「最近發現」與其完整 Results view 使用。
- Latest 是最近 7 個 Asia/Taipei 日曆日內第一次加入 ACG Map 的活動（包含今天），不得使用活動開始日、公告日、KV 日期、`DATA.updated` 或 Git 最新 commit 代替。
- 加入日期使用 stable event ID 對應的 persistent `data/event_first_seen.json`；既有 ID 保留原日期，新 ID 才登記台北當日，無法可靠回填時使用 `null`。
- Latest 共用 city、time、form、fee、multi 與 search，只改 Discover list，不得改 marker dataset、selection、popup、filters 或 map viewport；Discover 與 Latest 分別保存 scroll position。
- 點擊 Discover 活動卡時，地圖同步移動至該活動的代表地點；手機版接著切至 Map 並開啟該地點資訊卡。
- 一般篩選下 Discover 維持一活動一卡；只有選定特定「多店活動」時，改為逐門市列出同一活動。
- 多店活動篩選選項的數字代表目前其他篩選條件下的可見門市數，不是活動群組數。
- 活動 popup 只顯示目前定位的主要地點，不再列出其他活動地點。
- 桌機與手機 popup 共用同一個活動序列：以目前地點為原點，將目前篩選後的有效 map locations 依距離由近到遠排列；灰色左右箭頭不循環，手機 swipe 與箭頭走同一個移動函式，桌機另支援方向鍵。
- 手機版活動 popup 為橫式卡片（左 KV、右資訊）、高度約螢幕 1/3。單一場館多場活動不再另出選擇格。
- 桌機與手機 popup 顯示 IP、主辦、日期、目前活動地點；空 IP、空主辦與空地址整列不顯示，不以 placeholder 代替。浮動活動仍顯示「請至官方網站查詢地點」。本次 popup 不新增授權商。
- Popup 以目前 location 為中心顯示 2 公里內其他活動的 Nearby CTA。Nearby 尊重所有 active filters、排除目前 event、包含同場館的其他 event，並以 event 去重及最近 occurrence 作為目標。
- Nearby CTA 與桌機 Cluster 共用同一個 Fullscreen Activity Picker。Picker 是 transient UI，不寫入核心 selection 或 history；Nearby Picker 關閉後保留底層 popup，點卡片後一律關閉 Picker 再呼叫 `selectLocation()`。
- 桌機與手機的活動 popup 皆顯示目前地點所在縣市的 hashtag（例：`#台北市`）。
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
- 「查看更多」進入完整 Results mode，使用既有 Filter/List/Map 架構，並將 `未來 7 天` 作為正式 time filter preset；返回首頁時只撤回這個 route 注入的 time preset，不清除使用者在 Results 中主動修改的其他 Filter。
- 「附近」是首頁內容 section，不是 quick-sort pill。未授權時只顯示「使用目前位置」CTA；必須由使用者點擊後才呼叫 geolocation。授權後顯示 20 公里內最近 3 個不同 event，多店活動只取最近 eligible location；點卡片仍走 `selectLocation()`。使用者位置以獨立 marker 顯示；只有點「看地圖」才可主動調整 map viewport。
- 「最近發現」沿用 first_seen / Latest 最近 7 日定義；手機最多 3 筆 compact rows，桌機最多 4 張 2×2 cards。它可避開已出現在「這週想去哪？」的 event；Nearby 不為視覺去重而犧牲真實距離排序。
- Desktop Home 為 `Editorial content × persistent map` 兩欄；Filter sidebar 在 Home 隱藏，Filter 由 trigger 開啟 drawer。搜尋固定放在右側地圖上方，Marker 圖釘／圖片切換放右上。只有 Results mode 才恢復 Filter / List / Map 三欄工具架構。
- Desktop Home card hover 只 highlight 對應 marker，不 flyTo；click 才走既有 `selectLocation()` / reveal / popup pipeline。
- Mobile Home 頂部是 `ACG MAP` brand + search icon + filter icon；底部只有「探索／地圖」。首頁不把 search input 常駐成工具列；搜尋 icon 展開搜尋面板，輸入後進 Results mode。
- Home 與 Results 共用 light editorial consumer-product visual system；Positron 地圖與既有 pin 類型配色不變。Filter facet counts、日期、距離、Map cluster counts 屬功能性資訊，可保留；禁止的是把首頁做成統計儀表板。
- `selectLocation()`、Nearby popup、Popup carousel、lastViewed、Activity Picker、MarkerCluster/spiderfy、selectedLocationId SSOT、deep link、popstate 與 first_seen 定義不得因本次首頁重排而重構。

- 2026-08-12：Editorial C 介面提供暖白／黑色小型主題 switch。暖白為預設；使用者手動選擇會以 `localStorage` 的 `acg-map-theme` 保存。主題切換只改 UI visual chrome，不改活動資料、filter、selection、popup、cluster 或 map viewport state。
