#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每週一/四 11:10 的維護回報腳本。
讀 venues.json，與上次快照 _report_prev.json 比對，輸出：
 (1) 新增了什麼 (2) 資料缺口總覽(連結/KV/座標) (3) 分類複核(官網活動疑似漏判ACG) (4) 建議補什麼怎麼補。
跑完把目前 venues.json 存成 _report_prev.json 供下次比對。

2026/07/12 排呈調整（依 Daniel 需求）：
 - 地圖範圍已收斂為「ACG 活動 ＋ 六大文創園區活動」，官網爬蟲只留六大園區，
   前端圖釘也已改用活動形式圖示，不再顯示場館 logo（見 docs/README_docs.md 六欄交接狀態）。
   → 移除「缺場館 logo」統計與建議（此為配合前端改版的排呈調整，非資料判斷，需人工複核見報表末）。
 - 新增「分類複核」章節：官網（六大文創園區）來源的活動，目前分類機制（refresh_venues.py
   classify_theme_kw）靠關鍵字表判斷主題，新出現的 IP／角色若不在關鍵字表裡，會被歸到
   「其他文化」而非「ACG」。此區塊逐筆列出這類活動，供人工複核是否其實是 ACG，
   本腳本本身不會、也不能自動改動 venues.json 的分類（只讀不寫資料本體）。
