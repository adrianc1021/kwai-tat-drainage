# 快達通渠網站管理後台

這是網站的管理後台，與目前公開網站共用同一個 Django 服務，包含：

- 第一方訪問及查詢按鈕統計；
- 圖片上載、素材庫、頁面圖片替換及裁切焦點；
- 所有公開頁面的文字、SEO 標題及描述草稿／預覽／套用；
- 套用前版本保存及還原；
- 手動查詢紀錄及跟進狀態；
- 管理員、內容編輯、數據分析及營運權限；
- 修改紀錄、CSV 彙總匯出及本機私人備份；
- Blog 文章草稿／排程／發布、分類及封面圖片；
- SEO metadata、canonical、索引設定、Open Graph 預覽及動態 sitemap／robots；
- 服務頁、服務地區、工程個案、評價、宣傳活動及通知 Banner；
- GA4、Search Console、PageSpeed 及 Google Business Profile 的連接狀態頁（沒有憑證時保持空白狀態，不生成假數據）。

## 本機啟動

在專案根目錄執行：

```sh
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py init_cms
.venv/bin/python backend/manage.py runserver 127.0.0.1:8767
```

首次只可從本機開啟 `http://127.0.0.1:8767/manage/setup/`，自行建立管理帳戶及至少 12 字元密碼。首個帳戶建立後，首次設定入口會自動關閉。不要把密碼寫入此專案。

初始化會預填已確認的電話及 WhatsApp `+852 93339580`；管理員可在「系統設定」修改，後續執行初始化不會覆蓋已有值。

後台：`http://127.0.0.1:8767/manage/`  
後端網站：`http://127.0.0.1:8767/`

開發伺服器只供本機預覽，不可直接公開。Render 部署使用根目錄的 `render.yaml`，會執行 Django、收集靜態檔案及建立持久化資料磁碟。首次部署前，請在 Render 的私密環境變數設定：

- `CMS_ADMIN_USERNAME`：首次管理員帳戶名稱；
- `CMS_ADMIN_PASSWORD`：至少 12 個字元的首次管理員密碼。
- `RENDER_DEPLOY_HOOK_URL`：Render 服務的 Deploy Hook URL，只放在 Render 私密環境變數，不要提交到 Git。

如要使用正式分析整合，請把 OAuth client id、client secret 及 refresh token 只放在 server environment variables。後台只保存 property ID、連接開關、同步時間及錯誤摘要，不會把 secret 或 token 傳到瀏覽器。

啟動命令只會在資料庫沒有帳戶時建立一次管理員；之後移除這兩個環境變數亦不會刪除帳戶。正式網站及後台使用 `https://rapidflowhk.com/` 及 `https://rapidflowhk.com/manage/`，舊的 Render 網址會永久轉址到新網域。圖片入口為 `/manage/media/`；Render 持久化磁碟的 `CMS_DATA_DIR` 必須保留，否則資料庫、上載圖片及草稿會隨部署消失。

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

公開套用會先將內容寫入正式資料庫，網站隨即讀取新版本；如已設定 `RENDER_DEPLOY_HOOK_URL`，後台會再由伺服器通知 Render 重新部署。通知失敗不會撤回已公開內容，後台會顯示警告。

頁面文字只接受純文字，不允許貼入 HTML 或 JavaScript。仍被草稿、現行頁面或歷史版本引用的圖片不能刪除。

## Blog、SEO 及公開內容

在「Blog 文章」新增草稿，加入摘要、純文字內容、封面、分類及標籤；只有「已發布」文章會由 `/blog/` 公開讀取。狀態為「已排程」的文章由受控工作排程執行：

```sh
.venv/bin/python backend/manage.py publish_scheduled
```

正式環境可用 Render Cron、系統 cron 或其他受控工作流程每分鐘／每五分鐘執行一次。文章內容使用純文字輸入並由 Django 自動轉義，避免未經消毒的 HTML 或 script 注入。

「SEO 管理」可為頁面及 Blog 儲存 title、description、canonical、index/follow、Open Graph、關鍵字、breadcrumb 及 schema type。公開頁面會從已保存的 metadata 輸出 `<title>`、description、robots、canonical 及 Open Graph；`/sitemap.xml` 只列公開頁面和已發布文章。尚未連接 Search Console 時，介面會明確顯示「尚未連接」，不會顯示示範曝光或排名。

「服務頁」「服務地區」「工程個案」「評價」及「宣傳活動」都是獨立資料，支援草稿和封存。工程個案沒有公開同意或未完成去識別時應保持草稿；評價需有人手核准，系統不會自動生成評價。

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

## 資料表摘要

第一階段 migration `cms.0002` 加入 `BlogPost`、`BlogCategory`、`BlogTag`、`SeoMetadata`、`Redirect`、`Service`、`ServiceArea`、`CaseStudy`、`Review`、`Campaign`、`Integration`、`Notification`、`PageSection`。主要內容都有時間欄位、狀態及封存欄位；Django model permissions 和既有登入 guard 在 server-side 執行，內容編輯不能發布 Blog 或公開服務，除非獲得 `publish_blogpost` 或 `publish_page` 權限。

## 驗證

```sh
.venv/bin/python backend/manage.py test cms
NODE tests/backend-browser-check.cjs
```

目前核心 Django suite 共 19 項測試，涵蓋權限、CSRF、圖片驗證、草稿隔離、預覽、套用、還原、Blog 草稿及排程發布、SEO 保存、服務及整合保存、公開 sitemap／robots、分析同意／事件白名單及查詢個人資料。瀏覽器流程可再使用隔離資料庫檢查 `/manage/`、`/manage/blog/`、`/manage/seo/` 及 360px Drawer。
