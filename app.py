#!/usr/bin/env python3
"""
Sentiment Classifier & Annotation Studio
Clean, modern desktop GUI modeled after FacebookCommentScraper_Portable.
Symmetrical, balanced layout with mathematical alignment across all buttons.

Features:
- Pango + HarfBuzz native complex text layout engine (flawless Bengali/Indic conjuncts & ligatures)
- Perfectly symmetrical 4-column classification grid + balanced 50/50 navigation bar
- Sectioned ttk.LabelFrame layout matching FacebookCommentScraper_Portable
- Instant keyboard shortcuts (default ASDF, always listening, fully configurable)
- Auto-saves every 10 classifications
- Updates original CSV directly with 'sentiment' and 'status' columns
- Generates 4 split CSVs (_positive.csv, _negative.csv, _neutral.csv, _discard.csv)
- Previous & Next navigation, jump-to-row, and jump-to-last button
- 'More ▾' menu consolidating Shortcuts, Reset, Save CSV, and Unlabeled jump
- Cross-platform 'Open Output Folder' and 'Open CSV' with silenced background launch
"""

import os
import sys
import csv
import json
import time
import ctypes
import subprocess
from pathlib import Path
from typing import Optional, Tuple

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from tkinter.scrolledtext import ScrolledText
except ImportError:
    print("[ERROR] Tkinter is not installed on this system.")
    print(" - On Ubuntu/Debian: sudo apt-get install python3-tk")
    sys.exit(1)

__version__ = "2.3.0"
CONFIG_FILE = Path.home() / ".sentiment_annotator_config.json"

DEFAULT_SHORTCUTS = {
    "positive": "a",
    "neutral": "s",
    "negative": "d",
    "discard": "f",
    "prev": "Left",
    "next": "Right"
}


class PangoHarfBuzzRenderer:
    """
    Native Complex Text Layout (CTL) renderer using system Cairo and Pango/HarfBuzz.
    Renders Bengali, Indic scripts, Arabic, and mixed text with 100% accurate
    conjuncts, ligatures, pre-base matras (i-kar), and word-wrapping.
    """
    def __init__(self):
        self.available = False
        try:
            self.cairo = ctypes.CDLL("libcairo.so.2")
            self.pango = ctypes.CDLL("libpango-1.0.so.0")
            self.pangocairo = ctypes.CDLL("libpangocairo-1.0.so.0")
            self._init_c_signatures()
            self.available = True
        except Exception:
            self.available = False

    def _init_c_signatures(self):
        c = self.cairo
        p = self.pango
        pc = self.pangocairo

        c.cairo_image_surface_create.restype = ctypes.c_void_p
        c.cairo_image_surface_create.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        c.cairo_create.restype = ctypes.c_void_p
        c.cairo_create.argtypes = [ctypes.c_void_p]
        c.cairo_set_source_rgb.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_double]
        c.cairo_paint.argtypes = [ctypes.c_void_p]
        c.cairo_move_to.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double]
        c.cairo_surface_write_to_png.restype = ctypes.c_int
        c.cairo_surface_write_to_png.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        c.cairo_surface_destroy.argtypes = [ctypes.c_void_p]
        c.cairo_destroy.argtypes = [ctypes.c_void_p]

        pc.pango_cairo_create_layout.restype = ctypes.c_void_p
        pc.pango_cairo_create_layout.argtypes = [ctypes.c_void_p]
        pc.pango_cairo_show_layout.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        p.pango_font_description_from_string.restype = ctypes.c_void_p
        p.pango_font_description_from_string.argtypes = [ctypes.c_char_p]
        p.pango_font_description_free.argtypes = [ctypes.c_void_p]
        p.pango_layout_set_font_description.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        p.pango_layout_set_text.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        p.pango_layout_set_width.argtypes = [ctypes.c_void_p, ctypes.c_int]
        p.pango_layout_set_wrap.argtypes = [ctypes.c_void_p, ctypes.c_int]
        p.pango_layout_get_pixel_size.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
        p.g_object_unref.argtypes = [ctypes.c_void_p]

    def render(self, text: str, font_size: int = 14, width: int = 600) -> Optional[Tuple[int, int, str]]:
        if not self.available:
            return None

        clean_text = text if text and text.strip() else " "
        text_bytes = clean_text.encode("utf-8", errors="replace")
        PANGO_SCALE = 1024

        # Dummy surface to measure wrapped dimensions
        dummy_surf = self.cairo.cairo_image_surface_create(0, 1, 1)
        dummy_cr = self.cairo.cairo_create(dummy_surf)
        layout = self.pangocairo.pango_cairo_create_layout(dummy_cr)

        font_desc_str = f"Noto Sans Bengali, Vrinda, Kalpurush, FreeSans, Segoe UI, sans-serif {font_size}".encode("utf-8")
        font_desc = self.pango.pango_font_description_from_string(font_desc_str)
        self.pango.pango_layout_set_font_description(layout, font_desc)

        wrap_w = max(width - 36, 220)
        self.pango.pango_layout_set_width(layout, wrap_w * PANGO_SCALE)
        self.pango.pango_layout_set_wrap(layout, 0)  # PANGO_WRAP_WORD = 0
        self.pango.pango_layout_set_text(layout, text_bytes, -1)

        w = ctypes.c_int()
        h = ctypes.c_int()
        self.pango.pango_layout_get_pixel_size(layout, ctypes.byref(w), ctypes.byref(h))

        pad_x = 18
        pad_y = 16
        surf_w = max(w.value + pad_x * 2, width)
        surf_h = max(h.value + pad_y * 2, 80)

        # Real render surface
        surf = self.cairo.cairo_image_surface_create(0, surf_w, surf_h)
        cr = self.cairo.cairo_create(surf)

        # White clean background
        self.cairo.cairo_set_source_rgb(cr, 1.0, 1.0, 1.0)
        self.cairo.cairo_paint(cr)

        # Crisp dark text (#0F172A)
        self.cairo.cairo_set_source_rgb(cr, 0.06, 0.09, 0.16)
        self.cairo.cairo_move_to(cr, float(pad_x), float(pad_y))
        self.pangocairo.pango_cairo_show_layout(cr, layout)

        out_path = f"/tmp/bengali_viewer_render_{os.getpid()}.png"
        self.cairo.cairo_surface_write_to_png(surf, out_path.encode("utf-8"))

        # Free C resources
        self.pango.pango_font_description_free(font_desc)
        self.pango.g_object_unref(layout)
        self.cairo.cairo_destroy(cr)
        self.cairo.cairo_surface_destroy(surf)
        self.cairo.cairo_destroy(dummy_cr)
        self.cairo.cairo_surface_destroy(dummy_surf)

        return surf_w, surf_h, out_path


