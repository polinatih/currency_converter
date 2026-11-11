"""Main application window using Tkinter."""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from src.models.conversion_request import ConversionRequest
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
        self.geometry("450x440")
        self.minsize(400, 400)

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
        amount_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(amount_frame, text="Amount:", width=15, anchor="w").pack(side=tk.LEFT)
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(amount_frame, textvariable=self.amount_var)
        self.amount_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.amount_var.trace_add("write", self._on_input_changed)

        # Inline validation feedback under amount field [FR-006, FR-012]
        error_frame = ttk.Frame(main_frame)
        error_frame.pack(fill=tk.X, pady=(2, 4))
        ttk.Label(error_frame, text="", width=15).pack(side=tk.LEFT)
        self.amount_error_var = tk.StringVar(value="")
        self.amount_error_label = ttk.Label(
            error_frame,
            textvariable=self.amount_error_var,
            foreground="red",
            font=("Segoe UI", 8),
            wraplength=260,
        )
        self.amount_error_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

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
        """Enable or disable conversion button and update inline validation message [FR-003, FR-006, FR-012]."""
        raw_amount = self.amount_var.get()
        src = self.src_currency_var.get()
        tgt = self.tgt_currency_var.get()

        stripped = raw_amount.strip()
        if not stripped:
            # Empty field shows no error, but button remains disabled
            self.amount_error_var.set("")
            self.convert_button.config(state=tk.DISABLED)
            return

        is_valid_amount, amount_msg = self.validation_service.validate_amount(raw_amount)
        if not is_valid_amount:
            self.amount_error_var.set(amount_msg)
            self.convert_button.config(state=tk.DISABLED)
            return

        # Amount is valid; clear inline error
        self.amount_error_var.set("")

        is_valid_req, _ = self.validation_service.validate_request(raw_amount, src, tgt)
        if is_valid_req:
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
            else:
                self.info_var.set("Error: No exchange rates available from source or cache.")
        except Exception as e:
            self.info_var.set(f"Error: Unable to retrieve exchange rates: {e}")

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
                self.info_var.set(f"Error: Unable to retrieve exchange rates: {e}")
                messagebox.showerror("Rate Error", f"Unable to retrieve exchange rates: {e}")
                return

        if not self.rate_result:
            self.info_var.set("Error: No exchange rates available from source or cache.")
            messagebox.showerror("Rate Error", "No exchange rates available from source or cache.")
            return

        try:
            req = ConversionRequest(amount=amount, source_currency=src, target_currency=tgt)
            conv_res = self.rate_service.process_conversion_request(req, self.rate_result.rates)
            self.result_var.set(f"{conv_res.result_display} {tgt}")
            self.pair_rate_var.set(conv_res.pair_rate_display)

            metadata = f"Rate Date: {self.rate_result.effective_date} | Source: {self.rate_result.source_name}"
            if self.rate_result.notice:
                metadata = f"{self.rate_result.notice}\n{metadata}"
            self.info_var.set(metadata)

        except Exception as e:
            messagebox.showerror("Conversion Error", str(e))
