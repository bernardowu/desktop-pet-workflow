# 从现成表情到可安装桌宠

## 找到能用的原图

一二是白色小熊猫，布布是棕色小熊。外语平台常把两只写成 Bubu 和 Dudu，名字与中文对应关系不统一。看到搜索结果后，先看实际画面，再命名文件。可从[黄小B微博](https://weibo.com/u/2623471650)和微信表情商店的“小熊猫一二”核对正式作品。以下公开整理可以补充动作，来源不明的图片不要写成官方原画。

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

六款是当前发行清单，GUI、打包器和验收脚本都从配置读角色。扩展时同步更新 README 的版本表并测试原生压缩包和离线软件。用新的目录 ID 试装，可避免覆盖已有配置。确认不再引用旧素材后才从锁文件移除对应条目。
