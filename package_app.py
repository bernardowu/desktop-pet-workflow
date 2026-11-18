"""Freeze a portable Windows .exe or a macOS .app on the matching host."""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import TemporaryDirectory

from petkit import bundle_files
from yier_bubu import __version__
from yier_bubu.build import configurations

repo = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,default=repo/"dist")
    parser.add_argument("--bundle-pets",type=Path,
                        help="Use the prepared native bundles for an offline personal build.")
    parser.add_argument("--native-installer",action="store_true",
                        help="Build an app that installs to Codex and exits.")
    options = parser.parse_args()
    if sys.platform not in {"win32","darwin"}:
        parser.error("Build on Windows or macOS for that platform.")
    output = options.out.resolve()
    output.mkdir(parents=True,exist_ok=True)
    windows = sys.platform == "win32"
    kind = "Windows" if windows else "macOS"
    arch = {"amd64":"x64","x86_64":"x64","aarch64":"arm64"}.get(platform.machine().lower(),
                                                               platform.machine().lower())
    tag = "offline" if options.bundle_pets else "installer"
    app_name = "YierBubuCodexNative" if options.native_installer else "YierBubuPet"
    stem = f"{app_name}-{__version__}-{kind}-{arch}-{tag}"
    extension = ".exe" if windows else ".zip"
    result = output/(stem+extension)
    if result.exists():
        parser.error(f"Use a new output location: {result} already exists.")
    assets = options.bundle_pets.resolve() if options.bundle_pets else None
    args = ["--noconfirm","--clean","--windowed","--name",app_name,
            "--paths",str(repo),"--add-data",f"{repo/'yier_bubu/actions.json'}:yier_bubu",
            "--add-data",f"{repo/'yier_bubu/source-lock.json'}:yier_bubu"]
    if windows:
        args += ["--onefile"]
    else:
        args += ["--onedir","--osx-bundle-identifier",f"net.yierbubu.{app_name.lower()}"]
    if assets:
        for config in configurations():
            folder = assets/config["id"]
            pet_id, manifest, atlas = bundle_files(folder)
            for file in (manifest,atlas):
                args += ["--add-data",f"{file}:yier_bubu/bundled/{pet_id}"]
    with TemporaryDirectory(prefix="yier-bubu-build-",dir=output) as temp:
        stage = Path(temp)
        built = stage/"dist"
        launch_mode = stage/"launch-mode.json"
        launch_mode.write_text(json.dumps({"native_only":options.native_installer}),"utf-8")
        args += ["--add-data",f"{launch_mode}:yier_bubu"]
        subprocess.run([sys.executable,"-m","PyInstaller",*args,
                        "--distpath",str(built),"--workpath",str(stage/"work"),
                        "--specpath",str(stage),str(repo/"launch_pet.py")],check=True,cwd=repo,
                       env={**os.environ,"PYINSTALLER_CONFIG_DIR":str(stage/"cache")})
        if windows:
            (built/(app_name+".exe")).replace(result)
        else:
            app = built/(app_name+".app")
            subprocess.run(["/usr/bin/codesign","--verify","--deep","--strict",str(app)],check=True)
            subprocess.run(["/usr/bin/ditto","-c","-k","--sequesterRsrc","--keepParent",str(app),str(result)],check=True)
    print(result)


if __name__ == "__main__":
    main()
