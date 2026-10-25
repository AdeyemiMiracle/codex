from __future__ import annotations

import argparse
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from adsb_altitude_decoder import AltitudeRecord, read_first_messages

DEFAULT_LOG = Path(
    r"C:\Users\Adeyemi\xwechat_files\wxid_l9qsf7yn99j012_30c7\msg\file\2026-10\0116.txt"
)
BACKGROUND = "#f3f6fb"
NAVY = "#14263d"
BLUE = "#2563eb"
MUTED = "#62748a"


class SimulationApp:
    def __init__(self, log_path: Path) -> None:
        self.root = tk.Tk()
        self.root.title("AeroScope | ADS-B Altitude Lab")
        self.root.geometry("1180x790")
        self.root.minsize(900, 680)
        self.root.configure(background=BACKGROUND)

        self.log_path_var = tk.StringVar(value=str(log_path))
        self.icao_var = tk.StringVar()
        self.status_var = tk.StringVar(
            value="Enter a six-digit ICAO address to search the first 400 messages."
        )
        self.summary_var = tk.StringVar(value="No aircraft selected")
        self.count_var = tk.StringVar(value="—")
        self.range_var = tk.StringVar(value="—")
        self.records: tuple[AltitudeRecord, ...] = ()

        self._configure_styles()
        self._build_layout()

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("App.TFrame", background=BACKGROUND)
        style.configure("Card.TFrame", background="white")
        style.configure("Header.TFrame", background=NAVY)
        style.configure(
            "Title.TLabel",
            background=NAVY,
            foreground="white",
            font=("Segoe UI", 23, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=NAVY,
            foreground="#c3d3e5",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Section.TLabel",
            background="white",
            foreground=NAVY,
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Muted.TLabel",
            background="white",
            foreground=MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Value.TLabel",
            background="white",
            foreground=NAVY,
            font=("Segoe UI", 19, "bold"),
        )
        style.configure(
            "Primary.TButton",
            background=BLUE,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(16, 10),
            borderwidth=0,
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#1d4ed8"), ("disabled", "#9bb9f5")],
        )
        style.configure(
            "Secondary.TButton",
            background="#eaf0f8",
            foreground=NAVY,
            font=("Segoe UI", 9, "bold"),
            padding=(12, 8),
            borderwidth=0,
        )
        style.map("Secondary.TButton", background=[("active", "#dbe7f5")])
        style.configure(
            "Treeview",
            background="white",
            fieldbackground="white",
            foreground=NAVY,
            rowheight=30,
            font=("Segoe UI", 9),
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#edf2f8",
            foreground="#42566f",
            font=("Segoe UI", 9, "bold"),
            padding=(8, 9),
            borderwidth=0,
        )
        style.map("Treeview", background=[("selected", "#dce9ff")])

    def _build_layout(self) -> None:
        page = ttk.Frame(self.root, style="App.TFrame", padding=(28, 20))
        page.pack(fill="both", expand=True)
        page.columnconfigure(0, weight=1)
        page.rowconfigure(4, weight=1)

        header = ttk.Frame(page, style="Header.TFrame", padding=(24, 20))
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        ttk.Label(header, text="AeroScope", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="ADS-B ALTITUDE LAB     /     AIRBORNE POSITION TRACKING",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        source_card = ttk.Frame(page, style="Card.TFrame", padding=18)
        source_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        source_card.columnconfigure(1, weight=1)
        ttk.Label(source_card, text="Message file", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 16)
        )
        ttk.Entry(source_card, textvariable=self.log_path_var).grid(
            row=0, column=1, sticky="ew"
        )
        ttk.Button(
            source_card,
            text="Browse",
            style="Secondary.TButton",
            command=self._browse_file,
        ).grid(row=0, column=2, padx=(10, 0))
        ttk.Label(
            source_card,
            text="The search is limited to the first 400 non-empty messages in this file.",
            style="Muted.TLabel",
        ).grid(row=1, column=1, sticky="w", pady=(7, 0))

        search_card = ttk.Frame(page, style="Card.TFrame", padding=18)
        search_card.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        search_card.columnconfigure(1, weight=1)
        ttk.Label(search_card, text="Aircraft ICAO", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 16)
        )
        address_entry = ttk.Entry(
            search_card,
            textvariable=self.icao_var,
            font=("Consolas", 12),
            width=18,
        )
        address_entry.grid(row=0, column=1, sticky="w")
        address_entry.bind("<Return>", lambda _event: self._decode())
        ttk.Label(
            search_card,
            text="24-bit address · 6 hexadecimal characters",
            style="Muted.TLabel",
        ).grid(row=1, column=1, sticky="w", pady=(6, 0))
        self.graph_button = ttk.Button(
            search_card,
            text="View altitude graph",
            style="Secondary.TButton",
            command=self._show_graph,
            state="disabled",
        )
        self.graph_button.grid(row=0, column=3, sticky="e", padx=(10, 10))
        ttk.Button(
            search_card,
            text="Decode aircraft",
            style="Primary.TButton",
            command=self._decode,
        ).grid(row=0, column=4, sticky="e")

        stats = ttk.Frame(page, style="App.TFrame")
        stats.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        stats.columnconfigure(0, weight=1)
        stats.columnconfigure(1, weight=1)
        self._stat_card(stats, 0, "ALTITUDE OBSERVATIONS", self.count_var)
        self._stat_card(stats, 1, "ALTITUDE RANGE", self.range_var)

        results_card = ttk.Frame(page, style="Card.TFrame", padding=18)
        results_card.grid(row=4, column=0, sticky="nsew")
        results_card.columnconfigure(0, weight=1)
        results_card.rowconfigure(2, weight=1)
        heading = ttk.Frame(results_card, style="Card.TFrame")
        heading.grid(row=0, column=0, sticky="ew")
        heading.columnconfigure(0, weight=1)
        ttk.Label(heading, text="Decoded altitude history", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(heading, textvariable=self.summary_var, style="Muted.TLabel").grid(
            row=0, column=1, sticky="e"
        )
        ttk.Label(
            results_card,
            textvariable=self.status_var,
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 12))

        table_frame = ttk.Frame(results_card, style="Card.TFrame")
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        columns = ("timestamp", "altitude", "type_code", "q_bit", "frame")
        self.table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        for column, title, width, anchor in (
            ("timestamp", "DATE & TIME", 200, "w"),
            ("altitude", "ALTITUDE (FT)", 150, "e"),
            ("type_code", "TYPE CODE", 110, "center"),
            ("q_bit", "Q BIT", 80, "center"),
            ("frame", "112-BIT MESSAGE", 370, "w"),
        ):
            self.table.heading(column, text=title)
            self.table.column(column, width=width, anchor=anchor, stretch=column != "q_bit")
        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.table.yview
        )
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.table.tag_configure("even", background="#f7f9fc")
        self.table.tag_configure("odd", background="white")

        ttk.Label(
            page,
            text="ALTITUDE DECODING  ·  Type codes 9–18 and 20–22  ·  Q=1: 25 ft steps  ·  Q=0: Gillham code",
            background=BACKGROUND,
            foreground=MUTED,
            font=("Segoe UI", 8),
        ).grid(row=5, column=0, sticky="w", pady=(12, 0))

    @staticmethod
    def _stat_card(
        parent: ttk.Frame, column: int, label: str, value: tk.StringVar
    ) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=(18, 13))
        card.grid(row=0, column=column, sticky="ew", padx=(0, 8) if column == 0 else (8, 0))
        ttk.Label(card, text=label, style="Muted.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=value, style="Value.TLabel").pack(
            anchor="w", pady=(4, 0)
        )

    def _browse_file(self) -> None:
        current_path = Path(self.log_path_var.get()).expanduser()
        selected = filedialog.askopenfilename(
            title="Select an ADS-B message file",
            initialdir=str(current_path.parent) if current_path.parent.exists() else None,
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
        )
        if selected:
            self.log_path_var.set(selected)

    def _decode(self) -> None:
        icao_address = self.icao_var.get().strip().upper()
        if re.fullmatch(r"[0-9A-F]{6}", icao_address) is None:
            messagebox.showerror(
                "Invalid ICAO address",
                "Enter exactly six hexadecimal characters for the 24-bit ICAO address.",
                parent=self.root,
            )
            return

        log_path = Path(self.log_path_var.get()).expanduser()
        if not log_path.is_file():
            messagebox.showerror(
                "Message file not found",
                f"Select a readable ADS-B text file.\n\n{log_path}",
                parent=self.root,
            )
            return

        try:
            dataset = read_first_messages(log_path)
        except OSError as error:
            messagebox.showerror(
                "Could not read message file",
                str(error),
                parent=self.root,
            )
            return

        self.records = tuple(
            record
            for record in dataset.records
            if record.icao_address == icao_address
        )
        for row in self.table.get_children():
            self.table.delete(row)

        for index, record in enumerate(self.records):
            self.table.insert(
                "",
                "end",
                values=(
                    record.timestamp.strftime("%Y-%m-%d  %H:%M:%S.%f")[:-3],
                    f"{record.altitude_ft:,}",
                    record.type_code,
                    record.q_bit,
                    record.frame,
                ),
                tags=("even" if index % 2 == 0 else "odd",),
            )

        self.count_var.set(f"{len(self.records)}")
        if self.records:
            lowest = min(record.altitude_ft for record in self.records)
            highest = max(record.altitude_ft for record in self.records)
            self.range_var.set(f"{lowest:,} – {highest:,} ft")
            self.summary_var.set(f"ICAO {icao_address}  ·  {dataset.messages_scanned} messages scanned")
            self.status_var.set(
                f"Showing {len(self.records)} qualifying altitude messages for ICAO {icao_address}."
            )
        else:
            self.range_var.set("—")
            self.summary_var.set(f"ICAO {icao_address}  ·  {dataset.messages_scanned} messages scanned")
            self.status_var.set(
                f"No qualifying altitude messages for ICAO {icao_address} in the first "
                f"{dataset.messages_scanned} messages."
            )
        self.graph_button.configure(
            state="normal" if self.records else "disabled"
        )

    def _show_graph(self) -> None:
        if not self.records:
            return

        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.dates import DateFormatter
        from matplotlib.figure import Figure

        window = tk.Toplevel(self.root)
        window.title(f"Altitude profile · {self.records[0].icao_address}")
        window.geometry("960x590")
        window.configure(background=BACKGROUND)

        figure = Figure(figsize=(9.2, 5.2), dpi=100, facecolor="white")
        axis = figure.add_subplot(111)
        times = [record.timestamp for record in self.records]
        altitudes = [record.altitude_ft for record in self.records]
        axis.plot(
            times,
            altitudes,
            color=BLUE,
            linewidth=2,
            marker="o",
            markersize=4,
            markerfacecolor="white",
            markeredgewidth=1.5,
        )
        axis.fill_between(times, altitudes, min(altitudes), color=BLUE, alpha=0.08)
        axis.set_title(
            f"Aircraft {self.records[0].icao_address}  ·  Altitude over time",
            loc="left",
            color=NAVY,
            fontsize=13,
            fontweight="bold",
            pad=16,
        )
        axis.set_xlabel("Time", color=MUTED, labelpad=10)
        axis.set_ylabel("Altitude (ft)", color=MUTED, labelpad=10)
        axis.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
        axis.grid(axis="y", color="#e7edf5", linewidth=0.8)
        axis.spines[["top", "right"]].set_visible(False)
        axis.spines[["left", "bottom"]].set_color("#dce4ee")
        axis.tick_params(colors=MUTED)
        axis.margins(x=0.025, y=0.12)
        figure.autofmt_xdate()
        figure.tight_layout()

        canvas = FigureCanvasTkAgg(figure, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive ADS-B altitude decoder for the first 400 log messages."
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG,
        help="ADS-B text file to open (the file can also be changed in the window)",
    )
    args = parser.parse_args()
    SimulationApp(args.log).run()


if __name__ == "__main__":
    main()
