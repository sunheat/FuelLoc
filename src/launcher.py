"""Show the Windows startup window before loading the device stack."""

import os
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.request import urlopen


if getattr(sys, "frozen", False):
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")


def main():
    root = tk.Tk()
    root.title("FuelLoc setup")
    root.iconbitmap(default=str(Path(__file__).resolve().parent / 'static' / 'fuelloc.ico'))
    root.geometry("650x320")
    root.resizable(False, False)
    ttk.Label(root, text="Getting FuelLoc ready", font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=24, pady=(20, 5))
    ttk.Label(root, text="You can enter once the local app is ready, even if your iPhone is not connected yet.").pack(anchor="w", padx=24)

    names = ("Local app", "App window", "Apple device support", "iPhone connection")
    rows = []
    for name in names:
        row = ttk.Label(root, text=f"◐  {name}: checking...")
        row.pack(anchor="w", padx=30, pady=8)
        rows.append(row)

    events = queue.Queue()
    state = {"ready": False, "entered": False, "url": None, "app": None, "pending": set(range(len(rows)))}
    buttons = ttk.Frame(root)
    buttons.pack(side="bottom", fill="x", padx=24, pady=18)

    def enter():
        if not state["ready"]:
            return
        app = state["app"]
        if app.find_app_browser() is None:
            messagebox.showerror("FuelLoc", "Install Microsoft Edge or Google Chrome to open the app window.")
            return
        try:
            app.open_app_window(state["url"])
        except OSError as error:
            messagebox.showerror("FuelLoc", f"Could not open the app window: {error}")
            return
        state["entered"] = True
        root.destroy()

    enter_button = ttk.Button(buttons, text="Enter app", command=enter, state="disabled")
    enter_button.pack(side="right")

    def scan():
        app = state["app"]
        if app is None:
            return
        for index, (_, check) in enumerate(app.prerequisite_checks(), start=1):
            try:
                ok, detail = check()
            except Exception as error:
                ok, detail = False, str(error)
            events.put(("check", index, ok, detail))
        events.put(("checks_done",))

    def recheck():
        recheck_button.configure(state="disabled")
        if state["app"] is None:
            state["pending"].update(range(len(rows)))
            threading.Thread(target=start_server, daemon=True).start()
            return
        state["pending"].update((1, 2, 3))
        threading.Thread(target=scan, daemon=True).start()

    recheck_button = ttk.Button(buttons, text="Recheck", command=recheck, state="disabled")
    recheck_button.pack(side="right", padx=10)

    def start_server():
        try:
            import main as app
            from werkzeug.serving import make_server

            app.chosen_port = app.select_port(None)
            server = make_server("127.0.0.1", app.chosen_port, app.app, threaded=True)
            threading.Thread(target=server.serve_forever, name="fuel-loc-http", daemon=True).start()
            url = f"http://127.0.0.1:{app.chosen_port}"
            with urlopen(url, timeout=5) as response:
                if response.status != 200:
                    raise RuntimeError("The local app did not respond")
            events.put(("server", app, url))
        except Exception as error:
            events.put(("error", str(error)))

    def pump():
        try:
            while True:
                event = events.get_nowait()
                if event[0] == "server":
                    _, app, url = event
                    state.update({"ready": True, "url": url, "app": app})
                    state["pending"].discard(0)
                    rows[0].configure(text="✓  Local app: ready")
                    enter_button.configure(state="normal")
                    threading.Thread(target=scan, daemon=True).start()
                elif event[0] == "error":
                    state["pending"].clear()
                    rows[0].configure(text=f"✗  Local app: {event[1]}")
                    for index in range(1, len(rows)):
                        rows[index].configure(text=f"—  {names[index]}: waiting for the app to start")
                    recheck_button.configure(state="normal")
                elif event[0] == "checks_done":
                    recheck_button.configure(state="normal")
                else:
                    _, index, ok, detail = event
                    state["pending"].discard(index)
                    rows[index].configure(text=f"{'✓' if ok else '✗'}  {names[index]}: {detail}")
        except queue.Empty:
            pass
        root.after(100, pump)

    def animate(frame=0):
        symbols = "◐◓◑◒"
        for index in state["pending"]:
            rows[index].configure(text=f"{symbols[frame % 4]}  {names[index]}: checking...")
        root.after(180, animate, frame + 1)

    root.after(100, pump)
    root.after(180, animate)
    # Paint the prepared window before device imports can compete for the GIL.
    root.update_idletasks()
    threading.Thread(target=start_server, name="fuel-loc-startup", daemon=True).start()
    root.mainloop()
    if state["entered"]:
        threading.Event().wait()


if __name__ == "__main__":
    main()
