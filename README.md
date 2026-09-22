# 快達通渠網站

這個 repository 只包含快達通渠公開網站的建置檔及編譯後首頁，不包含內部文件或管理後台。

Render 使用根目錄的 `render.yaml`，建置流程會執行公開網站建置、Django migration 及靜態檔案收集，並以 Python Web Service 同時提供網站及管理後台。

管理後台版本已加入 Django。正式網站及後台使用 `https://rapidflowhk.com/` 及 `https://rapidflowhk.com/manage/`；舊的 Render 網址會永久轉址到新網域，並保留原有路徑及查詢參數。要在現有 Render 服務啟用後台，需在 Render 將 Blueprint 同步為 `render.yaml` 的 Python Web Service，並設定 `CMS_ADMIN_USERNAME`、`CMS_ADMIN_PASSWORD` 兩個私密環境變數。Render 必須保留 `cms-data` 持久化磁碟，否則上載圖片及草稿不會保留。

部署前需要在 Render 設定以下環境變數：

- `SITE_URL`：`https://rapidflowhk.com`
- `SITE_PHONE`：`85293339580`
- `SITE_WHATSAPP`：`85293339580`
- `PUBLISH_CONFIRMED`：`1`
- `RENDER_DEPLOY_HOOK_URL`：Render 服務的 Deploy Hook URL（私密環境變數；不應提交到 Git）

後台在「公開套用」成功後會先保存內容到正式資料庫，然後以 server-side POST 通知 Render 重新部署。Render 重建不是內容公開的必要條件，因為公開頁面會即時讀取資料庫；未設定 Deploy Hook 時，後台會明確提示而不會假裝已重新部署。

沒有正式網域時，請不要使用公開建置；建置器會拒絕缺少網域或發布確認的正式輸出。
