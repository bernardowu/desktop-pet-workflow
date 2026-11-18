"""Portable tests with synthetic atlas geometry and an isolated Codex home."""
from pathlib import Path
import json
import os
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from PIL import Image, ImageDraw

import petkit


class PetKitTest(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(prefix="petkit-测试-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def atlas(self, version, file):
        rows = petkit.VERSIONS[version]
        image = Image.new("RGBA", (1536, 208 * len(rows)))
        draw = ImageDraw.Draw(image)
        for row, (_, count) in enumerate(rows):
            for col in range(count):
                x, y = 192 * col + 65, 208 * row + 127
                draw.rectangle((x, y - col, x + 30, y + 40 - col), fill="#cb4b16")
        image.save(file, lossless=True)
        return image

    def cli(self, *args, code=0):
        result = subprocess.run(
            [sys.executable, str(Path(petkit.__file__).resolve()), *map(str, args)],
            capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result.stdout

    def test_validate_and_preview_v2_png(self):
        atlas = self.root / "v2.png"
        self.atlas("v2", atlas)
        preview = self.root / "preview"
        report = json.loads(self.cli("validate", atlas, "--version", "v2"))
        self.assertEqual(report["required_frames"], 73)
        self.cli("preview", atlas, "--out", preview)
        self.assertTrue((preview / "look-directions.png").is_file())
        with Image.open(preview / "idle-jump-idle.gif") as animation:
            self.assertGreater(animation.n_frames, 1)

    def test_reject_blank_required_frame_and_nonempty_padding(self):
        atlas = self.root / "broken.png"
        image = self.atlas("v1", atlas)
        image.paste((0, 0, 0, 0), (0, 0, 192, 208))
        image.putpixel((192 * 7 + 12, 12), (255, 0, 0, 255))
        image.save(atlas)
        report = json.loads(self.cli("validate", atlas, code=1))
        self.assertFalse(report["ok"])
        self.assertEqual(len(report["errors"]), 2)

    def test_package_zip_install_and_preserve_existing(self):
        atlas = self.root / "local.webp"
        self.atlas("v1", atlas)
        out = self.root / "dist"
        self.cli("package", atlas, "--version", "v1", "--out", out, "--id", "ember-moth",
                 "--name", "点灯蛾", "--description", "A tiny moth.", "--zip")
        with ZipFile(out / "ember-moth.zip") as archive:
            self.assertEqual(set(archive.namelist()), {"ember-moth/pet.json", "ember-moth/spritesheet.webp"})
            self.assertEqual(archive.read("ember-moth/spritesheet.webp"), atlas.read_bytes())
        home = self.root / "test codex home"
        bundle = out / "ember-moth"
        self.cli("install", bundle, "--codex-home", home)
        self.assertIn("Already installed", self.cli("install", bundle, "--codex-home", home))
        dest = home / "pets" / "ember-moth" / "pet.json"
        before = dest.read_bytes()
        self.assertEqual(json.loads(before)["displayName"], "点灯蛾")
        source = bundle / "pet.json"
        manifest = json.loads(source.read_bytes())
        manifest["description"] = "A new revision."
        source.write_text(json.dumps(manifest), encoding="utf-8")
        self.cli("install", bundle, "--codex-home", home, code=1)
        self.assertEqual(dest.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
