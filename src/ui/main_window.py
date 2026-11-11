"""Main application window — fintech-exchange style UI design."""

import queue
import threading
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from typing import Dict, List, Optional

from src.models.conversion_request import ConversionRequest
from src.services.rate_service import RateResult, RateService
from src.services.validation_service import ValidationService

# ── Colour palette ────────────────────────────────────────────────────────────
_BG        = "#FFFFFF"   # window / outer background
_PANEL_BG  = "#F1EFE8"   # rounded panel fill
_ACCENT    = "#0F6E56"   # primary green
_ACCENT_H  = "#085041"   # darker green (hover)
_ACCENT_D  = "#9FE1CB"   # disabled green
_TXT_DARK  = "#2C2C2A"   # header text
_TXT_MUTED = "#5F5E5A"   # muted / secondary
_TXT_GREEN = "#0F6E56"   # result amount
_ERR_FG    = "#DC2626"   # inline error
_PILL_BG   = "#E1F5EE"   # pill background
_PILL_FG   = "#085041"   # pill text
_NTC_BG    = "#FAEEDA"   # amber notice bg
_NTC_FG    = "#633806"   # amber notice text
_ERR_BG    = "#FEE2E2"   # red notice bg
_ERR_NF    = "#DC2626"   # red notice text

# ── Russian currency names (shown in dropdown list) ───────────────────────────
_RU_NAMES: Dict[str, str] = {
    "USD": "Доллар США",
    "EUR": "Евро",
    "MDL": "Молдавский лей",
    "RON": "Румынский лей",
    "GBP": "Фунт стерлингов",
    "UAH": "Украинская гривна",
    "RUB": "Российский рубль",
    "CHF": "Швейцарский франк",
    "JPY": "Японская иена",
    "CNY": "Китайский юань",
    "PLN": "Польский злотый",
    "CZK": "Чешская крона",
    "HUF": "Венгерский форинт",
    "SEK": "Шведская крона",
    "NOK": "Норвежская крона",
    "DKK": "Датская крона",
    "TRY": "Турецкая лира",
    "CAD": "Канадский доллар",
    "AUD": "Австралийский доллар",
    "NZD": "Новозеландский доллар",
    "BGN": "Болгарский лев",
    "XDR": "СДР (МВФ)",
}

# ── Layout constants ──────────────────────────────────────────────────────────
_PANEL_H  = 112   # height of each rounded panel
_PANEL_G  = 6     # visual gap between the two panels (swap overlaps it)
_SWAP_R   = 20    # radius of swap circle
_CANVAS_H = _PANEL_H * 2 + _PANEL_G   # total height of combined-panels canvas
_MARGIN   = 18    # horizontal margin inside panels

# ── Fonts ─────────────────────────────────────────────────────────────────────
_F_TITLE  = ("Segoe UI", 18, "bold")
_F_LABEL  = ("Segoe UI", 9)
_F_AMOUNT = ("Segoe UI", 22)
_F_RESULT = ("Segoe UI", 20, "bold")
_F_MUTED  = ("Segoe UI", 9)
_F_BTN    = ("Segoe UI", 11, "bold")
_F_COMBO  = ("Segoe UI", 10)
_F_ERR    = ("Segoe UI", 9)
_F_NTC    = ("Segoe UI", 9)
_F_PILL   = ("Segoe UI", 9, "bold")
_F_SWAP   = ("Segoe UI", 14, "bold")


# ── Drawing helper ────────────────────────────────────────────────────────────

def _draw_rounded_rect(
    canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float,
    r: float = 14, **kw
):
    """Draw a solid filled rounded rectangle on *canvas* using arcs + rectangles."""
    if "outline" not in kw and "fill" in kw:
        kw = dict(kw, outline=kw["fill"])
    canvas.create_arc(x1,       y1,       x1+2*r, y1+2*r, start=90,  extent=90,  style="pieslice", **kw)
    canvas.create_arc(x2-2*r,   y1,       x2,     y1+2*r, start=0,   extent=90,  style="pieslice", **kw)
    canvas.create_arc(x1,       y2-2*r,   x1+2*r, y2,     start=180, extent=90,  style="pieslice", **kw)
    canvas.create_arc(x2-2*r,   y2-2*r,   x2,     y2,     start=270, extent=90,  style="pieslice", **kw)
    canvas.create_rectangle(x1+r, y1,     x2-r, y2,   **kw)
    canvas.create_rectangle(x1,   y1+r,   x2,   y2-r, **kw)


