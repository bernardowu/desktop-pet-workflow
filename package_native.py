"""Export all checked native pets as one Windows/macOS archive."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from petkit import bundle_files
from yier_bubu import __version__
from yier_bubu.build import configurations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundles",type=Path,help="Folder containing the catalog's pet bundles.")
    parser.add_argument("--out",type=Path,default=Path("dist"))
    args = parser.parse_args()
    files = [bundle_files(args.bundles/item["id"]) for item in configurations()]
    args.out.mkdir(parents=True,exist_ok=True)
    result = args.out/f"YierBubuPet-{__version__}-Codex-Native-Windows-macOS.zip"
    with ZipFile(result,"x",compression=ZIP_DEFLATED) as output:
        for pet_id,manifest,atlas in files:
            output.write(manifest,f"{pet_id}/pet.json")
            output.write(atlas,f"{pet_id}/{atlas.name}")
        notes = (
            "Windows: %USERPROFILE%\\.codex\\pets\nmacOS: ~/.codex/pets\n"
            "Use CODEX_HOME/pets if configured. Copy each extracted pet folder into pets.\n"
            "In Codex, open Settings > Pets, refresh, then choose a character.\n"
            "Character creator: Huang Xiao B (黄小B), https://weibo.com/u/2623471650\n"
        )
        output.writestr("INSTALL.txt",notes)
    with ZipFile(result) as archive:
        if archive.testzip() is not None:
            raise ValueError("Native ZIP did not pass integrity verification")
    print(result.resolve())


if __name__ == "__main__":
    main()
