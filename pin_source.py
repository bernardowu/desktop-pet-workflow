"""Record a reviewed asset before mapping it into a pet."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlparse

from PIL import Image

lock = Path(__file__).resolve().parent/"yier_bubu/source-lock.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file",type=Path)
    parser.add_argument("--name",required=True,help="Example: bubu-blue-desk.gif")
    parser.add_argument("--page",required=True,help="Original or archived sticker page.")
    parser.add_argument("--url",required=True,help="Direct HTTPS image URL.")
    parser.add_argument("--cache",type=Path,default=Path("runs/yier-bubu-source"))
    args = parser.parse_args()
    if re.fullmatch(r"[a-z0-9][a-z0-9-]*\.(gif|png|webp)",args.name) is None:
        parser.error("Use a lowercase asset name with a GIF, PNG or WebP extension.")
    if any(urlparse(value).scheme != "https" or not urlparse(value).netloc
           for value in (args.page,args.url)):
        parser.error("Provide HTTPS page and media URLs.")
    if args.file.stat().st_size > 8*1024*1024:
        parser.error("Source must be 8 MiB or smaller.")
    with Image.open(args.file) as image:
        if image.format.lower() != Path(args.name).suffix.lstrip("."):
            parser.error("The asset name extension must match the actual image format.")
        if getattr(image,"n_frames",1) < 2:
            parser.error("Expected a genuinely animated sticker.")
        record = {"path":args.name,"source_url":args.url,"page":args.page,
                  "frames":image.n_frames,"size":list(image.size),
                  "sha256":sha256(args.file.read_bytes()).hexdigest()}
    catalog = json.loads(lock.read_text("utf-8"))
    if any(item["path"] == args.name for item in catalog["assets"]):
        parser.error("That asset name is already pinned. Use a new name.")
    args.cache.mkdir(parents=True,exist_ok=True)
    target = args.cache/args.name
    with args.file.open("rb") as source,target.open("xb") as destination:
        shutil.copyfileobj(source,destination)
    catalog["assets"].append(record)
    catalog["assets"].sort(key=lambda item:item["path"])
    lock.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n","utf-8")
    print(json.dumps(record,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
