# YouTube 订阅管理指南

## 1. 当前订阅列表

目前后端系统监控以下 2 个频道，每小时自动拉取最新视频：

| 频道名称 | 频道 ID | 备注 |
| :--- | :--- | :--- |
| **Google Developers** | `UC_x5XG1OV2P6uZZ5FSM9Ttw` | 默认示例 |
| **Bloomberg Technology** | `UCsBjURrPoezykLs9EqgamOA` | 默认示例 |

*配置文件位置：`Backend/data/channels.json`*

---

## 2. 如何添加新频道

当你想要在 App 中增加新的内容源时，只需在 GitHub 网页端简单操作，无需编写代码。

### 步骤一：获取频道 ID
1. 打开 YouTube 频道主页。
2. **如果 URL 是 `channel/UC...`**：
   - 直接复制 `UC` 开头的这串字符。
3. **如果 URL 是 `@username`**：
   - 随便点击该频道的一个视频。
   - 点击视频下方的频道头像/名称。
   - 查看浏览器地址栏，通常会变回 `channel/UC...` 格式。
   - 或者使用在线工具（搜索 "YouTube Channel ID Finder"）查询。

### 步骤二：更新配置文件
1. 登录 GitHub，进入仓库 `mumulinyi/onebook-backed`。
2. 导航到 **`Backend/data/channels.json`**。
3. 点击右上角的 **✏️ (Edit)** 图标。
4. 在 JSON 列表中添加新的对象（注意**逗号**）：

```json
[
    {
        "id": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
        "name": "Google Developers"
    },
    {
        "id": "UCsBjURrPoezykLs9EqgamOA",
        "name": "Bloomberg Technology"
    },  <-- 注意这里要加一个逗号
    {
        "id": "UCxxxxxxxxxxxxxx",
        "name": "你的新频道名称"
    }
]
```

5. 点击页面底部的绿色 **Commit changes** 按钮保存。

---

## 3. 生效时间

*   **自动更新**：GitHub Actions 会在**每小时的整点**（如 14:00, 15:00）自动运行。
*   **手动触发**（如果急需）：
    1. 点击仓库顶部的 **Actions**。
    2. 点击左侧 **Content Update**。
    3. 点击右侧 **Run workflow** -> **Run workflow**。
    4. 等待 1-2 分钟，直到变成绿色对钩。

---

## 4. 常见问题

*   **Q: 添加后 App 里没显示？**
    *   A: 请先确认 GitHub Actions 里的 `Content Update` 任务是否已经运行成功（绿色）。如果刚改完文件，需要等下一个整点，或者手动触发一次。
*   **Q: 频道 ID 填错了会怎样？**
    *   A: 脚本会自动跳过错误的 ID，不会影响其他频道的正常更新。你可以在 Actions 的运行日志里看到报错信息。
