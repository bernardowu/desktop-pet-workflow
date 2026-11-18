# 维护与排错

## 先定位变更

| 文件 | 维护内容 |
| --- | --- |
| `yier_bubu/actions.json` | 显示名和各状态的素材、抽帧、位置 |
| `yier_bubu/source-lock.json` | 素材出处、直链、尺寸、帧数和 SHA-256 |
| `yier_bubu/build.py` | 素材校验、去白底、统一比例、拼接和打包 |
| `petkit.py` | 通用 v1/v2 校验、预览与透明精灵表打包 |
| `yier_bubu/task_monitor.py` | 本地 Codex 任务事件归并 |
| `yier_bubu/local_pet.py` | 桌面浮窗、切换角色、状态循环和安装界面 |
| `yier_bubu/platform_support.py` | Windows 和 macOS 的配置目录、进程发现、单实例 |
| `package_app.py` | 冻结 Windows 或 macOS 应用 |
| `.github/workflows/release.yml` | Windows x64、macOS arm64 和 Intel 构建与上传 |

两种运行方式共用一张透明精灵表。原生版只安装 `pet.json` 和 `spritesheet.webp`，由 Codex 选状态并播画面。独立浮窗读取活动事件，再从精灵表取待机、工作和完成三行。显示逻辑可改，原生客户端的播放次数由客户端决定。

## 独立浮窗如何识别忙碌

使用 `CODEX_HOME`（默认 `~/.codex`）下 `sessions/rollout-*.jsonl` 的 `task_started`、`task_complete` 和 `turn_aborted`。监视器倒序读取，只保留事件类型、时间和 turn ID。只要还有一个活跃任务，界面就循环工作帧。最后一个完成后庆祝四秒，取消时回待机。用进程启动时间忽略上次异常退出留下的旧开始事件。

工作时不要用“多久没日志”判断任务结束。模型推理或长命令可以很久没有新事件。当前只追踪在本机写这些日志的任务。Windows 原生进程通过 Win32 查询，macOS 分支用 `ps`。可用 `--codex-home` 核对使用的账号目录。

## 排错顺序

1. 先看独立版还是原生版在睡觉。原生版在 Windows 客户端 26.1111.2228.0 上的工作动作约 2.46 秒后回待机，此现象与素材无关。
2. 独立版几秒后仍待机时，检查数据目录的 `runtime-status.json`，只读状态和渲染帧计数。Windows 在 `%LOCALAPPDATA%/YierBubuPet`，macOS 在 `~/Library/Application Support/YierBubuPet`。检查本机 Codex 存在活动进程及对应的本地日志。不要上传整个会话记录。
3. 启动报错查看同目录的 `startup-error.log`。已安装角色可作为素材来源。缺少原图时按 UI 提示下载或提供缓存。远端文件和锁指纹不符时，核实镜像或原图版本。
4. 原生安装若有同名不同内容，`petkit` 会保留旧包。先备份再换新的 ID 或替换目标目录。安装后刷新 Pets 列表。

## 验收

```text
python -m unittest -v
python -m yier_bubu.build --assets runs/yier-bubu-source --out runs/review
python test_packaged_app.py PATH_TO_INSTALLER
```

改状态逻辑时测试长任务无刷新、并行任务、取消和日志写到一半的情况。真实验收在 Windows 和 macOS 分别开启窗口并完成一轮任务，观察每种状态、右键选角色、拖动、多屏以及退出。打包烟测、合成素材测试、真机真实状态测试分别记结果。
