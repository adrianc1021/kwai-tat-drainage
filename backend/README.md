# 快達通渠網站管理後台

這是網站的管理後台，與目前公開網站共用同一個 Django 服務，包含：

- 第一方訪問及查詢按鈕統計；
- 圖片上載、素材庫、頁面圖片替換及裁切焦點；
- 所有公開頁面的文字、SEO 標題及描述草稿／預覽／套用；
- 套用前版本保存及還原；
- 手動查詢紀錄及跟進狀態；
- 管理員、內容編輯、數據分析及營運權限；
- 修改紀錄、CSV 彙總匯出及本機私人備份。

## 本機啟動

在專案根目錄執行：

```sh
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py init_cms
.venv/bin/python backend/manage.py runserver 127.0.0.1:8767
```

首次只可從本機開啟 `http://127.0.0.1:8767/manage/setup/`，自行建立管理帳戶及至少 12 字元密碼。首個帳戶建立後，首次設定入口會自動關閉。不要把密碼寫入此專案。

後台：`http://127.0.0.1:8767/manage/`  
後端網站：`http://127.0.0.1:8767/`

開發伺服器只供本機預覽，不可直接公開。Render 部署使用根目錄的 `render.yaml`，會執行 Django、收集靜態檔案及建立持久化資料磁碟。首次部署前，請在 Render 的私密環境變數設定：

- `CMS_ADMIN_USERNAME`：首次管理員帳戶名稱；
- `CMS_ADMIN_PASSWORD`：至少 12 個字元的首次管理員密碼。

啟動命令只會在資料庫沒有帳戶時建立一次管理員；之後移除這兩個環境變數亦不會刪除帳戶。後台入口為 `/manage/`，圖片入口為 `/manage/media/`。Render 持久化磁碟的 `CMS_DATA_DIR` 必須保留，否則資料庫、上載圖片及草稿會隨部署消失。

正式環境仍需使用 HTTPS、外部存取控制、備份監察及正式網域設定：

```sh
CMS_PRODUCTION=1 CMS_ALLOWED_HOSTS=example.com CMS_DATA_DIR=/private/path \
  .venv/bin/python backend/manage.py check --deploy
```

`CMS_PRODUCTION=1` 會關閉首次設定入口、強制 HTTPS、安全 Cookie 及 HSTS。正式帳戶須先在私人環境建立，並限制 `/manage/` 與 `/admin/` 的網絡存取。

## 圖片與內容流程

1. 在「圖片素材庫」上載 JPG、PNG 或 WebP。系統驗證實際圖像、限制 10 MB／2,500 萬像素、移除 EXIF、縮至最大 3200 px 並轉 WebP。
2. 前往「頁面與內容」選擇圖片位置、替代文字及裁切焦點。
3. 儲存草稿，打開草稿預覽。
4. 有發布權限的管理員把已儲存草稿套用到後端網站。
5. 套用前版本保留在資料庫，可還原為新草稿。

頁面文字只接受純文字，不允許貼入 HTML 或 JavaScript。仍被草稿、現行頁面或歷史版本引用的圖片不能刪除。

## 統計定義與私隱

統計預設關閉。啟用後，訪客仍須在前台選擇「允許」才記錄：

- `page_view`：頁面瀏覽；
- `whatsapp_click`：WhatsApp 查詢意向；
- `telephone_click`：電話查詢意向。

事件只接受頁面代號、裝置類別及事件代號。電話、地址、查詢內容、檔案名、URL 查詢參數及 IP 不寫入分析表。伺服器輸出亦關閉請求存取日誌。訪問次數使用 30 分鐘隨機識別；轉換率是「有查詢按鈕點擊的訪問 ÷ 全部訪問」。點擊不等於接通、已發訊息、派員或成交。本機資料標示為測試環境，管理員及草稿預覽不計入。

事件最多保留 90 日；應用程式運行時每小時檢查清理，也可排程：

```sh
.venv/bin/python backend/manage.py prune_analytics
```

查詢紀錄包含個人資料，只限獲授權營運帳戶存取；前台表單仍未啟用收件。

## 備份與更新

```sh
.venv/bin/python backend/manage.py backup_cms
```

備份寫入 `backend/private/backups/`，包含資料庫、圖片及 secret key，亦包含查詢個人資料，必須當作機密檔案。正式環境應把 `CMS_DATA_DIR` 放在網站根目錄之外，將加密備份送至另一受控位置並定期做還原演練。

重新執行 `init_cms` 不會覆蓋已存在的頁面內容。靜態原始頁面改動不會自動改寫後台資料；如要重新匯入，須先設計版本遷移，避免抹走管理員修改。

## 驗證

```sh
.venv/bin/python backend/manage.py test cms
NODE tests/backend-browser-check.cjs
```

瀏覽器流程使用隔離的 `.work/cms-browser-test` 資料庫。測試涵蓋權限、CSRF、圖片驗證、草稿隔離、預覽、套用、還原、分析同意／事件白名單、查詢刪除、21 組後台版面、axe A／AA 及 Chromium／WebKit 手機操作。