def open_file_or_folder(path: str):
    """
    Cross-platform utility to open a file or directory with default file explorer/app.
    Silences background terminal warnings (e.g. LibreOffice javaldx) by detaching
    and routing output to DEVNULL.
    """
    if not os.path.exists(path):
        messagebox.showerror("Not Found", f"Path does not exist:\n{path}")
        return

    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Linux: launch xdg-open in detached background process, suppressing stdout/stderr
            subprocess.Popen(
                ["xdg-open", path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
    except Exception as e:
        messagebox.showerror("Error Opening Path", f"Could not open path:\n{e}")


class SentimentClassifierGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"Sentiment Classifier Studio v{__version__} - Portable Edition")
        self.root.geometry("820x660")
        self.root.minsize(620, 480)

        # Apply modern style theme
        self.style = ttk.Style()
        available_themes = self.style.theme_names()
        if "vista" in available_themes:
            self.style.theme_use("vista")
        elif "clam" in available_themes:
            self.style.theme_use("clam")

        self._setup_styles()

        # Complex Script / Bengali Pango Renderer
        self.pango_renderer = PangoHarfBuzzRenderer()
        self.current_rendered_img: Optional[tk.PhotoImage] = None
        self.current_text: str = ""
        self._last_rendered_width: int = 0

        # State variables
        self.csv_path: Optional[Path] = None
        self.csv_headers = []
        self.rows = []
        self.text_column: Optional[str] = None
        self.current_index = 0
        self.labels = {}  # {row_index: label_str}
        self.autosave_interval = 10
        self.labels_since_last_save = 0
        self.font_size = 14

        self.input_file_var = tk.StringVar(value="No file loaded")
        self.text_col_var = tk.StringVar()
        self.jump_var = tk.StringVar()

        # Shortcuts
        self.shortcuts = dict(DEFAULT_SHORTCUTS)
        self._load_shortcuts()

        # Build Symmetrical UI
        self._create_widgets()

        # Keyboard listener
        self.root.bind("<Key>", self._handle_keypress)
        self.root.bind("<Control-c>", lambda e: self.copy_current_text())
        self.root.bind("<Control-C>", lambda e: self.copy_current_text())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Quick start if file argument provided
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            self.load_csv_file(sys.argv[1])

    def _setup_styles(self):
        """Configures ttk styles matching the clean aesthetic of FacebookCommentScraper."""
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#1E293B")
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 9), foreground="#64748B")
        self.style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground="#1E293B")
        self.style.configure("Status.TLabel", font=("Segoe UI", 9, "bold"), foreground="#1E293B")
        self.style.configure("Primary.TButton", font=("Segoe UI", 9, "bold"))
        self.style.configure("Subtle.TLabel", font=("Segoe UI", 9), foreground="#64748B")

    # ---------------- SHORTCUTS ----------------

    def _load_shortcuts(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.shortcuts.update(json.load(f))
            except Exception:
                pass

    def _save_shortcuts(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.shortcuts, f, indent=2)
        except Exception:
            pass

    def open_shortcut_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Configure Keyboard Shortcuts")
        dlg.geometry("380x360")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        hdr = ttk.Frame(dlg, padding="16 14 16 8")
        hdr.pack(fill=tk.X)
        ttk.Label(hdr, text="Configure Keyboard Shortcuts", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(hdr, text="Set custom keys for rapid single-finger annotation", style="SubHeader.TLabel").pack(anchor=tk.W)

        body = ttk.Frame(dlg, padding="16 8 16 12")
        body.pack(fill=tk.BOTH, expand=True)

        items = [
            ("positive", "Positive Label:"),
            ("neutral", "Neutral Label:"),
            ("negative", "Negative Label:"),
            ("discard", "Discard Label:"),
            ("prev", "Previous Row:"),
            ("next", "Next Row:")
        ]
        entries = {}

        for i, (key_id, label_text) in enumerate(items):
            row = ttk.Frame(body)
            row.pack(fill=tk.X, pady=4)
            ttk.Label(row, text=label_text, width=16, font=("Segoe UI", 9)).pack(side=tk.LEFT)
            ent = ttk.Entry(row, width=12, justify="center", font=("Segoe UI", 9, "bold"))
            ent.insert(0, self.shortcuts.get(key_id, ""))
            ent.pack(side=tk.LEFT)
            entries[key_id] = ent

        btn_row = ttk.Frame(dlg, padding="16 10 16 16")
        btn_row.pack(fill=tk.X)

        def save_keys():
            for k, e in entries.items():
                val = e.get().strip().lower()
                if val:
                    self.shortcuts[k] = val
            self._save_shortcuts()
            self._update_button_labels()
            dlg.destroy()

        def restore_defaults():
            for k, e in entries.items():
                e.delete(0, tk.END)
                e.insert(0, DEFAULT_SHORTCUTS[k])

        ttk.Button(btn_row, text="Restore Defaults", command=restore_defaults).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Save Keys", style="Primary.TButton", command=save_keys).pack(side=tk.RIGHT)

    # ---------------- WIDGET CREATION ----------------

    def _create_widgets(self):
        # 1. Top Header Banner (Compact single row)
        header_frame = ttk.Frame(self.root, padding="12 6 12 4")
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(
            header_frame,
            text=f"Sentiment Classifier Studio v{__version__}",
            style="Header.TLabel",
        )
        title_lbl.pack(side=tk.LEFT)

        sub_lbl = ttk.Label(
            header_frame,
            text="High-Speed Annotation • Complex Bengali Engine",
            style="SubHeader.TLabel",
        )
        sub_lbl.pack(side=tk.RIGHT, pady=(3, 0))

        # Main container
        main_frame = ttk.Frame(self.root, padding="10 2 10 4")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. PIN BOTTOM ELEMENTS FIRST so action buttons are NEVER pushed out of window
        # Progress bar at very bottom
        self.progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode="determinate")
        self.progress_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(1, 0))

        # Bottom controls and status bar
        ctl_frame = ttk.Frame(main_frame, padding=(0, 2, 0, 1))
        ctl_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Popup menu for 'More'
        self.more_menu = tk.Menu(self.root, tearoff=0)
        self.more_menu.add_command(label="⚙️  Shortcuts...", command=self.open_shortcut_dialog)
        self.more_menu.add_command(label="🔄  Reset...", command=self.prompt_reset)
        self.more_menu.add_separator()
        self.more_menu.add_command(label="💾  Save CSV Now", command=lambda: self.save_all(manual=True))
        self.more_menu.add_separator()
        self.more_menu.add_command(label="⚡  Next Unlabeled Row", command=self.jump_to_next_unlabeled)
        self.more_menu.add_command(label="⏮  Jump to First Row", command=self.jump_to_first)
        self.more_menu.add_command(label="⏭  Jump to Last Row", command=self.jump_to_last)

        # Rightmost buttons pinned first
        self.open_csv_btn = ttk.Button(ctl_frame, text="📄 Open Dataset CSV", command=self._open_output_csv)
        self.open_csv_btn.pack(side=tk.RIGHT)

        self.more_btn = ttk.Menubutton(ctl_frame, text="More", menu=self.more_menu)
        self.more_btn.pack(side=tk.RIGHT, padx=(0, 6))

        self.status_lbl = ttk.Label(ctl_frame, text="Status: Ready. Load a CSV to begin.", style="Status.TLabel")
        self.status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 2. Section 3: Classification Actions & Navigation (Pinned above bottom controls)
        action_group = ttk.LabelFrame(
            main_frame,
            text=" 3. Classification Actions [Shortcuts: A, S, D, F | Navigation: ←, →] ",
            style="Section.TLabelframe",
            padding="6 4 6 4"
        )
        action_group.pack(side=tk.BOTTOM, fill=tk.X, pady=(2, 2))

        # Symmetrical Grid Container: 4 equal columns with 100% proportional width
        action_grid = ttk.Frame(action_group)
        action_grid.pack(fill=tk.X)

        for col_idx in range(4):
            action_grid.columnconfigure(col_idx, weight=1, uniform="equal_cols")

        # Row 0: The 4 Classification Buttons (Equal 25% Width Each)
        self.btn_pos = tk.Button(
            action_grid,
            text="[ A ]  POSITIVE",
            bg="#10B981",
            fg="white",
            activebackground="#059669",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=4,
            cursor="hand2",
            command=lambda: self.label_row("positive")
        )
        self.btn_pos.grid(row=0, column=0, padx=(0, 2), sticky="ew")

        self.btn_neu = tk.Button(
            action_grid,
            text="[ S ]  NEUTRAL",
            bg="#3B82F6",
            fg="white",
            activebackground="#2563EB",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=4,
            cursor="hand2",
            command=lambda: self.label_row("neutral")
        )
        self.btn_neu.grid(row=0, column=1, padx=(2, 2), sticky="ew")

        self.btn_neg = tk.Button(
            action_grid,
            text="[ D ]  NEGATIVE",
            bg="#EF4444",
            fg="white",
            activebackground="#DC2626",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=4,
            cursor="hand2",
            command=lambda: self.label_row("negative")
        )
        self.btn_neg.grid(row=0, column=2, padx=(2, 2), sticky="ew")

        self.btn_dis = tk.Button(
            action_grid,
            text="[ F ]  DISCARD",
            bg="#F59E0B",
            fg="white",
            activebackground="#D97706",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=4,
            cursor="hand2",
            command=lambda: self.label_row("discard")
        )
        self.btn_dis.grid(row=0, column=3, padx=(2, 0), sticky="ew")

        # Row 1: Symmetrical 50/50 Navigation Buttons
        self.btn_prev = tk.Button(
            action_grid,
            text="◀  PREVIOUS",
            bg="#475569",
            fg="white",
            activebackground="#334155",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=4,
            cursor="hand2",
            command=self.prev_row
        )
        self.btn_prev.grid(row=1, column=0, columnspan=2, padx=(0, 2), pady=(3, 0), sticky="ew")

        self.btn_next = tk.Button(
            action_grid,
            text="NEXT  ▶",
            bg="#475569",
            fg="white",
            activebackground="#334155",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=4,
            cursor="hand2",
            command=self.next_row
        )
        self.btn_next.grid(row=1, column=2, columnspan=2, padx=(2, 0), pady=(3, 0), sticky="ew")

        # 3. TOP SECTION: Dataset File & Column Selection
        input_group = ttk.LabelFrame(main_frame, text=" 1. Dataset File & Column ", style="Section.TLabelframe", padding="6 3 6 4")
        input_group.pack(side=tk.TOP, fill=tk.X, pady=(0, 3))

        input_group.columnconfigure(0, weight=0)
        input_group.columnconfigure(1, weight=1)
        input_group.columnconfigure(2, weight=0)
        input_group.columnconfigure(3, weight=0)

        # Row 0: File selection row
        ttk.Label(input_group, text="Dataset CSV:", width=12).grid(row=0, column=0, sticky="w", pady=1)
        self.file_entry = ttk.Entry(input_group, textvariable=self.input_file_var, state="readonly")
        self.file_entry.grid(row=0, column=1, sticky="ew", padx=(0, 6), pady=1)

        browse_btn = ttk.Button(input_group, text="Browse...", width=10, command=self._browse_csv_file)
        browse_btn.grid(row=0, column=2, sticky="ew", padx=(0, 4), pady=1)

        open_folder_btn = ttk.Button(input_group, text="Open Folder", width=11, command=self._open_output_folder)
        open_folder_btn.grid(row=0, column=3, sticky="ew", pady=1)

        # Row 1: Column Selection & Jump Controls
        ttk.Label(input_group, text="Text Column:", width=12).grid(row=1, column=0, sticky="w", pady=1)
        self.col_combo = ttk.Combobox(input_group, textvariable=self.text_col_var, state="readonly")
        self.col_combo.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=1)
        self.col_combo.bind("<<ComboboxSelected>>", self._on_column_changed)

        jump_box = ttk.Frame(input_group)
        jump_box.grid(row=1, column=2, sticky="ew", padx=(0, 4), pady=1)

        ttk.Label(jump_box, text="Jump:").pack(side=tk.LEFT, padx=(0, 2))
        self.jump_entry = ttk.Entry(jump_box, textvariable=self.jump_var, width=5)
        self.jump_entry.pack(side=tk.LEFT, padx=(0, 2))
        self.jump_entry.bind("<Return>", lambda e: self.jump_to_row())

        jump_btn = ttk.Button(jump_box, text="Go", width=3, command=self.jump_to_row)
        jump_btn.pack(side=tk.LEFT)

        jump_last_btn = ttk.Button(input_group, text="Jump to Last", width=11, command=self.jump_to_last)
        jump_last_btn.grid(row=1, column=3, sticky="ew", pady=1)

        # 4. MIDDLE SECTION: Text Display Box (Expands/contracts dynamically)
        text_group = ttk.LabelFrame(main_frame, text=" 2. Current Row Text ", style="Section.TLabelframe", padding="6 4 6 4")
        text_group.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 3))

        meta_row = ttk.Frame(text_group)
        meta_row.pack(fill=tk.X, pady=(0, 3))

        self.row_indicator_lbl = ttk.Label(meta_row, text="Row: 0 / 0", style="Status.TLabel")
        self.row_indicator_lbl.pack(side=tk.LEFT)

        self.label_badge_lbl = ttk.Label(
            meta_row,
            text="[ PENDING ]",
            font=("Segoe UI", 9, "bold"),
            foreground="#64748B"
        )
        self.label_badge_lbl.pack(side=tk.LEFT, padx=14)

        ctrl_frame = ttk.Frame(meta_row)
        ctrl_frame.pack(side=tk.RIGHT)

        self.lbl_copy_feedback = ttk.Label(ctrl_frame, text="", font=("Segoe UI", 8, "bold"), foreground="#10B981")
        self.lbl_copy_feedback.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(ctrl_frame, text="📋 Copy", width=7, command=self.copy_current_text).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(ctrl_frame, text="A+", width=4, command=self.zoom_in).pack(side=tk.RIGHT, padx=(2, 0))
        ttk.Button(ctrl_frame, text="A-", width=4, command=self.zoom_out).pack(side=tk.RIGHT)

        viewer_frame = ttk.Frame(text_group)
        viewer_frame.pack(fill=tk.BOTH, expand=True)

        self.text_scrollbar = ttk.Scrollbar(viewer_frame, orient=tk.VERTICAL)
        self.text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_canvas = tk.Canvas(
            viewer_frame,
            bg="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CBD5E1",
            yscrollcommand=self.text_scrollbar.set,
            height=150
        )
        self.text_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.text_scrollbar.config(command=self.text_canvas.yview)

        self.text_canvas.bind("<Button-4>", lambda e: self.text_canvas.yview_scroll(-2, "units"))
        self.text_canvas.bind("<Button-5>", lambda e: self.text_canvas.yview_scroll(2, "units"))
        self.text_canvas.bind("<MouseWheel>", lambda e: self.text_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.text_canvas.bind("<Configure>", self._on_canvas_configure)

        self.fallback_text = ScrolledText(
            viewer_frame,
            wrap=tk.WORD,
            font=("Noto Sans Bengali", self.font_size),
            bg="#FFFFFF",
            fg="#0F172A",
            relief=tk.SOLID,
            bd=1,
            padx=10,
            pady=10
        )
        self.fallback_text.bind("<Key>", lambda e: "break")

        self._update_button_labels()

    def _update_button_labels(self):
        p = self.shortcuts.get("positive", "a").upper()
        s = self.shortcuts.get("neutral", "s").upper()
        d = self.shortcuts.get("negative", "d").upper()
        f = self.shortcuts.get("discard", "f").upper()
        prev_k = self.shortcuts.get("prev", "Left").upper()
        next_k = self.shortcuts.get("next", "Right").upper()

        self.btn_pos.config(text=f"[ {p} ]  POSITIVE")
        self.btn_neu.config(text=f"[ {s} ]  NEUTRAL")
        self.btn_neg.config(text=f"[ {d} ]  NEGATIVE")
        self.btn_dis.config(text=f"[ {f} ]  DISCARD")
        self.btn_prev.config(text=f"◀  PREVIOUS ({prev_k})")
        self.btn_next.config(text=f"NEXT ({next_k})  ▶")

    # ---------------- KEYBOARD SHORTCUTS ----------------

    def _handle_keypress(self, event):
        if event.widget == self.jump_entry:
            return

        key = event.keysym.lower()
        char = event.char.lower() if event.char else ""

        def matches(target):
            t = str(target).lower()
            return key == t or char == t

        if matches(self.shortcuts.get("positive", "a")):
            self._flash_button(self.btn_pos)
            self.label_row("positive")
            return "break"

        elif matches(self.shortcuts.get("neutral", "s")):
            self._flash_button(self.btn_neu)
            self.label_row("neutral")
            return "break"

        elif matches(self.shortcuts.get("negative", "d")):
            self._flash_button(self.btn_neg)
            self.label_row("negative")
            return "break"

        elif matches(self.shortcuts.get("discard", "f")):
            self._flash_button(self.btn_dis)
            self.label_row("discard")
            return "break"

        elif matches(self.shortcuts.get("prev", "left")) or key in ("left", "backspace"):
            self._flash_button(self.btn_prev)
            self.prev_row()
            return "break"

        elif matches(self.shortcuts.get("next", "right")) or key in ("right", "space", "return"):
            self._flash_button(self.btn_next)
            self.next_row()
            return "break"

    def _flash_button(self, btn):
        orig = btn.cget("background")
        btn.config(background="#FFFFFF")
        self.root.after(75, lambda: btn.config(background=orig))

    def copy_current_text(self):
        if self.current_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_text)
            self.lbl_copy_feedback.config(text="✓ Copied!")
            self.root.after(1500, lambda: self.lbl_copy_feedback.config(text=""))

    # ---------------- CSV MANAGEMENT ----------------

    def _browse_csv_file(self):
        f = filedialog.askopenfilename(
            title="Select CSV Dataset",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if f:
            self.load_csv_file(f)

    def load_csv_file(self, file_path: str):
        path = Path(file_path)
        if not path.exists():
            messagebox.showerror("File Not Found", f"Path does not exist:\n{path}")
            return

        self.csv_path = path
        self.input_file_var.set(str(path))
        self.status_lbl.config(text=f"Loading {path.name}...")
        self.root.update_idletasks()

        encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
        loaded_rows = []
        headers = []

        for enc in encodings:
            try:
                with open(path, mode="r", encoding=enc, errors="replace") as f:
                    sample = f.read(4096)
                    f.seek(0)
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                        delimiter = dialect.delimiter
                    except Exception:
                        delimiter = ","

                    reader = csv.DictReader(f, delimiter=delimiter)
                    headers = list(reader.fieldnames or [])
                    loaded_rows = list(reader)
                    break
            except Exception:
                continue

        if not loaded_rows:
            messagebox.showerror("Load Failed", f"Could not parse or file is empty:\n{path}")
            return

        self.rows = loaded_rows
        self.csv_headers = headers
        self.labels.clear()

        # Check existing labels in original CSV
        for idx, r in enumerate(self.rows):
            existing = r.get("sentiment", "").strip().lower()
            if existing in ("positive", "neutral", "negative", "discard"):
                self.labels[idx] = existing

        # Populate column dropdown
        self.col_combo["values"] = self.csv_headers
        best_col = None
        for cand in ["text", "review", "content", "comment", "body", "tweet", "message", "sentence", "description"]:
            for col in self.csv_headers:
                if cand in col.lower():
                    best_col = col
                    break
            if best_col:
                break

        if not best_col and self.csv_headers:
            best_col = self.csv_headers[0]

        self.text_column = best_col
        self.text_col_var.set(best_col)

        # Load external JSON state if exists
        self._load_progress_json()

        # Find first unlabeled row
        first_unlabeled = self._find_first_unlabeled()
        self.current_index = first_unlabeled if first_unlabeled is not None else 0

        self.update_display()
        self.status_lbl.config(text=f"Status: Loaded {len(self.rows):,} rows from {path.name}")

    def _on_column_changed(self, event=None):
        sel = self.text_col_var.get()
        if sel and sel in self.csv_headers:
            self.text_column = sel
            self.update_display()

    def _get_progress_file(self) -> Path:
        if not self.csv_path:
            return None
        return self.csv_path.parent / f"{self.csv_path.stem}_label_progress.json"

    def _load_progress_json(self):
        pf = self._get_progress_file()
        if pf and pf.exists():
            try:
                with open(pf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.get("labels", {}).items():
                        idx = int(k)
                        if idx < len(self.rows):
                            self.labels[idx] = v
            except Exception:
                pass

    def label_row(self, sentiment: str):
        if not self.rows:
            return

        self.labels[self.current_index] = sentiment
        self.labels_since_last_save += 1

        # Auto-save every 10 classifications
        if self.labels_since_last_save >= self.autosave_interval:
            self.save_all(manual=False)
            self.labels_since_last_save = 0

        # Auto-advance
        if self.current_index < len(self.rows) - 1:
            self.current_index += 1

        self.update_display()

    def prev_row(self):
        if self.rows and self.current_index > 0:
            self.current_index -= 1
            self.update_display()

    def next_row(self):
        if self.rows and self.current_index < len(self.rows) - 1:
            self.current_index += 1
            self.update_display()

    def jump_to_first(self):
        if not self.rows:
            return
        self.current_index = 0
        self.update_display()

    def jump_to_last(self):
        if not self.rows:
            return
        self.current_index = len(self.rows) - 1
        self.update_display()

    def jump_to_next_unlabeled(self):
        if not self.rows:
            return
        idx = self._find_first_unlabeled(start=self.current_index + 1)
        if idx is None:
            idx = self._find_first_unlabeled(start=0)
        if idx is not None:
            self.current_index = idx
            self.update_display()
        else:
            messagebox.showinfo("Completed", "All rows in this dataset have been classified!")

    def jump_to_row(self):
        val = self.jump_var.get().strip()
        if val.isdigit():
            idx = int(val) - 1
            if 0 <= idx < len(self.rows):
                self.current_index = idx
                self.jump_var.set("")
                self.update_display()
            else:
                messagebox.showwarning("Out of Range", f"Please enter a row between 1 and {len(self.rows):,}")

    def _find_first_unlabeled(self, start=0):
        for i in range(start, len(self.rows)):
            if i not in self.labels:
                return i
        return None

    def _on_canvas_configure(self, event):
        """Re-renders text to wrap cleanly when the window is resized."""
        if self.current_text and abs(event.width - self._last_rendered_width) > 30:
            self._render_text_to_canvas(self.current_text, width=event.width)

    def _render_text_to_canvas(self, text_str: str, width: Optional[int] = None):
        """
        Renders text using Pango/HarfBuzz with flawless Bengali conjunct shaping.
        Falls back to standard ScrolledText if Pango libraries are unavailable.
        """
        self.current_text = text_str

        if not self.pango_renderer.available:
            # Fallback to Text widget
            self.text_canvas.pack_forget()
            self.text_scrollbar.pack_forget()
            self.fallback_text.pack(fill=tk.BOTH, expand=True)
            self.fallback_text.config(state=tk.NORMAL)
            self.fallback_text.delete("1.0", tk.END)
            self.fallback_text.insert("1.0", text_str)
            self.fallback_text.config(state=tk.DISABLED)
            return

        # Ensure canvas is visible
        self.fallback_text.pack_forget()
        self.text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas_w = width or self.text_canvas.winfo_width()
        if canvas_w < 100:
            canvas_w = 680

        res = self.pango_renderer.render(text_str, font_size=self.font_size, width=canvas_w)
        if res:
            surf_w, surf_h, png_path = res
            self._last_rendered_width = canvas_w

            # Load into PhotoImage and display on canvas
            self.current_rendered_img = tk.PhotoImage(file=png_path)
            self.text_canvas.delete("all")
            self.text_canvas.create_image(0, 0, anchor="nw", image=self.current_rendered_img)
            self.text_canvas.config(scrollregion=(0, 0, surf_w, surf_h))
            self.text_canvas.yview_moveto(0.0)

    def update_display(self):
        total = len(self.rows)
        if total == 0:
            return

        idx = self.current_index
        row_data = self.rows[idx]

        # Record counter
        self.row_indicator_lbl.config(text=f"Row: {idx + 1:,} of {total:,}")

        # Current status badge
        current_lbl = self.labels.get(idx)
        if current_lbl == "positive":
            self.label_badge_lbl.config(text="● LABEL: POSITIVE", foreground="#10B981")
        elif current_lbl == "neutral":
            self.label_badge_lbl.config(text="● LABEL: NEUTRAL", foreground="#3B82F6")
        elif current_lbl == "negative":
            self.label_badge_lbl.config(text="● LABEL: NEGATIVE", foreground="#EF4444")
        elif current_lbl == "discard":
            self.label_badge_lbl.config(text="● LABEL: DISCARD", foreground="#F59E0B")
        else:
            self.label_badge_lbl.config(text="○ PENDING", foreground="#64748B")

        # Text display via Pango HarfBuzz
        col = self.text_column or (self.csv_headers[0] if self.csv_headers else None)
        text_str = str(row_data.get(col, "")) if col else ""
        self._render_text_to_canvas(text_str)

        # Progress bar
        pct = (len(self.labels) / total) * 100 if total > 0 else 0
        self.progress_bar["value"] = pct

    # ---------------- SAVE & EXPORT ----------------

    def save_all(self, manual=False):
        if not self.csv_path or not self.rows:
            return

        fieldnames = list(self.csv_headers)
        if "sentiment" not in fieldnames:
            fieldnames.append("sentiment")
        if "status" not in fieldnames:
            fieldnames.append("status")

        for idx, row in enumerate(self.rows):
            if idx in self.labels:
                row["sentiment"] = self.labels[idx]
                row["status"] = "LABELED"
            else:
                row["sentiment"] = ""
                row["status"] = "PENDING"

        # Update original CSV safely
        tmp_og = self.csv_path.with_suffix(".tmp")
        try:
            with open(tmp_og, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.rows)
            tmp_og.replace(self.csv_path)
            self.csv_headers = fieldnames
        except Exception as e:
            if manual:
                messagebox.showerror("Save Error", f"Could not update original CSV:\n{e}")
            return

        # Write the 4 split CSVs
        stem = self.csv_path.stem
        parent = self.csv_path.parent
        split_map = {
            "positive": parent / f"{stem}_positive.csv",
            "negative": parent / f"{stem}_negative.csv",
            "neutral": parent / f"{stem}_neutral.csv",
            "discard": parent / f"{stem}_discard.csv",
        }
        buckets = {k: [] for k in split_map}

        for idx, row in enumerate(self.rows):
            lbl = self.labels.get(idx)
            if lbl in buckets:
                buckets[lbl].append(row)

        for sentiment_name, target_p in split_map.items():
            try:
                with open(target_p, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(buckets[sentiment_name])
            except Exception:
                pass

        # Progress JSON
        pf = self._get_progress_file()
        try:
            with open(pf, "w", encoding="utf-8") as f:
                json.dump({
                    "csv_path": str(self.csv_path),
                    "total_rows": len(self.rows),
                    "labels": self.labels,
                    "last_saved": time.strftime("%H:%M:%S")
                }, f)
        except Exception:
            pass

        t_str = time.strftime("%H:%M:%S")
        self.status_lbl.config(text=f"Status: Auto-saved at {t_str} (Original CSV + 4 split files updated)")

        if manual:
            messagebox.showinfo(
                "Save Successful",
                f"Progress saved successfully to:\n• {self.csv_path.name}\n• 4 split CSV files"
            )

    # ---------------- RESET ----------------

    def prompt_reset(self):
        if not self.rows:
            return

        ans = messagebox.askyesnocancel(
            "Reset Options",
            "Choose Reset Action:\n\n"
            "• [Yes]: Clear CURRENT ROW label\n"
            "• [No]: Reset ENTIRE FILE (all labels cleared)\n"
            "• [Cancel]: Abort"
        )
        if ans is True:
            if self.current_index in self.labels:
                del self.labels[self.current_index]
                self.save_all(manual=False)
                self.update_display()
                self.status_lbl.config(text=f"Status: Cleared label for Row {self.current_index + 1}")

        elif ans is False:
            confirm = messagebox.askyesno(
                "Confirm Reset All",
                "⚠️ Are you sure you want to clear ALL labels in this dataset?"
            )
            if confirm:
                self.labels.clear()
                self.save_all(manual=False)
                self.update_display()
                self.status_lbl.config(text="Status: All labels reset")

    # ---------------- FOLDER / CSV OPEN HELPERS ----------------

    def _open_output_folder(self):
        if self.csv_path and self.csv_path.exists():
            folder = str(self.csv_path.parent)
        else:
            folder = os.getcwd()
        open_file_or_folder(folder)

    def _open_output_csv(self):
        if self.csv_path and self.csv_path.exists():
            open_file_or_folder(str(self.csv_path))
        else:
            messagebox.showinfo("No File", "No CSV file is currently loaded.")

    # ---------------- ZOOM & CLOSE ----------------

    def zoom_in(self):
        if self.font_size < 32:
            self.font_size += 2
            if self.current_text:
                self._render_text_to_canvas(self.current_text)

    def zoom_out(self):
        if self.font_size > 10:
            self.font_size -= 2
            if self.current_text:
                self._render_text_to_canvas(self.current_text)

    def on_close(self):
        if self.rows and self.csv_path:
            self.save_all(manual=False)
        self.root.destroy()


def main():
    root = tk.Tk()
    app = SentimentClassifierGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
