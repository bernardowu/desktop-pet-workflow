"""A local Windows and macOS pet that loops Codex activity until completion."""
import argparse
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
from queue import Empty, Queue
import sys
from threading import Event, Thread
import time
import tkinter as tk
from tkinter import messagebox, ttk
import traceback

from PIL import Image, ImageTk

from yier_bubu.library import Library
from yier_bubu.platform_support import app_data, engine_started, instance
from yier_bubu.task_monitor import TaskMonitor

codex_home = Path(os.environ.get("CODEX_HOME") or Path.home()/".codex")
background = "systemTransparent" if sys.platform == "darwin" else "#ff00ff"
rows = {"idle": 0, "running": 7, "review": 8}
delays_ms = {"idle": 185, "running": 135, "review": 135}
pet_width, pet_height = 150, 163


def save_json(path, data):
    pending = path.with_suffix(".tmp")
    pending.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n","utf-8")
    pending.replace(path)


def track(queue, stopped, sessions):
    monitor = TaskMonitor(sessions)
    stamp, refreshed = None, 0
    previous = None
    while not stopped.is_set():
        now = time.time()
        if now - refreshed > 3:
            stamp, refreshed = engine_started(), now
        current = monitor.sample(engine_started=stamp, now=now)
        if current != previous:
            queue.put(current)
            previous = current
        stopped.wait(0.7)


def sprite_frames(folder):
    with Image.open(folder/"spritesheet.webp") as image:
        atlas = image.convert("RGBA")
    if atlas.size != (1536,1872):
        raise ValueError(f"Unsupported atlas size in {folder}")
    layers = {}
    for state,row in rows.items():
        layers[state] = []
        for col in range(6):
            tile = atlas.crop((col*192,row*208,(col+1)*192,(row+1)*208))
            tile = tile.resize((pet_width,pet_height),Image.Resampling.LANCZOS)
            # A color-key window needs fully transparent edge pixels to stay invisible.
            if sys.platform == "win32":
                tile.putalpha(tile.getchannel("A").point(lambda value: 255 if value >= 112 else 0))
            layers[state].append(tile)
    return layers


