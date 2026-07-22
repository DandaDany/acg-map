# 待補 KV 工單

產生日期：2026-07-22　本檔由 `backend/report_event_kv.py` 隨 `update_all.py` 自動重產，請勿手改。

目前 146 場活動：已自存 115、有風險 31（其中 FB/IG 會過期 30 筆、已破圖 29 筆、官網未自存 1 筆、無圖 0 筆）。

## 補圖 SOP（A 區每筆照做，比照『藍色監獄×指南針武昌店』那筆）

1. 開該筆「來源連結」的 FB/IG 貼文，找官方主視覺（hi-res）。
2. 下載存到 `data/manual/_kv_cache/`，檔名建議 `作品_場地_YYYYMMDD.jpg`。
3. 在 `data/manual/acg_events.json` 對應活動的 `KV` 欄改成 repo 內永久 raw URL：`https://raw.githubusercontent.com/DandaDany/acg-map/main/data/manual/_kv_cache/<檔名>`
4. commit（含圖檔）。下次 `update_all.py` 的 `download_event_kv` 會再自存到 `public/kv/`，雙保險。

## A. 需人工補（FB/IG 會過期，無法自動抓回）— 30 筆

| # | 完成 | 場館 | 活動 | 狀況 | 來源連結 |
|---|---|---|---|---|---|
| 1 | ☐ | 台北三創生活園區 6F INCUBASE Arena | 《東京喰種》期間限定快閃店 | 已過期破圖（到期 2026-07-06） | https://www.instagram.com/p/DZpKKNpDIN3/ |
| 2 | ☐ | LaLaport 台中北館1F | 名偵探柯南 高速公路的墮天使 快閃店 | 已過期破圖（到期 2026-07-16） | https://www.instagram.com/p/DZGy_q_ARWM/?img_index=1 |
| 3 | ☐ | MITSUI OUTLET PARK 林口I館室內棟1F 六角廣場 | 名偵探柯南 高速公路的墮天使 快閃店 | 已過期破圖（到期 2026-07-16） | https://www.instagram.com/p/DZGy_q_ARWM/?img_index=1 |
| 4 | ☐ | 中友百貨 | 孤獨搖滾！動畫展（台中場） | 已過期破圖（到期 2026-06-26） | https://www.instagram.com/p/DY3xo0lDO42/ |
| 5 | ☐ | 光點台北側門 羊空間 YOUNG SPACE | AIR TWOKYO POP UP STORE | 已過期破圖（到期 2026-07-14） | https://www.instagram.com/p/DaWucdFv8Yj |
| 6 | ☐ | 台中中友百貨B棟13樓 | 名偵探柯南 高速公路的墮天使 快閃店 | 已過期破圖（到期 2026-07-16） | https://www.instagram.com/p/DZGy_q_ARWM/?img_index=1 |
| 7 | ☐ | 台中中友百貨B棟13樓 文化大廳 | 三麗鷗甜心復古快閃店 | 已過期破圖（到期 2026-07-14） | https://www.instagram.com/p/DaUNtsBJxu0 |
| 8 | ☐ | 台北三創生活園區 | 九井諒子展 及 《迷宮飯》迷宮探索展 台灣站 | 已過期破圖（到期 2026-06-26） | https://www.facebook.com/ryoko.kui.dungeonmeshi.exhibit/posts/pfbid032Ef5k9GqKLmkeKPBAbZ6PxRL2Ffum338mMXYLEaJyp5GArNZNXLzi74DRYHFgp1Tl?locale=zh_TW |
| 9 | ☐ | 台北世界貿易中心展覽一館 | 《落第忍者亂太郎》40週年紀念原畫展（海外首度登場） | 已過期破圖（到期 2026-07-14） | https://www.instagram.com/p/DaUQi_4FctQ |
| 10 | ☐ | 台東縣鹿野鄉高台 | 吉伊卡哇-2026 臺灣國際熱氣球嘉年華 | 已過期破圖（到期 2026-06-26） | https://www.facebook.com/balloontaiwan |
| 11 | ☐ | 夢時代購物中心Ｘ野獸國 | ANI-FEST期間限定店 | 已過期破圖（到期 2026-06-26） | https://www.instagram.com/p/DYWFmd8jRZ2/ |
| 12 | ☐ | 微風廣場 Breeze MEGA Studio 8F C廳 & 9F D廳 藝文中心 | San-X 90週年紀念展in台灣 | 已過期破圖（到期 2026-06-26） | https://www.instagram.com/p/DZJepmSjPht/?img_index=1 |
| 13 | ☐ | 新光三越台北信義新天地A8館5樓 | 名偵探柯南 高速公路的墮天使 快閃店 | 已過期破圖（到期 2026-07-16） | https://www.instagram.com/p/DZGy_q_ARWM/?img_index=1 |
| 14 | ☐ | 新光三越台北南西店 一館 9F 活動會館 | JOJO CARAVAN 飆馬野郎複製原畫展 | 已過期破圖（到期 2026-06-26） | https://www.facebook.com/emuse.com.tw/photos/%F0%9D%97%9D%F0%9D%97%A2%F0%9D%97%9D%F0%9D%97%A2-%F0%9D%97%96%F0%9D%97%94%F0%9D%97%A5%F0%9D%97%94%F0%9D%97%A9%F0%9D%97%94%F0%9D%97%A1-%E5%8D%B3%E5%B0%87%E7%99%BB%E5%A0%B4%E7%82%BA%E7%B4%80%E5%BF%B5jojo-%E7%9A%84%E5%A5%87%E5%A6%99%E5%86%92%E9%9A%AA%E7%AC%AC%E4%B8%83%E9%83%A8steel-ball-run-%E9%A3%86%E9%A6%AC%E9%87%8E%E9%83%8E%E6%AD%A3%E5%BC%8F%E5%8B%95%E7%95%AB%E5%8C%96%E5%AE%98%E6%96%B9%E5%B7%A1%E8%BF%B4%E5%B1%95%E8%A6%BDjojo-caravan%E5%8D%B3%E5%B0%87%E4%BE%86%E5%8F%B0%E7%8F%BE/1478337260995605/ |
| 15 | ☐ | 新光三越台南小北門店1F | GODZILLA STORE 台南期間限定快閃店 | 已過期破圖（到期 2026-07-14） | https://www.instagram.com/p/DaT8RkDAeAX |
| 16 | ☐ | 新光三越高雄左營店 10F | Hello Kitty展 高雄站 | 已過期破圖（到期 2026-06-26） | https://www.instagram.com/p/DZHVbrREseB/?img_index=1 |
| 17 | ☐ | 花蓮縣壽豐鄉鯉魚潭 | 2026花蓮FUN暑假 | 已過期破圖（到期 2026-07-06） | https://www.instagram.com/p/DZrU9yxgT5x/ |
| 18 | ☐ | 誠品R79 中山地下書街B1 | mofusand快閃店 | 已過期破圖（到期 2026-07-14） | https://www.instagram.com/p/DaURh41Sp6r |
| 19 | ☐ | 誠品生活新店 | 「夏日動漫時光機」展 | 已過期破圖（到期 2026-07-16） | https://www.instagram.com/p/Daj62-JJU6Q |
| 20 | ☐ | 誠品生活松菸店 | 「夏日動漫時光機」展 | 已過期破圖（到期 2026-07-16） | https://www.instagram.com/p/Daj62-JJU6Q |
| 21 | ☐ | 誠品生活武昌店 | 「夏日動漫時光機」展 | 已過期破圖（到期 2026-07-16） | https://www.instagram.com/p/Daj62-JJU6Q |
| 22 | ☐ | 誠品生活西門店 | 「夏日動漫時光機」展 | 已過期破圖（到期 2026-07-16） | https://www.instagram.com/p/Daj62-JJU6Q |
| 23 | ☐ | 駁二藝術特區 | 《凡爾賽玫瑰》快閃空間 | 已過期破圖（到期 2026-06-26） | https://www.instagram.com/p/DZZ0g9UpJHY/ |
| 24 | ☐ | 高雄夢時代購物中心 1F | 名偵探柯南 高速公路的墮天使 快閃店 | 已過期破圖（到期 2026-07-16） | https://www.instagram.com/p/DZGy_q_ARWM/?img_index=1 |
| 25 | ☐ | 高雄夢時代購物中心8樓 時代會館 | primaniacs 夢時代POPUP 2026 | 已過期破圖（到期 2026-07-14） | https://www.instagram.com/p/DaU5z0TFPTd |
| 26 | ☐ | 高雄駅一番街・北站 高雄捷運高雄車站B2 | 藥師少女的獨語展 | 已過期破圖（到期 2026-06-26） | https://www.instagram.com/p/DZXNgpEH63L/?igsh=aTBkbWdxNGp3cXBl |
| 27 | ☐ | 早點出發 / EATWITHGO | 早點出發 / EATWITHGO / 日式喫茶店 / 貝果專賣 / 神奇寶貝同好交流 | 已過期破圖（到期 2026-06-26） | https://www.instagram.com/eatwithgo/ |
| 28 | ☐ | 凱岩咖啡 - 忠孝店 | 楓之谷 x 凱岩主題餐廳 | 已過期破圖（到期 2026-07-06） | https://www.cayenne-cafe.com.tw/NewsCount.aspx?id=23 |
| 29 | ☐ | 凱岩咖啡 - 永康店 | 賽爾號 x 凱岩主題餐廳 | 已過期破圖（到期 2026-06-25） | https://www.cayenne-cafe.com.tw/NewsCount.aspx?id=22 |
| 30 | ☐ | object taipei store | 《Marshville Quokscout》 | 會過期（到期 未知） | https://www.instagram.com/p/DZwtQdGE2ro?img_index=1 |

## B. 官網外站圖（下次 update_all 自動自存，通常免手動）— 1 筆

| # | 場館 | 活動 | 狀況 | 來源連結 |
|---|---|---|---|---|
| 1 | 華山1914文化創意產業園區 | 《天官賜福》 | 尚未自存（外站官網圖，下次 update_all 可自動修） | https://www.huashan1914.com/w/huashan1914/exhibition_26062413384986627 |
