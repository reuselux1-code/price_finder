from __future__ import annotations

import json
import logging
import statistics
import threading
import tkinter as tk
from dataclasses import asdict
from tkinter import messagebox
from typing import List
import webbrowser

from fetcher import FetchConfig, fetch_content
from fx import FxConverter
from google_search import GoogleSearchConfig, search_google
from matcher import page_contains_reference
from models import Result, SourcePrice
from price_extract import extract_single_price
from utils import dedupe_by_domain, save_json, setup_logging


MAX_VALID_SOURCES = 8


class PriceFinderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Price Finder")
        self.fx_converter = FxConverter()
        self.status_var = tk.StringVar(value="Prêt")
        self.result_var = tk.StringVar(value="")
        self.sources: List[SourcePrice] = []

        self._build_ui()

    def _build_ui(self) -> None:
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Nom du produit").grid(row=0, column=0, sticky=tk.W)
        self.name_entry = tk.Entry(frame, width=50)
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, pady=2)

        tk.Label(frame, text="Référence fabricant (P/N)*").grid(
            row=1, column=0, sticky=tk.W
        )
        self.ref_entry = tk.Entry(frame, width=50)
        self.ref_entry.grid(row=1, column=1, sticky=tk.EW, pady=2)

        self.search_button = tk.Button(
            frame, text="Rechercher", command=self.start_search
        )
        self.search_button.grid(row=2, column=0, columnspan=2, pady=6)

        tk.Label(frame, textvariable=self.status_var, fg="blue").grid(
            row=3, column=0, columnspan=2, sticky=tk.W
        )

        tk.Label(frame, text="Résultats").grid(row=4, column=0, sticky=tk.W)
        self.result_label = tk.Label(frame, textvariable=self.result_var, justify=tk.LEFT)
        self.result_label.grid(row=5, column=0, columnspan=2, sticky=tk.W)

        tk.Label(frame, text="Sources").grid(row=6, column=0, sticky=tk.W)
        self.sources_listbox = tk.Listbox(frame, height=8)
        self.sources_listbox.grid(row=7, column=0, columnspan=2, sticky=tk.EW)
        self.sources_listbox.bind("<<ListboxSelect>>", self.open_selected_url)

        self.copy_button = tk.Button(frame, text="Copier résumé", command=self.copy_summary)
        self.copy_button.grid(row=8, column=0, columnspan=2, pady=6)

        frame.columnconfigure(1, weight=1)

    def start_search(self) -> None:
        if not self.ref_entry.get().strip():
            messagebox.showerror("Erreur", "La référence fabricant est obligatoire.")
            return
        self.search_button.configure(state=tk.DISABLED)
        self.status_var.set("Recherche en cours...")
        self.result_var.set("")
        self.sources_listbox.delete(0, tk.END)
        self.sources.clear()

        thread = threading.Thread(target=self.run_search, daemon=True)
        thread.start()

    def run_search(self) -> None:
        try:
            result = self._perform_search()
            self.root.after(0, lambda: self.display_result(result))
        except Exception as exc:
            logging.exception("Search failed")
            self.root.after(0, lambda: self.show_error(str(exc)))

    def _perform_search(self) -> Result:
        name_raw = self.name_entry.get().strip()
        ref_raw = self.ref_entry.get().strip()
        query = f'"{ref_raw}" {name_raw}'.strip()

        search_config = GoogleSearchConfig()
        urls = search_google(query, search_config)
        urls = dedupe_by_domain(urls)

        fetch_config = FetchConfig(user_agent=search_config.user_agent)
        sources: List[SourcePrice] = []

        for url in urls:
            if len(sources) >= MAX_VALID_SOURCES:
                break
            html = fetch_content(url, fetch_config)
            if not html:
                continue
            if not page_contains_reference(html, ref_raw):
                continue
            price_candidate = extract_single_price(html)
            if not price_candidate:
                continue
            price_eur = self.fx_converter.to_eur(
                price_candidate.amount, price_candidate.currency
            )
            sources.append(
                SourcePrice(
                    url=url,
                    price_original=price_candidate.amount,
                    currency=price_candidate.currency,
                    price_eur=price_eur,
                )
            )

        eur_values = [source.price_eur for source in sources]
        reliability = "fiabilité faible" if len(eur_values) < 3 else "fiabilité correcte"
        if eur_values:
            min_eur = min(eur_values)
            max_eur = max(eur_values)
            median_eur = statistics.median(eur_values)
        else:
            min_eur = max_eur = median_eur = None

        result = Result(
            sources=sources,
            min_eur=min_eur,
            median_eur=median_eur,
            max_eur=max_eur,
            reliability=reliability,
        )

        save_json("last_results.json", {
            "query": query,
            "result": asdict(result),
        })

        return result

    def display_result(self, result: Result) -> None:
        self.search_button.configure(state=tk.NORMAL)
        self.status_var.set("Terminé")
        self.sources = result.sources

        if result.min_eur is None:
            self.result_var.set("Aucun résultat valide trouvé.")
        else:
            summary = (
                f"Min: {result.min_eur:.2f} EUR\n"
                f"Médiane: {result.median_eur:.2f} EUR\n"
                f"Max: {result.max_eur:.2f} EUR\n"
                f"Sources: {len(result.sources)} ({result.reliability})"
            )
            self.result_var.set(summary)

        self.sources_listbox.delete(0, tk.END)
        for source in result.sources:
            self.sources_listbox.insert(tk.END, source.url)

    def open_selected_url(self, event: tk.Event) -> None:
        selection = self.sources_listbox.curselection()
        if not selection:
            return
        url = self.sources_listbox.get(selection[0])
        webbrowser.open(url)

    def copy_summary(self) -> None:
        if not self.sources:
            return
        text_lines = [self.result_var.get(), "", "Sources:"]
        text_lines.extend(source.url for source in self.sources)
        summary = "\n".join(text_lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(summary)
        self.status_var.set("Résumé copié")

    def show_error(self, message: str) -> None:
        self.search_button.configure(state=tk.NORMAL)
        self.status_var.set("Erreur")
        messagebox.showerror("Erreur", message)


def main() -> None:
    setup_logging()
    root = tk.Tk()
    app = PriceFinderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
