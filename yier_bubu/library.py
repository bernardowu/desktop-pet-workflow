"""Read local pet libraries, prepare missing images, and install native bundles."""
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from petkit import bundle_files
from yier_bubu.build import build_bundles, call_kit, configurations

package_dir = Path(__file__).resolve().parent


class Library:
    def __init__(self, data_dir, codex_home, *, allow_native_cache=True):
        self.data_dir = data_dir
        self.codex_home = codex_home
        self.catalog = {item["id"]:item for item in configurations()}
        self.candidates = [data_dir/"pets",package_dir/"bundled"]
        if allow_native_cache:
            self.candidates.append(codex_home/"pets")

    def folder(self, pet_id):
        for directory in self.candidates:
            path = directory/pet_id
            if (path/"pet.json").is_file() and (path/"spritesheet.webp").is_file():
                return path
        return None

    def missing(self):
        return [item for key,item in self.catalog.items() if self.folder(key) is None]

    def prepare(self, *, download=False):
        missing = self.missing()
        if not missing:
            return
        target = self.data_dir/"pets"
        target.mkdir(parents=True,exist_ok=True)
        with TemporaryDirectory(dir=self.data_dir,prefix="prepare-") as name:
            built = build_bundles(self.data_dir/"sources",Path(name),
                                  selected=missing,download=download)
            for item in missing:
                destination = target/item["id"]
                if destination.exists():
                    raise FileExistsError(f"Existing incomplete pet folder: {destination}")
            for item in missing:
                source = built/item["id"]
                source.rename(target/item["id"])

    def install_native(self):
        sources = [self.folder(pet_id) for pet_id in self.catalog]
        if any(source is None for source in sources):
            raise ValueError("Prepare the missing assets first.")
        for source in sources:
            bundle_files(source)
        for source in sources:
            call_kit("install",source,"--codex-home",self.codex_home)
