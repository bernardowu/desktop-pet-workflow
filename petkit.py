"""Inspect, preview, package, and install transparent desktop pet atlases."""
import argparse
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import sys
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image, ImageDraw, UnidentifiedImageError

CELL_W = 192
CELL_H = 208
COLUMNS = 8
MAX_BYTES = 20 * 1024 * 1024
STATES = (
    ("idle", 6), ("running-right", 8), ("running-left", 8),
    ("waving", 4), ("jumping", 5), ("failed", 8),
    ("waiting", 6), ("running", 6), ("review", 6),
)
LOOK = tuple(f"{i * 22.5:g}" for i in range(16))
VERSIONS = {"v1": STATES, "v2": STATES + (("look-1", 8), ("look-2", 8))}
FORMATS = {".png": "PNG", ".webp": "WEBP"}


def check_id(pet_id):
    if not isinstance(pet_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,62}", pet_id):
        raise ValueError("Pet ID must use 1–63 lowercase ASCII letters, digits, hyphens or underscores.")
    if re.fullmatch(r"con|prn|aux|nul|com[1-9]|lpt[1-9]", pet_id):
        raise ValueError("Pet ID is a reserved Windows basename.")
    return pet_id


def cell(image, row, col):
    x, y = col * CELL_W, row * CELL_H
    return image.crop((x, y, x + CELL_W, y + CELL_H))


def inspect_atlas(path, expected="auto"):
    suffix = path.suffix.lower()
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if suffix not in FORMATS or not 0 < len(data) <= MAX_BYTES:
        raise ValueError("Expected a nonempty PNG or WebP no larger than 20 MiB.")
    with Image.open(BytesIO(data)) as source:
        if source.format != FORMATS[suffix] or getattr(source, "n_frames", 1) != 1:
            raise ValueError("File format must match its extension and contain a single image.")
        version = next((name for name, rows in VERSIONS.items()
                        if source.size == (COLUMNS * CELL_W, len(rows) * CELL_H)), None)
        if version is None:
            raise ValueError(f"{source.width}×{source.height}: expected 1536×1872 or 1536×2288.")
        if expected != "auto" and version != expected:
            raise ValueError(f"Expected {expected}, got {version}.")
        image = source.convert("RGBA")
    errors = []
    edge_cells = []
    rows = VERSIONS[version]
    for row, (state, count) in enumerate(rows):
        for col in range(COLUMNS):
            alpha = cell(image, row, col).getchannel("A")
            bounds = alpha.getbbox()
            if col < count:
                if not bounds:
                    errors.append(f"{state}, cell ({row},{col}): blank required frame")
                elif alpha.getextrema()[0] != 0:
                    errors.append(f"{state}, cell ({row},{col}): no transparent background")
                elif bounds[0] == 0 or bounds[1] == 0 or bounds[2] == CELL_W or bounds[3] == CELL_H:
                    edge_cells.append(f"{state} ({row},{col})")
            elif bounds:
                errors.append(f"{state}, cell ({row},{col}): unused slot is not transparent")
    report = {
        "ok": not errors,
        "version": version,
        "format": FORMATS[suffix],
        "dimensions": list(image.size),
        "required_frames": sum(count for _, count in rows),
        "sha256": sha256(data).hexdigest(),
        "errors": errors,
        "check_edges_visually": edge_cells,
    }
    return image, report


def require_valid(report):
    if not report["ok"]:
        raise ValueError("\n".join(report["errors"]))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_previews(image, version, output):
    output.mkdir(parents=True, exist_ok=True)
    width, height = CELL_W // 2, CELL_H // 2
    gutter, label = 6, 20
    rows = VERSIONS[version]
    sheet = Image.new("RGB", (COLUMNS * (width + gutter), len(rows) * (height + label + gutter)), "#0a0c10")
    draw = ImageDraw.Draw(sheet)
    for row, (state, count) in enumerate(rows):
        frames = []
        for col in range(count):
            frame = cell(image, row, col)
            matte = Image.new("RGBA", frame.size, "#161b22")
            matte.alpha_composite(frame)
            preview = matte.convert("RGB")
            frames.append(preview)
            x, y = col * (width + gutter), row * (height + label + gutter)
            title = LOOK[(row - len(STATES)) * 8 + col] + " deg" if row >= len(STATES) else f"{state} {col + 1}"
            draw.text((x + 3, y + 3), title, fill="#f5f1ec")
            sheet.paste(preview.resize((width, height), Image.Resampling.LANCZOS), (x, y + label))
        if row < len(STATES):
            frames[0].save(output / f"{state}.gif", save_all=True, append_images=frames[1:], duration=130, loop=0)
    sheet.save(output / "contact-sheet.png")
    if version == "v2":
        sheet.crop((0, len(STATES) * (height + label + gutter), sheet.width, sheet.height)).save(output / "look-directions.png")
    transition = [cell(image, row, col) for row in (0, 4, 0) for col in range(STATES[row][1])]
    matte_frames = []
    for frame in transition:
        matte = Image.new("RGBA", frame.size, "#161b22")
        matte.alpha_composite(frame)
        matte_frames.append(matte.convert("RGB"))
    matte_frames[0].save(output / "idle-jump-idle.gif", save_all=True, append_images=matte_frames[1:], duration=130, loop=0)