class PetWindow:
    def __init__(self, root, library, pet_id=None, *, monitor=True):
        self.root = root
        self.library = library
        self.catalog = library.catalog
        self.config_path = library.data_dir/"preferences.json"
        self.status_path = library.data_dir/"runtime-status.json"
        self.state, self.active_count = "idle", 0
        self.frame = 0
        self.next_frame = 0
        self.render_count = 0
        self.last_status = 0
        self.stopped = Event()
        self.queue = Queue()
        try:
            self.saved = json.loads(self.config_path.read_text("utf-8"))
        except (OSError, ValueError):
            self.saved = {}
        if not isinstance(self.saved,dict):
            self.saved = {}
        pet_id = pet_id or self.saved.get("pet_id")
        self.pet_id = pet_id if pet_id in self.catalog else "yier-solo-v2"
        self.choice = tk.StringVar(value=self.pet_id)
        self.sprite = tk.Label(root, background=background, borderwidth=0, highlightthickness=0)
        self.sprite.pack(fill="both",expand=True)
        root.title("一二布布 · 本地桌宠")
        root.configure(background=background)
        root.overrideredirect(True)
        root.wm_attributes("-topmost",True)
        if sys.platform == "win32":
            root.wm_attributes("-toolwindow",True)
            root.wm_attributes("-transparentcolor",background)
        else:
            root.wm_attributes("-transparent",True)
        screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
        x = self.saved.get("x")
        y = self.saved.get("y")
        x = x if isinstance(x,int) else screen_width-pet_width-28
        y = y if isinstance(y,int) else screen_height-pet_height-76
        x = min(max(0,x),screen_width-pet_width)
        y = min(max(0,y),screen_height-pet_height)
        root.geometry(f"{pet_width}x{pet_height}+{x}+{y}")
        self.anchor = (0,0)
        self.sprite.bind("<ButtonPress-1>",self.anchor_drag)
        self.sprite.bind("<B1-Motion>",self.drag)
        self.sprite.bind("<ButtonRelease-1>",lambda _event:self.save_preferences())
        self.sprite.bind("<Button-3>",self.menu)
        if sys.platform == "darwin":
            self.sprite.bind("<Button-2>",self.menu)
            self.sprite.bind("<Control-Button-1>",self.menu)
        root.protocol("WM_DELETE_WINDOW",self.close)
        self.load_pet(self.pet_id, save=False)
        if monitor:
            Thread(target=track,args=(self.queue,self.stopped,library.codex_home/"sessions"),daemon=True).start()
        self.tick()

    def load_pet(self, pet_id, save=True):
        self.pet_id = pet_id
        self.frames = {state:[ImageTk.PhotoImage(tile,master=self.root) for tile in tiles]
                       for state,tiles in sprite_frames(self.library.folder(pet_id)).items()}
        self.frame, self.next_frame, self.render_count = 0, 0, 0
        self.sprite.configure(image=self.frames[self.state][0])
        if save:
            self.save_preferences()
        self.write_status()

    def write_status(self):
        self.last_status = time.monotonic()
        try:
            save_json(self.status_path,{"pet_id":self.pet_id,"state":self.state,
                                  "active_local_tasks":self.active_count,
                                  "frames_rendered_in_state":self.render_count,
                                  "updated_at":datetime.now().astimezone().isoformat()})
        except OSError:
            pass

    def save_preferences(self):
        save_json(self.config_path,{"pet_id":self.pet_id,"x":self.root.winfo_x(),"y":self.root.winfo_y()})

    def anchor_drag(self,event):
        self.anchor = (event.x_root-self.root.winfo_x(),event.y_root-self.root.winfo_y())

    def drag(self,event):
        x, y = event.x_root-self.anchor[0], event.y_root-self.anchor[1]
        self.root.geometry(f"{x:+d}{y:+d}")

    def menu(self,event):
        menu = tk.Menu(self.root,tearoff=False)
        for pet_id,item in self.catalog.items():
            menu.add_radiobutton(label=item["name"],variable=self.choice,value=pet_id,
                                 command=lambda chosen=pet_id:self.load_pet(chosen))
        menu.add_separator()
        menu.add_command(label="安装 Codex 原生桌宠",command=self.install_native)
        menu.add_command(label="退出本地桌宠",command=self.close)
        try:
            menu.tk_popup(event.x_root,event.y_root)
        finally:
            menu.grab_release()

    def install_native(self):
        install_with_dialog(self.root,self.library)

    def tick(self):
        latest = None
        while True:
            try:
                latest = self.queue.get_nowait()
            except Empty:
                break
        if latest and latest != (self.state,self.active_count):
            state,count = latest
            if state != self.state:
                self.frame, self.next_frame, self.render_count = 0, 0, 0
            self.state, self.active_count = state,count
            self.write_status()
        now = time.monotonic()
        if now >= self.next_frame:
            frames = self.frames[self.state]
            self.sprite.configure(image=frames[self.frame])
            self.frame = (self.frame + 1) % len(frames)
            self.next_frame = now + delays_ms[self.state]/1000
            self.render_count += 1
        if now - self.last_status >= 3:
            self.write_status()
        self.root.after(30,self.tick)

    def close(self):
        self.stopped.set()
        self.save_preferences()
        self.root.destroy()


def install_with_dialog(root, library):
    try:
        library.install_native()
    except (OSError,ValueError) as error:
        messagebox.showerror("安装遇到问题",str(error),parent=root)
    else:
        messagebox.showinfo("六款已安装","请在 Codex 的设置 → Pets 中刷新并选择角色。",parent=root)


