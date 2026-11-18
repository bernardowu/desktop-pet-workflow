"""Build the Codex pets from the pinned, separately supplied sticker files."""
import argparse
from bisect import bisect_right
from concurrent.futures import ThreadPoolExecutor
from functools import cache
from hashlib import sha256
from itertools import accumulate
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageOps, ImageSequence
import petkit

root = Path(__file__).resolve().parent
repo = root.parent
states = ("idle", "running-right", "running-left", "waving", "jumping",
          "failed", "waiting", "running", "review")
counts = (6, 8, 8, 4, 5, 8, 6, 6, 6)
max_asset_size = 8 * 1024 * 1024

def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")

def download_asset(entry):
    url = entry["source_url"]
    if urlparse(url).scheme != "https":
        raise ValueError(f"Expected an HTTPS source for {entry['path']}")
    request = Request(url, headers={"User-Agent": "desktop-pet-workflow/1.0"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=20) as remote:
                if urlparse(remote.geturl()).scheme != "https":
                    raise ValueError(f"Source redirected outside HTTPS: {entry['path']}")
                return remote.read(max_asset_size + 1)
        except (URLError,OSError) as error:
            permanent = isinstance(error,HTTPError) and error.code not in {408,429,500,502,503,504}
            if attempt == 2 or permanent:
                raise OSError(f"Could not fetch {entry['path']} from {entry['page']}: {error}") from error
            sleep(.75*(attempt+1))


def verify_sources(directory, index, names, download):
    missing = []
    for name in sorted(names):
        entry = index[name]
        path = directory / name
        if path.is_file():
            if sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError(f"Source hash mismatch: {path}")
            continue
        if not download:
            raise FileNotFoundError(f"Missing {path}. Supply the pinned file or use --download.")
        missing.append(entry)
    if not missing:
        return
    directory.mkdir(parents=True, exist_ok=True)

    def save(entry):
        data = download_asset(entry)
        name = entry["path"]
        if len(data) > max_asset_size or sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"The original file changed or was too large: {name} ({entry['page']})")
        with NamedTemporaryFile(dir=directory,prefix=".asset-",delete=False) as temporary:
            temporary.write(data)
        staged = Path(temporary.name)
        try:
            staged.replace(directory/name)
        finally:
            staged.unlink(missing_ok=True)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(save,missing))

def remove_white(frame):
    """Clear light pixels connected to the outside, leaving enclosed white fur."""
    test = Image.new("L", frame.size)
    test.putdata([255 if a == 0 or (min(r,g,b) >= 228 and max(r,g,b)-min(r,g,b) <= 23)
                  else 0 for r,g,b,a in frame.get_flattened_data()])
    border = ImageOps.expand(test, border=1, fill=255)
    ImageDraw.floodfill(border, (0,0), 128)
    mask = border.crop((1,1,frame.width+1,frame.height+1)).point(lambda p: 0 if p==128 else 255)
    frame.putalpha(Image.composite(frame.getchannel("A"), Image.new("L",frame.size), mask))
    return frame

@cache
def read_frames(path, remove_background, erase):
    frames, timings = [], []
    with Image.open(path) as image:
        for i, frame in enumerate(ImageSequence.Iterator(image)):
            if i == 0 and image.info.get("default_image"):
                continue
            rgba = frame.convert("RGBA")
            if remove_background:
                rgba = remove_white(rgba)
            for rectangle in erase:
                rgba.paste((0,0,0,0),rectangle)
            frames.append(rgba)
            timings.append(max(30,frame.info.get("duration",100)))
    return frames, list(accumulate(timings))

