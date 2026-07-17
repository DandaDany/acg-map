#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""download_event_kv 的離線單元測試（不連網，用注入式下載器 + 暫存目錄）。"""
import os, sys, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import download_event_kv as m


def test_is_expiring():
    assert m.is_expiring("https://scontent-tpe1-1.cdninstagram.com/x.jpg") is True
    assert m.is_expiring("https://instagram.frmq3-3.fna.fbcdn.net/x.jpg") is True
    assert m.is_expiring("https://media.huashan1914.com/a.jpg?oe=abcd") is True  # 帶 oe=
    assert m.is_expiring("https://media.huashan1914.com/a.jpg") is False         # 穩定官網
    assert m.is_expiring("https://www.g9cip.com/b.png") is False
    assert m.is_expiring("kv/deadbeef.jpg") is False                             # 已本地化
    assert m.is_expiring("") is False
    print("test_is_expiring: PASS")


def test_localize_and_gc():
    d = tempfile.mkdtemp()
    try:
        venues = [
            {"name": "駁二藝術特區", "ex": [
                {"t": "IG活動A", "s": "2026-08-01", "img": "https://scontent.cdninstagram.com/a.jpg?oe=1"},
                {"t": "官網活動B", "s": "2026-08-02", "img": "https://www.g9cip.com/b.png"},
            ]},
            {"name": "華山1914", "ex": [
                {"t": "IG活動C", "s": "2026-08-03", "img": "https://x.fbcdn.net/c.jpg"},
            ]},
        ]
        # 注入式下載器：只寫一個假檔，不連網
        def fake_dl(url, dest):
            with open(dest, "wb") as f:
                f.write(b"x" * 1024)
        rewritten, downloaded, failed = m.localize(venues, d, downloader=fake_dl, log=lambda *a, **k: None)
        assert (rewritten, downloaded, failed) == (2, 2, 0), (rewritten, downloaded, failed)
        # 兩個 IG 圖被改寫為站內路徑、官網圖不動
        assert venues[0]["ex"][0]["img"].startswith("kv/")
        assert venues[0]["ex"][1]["img"] == "https://www.g9cip.com/b.png"
        assert venues[1]["ex"][0]["img"].startswith("kv/")
        # 檔案確實落地
        assert len(os.listdir(d)) == 2
        print("test_localize_rewrite: PASS")

        # 冪等：真實管線每輪 refresh 會把 e.img 重寫回 IG 原網址，故先還原再跑，
        # 驗證「檔已存在→只改寫路徑、不重複下載」：改寫數 2、下載數 0。
        venues[0]["ex"][0]["img"] = "https://scontent.cdninstagram.com/a.jpg?oe=1"
        venues[1]["ex"][0]["img"] = "https://x.fbcdn.net/c.jpg"
        r2, d2, f2 = m.localize(venues, d, downloader=fake_dl, log=lambda *a, **k: None)
        assert (r2, d2, f2) == (2, 0, 0), (r2, d2, f2)
        print("test_localize_idempotent: PASS")

        # GC：模擬「活動C 過期被移除」→ 其圖檔應被清掉，另加一個孤兒檔也應清掉
        orphan = os.path.join(d, "orphan_deadbeef.jpg")
        with open(orphan, "wb") as f:
            f.write(b"z")
        venues_after_expire = [venues[0]]  # 華山那筆（含活動C）整個過期消失
        removed = m.gc_orphans(venues_after_expire, d, log=lambda *a, **k: None)
        # 應刪：活動C 的圖 + orphan = 2；保留：活動A 的圖
        assert removed == 2, removed
        remaining = os.listdir(d)
        assert len(remaining) == 1
        assert remaining[0] == os.path.basename(venues[0]["ex"][0]["img"])
        print("test_gc_orphans: PASS")
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    test_is_expiring()
    test_localize_and_gc()
    print("ALL TESTS PASS")
