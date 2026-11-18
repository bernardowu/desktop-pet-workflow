# 一二布布桌宠 · Yier & Bubu Desktop Pets

六款电脑桌宠，包含布布、一二和双人组合。角色出自[黄小B](https://weibo.com/u/2623471650)，动画从有出处的现成表情中抽帧。这个项目提供独立本地软件和 Codex 原生桌宠两种用法。

| 版本 | 待机 | 工作 | 完成 |
| --- | --- | --- | --- |
| 布布 v1 | 站着眨眼 | 敲笔记本 | 跳舞 |
| 布布 v2 | 趴桌打盹 | 蓝色电脑 | 戴墨镜跳舞 |
| 一二 v1 | 站着眨眼 | 敲粉色笔记本 | 跳舞 |
| 一二 v2 | 抱枕睡觉 | 敲台式机键盘 | 穿虎装跳舞 |
| 合体 v2 | 贴脸 | 各敲一台笔记本 | 双人跳舞 |
| 合体 v3 | 依偎打盹 | 一二敲键盘，布布陪着 | 双人摇摆 |

## 下载与安装

打开仓库的 [Releases](https://github.com/bernardowu/desktop-pet-workflow/releases)，按用途和系统选对应安装器。

| 文件名前缀 | 用途 |
| --- | --- |
| `YierBubuPet-` | 独立浮窗，工作期间持续敲键盘。右键切换角色、安装原生版或退出 |
| `YierBubuCodexNative-` | 将六款安装到 Codex 的 Pets，安装完成后退出 |

Windows x64 双击 `.exe`。macOS 解压与芯片匹配的 ZIP，打开里面的 `.app`，Apple 芯片选 `arm64`，Intel 选 `x64`。发布流程生成的 macOS 构建需要在正式公开分发前完成开发者签名与公证；仓库未配置这些凭据。

首次使用时，程序经确认后在本机下载锁定的表情并生成精灵图。下载发生在你的设备上。独立浮窗只读取本地 Codex 会话的状态事件，任务文本不会上传。

原生版安装后，在 Codex **设置 → Pets → 刷新**切换。原生浮窗的状态和播放次数由客户端控制。已验证的 Windows 客户端 `26.1111.2228.0` 会在工作动画播三轮后返回待机。需要持续循环时开启独立浮窗。

## 从源码构建

需要带 Tk 的 Python 3.12 或通过测试的 3.13。Windows 和 macOS 使用相同命令。

```text
python -m pip install -r requirements-build.txt
python -m unittest -v
python launch_pet.py
python launch_pet.py --native-only
```

只生成原生桌宠和预览时运行以下命令。素材可以预先放入 `runs/yier-bubu-source/`。

```text
python -m yier_bubu.build --download
python package_native.py runs/yier-bubu/dist
```

已准备好素材时，也可以将原生包传给打包器，生成离线自用程序。

```text
python package_app.py --bundle-pets runs/yier-bubu/dist
```

## 交给下一个 agent

先读 [AGENTS.md](AGENTS.md)，然后按需要打开以下文档。

- [素材搜集、登记、抽帧与换角色](docs/ASSETS.md)
- [架构、状态逻辑和排错](docs/MAINTENANCE.md)
- [Windows 和 macOS 发布流程](docs/RELEASE.md)
- [原有的通用桌宠工具快速开始](WORKFLOW-QUICKSTART.md)

GitHub 上的安装器只包含程序和素材来源清单。现成表情的原图及含图成品由用户在本机生成。素材权利和来源记录见 [ASSETS.md](docs/ASSETS.md)。
