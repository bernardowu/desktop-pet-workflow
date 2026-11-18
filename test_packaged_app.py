"""Smoke-check frozen installers with synthetic artwork and a clean Codex home."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw
from petkit import STATES, CELL_W, CELL_H, COLUMNS
from yier_bubu.build import configurations


def fixture(root):
    for pet in configurations():
        folder = root/"pets"/pet["id"]
        folder.mkdir(parents=True)
        atlas = Image.new("RGBA",(CELL_W*COLUMNS,CELL_H*len(STATES)))
        draw = ImageDraw.Draw(atlas)
        for r,(_,count) in enumerate(STATES):
            for frame in range(count):
                x = frame*CELL_W+45+frame*2
                y = r*CELL_H+65
                draw.ellipse((x,y,x+75,y+80),fill=(63,45,121,255))
        atlas.save(folder/"spritesheet.webp",lossless=True,exact=True)
        manifest = {"id":pet["id"],"displayName":pet["name"],"description":"Synthetic test sprite",
                    "spritesheetPath":"spritesheet.webp"}
        (folder/"pet.json").write_text(json.dumps(manifest),"utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact",type=Path)
    parser.add_argument("--gui",action="store_true")
    parser.add_argument("--embedded",action="store_true",help="Test the embedded offline assets.")
    args = parser.parse_args()
    artifact = args.artifact.resolve()
    native = artifact.name.startswith("YierBubuCodexNative-")
    with TemporaryDirectory() as name:
        scratch = Path(name)
        if artifact.suffix == ".zip" and sys.platform == "darwin":
            subprocess.run(["/usr/bin/ditto","-x","-k",str(artifact),str(scratch)],check=True)
            name = artifact.name.split("-",1)[0]
            artifact = scratch/f"{name}.app/Contents/MacOS/{name}"
        app_data = scratch/"data"
        if not args.embedded:
            fixture(app_data)
        report = scratch/"report.json"
        subprocess.run([str(artifact),"--data-dir",str(app_data),"--codex-home",str(scratch/"no-codex"),
                        "--bundled-only","--report",str(report),
                        "--gui-smoke" if args.gui else "--check"],check=True,timeout=50)
        result = json.loads(report.read_text("utf-8"))
        if len(result["pets"]) != len(configurations()) or any(n<2 for n in result["pets"].values()):
            raise ValueError("The frozen app did not load all animated pets.")
        if result["native_only"] != native:
            raise ValueError("Installer launched in the wrong mode.")
        if args.gui and not result["gui"]:
            raise ValueError("The frozen app did not render its smoke-test window.")
        if native:
            codex_home = scratch/"codex-install-check"
            subprocess.run([str(artifact),"--data-dir",str(app_data),"--codex-home",str(codex_home),
                            "--bundled-only","--install-native"],check=True,timeout=50)
            if not all((codex_home/"pets"/pet["id"]/"pet.json").is_file() for pet in configurations()):
                raise ValueError("Native installer did not install all bundles.")
        print(json.dumps(result))


if __name__ == "__main__":
    main()
