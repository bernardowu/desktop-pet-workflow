# 发布与验证

## 本地生成两种交付物

使用目标系统的 Python 3.12 和带 Tk 的环境。Windows 和 macOS 分别构建，Apple 芯片与 Intel 使用对应架构。先在该系统验证原生精灵图和动画。

```text
python -m pip install -r requirements-build.txt
python -m unittest -v
python -m yier_bubu.build --assets runs/yier-bubu-source --out runs/release-check
python package_native.py runs/release-check/dist
python package_app.py --bundle-pets runs/release-check/dist
python test_packaged_app.py PATH_TO_OFFLINE_ARTIFACT --embedded --gui
```

`package_native.py` 生成 Windows 和 macOS 通用的原生桌宠 ZIP，自动包含当前清单。将解压出的各个角色目录放到 `CODEX_HOME/pets`，再在 Codex 里刷新。包内素材用于本机自用。要发布含图 ZIP 或离线应用，请先核对公开再分发权限以及应保留的授权说明。

## GitHub 发行

1. 更新版本 `yier_bubu/__init__.py`。审查代码和锁文件，确认不包含原图、会话、个人路径、发布密钥或未经授权的成品。
2. 手动触发 `.github/workflows/release.yml` 做一次跨平台构建。三个 runner 各生成独立浮窗安装器和原生安装器，使用合成素材对包做自检。检查所有构建输出、架构和 SHA-256。
3. macOS 输出为未公证的 `.app` ZIP。面向公众交付前，使用项目自己的 Apple Developer ID 签名与公证，并在干净机器验证。此仓库没有签名密钥。Windows 可在有签名证书时对 EXE 做 Authenticode 签名。
4. 审查通过后推送版本标签。工作流会生成 GitHub Release 和 `SHA256SUMS.txt`。发布器中只有代码和来源清单。用户第一次同意下载后在本机生成素材，后续使用可离线。

```text
git tag v0.1.0
git push origin v0.1.0
```

版本回滚通过选择上一个 Release。已经存到本机的桌宠和偏好在应用数据目录中，应用版本可独立回滚。若需要补发同一版本，请先检查已经存在的标签及 Release，正常创建新补丁版本，避免重写已经下载的二进制。
