# 快達通渠網站

這個 repository 只包含快達通渠公開網站的建置檔及編譯後首頁，不包含內部文件或管理後台。

Render 使用根目錄的 `render.yaml`，建置流程會執行 `python3 production/build.py --public`，並將 `production/site` 發布為 Static Site。

部署前需要在 Render 設定以下環境變數：

- `SITE_URL`：正式 HTTPS 網域
- `SITE_PHONE`：`85293339580`
- `SITE_WHATSAPP`：`85293339580`
- `PUBLISH_CONFIRMED`：`1`

沒有正式網域時，請不要使用公開建置；建置器會拒絕缺少網域或發布確認的正式輸出。