# ── Canvas-drawn rounded button ───────────────────────────────────────────────

class _CanvasButton:
    """Rounded button drawn on a tk.Canvas; exposes convert_button["state"] / .config() for tests."""

    def __init__(
        self, parent: tk.Widget, text: str, command,
        font=_F_BTN, height: int = 50, radius: int = 10,
    ):
        self._state: str = tk.NORMAL
        self._command = command
        self._text = text
        self._font = font
        self._radius = radius
        self._height = height
        self._hovering = False

        self.canvas = tk.Canvas(
            parent, height=height, bg=_BG,
            bd=0, highlightthickness=0, cursor="hand2",
        )
        self.canvas.bind("<Configure>", self._redraw)
        self.canvas.bind("<Button-1>",  self._on_click)
        self.canvas.bind("<Enter>",     self._on_enter)
        self.canvas.bind("<Leave>",     self._on_leave)

    # ── Widget delegation (used by layout and tests) ──

    def pack(self, **kw):
        self.canvas.pack(**kw)

    def __getitem__(self, key: str) -> str:
        if key == "state":
            return self._state
        raise KeyError(key)

    def config(self, **kw):
        if "state" in kw:
            self._state = str(kw["state"])
        self._redraw()

    configure = config

    def invoke(self):
        if self._state != tk.DISABLED:
            self._command()

    # ── Drawing ──

    def _fill(self) -> str:
        if self._state == tk.DISABLED:
            return _ACCENT_D
        return _ACCENT_H if self._hovering else _ACCENT

    def _redraw(self, _e=None):
        c = self.canvas
        c.delete("all")
        w = c.winfo_width() or 400
        h = self._height
        bg = self._fill()
        _draw_rounded_rect(c, 1, 1, w - 1, h - 1, r=self._radius, fill=bg)
        c.create_text(w // 2, h // 2, text=self._text, font=self._font, fill="#FFFFFF")

    def _on_click(self, _e=None):
        if self._state != tk.DISABLED:
            self._command()

    def _on_enter(self, _e=None):
        self._hovering = True
        self._redraw()

    def _on_leave(self, _e=None):
        self._hovering = False
        self._redraw()


# ── Swap-button wrapper ───────────────────────────────────────────────────────

class _SwapButton:
    """Thin wrapper around the canvas swap circle; exposes invoke() so tests can call swap_button.invoke()."""

    def __init__(self, command):
        self._command = command

    def invoke(self):
        self._command()


# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(tk.Tk):
    """Currency converter — fintech-exchange style layout."""

    def __init__(
        self,
        rate_service: Optional[RateService] = None,
        validation_service: Optional[ValidationService] = None,
        async_load: bool = True,
    ):
        super().__init__()
        self.title("Обмен валют")
        self.configure(bg=_BG)
        self.resizable(False, False)

        self.rate_service = rate_service or RateService()
        self.validation_service = validation_service or ValidationService()

        self.rate_result: Optional[RateResult] = None
        self.currencies: List[str] = ["USD", "EUR", "MDL", "RON", "GBP", "UAH"]
        self.currency_display_map: Dict[str, str] = {}
        self.display_to_code: Dict[str, str] = {}

        self._setup_ttk_style()
        self._create_widgets()
        self._center_window(440, 560)

        self.bind("<Return>", lambda _e: self._on_enter_pressed())
        self._load_initial_rates(async_load=async_load)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _setup_ttk_style(self):
        """Configure ttk style for compact chip-style comboboxes."""
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure(
            "Chip.TCombobox",
            fieldbackground="#FFFFFF",
            background="#FFFFFF",
            selectbackground="#FFFFFF",
            selectforeground=_TXT_DARK,
            borderwidth=1,
            arrowcolor=_TXT_MUTED,
            padding=(4, 2),
        )
        s.map(
            "Chip.TCombobox",
            fieldbackground=[("readonly", "#FFFFFF")],
            selectbackground=[("readonly", "#FFFFFF")],
            selectforeground=[("readonly", _TXT_DARK)],
        )

    def _center_window(self, w: int, h: int):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{max(0,(sw-w)//2)}+{max(0,(sh-h)//2)}")

    def _get_code(self, val: str) -> str:
        """Extract currency code from display string ('USD — Доллар США' → 'USD')."""
        if not val:
            return ""
        if val in self.display_to_code:
            return self.display_to_code[val]
        if " — " in val:
            return val.split(" — ")[0].strip()
        if " - " in val:
            return val.split(" - ")[0].strip()
        return val.strip()

    # ── Widget construction ────────────────────────────────────────────────────

    def _create_widgets(self):
        self._outer = tk.Frame(self, bg=_BG)
        self._outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=18)

        self._build_header(self._outer)
        self._build_panels(self._outer)

        # Inline validation error (below combined panels canvas)
        self.amount_error_var = tk.StringVar(value="")
        self.amount_error_label = tk.Label(
            self._outer, textvariable=self.amount_error_var,
            font=_F_ERR, bg=_BG, fg=_ERR_FG, anchor="w",
        )
        self.amount_error_label.pack(fill=tk.X, pady=(3, 0))

        # Pair-rate muted line  (pair_rate_var stays pure for tests; label gets full text)
        self.pair_rate_var = tk.StringVar(value="")
        self._pair_lbl = tk.Label(
            self._outer, text="",
            font=_F_MUTED, bg=_BG, fg=_TXT_MUTED,
            anchor="center", justify="center",
        )
        self._pair_lbl.pack(fill=tk.X, pady=(6, 8))

        # rate_meta_var kept for compatibility
        self.rate_meta_var = tk.StringVar(value="")

        # Rounded convert button (canvas-drawn)
        self.convert_button = _CanvasButton(
            self._outer, text="Конвертировать",
            command=self.on_convert, font=_F_BTN, height=50, radius=10,
        )
        self.convert_button.pack(fill=tk.X, pady=(0, 10))

        # Notice / error box (packed on demand)
        self._ntc_frame = tk.Frame(self._outer, bg=_BG)
        self._ntc_frame.pack(fill=tk.X)
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            self._ntc_frame, textvariable=self.status_var,
            font=_F_NTC, bg=_NTC_BG, fg=_NTC_FG,
            padx=10, pady=6, anchor="w", wraplength=360, justify="left",
        )

        # Compatibility var (date + notice concatenated; read by tests via info_var.get())
        self.info_var = tk.StringVar(value="")

        self._update_convert_button_state()

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self, parent: tk.Frame):
        hdr = tk.Frame(parent, bg=_BG)
        hdr.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            hdr, text="Обмен валют",
            font=_F_TITLE, bg=_BG, fg=_TXT_DARK,
        ).pack(side=tk.LEFT, anchor="w")

        # Fully-rounded pill label drawn on a small canvas
        self._pill_canvas = tk.Canvas(hdr, height=26, bg=_BG, bd=0, highlightthickness=0)
        self._pill_canvas.pack(side=tk.RIGHT, anchor="e")
        self._update_pill("Загрузка…")

    def _update_pill(self, text: str):
        """Redraw the rounded date pill with the given text."""
        c = self._pill_canvas
        c.delete("all")
        try:
            f = tkfont.Font(family="Segoe UI", size=9, weight="bold")
            tw = f.measure(text)
        except Exception:
            tw = max(len(text) * 7, 60)
        px, h = 12, 24
        w = tw + px * 2 + 4
        c.config(width=w)
        _draw_rounded_rect(c, 0, 1, w - 1, h - 1, r=12, fill=_PILL_BG)
        c.create_text(w // 2, h // 2 + 1, text=text, font=_F_PILL, fill=_PILL_FG)

    # ── Combined panels + circular swap button ────────────────────────────────

    def _build_panels(self, parent: tk.Frame):
        """
        One tk.Canvas that draws:
          • top panel rounded rect  (y = 0 … _PANEL_H)
          • bottom panel rounded rect (y = _PANEL_H+_PANEL_G … _CANVAS_H)
          • green circle swap button  (centred at the junction, overlapping both panels)

        Widgets are embedded with create_window and repositioned on <Configure>.
        """
        canvas = tk.Canvas(
            parent, height=_CANVAS_H, bg=_BG,
            bd=0, highlightthickness=0,
        )
        canvas.pack(fill=tk.X)
        self._panels_canvas = canvas

        # ── Widgets that live inside the canvas ──────────────────────────────

        # "Отдаю" label
        _give_lbl = tk.Label(canvas, text="Отдаю",
                             font=_F_LABEL, bg=_PANEL_BG, fg=_TXT_MUTED)

        # Amount entry — large, borderless, panel bg
        self.amount_var = tk.StringVar()
        self.amount_entry = tk.Entry(
            canvas, textvariable=self.amount_var,
            font=_F_AMOUNT, bg=_PANEL_BG, fg=_TXT_DARK,
            bd=0, highlightthickness=0, insertbackground=_TXT_DARK, width=10,
        )
        self.amount_var.trace_add("write", self._on_input_changed)

        # Source combobox — compact chip, shows just the code when closed
        self.src_currency_var = tk.StringVar(value="USD")
        self.src_currency_combo = ttk.Combobox(
            canvas, textvariable=self.src_currency_var,
            values=self.currencies, state="readonly",
            width=8, font=_F_COMBO, style="Chip.TCombobox",
        )
        self.src_currency_var.trace_add("write", self._on_input_changed)
        self.src_currency_combo.bind(
            "<<ComboboxSelected>>",
            lambda _e: self._on_combo_selected(self.src_currency_var),
        )

        # "Получаю" label
        _get_lbl = tk.Label(canvas, text="Получаю",
                            font=_F_LABEL, bg=_PANEL_BG, fg=_TXT_MUTED)

        # Result label — big, green
        self.result_var = tk.StringVar(value="—")
        _result_lbl = tk.Label(
            canvas, textvariable=self.result_var,
            font=_F_RESULT, bg=_PANEL_BG, fg=_TXT_GREEN,
            anchor="w", width=14,
        )

        # Target combobox
        self.tgt_currency_var = tk.StringVar(value="MDL")
        self.tgt_currency_combo = ttk.Combobox(
            canvas, textvariable=self.tgt_currency_var,
            values=self.currencies, state="readonly",
            width=8, font=_F_COMBO, style="Chip.TCombobox",
        )
        self.tgt_currency_var.trace_add("write", self._on_input_changed)
        self.tgt_currency_combo.bind(
            "<<ComboboxSelected>>",
            lambda _e: self._on_combo_selected(self.tgt_currency_var),
        )

        # ── Create canvas window items (repositioned in _redraw_panels) ──────
        BOT = _PANEL_H + _PANEL_G   # y-start of bottom panel

        self._wid_give_lbl  = canvas.create_window(_MARGIN, 10,       anchor="nw", window=_give_lbl)
        self._wid_amount    = canvas.create_window(_MARGIN, 38,       anchor="nw", window=self.amount_entry)
        self._wid_src_combo = canvas.create_window(390, _PANEL_H // 2, anchor="e",  window=self.src_currency_combo)
        self._wid_get_lbl   = canvas.create_window(_MARGIN, BOT + 10, anchor="nw", window=_get_lbl)
        self._wid_result    = canvas.create_window(_MARGIN, BOT + 38, anchor="nw", window=_result_lbl)
        self._wid_tgt_combo = canvas.create_window(390, BOT + _PANEL_H // 2, anchor="e", window=self.tgt_currency_combo)

        # Swap button: wrapper for tests; visuals are canvas items drawn in _redraw_panels
        self.swap_button = _SwapButton(self._on_swap_currencies)

        canvas.bind("<Configure>", self._redraw_panels)
        self.after(20, self._redraw_panels)

    def _redraw_panels(self, _event=None):
        """Redraw panel backgrounds + swap circle; reposition embedded windows."""
        c = self._panels_canvas
        w = c.winfo_width()
        if w < 20:
            return

        ph  = _PANEL_H
        gap = _PANEL_G
        bot = ph + gap          # y-start of bottom panel
        cx  = w // 2            # horizontal centre
        sy  = ph + gap // 2     # swap-circle centre y

        # ── Backgrounds (delete + redraw) ────────────────────────────────────
        c.delete("panel_bg")

        # Top panel
        _draw_rounded_rect(c, 2, 2, w - 2, ph - 2, r=14,
                           fill=_PANEL_BG, tags="panel_bg")
        # Bottom panel
        _draw_rounded_rect(c, 2, bot + 2, w - 2, _CANVAS_H - 2, r=14,
                           fill=_PANEL_BG, tags="panel_bg")

        # Swap: white ring (3 px) → green circle → icon
        c.create_oval(
            cx - _SWAP_R - 3, sy - _SWAP_R - 3,
            cx + _SWAP_R + 3, sy + _SWAP_R + 3,
            fill=_BG, outline=_BG, tags=("panel_bg", "swap_ring"),
        )
        c.create_oval(
            cx - _SWAP_R, sy - _SWAP_R,
            cx + _SWAP_R, sy + _SWAP_R,
            fill=_ACCENT, outline=_ACCENT,
            tags=("panel_bg", "swap_circle"),
        )
        c.create_text(
            cx, sy, text="⇅", font=_F_SWAP, fill="#FFFFFF",
            tags=("panel_bg", "swap_text"),
        )

        # Interaction on swap circle + text
        for tag in ("swap_circle", "swap_text", "swap_ring"):
            c.tag_bind(tag, "<Button-1>", lambda _e: self._on_swap_currencies())
            c.tag_bind(tag, "<Enter>",    lambda _e: c.config(cursor="hand2"))
            c.tag_bind(tag, "<Leave>",    lambda _e: c.config(cursor=""))

        # Push panel_bg below the embedded windows
        c.tag_lower("panel_bg")

        # ── Reposition embedded window items ──────────────────────────────────
        right = w - 10
        c.coords(self._wid_give_lbl,  _MARGIN, 10)
        c.coords(self._wid_amount,    _MARGIN, 40)
        c.coords(self._wid_src_combo, right,   ph // 2)
        c.coords(self._wid_get_lbl,   _MARGIN, bot + 10)
        c.coords(self._wid_result,    _MARGIN, bot + 40)
        c.coords(self._wid_tgt_combo, right,   bot + ph // 2)

    # ── Status helpers ─────────────────────────────────────────────────────────

    def _set_status(self, message: str, is_error: bool = False):
        self.status_var.set(message)
        self.status_label.configure(
            bg=_ERR_BG if is_error else _NTC_BG,
            fg=_ERR_NF if is_error else _NTC_FG,
        )
        self.status_label.pack(fill=tk.X)

    def _clear_status(self):
        self.status_var.set("")
        self.status_label.pack_forget()

    # ── Button state helpers ───────────────────────────────────────────────────

    def _set_button_enabled(self):
        self.convert_button.config(state=tk.NORMAL)

    def _set_button_disabled(self):
        self.convert_button.config(state=tk.DISABLED)

    # ── Event handlers ─────────────────────────────────────────────────────────

    def _on_combo_selected(self, var: tk.StringVar):
        """After dropdown selection trim the value to just the currency code."""
        code = self._get_code(var.get())
        if code:
            var.set(code)

    def _on_swap_currencies(self):
        src = self.src_currency_var.get()
        tgt = self.tgt_currency_var.get()
        self.src_currency_var.set(tgt)
        self.tgt_currency_var.set(src)
        self._on_input_changed()

    def _on_enter_pressed(self):
        if str(self.convert_button["state"]) == "normal":
            self.on_convert()

    def _on_input_changed(self, *args):
        # manual fix: drop a stale result as soon as amount or currencies change,
        # so an old value is never shown next to new (possibly invalid) input
        self._clear_result()
        self._update_convert_button_state()

    def _clear_result(self):
        self.result_var.set("—")
        self.pair_rate_var.set("")
        self._pair_lbl.config(text="")

    def _update_convert_button_state(self):
        """Enable / disable convert button; update inline validation label."""
        raw = self.amount_var.get()
        src = self._get_code(self.src_currency_var.get())
        tgt = self._get_code(self.tgt_currency_var.get())

        if not raw.strip():
            self.amount_error_var.set("")
            self._set_button_disabled()
            return

        ok, msg = self.validation_service.validate_amount(raw)
        if not ok:
            self.amount_error_var.set(msg)
            self._set_button_disabled()
            return

        self.amount_error_var.set("")
        ok_req, _ = self.validation_service.validate_request(raw, src, tgt)
        if ok_req and self.rate_result is not None:
            self._set_button_enabled()
        else:
            self._set_button_disabled()

    # ── Rate loading ───────────────────────────────────────────────────────────

    def _load_initial_rates(self, async_load: bool = True):
        self._set_status("Загрузка курсов…")
        self._set_button_disabled()

        if not async_load:
            try:
                res = self.rate_service.get_rates_with_fallback()
                self._on_rates_loaded(res, None)
            except Exception as exc:
                self._on_rates_loaded(None, exc)
            return

        self._rates_queue: queue.Queue = queue.Queue()

        def _worker():
            try:
                self._rates_queue.put((self.rate_service.get_rates_with_fallback(), None))
            except Exception as exc:
                self._rates_queue.put((None, exc))

        def _poll():
            try:
                res, err = self._rates_queue.get_nowait()
                self._on_rates_loaded(res, err)
            except queue.Empty:
                self.after(30, _poll)

        self.after(30, _poll)
        self._load_thread = threading.Thread(target=_worker, daemon=True)
        self._load_thread.start()

    def _on_rates_loaded(self, result: Optional[RateResult], error: Optional[Exception]):
        """Main-thread callback — called after background rate fetch."""
        if error is not None:
            self.rate_result = None
            # manual fix: user-friendly text instead of the raw exception
            msg = (
                "Ошибка: не удалось получить курсы валют. "
                "Нет подключения к интернету, а сохранённых курсов пока нет. "
                "Подключитесь к сети и перезапустите приложение."
            )
            self._update_pill("Нет данных")
            self._set_status(msg, is_error=True)
            self.info_var.set(msg)
            self._update_convert_button_state()
            return

        if not result:
            self.rate_result = None
            msg = "Ошибка: нет доступных курсов валют."
            self._update_pill("Нет данных")
            self._set_status(msg, is_error=True)
            self.info_var.set(msg)
            self._update_convert_button_state()
            return

        self.rate_result = result
        loaded_codes = sorted(result.rates.keys())
        self.currencies = loaded_codes

        # Build display strings with Russian names
        self.currency_display_map = {}
        self.display_to_code = {}
        display_values: List[str] = []
        for code in loaded_codes:
            rate = result.rates[code]
            en_name = getattr(rate, "currency_name", "") or ""
            name = _RU_NAMES.get(code, en_name) or en_name
            display_str = f"{code} — {name}" if name else code
            self.currency_display_map[code] = display_str
            self.display_to_code[display_str] = code
            self.display_to_code[code] = code
            display_values.append(display_str)

        self.src_currency_combo["values"] = display_values
        self.tgt_currency_combo["values"] = display_values

        # Keep combobox entry showing just the code (chip style)
        curr_src = self._get_code(self.src_currency_var.get()) or "USD"
        curr_tgt = self._get_code(self.tgt_currency_var.get()) or "MDL"
        self.src_currency_var.set(curr_src)
        self.tgt_currency_var.set(curr_tgt)

        # Update pill
        self._update_pill(f"Курс НБМ · {result.effective_date}")

        meta = f"Курс на {result.effective_date} · Источник: {result.source_name}"
        self.rate_meta_var.set(meta)

        if result.notice:
            self._set_status(result.notice)
            self.info_var.set(f"{result.notice}\n{meta}")
        else:
            self._clear_status()
            self.info_var.set(meta)

        self._update_convert_button_state()

    # ── Conversion ─────────────────────────────────────────────────────────────

    def on_convert(self):
        """Execute currency conversion and update result / pair-rate display."""
        amount_str = self.amount_var.get()
        src = self._get_code(self.src_currency_var.get())
        tgt = self._get_code(self.tgt_currency_var.get())

        ok, err = self.validation_service.validate_request(amount_str, src, tgt)
        if not ok:
            self.amount_error_var.set(err)
            self._set_status(err, is_error=True)
            return

        try:
            amount = float(amount_str)
        except ValueError:
            msg = "Введите корректное число."
            self.amount_error_var.set(msg)
            self._set_status(msg, is_error=True)
            return

        if not self.rate_result:
            msg = "Ошибка: нет доступных курсов валют."
            self._set_status(msg, is_error=True)
            self.info_var.set(msg)
            return

        try:
            req = ConversionRequest(amount=amount, source_currency=src, target_currency=tgt)
            res = self.rate_service.process_conversion_request(req, self.rate_result.rates)

            # result_var: "90.00 EUR" — format tests rely on this exact shape
            self.result_var.set(f"{res.result_display} {tgt}")

            # pair_rate_var: pure pair rate string — tests assert on this directly
            self.pair_rate_var.set(res.pair_rate_display)

            # Muted info line under the panels (enriched with date + source)
            eff = self.rate_result.effective_date
            src_name = self.rate_result.source_name
            self._pair_lbl.config(
                text=f"{res.pair_rate_display} · {eff} · {src_name}"
            )

            meta = f"Курс на {eff} · Источник: {src_name}"
            self.rate_meta_var.set(meta)

            if self.rate_result.notice:
                self._set_status(self.rate_result.notice)
                self.info_var.set(f"{self.rate_result.notice}\n{meta}")
            else:
                self._clear_status()
                self.info_var.set(meta)

        except Exception as exc:
            msg = f"Ошибка конвертации: {exc}"
            self._set_status(msg, is_error=True)
            self.info_var.set(msg)