用法：python3 report_status.py
"""
import json, os, time, datetime
from paths import path as P
from report_event_kv import kv_status  # 共用同一套 KV 判斷（img 空 / 會過期外站網址 / 已自存）

HERE = os.path.dirname(os.path.abspath(__file__))
def load(path, retries=6):
    for i in range(retries):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except OSError:        # 同步掛載偶發 Resource deadlock avoided
            time.sleep(2)
        except Exception:
            return None
    return None

def venues_of(d):
    if isinstance(d, dict): return d.get("venues", [])
    return d or []

def main():
    cur = load(P("venues.json"))
    if cur is None:
        print("⚠️ 無法讀取 venues.json（檔案系統忙碌/鎖定），本次回報略過。"); return
    vs = venues_of(cur)
    prev = load(P("_report_prev.json"))
    pvs = venues_of(prev) if prev else []

    # 索引
    def ex_key(vn, e): return (vn, e.get("t", ""))
    cur_v = {v["name"] for v in vs}
    prev_v = {v["name"] for v in pvs}
    cur_ex = {ex_key(v["name"], e) for v in vs for e in v.get("ex", [])}
    prev_ex = {ex_key(v["name"], e) for v in pvs for e in v.get("ex", [])}

    new_venues = sorted(cur_v - prev_v)
    gone_venues = sorted(prev_v - cur_v)
    new_ex = [k for k in cur_ex - prev_ex]

    # 統計
    n_v = len(vs); n_e = sum(len(v.get("ex", [])) for v in vs)
    miss_link = [(v["name"], e["t"]) for v in vs for e in v.get("ex", []) if not e.get("l")]
    # 缺 KV = 完全沒圖 或 img 仍指向會過期外站網址（cdninstagram/fbcdn/oe=，會破圖）。
    # 只判 e.get("img") 為空會漏掉「假有圖、實破圖」的活動，故改用 kv_status 一併揪出。
    miss_kv = []
    for v in vs:
        for e in v.get("ex", []):
            code, expiry = kv_status(e.get("img"))
            if code == "ok":
                continue
            if code == "empty":
                note = "無圖"
            elif code == "expiring":
                note = "已過期破圖" if (expiry and expiry < datetime.date.today().isoformat()) else "會過期外站網址"
            else:  # remote
                note = "尚未自存(外站官網圖)"
            miss_kv.append((v["name"], e["t"], note))
    approx    = [v["name"] for v in vs if v.get("loc") and v["loc"] != "exact"]
    from collections import Counter
    src = Counter(v.get("src", "?") for v in vs)
    cats = Counter(e.get("c", "?") for v in vs for e in v.get("ex", []))

    pct = lambda a, b: f"{a*100//b}%" if b else "0%"
    print(f"# 全台 ACG 活動地圖　維護回報　{datetime.date.today():%Y/%m/%d}")
    print(f"目前：{n_v} 場館 / {n_e} 場活動　｜　來源 {dict(src)}　｜　主題分布 {dict(cats)}")
    print("（範圍已收斂為 ACG 活動＋六大文創園區活動，來源：文化部 API 已停用、官網爬蟲僅留六大園區＋手動/CACO/Cayenne，"
          "見 docs/README_docs.md 交接狀態 ✅已驗證）")
    print()
    print("## 1. 新增了什麼")
    if not prev:
        print("（首次執行，尚無上次快照可比對，已建立基準。）")
    else:
        print(f"- 新增場館 {len(new_venues)} 個" + (f"：{'、'.join(new_venues[:15])}" if new_venues else ""))
        print(f"- 新增活動 {len(new_ex)} 場" + (f"，例如：{'、'.join(t for _,t in new_ex[:10])}" if new_ex else ""))
        if gone_venues: print(f"- 減少/改名場館 {len(gone_venues)} 個：{'、'.join(gone_venues[:10])}")
    print()

    print("## 2. 資料缺口總覽")
    print("（場館 logo 自 2026/07/12 起不再列入本報表：前端圖釘已改用活動形式圖示，不再顯示場館 logo，"
          "logo 缺漏對現行地圖已無實質影響，此為配合前端改版的排呈調整 ⚠️需你覆核是否同意）")
    print(f"- 缺官方連結：{len(miss_link)} / {n_e} 場（{pct(len(miss_link),n_e)}）")
    if miss_link:
        print("  | 場館 | 活動 |")
        print("  |---|---|")
        for vn, t in miss_link:
            print(f"  | {vn} | {t} |")
    print(f"- 缺主視覺 KV：{len(miss_kv)} / {n_e} 場（{pct(len(miss_kv),n_e)}）"
          "（含 img 為空 與「仍指向會過期外站網址、已破圖/將破圖」者）")
    if miss_kv:
        print("  | 場館 | 活動 | 狀況 |")
        print("  |---|---|---|")
        for vn, t, note in miss_kv:
            print(f"  | {vn} | {t} | {note} |")
    print(f"- 約略定位（非精確座標）：{len(approx)} / {n_v} 館（{pct(len(approx),n_v)}）" + (f"：{'、'.join(approx)}" if approx else ""))
    print()

    print("## 3. 分類複核：官網（六大文創園區）活動疑似漏判 ACG")
    official_ev = [(v["name"], e) for v in vs for e in v.get("ex", []) if e.get("src") == "official"]
    official_non_acg = [(vn, e) for vn, e in official_ev if e.get("c") != "ACG"]
    n_off = len(official_ev); n_off_acg = n_off - len(official_non_acg)
    print(f"- 官網來源活動共 {n_off} 場，目前已標記 ACG {n_off_acg} 場（{pct(n_off_acg, n_off)}），"
          f"其餘 {len(official_non_acg)} 場（{pct(len(official_non_acg), n_off)}）為「其他文化／藝術設計」。")
    print("  原因：這些活動的主題判斷靠 refresh_venues.py 的關鍵字表（THEME_ACG_KW），"
          "新出現、不在關鍵字表裡的角色/作品名稱（例如新連載漫畫、新番動畫、新角色聯名）不會被抓出來，"
          "只會落到「其他文化」，不是程式判定它們一定不是 ACG。")
    if official_non_acg:
        print("  逐筆列出如下，標 ★ 者為「快閃店」形式（經驗上與角色 IP 聯名快閃重疊率較高，建議優先看）：")
        print("  | 場館 | 活動 | 目前主題(c) | 目前形式(c2) |")
        print("  |---|---|---|---|")
        for vn, e in official_non_acg:
            mark = "★ " if e.get("c2") == "快閃店" else ""
            print(f"  | {vn} | {mark}{e.get('t','')} | {e.get('c','')} | {e.get('c2','')} |")
    flagged = [(v["name"], e) for v in vs for e in v.get("ex", []) if e.get("c_flag")]
    if flagged:
        print(f"  另有 {len(flagged)} 筆既有「模糊比對」警示（c_flag=需人工確認，與 Excel 活動標題相似度 0.70–0.85）：")
        for vn, e in flagged:
            print(f"    - {vn}｜{e.get('t','')}（目前 c={e.get('c','')}）")
    print("  複核方式：確認是 ACG 的話，不需改程式碼，在 data/manual/event_overrides.json 加一筆"
          "（格式：{\"活動標題\": {\"c\": \"ACG\"}}，可一併指定 c2），下次跑 update_all.py 會覆蓋自動判斷。")
    print()

    print("## 4. 建議執行順序（AI 判斷，非需求指示，僅供參考）")
    if official_non_acg:
        print(f"1. 分類複核：{len(official_non_acg)} 場官網活動疑似漏判 ACG，本輪新增部分（見第1節「新增活動」）優先看，"
              "確認後補 event_overrides.json。")
    if miss_kv:
        print(f"2. KV：{len(miss_kv)} 場缺/破圖主視覺。有官方活動頁者跑 collect_event_kv.py "
              "--browser-fallback 多數可自動補齊；標『會過期/已破圖』者屬 FB/IG 簽章網址，"
              "須趁未過期時下載官方主視覺、commit 進 data/manual/_kv_cache/ 並改引用 repo 內"
              "永久 raw URL（比照『藍色監獄×指南針武昌店』那筆），無法靠自動抓取救回。")
    if approx:
        print(f"3. 座標：{len(approx)} 館還是約略定位 → 補完整地址後跑 geocode_venues.py。")
    if len(miss_link) > n_e * 0.3:
        print(f"4. 連結：{pct(len(miss_link),n_e)} 活動沒有官方連結 → 補進 event_link_overrides.json。")
    print("- 持續把新檔期/快閃整理進 manual_extra.json（或品牌收集器），維持 ACG 產品主打。")
    print()
    print("## 需人工確認清單（不確定/疑似異常，未自行判定）")
    print("- 第2節移除 logo 統計，是配合前端已完成的改版（README_docs.md 已標記 ✅已完成），"
          "但本報表這項排呈調整本身是 AI 判斷，非你逐字指示的規格，請覆核是否同意完全移除、或保留精簡版供未來復用 logo 時參考。")
    print("- 第3節「★快閃店優先看」的排序提示是 AI 依經驗判斷的排序建議，不是分類結論；"
          "清單本身逐筆列出未經篩選，避免遺漏。")

    # 存快照
    try:
        json.dump(cur, open(P("_report_prev.json"), "w", encoding="utf-8"), ensure_ascii=False)
    except Exception:
        pass

if __name__ == "__main__":
    main()
