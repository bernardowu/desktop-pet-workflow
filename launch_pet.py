import json
from pathlib import Path
import sys
import traceback

from yier_bubu.local_pet import main
from yier_bubu.platform_support import app_data


if __name__ == "__main__":
    try:
        if getattr(sys,"frozen",False):
            mode = Path(__file__).resolve().parent/"yier_bubu/launch-mode.json"
            if json.loads(mode.read_text("utf-8"))["native_only"]:
                sys.argv.append("--native-only")
        main()
    except Exception:
        folder = app_data()
        folder.mkdir(parents=True, exist_ok=True)
        (folder/"startup-error.log").write_text(traceback.format_exc(),"utf-8")
        raise
