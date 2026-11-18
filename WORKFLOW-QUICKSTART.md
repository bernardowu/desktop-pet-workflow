# Desktop Pet Workflow

一套从角色简报、动作生成、精灵表验收到打包安装的桌宠工作流。目标平台是 **Windows 和 macOS**。先做一个角色，再换简报和参考图复用同一套流程。

有两个目标入口。先选要装到哪里，再开始生成动画。

| 入口 | 制作工具 | 交付 |
| --- | --- | --- |
| Codex 本地桌宠 | OpenAI 的 [hatch-pet](https://github.com/openai/skills/tree/main/skills/.curated/hatch-pet) | 放入 Codex 的 `pet.json` 和 PNG/WebP 精灵表 |
| ChatGPT Work 桌宠 | Work Pets 插件的 `create-pet` 技能 | v2 精灵表，通过 Work 的上传流程创建 |

其他独立桌宠应用也可以复用角色稿、动作帧、预览和验收记录，再用自己的运行时读取动画。透明窗口、拖动和交互需要按目标应用实现。

## 第一次上手

1. 用 Git 克隆本仓库。把 [brief.example.json](brief.example.json) 复制为新项目简报，填写角色、造型锁定项、参考图权利和目标入口。
2. 把 [AGENTS.md](AGENTS.md) 交给接手的 agent。它应先读 [WORKFLOW.md](WORKFLOW.md)，再按所选的官方技能生成角色和动作。
可以直接把这句话发给另一台电脑上的 agent：

> 克隆 https://github.com/bernardowu/desktop-pet-workflow ，先读 AGENTS.md 和 WORKFLOW.md，以 brief.example.json 为模板做一只原创 Codex 桌宠，交付校验报告、动作预览和可安装 ZIP。我的平台是 Windows 或 macOS，请先记录实际客户端版本。

3. 项目素材放在 `runs/<pet-id>/`。先审分镜和实际动图，再打包。下方工具使用同一份最终 PNG 或 WebP，无需调用图像生成服务即可做验收和安装。

使用 Python 3.12。Windows 可以用 Python Launcher，也可以用已配置好的 `python`。

**Windows PowerShell**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest -v
```

**macOS**

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v
```

以下命令中的 `python` 指上面虚拟环境里的解释器。先把路径换成你实际产出的精灵表。

```text
python petkit.py validate runs/ember-moth/final/spritesheet.webp --version v1 --json-out runs/ember-moth/qa/structure.json
python petkit.py preview runs/ember-moth/final/spritesheet.webp --out runs/ember-moth/qa/previews
python petkit.py package runs/ember-moth/final/spritesheet.webp --version v1 --id ember-moth --name "Ember Moth" --description "A quiet moth with folded paper wings." --out dist --zip
python petkit.py install dist/ember-moth
```

- `validate` 给出尺寸、格位和 SHA-256。需要人工看图的贴边帧会单独列出。
- `preview` 生成总览图、每状态 GIF 和待机到跳跃再回待机的 GIF。v2 另有视线方向图。
- `package` 生成文件夹和可选 ZIP，保持原始精灵表字节。清单与 ZIP 可直接交给另一台电脑。
- `install` 安装到当前主目录下的 `.codex/pets/`，优先使用已设置的 `CODEX_HOME`。也可用 `--codex-home` 指定。已有同名且内容不同的桌宠会保留，换一个 ID 即可并排验收。

在另一台电脑上，把 ZIP 解压后对其中的角色目录运行 `install`，然后打开桌面客户端的 Settings → Pets 检查角色。入口有 Refresh 时点一次，必要时重启客户端再检查。Windows 默认目录是 `%USERPROFILE%\.codex\pets`，macOS 默认目录是 `~/.codex/pets`。只有使用相同配置目录的客户端才能发现安装包。

Codex 的公开 `hatch-pet` 契约列出 **v1**。本工具能校验 **v1 和 v2**，本地安装教程默认用 v1。向某个 Codex 版本发 v2 前，应该在那个版本里实际验证。Work Pets 的创建流程使用它自己的 v2 质量门和上传接口。上传前须预览动画，并按该技能验证最终文件。

## 交接

给接手者角色简报、参考图来源、最终精灵表 SHA-256、检查报告、预览和客户端版本。Windows 与 macOS 的 CLI 测试由 [GitHub Actions](https://github.com/bernardowu/desktop-pet-workflow/actions) 跑。桌面渲染、拖动和触发状态以实际客户端验收为准。

## English quick start

Choose the target in the table above. Start from [brief.example.json](brief.example.json) and hand [AGENTS.md](AGENTS.md) and [WORKFLOW.md](WORKFLOW.md) to the producing agent. Use the official skill to create and review the art. This repo supplies portable validation, contact sheets, GIF previews, Codex packaging and a non-overwriting installer. Run the commands above from the repo root. Distribute only assets you have permission to share.