def place(spec, count, default_width, assets):
    filename = spec["source"]
    frames, ends = read_frames(assets/filename,spec.get("white",False),
                              tuple(tuple(rect) for rect in spec.get("erase",[])))
    indices = spec.get("frames", [bisect_right(ends,i*ends[-1]//count) for i in range(count)])
    if len(indices) != count or not all(0 <= i < len(frames) for i in indices):
        raise ValueError(f"Invalid frame selection for {filename}: {indices}")
    frames = [frames[i] for i in indices]
    boxes = [frame.getchannel("A").getbbox() for frame in frames]
    if any(box is None for box in boxes):
        raise ValueError(f"Blank source frame: {filename}")
    left,top,right,bottom = (min(b[0] for b in boxes), min(b[1] for b in boxes),
                            max(b[2] for b in boxes), max(b[3] for b in boxes))
    width,height = right-left,bottom-top
    scale = min(spec.get("width",default_width)/width, spec.get("height",148)/height)
    size = (round(width*scale),round(height*scale))
    x = spec.get("center",96)-size[0]//2
    y = spec.get("floor",179)-size[1]
    lift = spec.get("lift",[0]*count)
    sprites = [(frame.crop((left,top,right,bottom)).resize(size, Image.Resampling.LANCZOS), (x,y-shift))
               for frame,shift in zip(frames,lift)]
    return sprites, {**spec,"frames":indices,"output_size":list(size)}

def clean_rgba(image):
    image.putdata([p if p[3] else (0,0,0,0) for p in image.get_flattened_data()])

def make_pet(config, index, assets, output):
    folder = output/"pets"/config["id"]
    (folder/"final").mkdir(parents=True, exist_ok=True)
    (folder/"qa").mkdir(exist_ok=True)
    atlas = Image.new("RGBA",(1536,1872))
    report, tiles = {}, {}
    for row,(state,count) in enumerate(zip(states,counts)):
        if state in {"running-right","running-left"}:
            # Preserve the required data rows, reusing the exact resting pixels.
            sequence = [tiles["idle"][i * len(tiles["idle"]) // count] for i in range(count)]
            report[state] = {"reuse":"idle","intent":"Resting appearance while dragged."}
        else:
            specs = config["states"][state]
            layers = [place(spec,count,config["width"],assets) for spec in specs]
            sequence = [Image.new("RGBA",(192,208)) for _ in range(count)]
            for sprites,_ in layers:
                for tile,(sprite,xy) in zip(sequence,sprites):
                    tile.alpha_composite(sprite,xy)
            report[state] = {"layers":[{**spec,"asset":index[spec["source"]]} for _,spec in layers]}
        tiles[state] = sequence
        for col,tile in enumerate(sequence):
            bounds = tile.getchannel("A").getbbox()
            if not bounds or min(bounds[0],bounds[1],192-bounds[2],208-bounds[3]) < 2:
                raise ValueError(f"{config['id']} {state} frame {col} clipped or blank")
            atlas.paste(tile,(192*col,208*row))
    clean_rgba(atlas)
    atlas.save(folder/"final/spritesheet.webp",lossless=True,exact=True,method=6)
    write_json(folder/"qa/state-mapping.json",report)
    return folder

def call_kit(*args):
    status = petkit.main([str(value) for value in args])
    if status:
        raise ValueError(f"petkit {args[0]} failed")


def configurations():
    return json.loads((root/"actions.json").read_text("utf-8"))


def build_bundles(assets, output, *, selected=None, download=False, previews=False, zip_bundles=False):
    selected = configurations() if selected is None else selected
    dist = output/"dist"
    for item in selected:
        pet_id = item["id"]
        if (dist/pet_id).exists() or (dist/f"{pet_id}.zip").exists():
            raise ValueError(f"A bundle for {pet_id} already exists. Choose a new output folder.")
    entries = json.loads((root/"source-lock.json").read_text("utf-8"))["assets"]
    index = {entry["path"]:entry for entry in entries}
    names = {layer["source"] for pet in selected for layers in pet["states"].values() for layer in layers}
    verify_sources(assets,index,names,download)
    for item in selected:
        folder = make_pet(item,index,assets,output)
        atlas = folder/"final/spritesheet.webp"
        call_kit("validate",atlas,"--version","v1","--json-out",folder/"qa/structure.json")
        if previews:
            call_kit("preview",atlas,"--version","v1","--out",folder/"qa/previews")
        extra = ["--zip"] if zip_bundles else []
        call_kit("package",atlas,"--id",item["id"],"--name",item["name"],
                 "--description",item["description"],"--version","v1","--out",dist,*extra)
    return dist

def main():
    configs = configurations()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets",type=Path,default=repo/"runs/yier-bubu-source")
    parser.add_argument("--out",type=Path,default=repo/"runs/yier-bubu")
    parser.add_argument("--pet",choices=[item["id"] for item in configs])
    parser.add_argument("--download",action="store_true",help="Fetch missing source files and verify their SHA-256.")
    args = parser.parse_args()
    selected = [item for item in configs if args.pet is None or item["id"] == args.pet]
    assets = args.assets.resolve()
    output = args.out.resolve()
    try:
        build_bundles(assets,output,selected=selected,download=args.download,previews=True,zip_bundles=True)
    except (OSError, ValueError) as error:
        parser.exit(1,f"{error}\n")

if __name__ == "__main__":
    main()
