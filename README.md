# 打字恐慌桌宠 · v0.4

你打字越快，它越慌；一直狂敲它会崩溃，停下来它会慢慢缓过来。

## v0.4 新增
- 托盘菜单加了「**开机自启**」（默认关，勾上就开机自动出现；Windows 写注册表启动项，Mac 用 LaunchAgent）
- **只开一只**：重复启动不会冒出第二只团子，只会把现有的召回右下角
- release 编译开了 LTO、按体积优化、去掉调试符号，安装包更小
- **一键打包**：项目自带 GitHub Actions（`.github/workflows/release.yml`）

## 发布安装包
**方式 A：本机打包**（只能打当前系统的包）
```bash
npm run build
```
产物在 `src-tauri/target/release/bundle/`：Windows 是 `.msi` 和 `-setup.exe`，Mac 是 `.app` 和 `.dmg`。

**方式 B：GitHub 自动打包**（Windows + 两种 Mac 一次全出）
```bash
git init && git add . && git commit -m "v0.4.0"
git remote add origin git@github.com:<你的用户名>/typing-panic-pet.git
git push -u origin main
git tag v0.4.0 && git push origin v0.4.0
```
大约 15 分钟后，仓库的 Releases 里会出现一个草稿版本，安装包都在里面，点「Publish」就发布了。

> 没签名的安装包第一次打开会被拦：Windows 点「更多信息 → 仍要运行」；Mac 右键 →「打开」，或到「系统设置 → 隐私与安全性」里点「仍要打开」。

## v0.3 新增
- **重画团子**：48×48、3 倍放大；暖棕色轮廓、球面三层光影、带高光的大眼睛、腮红、头顶两片小叶子
- **17:30 背包下班**（周一到周五）：背上小书包挥手「下班啦～」，然后走出窗口。之后你再打字，它会从边上探头：「你怎么还在加班…」。第二天 09:00 自动回来。时间和工作日在 `src/offwork.js` 的 `DEFAULTS` 里改
- **托盘菜单**：暂停感知键盘、鼠标穿透（不挡点击）、灵敏度 低/中/高、下班 / 回来上班（随时预览下班动画）、回到右下角、退出
- 浏览器预览模式下按 **F2** 预览下班

## 第二步新增
- 一只 像素风小团子替换 emoji，按 4 倍放大、保持像素锐利
- 新增两个状态：**警觉**（盯着你、头顶感叹号）和**恐慌**（满窗口乱跑、尖叫、飙泪）
- 状态顺序：悠闲 → 警觉 → 紧张 → 恐慌 → 崩溃（灵魂出窍）；闲置 5 分钟睡觉
- 精灵图由 `tools/make_sprites.py` 用代码生成，改颜色、表情直接改脚本再跑一次

## 第一步做了什么
- 透明、无边框、置顶的小窗口，启动后停在屏幕右下角，可以拖动
- 全局键盘计速（别的软件在前台也能感知）。**只统计按键次数和类型，不记录你敲的内容**
- 压力模型：快速打字时压力上升，停下时回落
- 状态：😌 悠闲 → 😰 紧张（发抖）→ 😵 崩溃（躺平）；5 分钟没动静就 😴 睡觉
- 小彩蛋：连按 3 次退格 🤦、回车 🤸、Ctrl/Cmd+S 👍
- 底部小条显示压力值（绿→橙→红）

## 目录
```
src/            前端（纯 HTML/CSS/JS，无需打包工具）
  pet.js        宠物「大脑」：KPS、压力、状态机（纯函数，可单测）
  sprites/      各状态的精灵条（PNG，48×48 一帧）
  main.js       渲染与事件绑定
src-tauri/      Rust 外壳：窗口 + 全局键盘监听（device_query）
test/           pet.js 的单元测试
tools/          make_sprites.py 精灵图生成脚本、preview.png 预览
```

## 运行
1. 装好 Rust（https://rustup.rs）和 Node 18+
   - Windows：还需要 Visual Studio 的「C++ 生成工具」，WebView2 系统自带
   - Mac：`xcode-select --install`
2. 在项目根目录：
   ```bash
   npm install
   npm run dev        # 开发模式，第一次编译要几分钟
   npm run build      # 打包成 .exe / .msi 或 .app / .dmg
   npm test           # 跑状态机和下班时间测试
   ```
3. **Mac 额外一步**：第一次运行后，到「系统设置 → 隐私与安全性 → 辅助功能」（部分系统版本还要「输入监控」）里勾选终端或 TypingPanicPet，然后重启程序，否则听不到键盘。
4. 开了「鼠标穿透」就拖不动它了，从托盘取消勾选即可
5. 只想看界面：直接用浏览器打开 `src/index.html`，在页面里打字就行（这时只听本页面的按键）。

## 调手感
参数都在 `src/pet.js` 顶部 `DEFAULTS`：
| 参数 | 默认 | 作用 |
|---|---|---|
| calmKps | 3 | 每秒低于这么多键，压力就回落 |
| alertKps | 2.5 | 平滑后超过这个就警觉 |
| nervousKps | 5 | 平滑后超过这个就紧张 |
| panicStress | 70 | 压力超过这个就恐慌乱跑 |
| gain | 0.2 | 压力上涨速度 |
| decay | 2 | 压力回落速度（每秒） |
| recoverBelow / recoverIdleMs | 30 / 3000 | 崩溃后要压力低于 30 且停手 3 秒才爬起来 |

按默认值，持续每秒 6 键约 2 分 50 秒崩溃，每秒 10 键约 1 分 10 秒。

## 下一步（计划）
- ~~第二步：像素精灵图 + 警觉、恐慌状态~~ ✅
- ~~第三步：17:30 背包下班、托盘菜单、鼠标穿透~~ ✅
- ~~第四步：开机自启、打包发布~~ ✅
