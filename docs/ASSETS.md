# 从现成表情到可安装桌宠

## 找到能用的原图

一二是白色小熊猫，布布是棕色小熊。外语平台常把两只写成 Bubu 和 Dudu，名字与中文对应关系不统一。看到搜索结果后，先看实际画面，再命名文件。可从[黄小B微博](https://weibo.com/u/2623471650)和微信表情商店的“小熊猫一二”核对正式作品。以下公开整理可以补充动作，来源不明的图片不要写成官方原画。

### 黄小B的表情专辑

微信表情商店可直接搜索“一二”或“一二第18弹”，核对署名“黄小B”。作者在抖音发布过第13弹和第16弹，在微博发布过第18弹上架预告。第18弹预告里的摸头动图有 700 × 700 的透明 GIF，可直接对应到作者微博。[第13弹发布](https://www.douyin.com/video/7182014417805118755) · [第16弹发布](https://www.douyin.com/video/7381657265582902564) · [第18弹预告](https://weibo.com/2623471650/R6MuftVTl)

[按弹数整理的候选目录](https://www.sigstick.com/collection/aL0sre4mHbvOXsYSKOVj)收录第1至18弹及节日篇等表情。这是第三方目录，主要作用是定位某弹及其单张候选图。标题里的作者署名由上传者填写。查找时优先选普通版，看到“反转版”“反串版”再逐张核对谁是一二、谁是布布。社交平台的预告片也适合比对造型和动作。可把发布证据和实际下载地址一起记录。

早期的第1弹以一二单人为主。第2弹的搭档仍是淡色，做棕色布布版时容易认错。第3弹已经可以看到熟悉的棕色布布和贴贴动作。第4弹有同被窝，第5弹有背背、亲亲和晚安，适合作为以后挑选双人待机动作的入口。[第1弹存档](https://www.sigstick.com/pack/j2yIUwIxkHnOYeNi7CU4) · [第2弹](https://www.sigstick.com/pack/jUkawOg2yB2W0PJp5ClN) · [第3弹](https://www.sigstick.com/pack/nfUo2wf2I1inRdyxdosy) · [第4弹](https://www.sigstick.com/pack/lTPG3UYiIva6CqErL3FD) · [第5弹](https://www.sigstick.com/pack/4aUk7gxyvfYx7e2uN0ao)

| v0.2 新款 | 新素材如何选 | 仍需标明的来源 |
| --- | --- | --- |
| 一二 · 长颈鹿下班 | 第8弹的粉色电脑和长颈鹿装，第16弹的粉垫，以及作者第18弹公开预告原图 | 编号专辑里的动图字节来自第三方存档 |
| 布布 · 花花午休 | 第7弹黄垫、第17弹弹簧跳和第18弹小花庆祝 | 工作动作来自 Tenor 的 498 × 498 整理图，原始弹数未确认 |
| 一二和布布 · 同桌来信 | 第3弹贴贴，第8弹敲键盘和庆祝，第16弹惊讶动作与第18弹递信 | 双人工作画面由两张表情在本地合成 |

原始表情的尺寸以锁文件为准。编号存档大多为 240 × 240，足够覆盖 192 × 208 的 Codex 单帧。查看清晰度时关注角色实际占用像素、边缘和手部运动。使用贴纸详情页标出的动图地址并核对文件魔数。部分地址以 `.png` 结尾，返回的是 GIF；`--name` 需要按实际格式填写。作者直接发布的文件用 `creator-post`，专辑存档用 `collection-archive`，未核实弹数的转载用 `repost`。专辑与发布预告可用 `--collection` 和 `--announcement` 一起登记。

| 需求 | 搜索词 | 当前素材线索 |
| --- | --- | --- |
| 待机 | 一二布布贴贴、布布打盹、Yier Bubu cuddle | [Away6v 整理库](https://github.com/Away6v/oneno-pet/tree/main/public/assets) |
| 工作 | 一二敲键盘、布布笔记本、panda typing desk sticker | [一二台式机](https://tenor.com/view/bubu-dudu-sseeyall-gif-13731785153636919052)、[布布笔记本](https://tenor.com/view/bubududu-work-gif-4883452236397020407) |
| 庆祝 | 一二布布跳舞、Bubu Dudu party dance | [舞蹈贴纸包](https://www.sigstick.com/pack/Bbg3qTSiqHW8SyVDaOEm-bubu-dudu-party) |

优先选原始 GIF、动画 WebP 或 APNG，避免把静态封面、视频截图或压缩预览当原素材。Pillow 的 `Image.open(...).n_frames` 应大于 1。查看完整一轮，检查角色配色、透明边、字幕和水印。保留作者署名与水印。如果水印、嵌字或背景影响桌宠效果，先找无干扰的授权原图。下载用的地址应是实际图片 URL，不是表情详情页、登录跳转或暂时有效的签名链接。

## 锁定和缓存

原始字节放在忽略目录 `runs/yier-bubu-source/`。先弄清使用范围，原始出处不明时把来源记为转载。公开仓库提交来源、尺寸、帧数和 SHA-256，别把授权未明的原图、精灵图、相关预览或带图软件传到公开发行包。

```text
python pin_source.py PATH_TO_ANIMATED_GIF --name bubu-office-v2.gif --page HTTPS_SOURCE_PAGE --url HTTPS_MEDIA_FILE
```

该命令检查实际图像格式、动图帧数和大小，复制到本地素材缓存，并更新 [source-lock.json](../yier_bubu/source-lock.json)。已有文件名保留，新素材用新名字。如果来源服务后来返回不同字节，构建会报错。核实原图和动作之后才登记新版本，别只更新哈希让校验通过。

## 把动作放进桌宠

编辑 [actions.json](../yier_bubu/actions.json)。每款用小写英文 ID，例如 `bubu-solo-v3`，展示名可以用中文。优先复制造型最接近的一款，逐项替换状态。一个状态允许一个或多个图层，双人版有两张敲电脑动图并排时，各自确定 `center` 与 `floor`。只在每格都装得下时才组合。

| 状态 | 原生行号 | 帧数 | 用途 |
| --- | ---: | ---: | --- |
| idle | 0 | 6 | 贴贴、眨眼或打盹 |
| running-right / running-left | 1 / 2 | 各 8 | 复用待机，拖动时保持原样 |
| waving | 3 | 4 | 打招呼 |
| jumping | 4 | 5 | 短跳，回到同一基线 |
| failed | 5 | 8 | 失败或受挫 |
| waiting | 6 | 6 | 等你回应 |
| running | 7 | 6 | 循环敲键盘 |
| review | 8 | 6 | 任务完成后庆祝 |

按画面挑选 `frames`，编号从 0 开始，保持动作方向和自然节奏。白底转载图可用 `white: true` 清理与画布外沿相连的浅色，保留轮廓内的白色毛皮。只在不碰主体和署名时使用 `erase` 处理分离的装饰字。把每条动作的帧当一组缩放，通过 `width` 和 `height` 控制最大轮廓，通过 `floor` 对齐落点。短跳可以用 `lift` 指定原图每帧的垂直偏移。不要按帧单独裁切并撑满画格，否则大小和位置会跳。

```text
python -m yier_bubu.build --pet YOUR_NEW_PET_ID --out runs/review-new-pet
```

打开 `runs/review-new-pet/pets/YOUR_NEW_PET_ID/qa/previews/` 的状态 GIF。对照原图检查主角、方向和动作含义，使用深浅两种背景看边缘，确认工作 GIF 在首尾衔接时没有一帧待机或突然跳位。固定格式是 (1536×1872) WebP，格子 (192×208)，57 个有内容的格和 15 个全透明格。查看 `qa/structure.json` 的校验结果和 `qa/state-mapping.json` 的动作来源与变换。

## 新角色或更多角色

GUI、打包器和验收脚本都从配置读取角色。新增款在 `character` 填 `yier`、`bubu` 或 `duo`，给它一个能辨认待机和完成动作的中文名字。扩展时同步更新 README 的版本表并测试原生压缩包和离线软件。用新的目录 ID 试装，便于保留用户已有选择。确认不再引用旧素材后才从锁文件移除对应条目。