def prepare_with_dialog(root,library):
    if not library.missing():
        return True
    if not messagebox.askokcancel(
        "准备桌宠素材",
        "首次使用需要从已记录的公开来源下载表情，并在本机生成六款桌宠。任务内容不会发送。现在准备吗？",
        parent=root,
    ):
        return False
    progress = tk.Toplevel(root)
    progress.title("准备桌宠素材")
    progress.resizable(False,False)
    progress.protocol("WM_DELETE_WINDOW",lambda: None)
    ttk.Label(progress,text="正在下载并校验素材",padding=18).pack()
    bar = ttk.Progressbar(progress,mode="indeterminate",length=250)
    bar.pack(padx=18,pady=(0,18))
    bar.start(14)
    result = Queue()
    def prepare():
        try:
            library.prepare(download=True)
        except Exception as error:
            result.put(str(error))
        else:
            result.put(None)
    Thread(target=prepare,daemon=True).start()
    errors = []
    def check():
        try:
            error = result.get_nowait()
        except Empty:
            progress.after(150,check)
            return
        if error:
            errors.append(error)
        progress.destroy()
    progress.after(150,check)
    root.wait_window(progress)
    if errors:
        messagebox.showerror("素材准备失败",errors[0],parent=root)
    return not errors


def check_assets(library):
    verified = {}
    for pet_id in library.catalog:
        folder = library.folder(pet_id)
        if folder is None:
            raise FileNotFoundError(f"Missing spritesheet for {pet_id}")
        frames = sprite_frames(folder)
        verified[pet_id] = len({sha256(tile.tobytes()).digest() for tile in frames["running"]})
        if verified[pet_id] < 2:
            raise ValueError(f"{pet_id} has no working animation")
    return verified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pet")
    parser.add_argument("--data-dir",type=Path,default=app_data())
    parser.add_argument("--codex-home",type=Path,default=codex_home)
    parser.add_argument("--check",action="store_true")
    parser.add_argument("--report",type=Path,help="Write self-check results to a JSON file.")
    parser.add_argument("--gui-smoke",action="store_true",help="Exercise the GUI briefly and exit.")
    parser.add_argument("--native-only",action="store_true",help="Install the native pets without keeping the companion open.")
    parser.add_argument("--install-native",action="store_true",help="Install already prepared packs without opening a window.")
    parser.add_argument("--bundled-only",action="store_true",help="Ignore existing Codex pet assets.")
    args = parser.parse_args()
    args.data_dir.mkdir(parents=True,exist_ok=True)
    library = Library(args.data_dir,args.codex_home,allow_native_cache=not args.bundled_only)
    if args.pet and args.pet not in library.catalog:
        parser.error(f"Unknown pet: {args.pet}")
    if args.check or args.gui_smoke:
        verified = check_assets(library)
        report = {"pets":verified,"gui":False,"native_only":args.native_only}
        if args.gui_smoke:
            window = tk.Tk()
            pet = PetWindow(window,library,args.pet,monitor=False)
            window.after(550,pet.close)
            window.mainloop()
            report["gui"] = pet.render_count >= 2
            if not report["gui"]:
                raise RuntimeError("The GUI did not render two animation frames.")
        if args.report:
            save_json(args.report,report)
        print(json.dumps(report))
        return
    if args.install_native:
        library.install_native()
        return
    if args.native_only:
        window = tk.Tk()
        window.withdraw()
        if prepare_with_dialog(window,library):
            install_with_dialog(window,library)
        window.destroy()
        return
    with instance(args.data_dir) as owned:
        if not owned:
            return
        window = tk.Tk()
        window.withdraw()
        if not prepare_with_dialog(window,library):
            window.destroy()
            return
        PetWindow(window,library,args.pet)
        window.deiconify()
        window.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        path = app_data()
        path.mkdir(parents=True,exist_ok=True)
        (path/"startup-error.log").write_text(traceback.format_exc(),"utf-8")
        raise
