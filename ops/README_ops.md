# ops

維運與排程入口。

檔案：
- `run_scheduled_update.sh`：launchd 實際執行的更新 wrapper。
- `_install_schedule.command`：安裝或更新 macOS launchd 排程。
- `_final_update.command`：手動完整更新與備份用腳本。

log 與狀態檔放在 `runtime/logs/`、`runtime/state/`。
