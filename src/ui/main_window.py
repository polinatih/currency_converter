"""Main application window using Tkinter."""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from src.services.rate_service import RateResult, RateService
from src.services.validation_service import ValidationService


class MainWindow(tk.Tk):
    """Main window for Currency Converter application."""

    def __init__(
        self,
        rate_service: Optional[RateService] = None,
        validation_service: Optional[ValidationService] = None,
    ):
        super().__init__()
        self.title("Currency Converter")
        self.geometry("450x420")
        self.minsize(400, 380)

        self.rate_service = rate_service or RateService()
        self.validation_service = validation_service or ValidationService()

        self.rate_result: Optional[RateResult] = None
        self.currencies = ["USD", "EUR", "MDL", "RON", "GBP", "UAH"]

        self._create_widgets()
        self._load_initial_rates()

    def _create_widgets(self):
        """Create and lay out GUI widgets."""
        main_frame = ttk.Frame(self, padding="15 15 15 15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Currency Converter",
            font=("Segoe UI", 16, "bold"),
        )
        title_label.pack(pady=(0, 15))

        # Amount Input
        amount_frame = ttk.Frame(main_frame)
        amount_frame.pack(fill=tk.X, pady=5)
        ttk.Label(amount_frame, text="Amount:", width=15, anchor="w").pack(side=tk.LEFT)
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(amount_frame, textvariable=self.amount_var)
        self.amount_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.amount_var.trace_add("write", self._on_input_changed)

        # Source Currency
        src_frame = ttk.Frame(main_frame)
        src_frame.pack(fill=tk.X, pady=5)
        ttk.Label(src_frame, text="From Currency:", width=15, anchor="w").pack(side=tk.LEFT)
        self.src_currency_var = tk.StringVar(value="USD")
        self.src_currency_combo = ttk.Combobox(
            src_frame,
            textvariable=self.src_currency_var,
            values=self.currencies,
            state="readonly",
        )
        self.src_currency_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.src_currency_var.trace_add("write", self._on_input_changed)

        # Target Currency
        tgt_frame = ttk.Frame(main_frame)
        tgt_frame.pack(fill=tk.X, pady=5)
        ttk.Label(tgt_frame, text="To Currency:", width=15, anchor="w").pack(side=tk.LEFT)
        self.tgt_currency_var = tk.StringVar(value="MDL")
        self.tgt_currency_combo = ttk.Combobox(
            tgt_frame,
            textvariable=self.tgt_currency_var,
            values=self.currencies,
            state="readonly",
        )
        self.tgt_currency_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.tgt_currency_var.trace_add("write", self._on_input_changed)

        # Convert Button
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=15)
        self.convert_button = ttk.Button(
            btn_frame,
            text="Convert",
            command=self.on_convert,
            state=tk.DISABLED,
        )
        self.convert_button.pack(fill=tk.X)

        # Result Display
        result_group = ttk.LabelFrame(main_frame, text="Conversion Result", padding="10")
        result_group.pack(fill=tk.BOTH, expand=True, pady=5)

        self.result_var = tk.StringVar(value="—")
        self.result_label = ttk.Label(
            result_group,
            textvariable=self.result_var,
            font=("Segoe UI", 14, "bold"),
            anchor="center",
        )
        self.result_label.pack(fill=tk.X, pady=2)

        self.pair_rate_var = tk.StringVar(value="")
        self.pair_rate_label = ttk.Label(
            result_group,
            textvariable=self.pair_rate_var,
            font=("Segoe UI", 10),
            anchor="center",
        )
        self.pair_rate_label.pack(fill=tk.X, pady=2)

        # Notice / Error / Metadata info
        self.info_var = tk.StringVar(value="")
        self.info_label = ttk.Label(
            result_group,
            textvariable=self.info_var,
            font=("Segoe UI", 9, "italic"),
            wraplength=380,
            justify="center",
        )
        self.info_label.pack(fill=tk.X, pady=(5, 0))

        # Initial validation state check
        self._update_convert_button_state()

    def _on_input_changed(self, *args):
        """Callback when amount or currencies change."""
        self._update_convert_button_state()

    def _update_convert_button_state(self):
        """Enable or disable conversion button based on input validity [FR-003]."""
        amount = self.amount_var.get()
        src = self.src_currency_var.get()
        tgt = self.tgt_currency_var.get()

        is_valid, _ = self.validation_service.validate_request(amount, src, tgt)
        if is_valid:
            self.convert_button.config(state=tk.NORMAL)
        else:
            self.convert_button.config(state=tk.DISABLED)

    def _load_initial_rates(self):
        """Attempt to load rates on startup."""
        try:
            self.rate_result = self.rate_service.get_rates_with_fallback()
            if self.rate_result:
                # Update currency dropdown options
                loaded_currencies = sorted(list(self.rate_result.rates.keys()))
                self.currencies = loaded_currencies
                self.src_currency_combo["values"] = self.currencies
                self.tgt_currency_combo["values"] = self.currencies

                metadata = f"Rate Date: {self.rate_result.effective_date} | Source: {self.rate_result.source_name}"
                if self.rate_result.notice:
                    metadata = f"{self.rate_result.notice}\n{metadata}"
                self.info_var.set(metadata)
        except Exception as e:
            self.info_var.set(f"Could not load rates: {e}")

    def on_convert(self):
        """Execute conversion when user clicks Convert."""
        amount_str = self.amount_var.get()
        src = self.src_currency_var.get()
        tgt = self.tgt_currency_var.get()

        is_valid, err_msg = self.validation_service.validate_request(amount_str, src, tgt)
        if not is_valid:
            messagebox.showerror("Validation Error", err_msg)
            return

        try:
            amount = float(amount_str)
        except ValueError:
            messagebox.showerror("Validation Error", "Amount must be a valid number.")
            return

        # Fetch / ensure rates
        if not self.rate_result:
            try:
                self.rate_result = self.rate_service.get_rates_with_fallback()
            except Exception as e:
                messagebox.showerror("Rate Error", f"Unable to retrieve exchange rates: {e}")
                return

        if not self.rate_result:
            messagebox.showerror("Rate Error", "No exchange rates available.")
            return

        try:
            converted = self.rate_service.convert(amount, src, tgt, self.rate_result.rates)
            result_str = self.rate_service.format_result(converted)
            self.result_var.set(f"{result_str} {tgt}")

            pair_display = self.rate_service.get_pair_rate_display(src, tgt, self.rate_result.rates)
            self.pair_rate_var.set(pair_display)

            metadata = f"Rate Date: {self.rate_result.effective_date} | Source: {self.rate_result.source_name}"
            if self.rate_result.notice:
                metadata = f"{self.rate_result.notice}\n{metadata}"
            self.info_var.set(metadata)

        except Exception as e:
            messagebox.showerror("Conversion Error", str(e))
