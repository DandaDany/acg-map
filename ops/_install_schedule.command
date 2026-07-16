#!/bin/bash
# 安裝「每週一、週四 11:30 自動更新」launchd 排程（避開 11:00 social crawler）。由 Claude 建立。
# 解除安裝：launchctl unload ~/Library/LaunchAgents/com.danielcheng.twexhibmap.plist 後刪除該檔。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PY="/Users/daniel0522/miniforge3/bin/python3"
LABEL="com.danielcheng.twexhibmap"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$DIR/runtime/logs" "$DIR/runtime/state"
cat > "$PLIST" << XML
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$DIR/ops/run_scheduled_update.sh</string>
  </array>
  <key>WorkingDirectory</key><string>$DIR</string>
  <key>StartCalendarInterval</key>
  <array>
    <dict>
      <key>Weekday</key><integer>1</integer>
      <key>Hour</key><integer>11</integer>
      <key>Minute</key><integer>30</integer>
    </dict>
    <dict>
      <key>Weekday</key><integer>4</integer>
      <key>Hour</key><integer>11</integer>
      <key>Minute</key><integer>30</integer>
    </dict>
  </array>
  <key>StandardOutPath</key><string>$DIR/runtime/logs/scheduled_update.log</string>
  <key>StandardErrorPath</key><string>$DIR/runtime/logs/scheduled_update.log</string>
  <key>RunAtLoad</key><false/>
</dict>
</plist>
XML
echo "已寫入排程設定：$PLIST"
launchctl unload "$PLIST" 2>/dev/null
launchctl load -w "$PLIST" && echo "✅ 已啟用：每週一、週四 11:30 自動執行 ops/run_scheduled_update.sh"
echo "--- 確認 ---"
launchctl list | grep "$LABEL" && echo "（左欄 PID 為 - 屬正常，代表排程已登錄、等待時間到）"
echo "排程程式：/bin/bash $DIR/ops/run_scheduled_update.sh"
echo "工作目錄：$DIR"
echo "更新 log 會寫到：$DIR/runtime/logs/scheduled_update.log"
echo ""; echo "完成，此視窗可關閉。"