def bundle_files(folder):
    manifest_file = folder / "pet.json"
    if manifest_file.is_symlink():
        raise ValueError("pet.json must be a regular file inside the package.")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("pet.json must be a JSON object.")
    pet_id = check_id(manifest.get("id"))
    if pet_id != folder.name:
        raise ValueError("Bundle folder name must equal the pet.json id.")
    for field in ("displayName", "description"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            raise ValueError(f"Missing nonempty pet.json field: {field}")
    filename = manifest.get("spritesheetPath")
    if filename not in ("spritesheet.png", "spritesheet.webp"):
        raise ValueError("spritesheetPath must be spritesheet.png or spritesheet.webp.")
    atlas = folder / filename
    if not atlas.is_file() or atlas.is_symlink():
        raise ValueError("The sprite sheet must be a regular file inside the package.")
    _, report = inspect_atlas(atlas)
    require_valid(report)
    return pet_id, manifest_file, atlas


def stage_bundle(destination, populate):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Already exists: {destination}")
    with TemporaryDirectory(prefix=".petkit-", dir=destination.parent) as stage:
        ready = Path(stage) / destination.name
        ready.mkdir()
        populate(ready)
        ready.rename(destination)


def package(args):
    pet_id = check_id(args.id)
    if not args.name.strip() or not args.description.strip():
        raise ValueError("Name and description cannot be blank.")
    _, report = inspect_atlas(args.atlas, args.version)
    require_valid(report)
    destination = args.out / pet_id
    filename = "spritesheet" + args.atlas.suffix.lower()
    archive = args.out / f"{pet_id}.zip"
    if args.zip and (archive.exists() or archive.is_symlink()):
        raise FileExistsError(f"Already exists: {archive}")

    def populate(folder):
        shutil.copyfile(args.atlas, folder / filename)
        if sha256((folder / filename).read_bytes()).hexdigest() != report["sha256"]:
            raise ValueError("Atlas changed after validation. Re-run packaging.")
        write_json(folder / "pet.json", {
            "id": pet_id, "displayName": args.name.strip(),
            "description": args.description.strip(), "spritesheetPath": filename,
        })

    stage_bundle(destination, populate)
    if args.zip:
        with TemporaryDirectory(prefix=".petkit-", dir=args.out) as stage:
            built = Path(stage) / archive.name
            with ZipFile(built, "w", compression=ZIP_DEFLATED) as stream:
                for name in ("pet.json", filename):
                    stream.write(destination / name, f"{pet_id}/{name}")
            built.rename(archive)
        print(archive.resolve())
    print(destination.resolve())


def install(args):
    pet_id, manifest, atlas = bundle_files(args.bundle)
    codex_home = args.codex_home or Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    destination = codex_home.expanduser() / "pets" / pet_id
    if destination.is_dir() and not destination.is_symlink():
        originals = (manifest, atlas)
        if all((destination / item.name).is_file() and not (destination / item.name).is_symlink()
               and (destination / item.name).read_bytes() == item.read_bytes() for item in originals):
            print(f"Already installed: {destination}")
            return

    def populate(folder):
        for item in (manifest, atlas):
            shutil.copyfile(item, folder / item.name)
        bundle_files(folder)

    stage_bundle(destination, populate)
    print(f"Installed: {destination}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "preview", "package"):
        command = sub.add_parser(name)
        command.add_argument("atlas", type=Path)
        command.add_argument("--version", choices=("auto", *VERSIONS), default="auto")
        if name == "validate":
            command.add_argument("--json-out", type=Path)
        elif name == "preview":
            command.add_argument("--out", type=Path, required=True)
        else:
            command.add_argument("--out", type=Path, required=True)
            command.add_argument("--id", required=True)
            command.add_argument("--name", required=True)
            command.add_argument("--description", required=True)
            command.add_argument("--zip", action="store_true")
    command = sub.add_parser("install")
    command.add_argument("bundle", type=Path)
    command.add_argument("--codex-home", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "install":
            install(args)
        elif args.command == "package":
            package(args)
        else:
            image, report = inspect_atlas(args.atlas, args.version)
            if args.command == "validate":
                if args.json_out:
                    args.json_out.parent.mkdir(parents=True, exist_ok=True)
                    write_json(args.json_out, report)
                print(json.dumps(report, ensure_ascii=False, indent=2))
                return 0 if report["ok"] else 1
            require_valid(report)
            make_previews(image, report["version"], args.out)
            print(args.out.resolve())
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
