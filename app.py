#!/usr/bin/env python3
"""CV Üretici - masaüstü arayüzü. Form doldurun, Word ve PDF üretin."""
import sys
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

import build_cv
from cv_model import (ITEM_TYPES, ITEM_FIELDS, empty_cv, load_cv, save_cv, next_copy_path,
                      split_contact, build_contact, new_item, describe_item, clean_item,
                      analyze, tailor)

LANGS = {"Türkçe": "tr", "English": "en"}


def app_dir():
    # When packaged with PyInstaller, files sit next to the .exe
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


class ItemDialog(tk.Toplevel):
    """Add or edit one item. Type can be changed; fields follow the type."""

    def __init__(self, master, item, on_ok):
        super().__init__(master)
        self.title("Öğe")
        self.transient(master)
        self.resizable(False, False)
        self.on_ok = on_ok
        self.item = dict(item)
        self.type_var = tk.StringVar(value=ITEM_TYPES[self.item["type"]])
        self.field_vars = {}

        top = ttk.Frame(self, padding=12)
        top.pack(fill="both", expand=True)
        ttk.Label(top, text="Tür").grid(row=0, column=0, sticky="w", pady=4)
        combo = ttk.Combobox(top, textvariable=self.type_var, state="readonly", width=34,
                             values=list(ITEM_TYPES.values()))
        combo.grid(row=0, column=1, sticky="ew", pady=4)
        combo.bind("<<ComboboxSelected>>", lambda e: self._rebuild_fields())
        self.fields_frame = ttk.Frame(top)
        self.fields_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        buttons = ttk.Frame(top)
        buttons.grid(row=2, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="İptal", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(buttons, text="Tamam", command=self._ok).pack(side="right")
        self._rebuild_fields()
        self.grab_set()

    def _selected_type(self):
        label = self.type_var.get()
        return next(k for k, v in ITEM_TYPES.items() if v == label)

    def _rebuild_fields(self):
        # keep values the new type also uses
        for key, var in self.field_vars.items():
            self.item[key] = var.get()
        new_type = self._selected_type()
        self.item["type"] = new_type
        for w in self.fields_frame.winfo_children():
            w.destroy()
        self.field_vars = {}
        for row, (key, label) in enumerate(ITEM_FIELDS[new_type]):
            ttk.Label(self.fields_frame, text=label).grid(row=row, column=0, sticky="w", pady=4, padx=(0, 8))
            var = tk.StringVar(value=self.item.get(key, ""))
            ttk.Entry(self.fields_frame, textvariable=var, width=50).grid(row=row, column=1, sticky="ew", pady=4)
            self.field_vars[key] = var

    def _ok(self):
        values = {k: v.get().strip() for k, v in self.field_vars.items()}
        result = clean_item({"type": self._selected_type(), **values})
        self.on_ok(result)
        self.destroy()


class TailorDialog(tk.Toplevel):
    """Paste a job ad, see which skills match, and optionally move matching items up."""

    def __init__(self, master, get_cv, apply_cb):
        super().__init__(master)
        self.title("İlana göre uyarla")
        self.geometry("620x560")
        self.transient(master)
        self.get_cv = get_cv
        self.apply_cb = apply_cb
        self.matched = []

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="İlan metnini buraya yapıştır:").pack(anchor="w")
        self.ad_text = tk.Text(frame, height=12, wrap="word")
        self.ad_text.pack(fill="both", expand=True, pady=(4, 8))

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Analiz et", command=self._analyze).pack(side="left")
        self.apply_btn = ttk.Button(buttons, text="Eşleşenleri öne çıkar", command=self._apply, state="disabled")
        self.apply_btn.pack(side="left", padx=6)

        self.result = ttk.Label(frame, text="", wraplength=580, justify="left")
        self.result.pack(anchor="w", fill="x", pady=(12, 0))
        ttk.Label(frame, text="Not: Bu araç hiçbir beceriyi kendiliğinden eklemez. "
                              "Eksik olanları yalnızca gerçekten biliyorsan kendin ekle.",
                  foreground="#666", wraplength=580, justify="left").pack(anchor="w", pady=(10, 0))

    def _analyze(self):
        ad = self.ad_text.get("1.0", "end").strip()
        if not ad:
            messagebox.showinfo("İlan yok", "Önce ilan metnini yapıştır.", parent=self)
            return
        res = analyze(self.get_cv(), ad)
        self.matched = res["matched"]
        lines = []
        lines.append("Eşleşen (CV'nde var): " + (", ".join(res["matched"]) or "yok"))
        lines.append("")
        lines.append("İlanda var, CV'de yok: " + (", ".join(res["missing"]) or "yok"))
        self.result.configure(text="\n".join(lines))
        self.apply_btn.configure(state="normal" if self.matched else "disabled")

    def _apply(self):
        self.apply_cb(self.matched)
        messagebox.showinfo("Tamam", "Eşleşen beceriler ve ilgili maddeler öne alındı.\n"
                                     "Değişiklik kalıcı olsun diye Kaydet'e bas.", parent=self)
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CV Üretici")
        self.geometry("980x640")
        self.minsize(860, 560)
        self.folder = app_dir()
        self.current_code = "tr"
        self.data = {}
        self.name_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.linkedin_var = tk.StringVar()
        self.github_var = tk.StringVar()
        self.section_var = tk.StringVar()
        self.pdf_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Hazır")
        self.loaded_from = {}  # language code -> file the CV was opened from
        self._build_ui()
        self._load_folder(self.folder)

    # ---------- layout ----------
    def _build_ui(self):
        top = ttk.Frame(self, padding=(12, 10))
        top.pack(fill="x")
        ttk.Label(top, text="Klasör:").pack(side="left")
        self.folder_label = ttk.Label(top, text="", foreground="#444")
        self.folder_label.pack(side="left", padx=6)
        ttk.Button(top, text="Klasör seç", command=self._choose_folder).pack(side="left")
        ttk.Button(top, text="CV dosyası aç", command=self._open_cv_file).pack(side="left", padx=6)
        ttk.Label(top, text="Dil:").pack(side="right", padx=(0, 4))
        self.lang_combo = ttk.Combobox(top, state="readonly", width=12, values=list(LANGS))
        self.lang_combo.set("Türkçe")
        self.lang_combo.pack(side="right")
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_lang_change)

        body = ttk.Frame(self, padding=(12, 0))
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # left: header fields
        left = ttk.LabelFrame(body, text="Kişisel bilgiler", padding=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        fields = [("Ad Soyad", self.name_var), ("Ünvan", self.title_var),
                  ("Konum ve telefon", self.location_var), ("E-posta", self.email_var),
                  ("LinkedIn bağlantısı", self.linkedin_var), ("GitHub bağlantısı", self.github_var)]
        for row, (label, var) in enumerate(fields):
            ttk.Label(left, text=label).grid(row=row * 2, column=0, sticky="w")
            ttk.Entry(left, textvariable=var, width=34).grid(row=row * 2 + 1, column=0, sticky="ew", pady=(0, 8))

        # right: sections and items
        right = ttk.LabelFrame(body, text="Bölümler", padding=10)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)
        sec_row = ttk.Frame(right)
        sec_row.grid(row=0, column=0, sticky="ew")
        self.section_combo = ttk.Combobox(sec_row, textvariable=self.section_var, state="readonly", width=30)
        self.section_combo.pack(side="left", fill="x", expand=True)
        self.section_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_items())
        ttk.Button(sec_row, text="Yeni bölüm", command=self._new_section).pack(side="left", padx=4)
        ttk.Button(sec_row, text="Bölümü sil", command=self._delete_section).pack(side="left")

        btn_row = ttk.Frame(right, padding=(0, 8))
        btn_row.grid(row=1, column=0, sticky="ew")
        for text, cmd in [("Ekle", self._add_item), ("Düzenle", self._edit_item),
                          ("Sil", self._delete_item), ("Yukarı", lambda: self._move(-1)),
                          ("Aşağı", lambda: self._move(1))]:
            ttk.Button(btn_row, text=text, command=cmd).pack(side="left", padx=2)

        list_frame = ttk.Frame(right)
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.items_list = tk.Listbox(list_frame, activestyle="none", font=("Segoe UI", 10))
        self.items_list.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(list_frame, command=self.items_list.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.items_list.configure(yscrollcommand=scroll.set)
        self.items_list.bind("<Double-1>", lambda e: self._edit_item())

        # bottom: actions
        bottom = ttk.Frame(self, padding=12)
        bottom.pack(fill="x")
        ttk.Checkbutton(bottom, text="PDF de oluştur", variable=self.pdf_var).pack(side="left")
        ttk.Button(bottom, text="İlana göre uyarla", command=self._open_tailor).pack(side="left", padx=12)
        ttk.Button(bottom, text="Kaydet", command=self._save).pack(side="right", padx=4)
        ttk.Button(bottom, text="Word / PDF oluştur", command=self._generate).pack(side="right")
        ttk.Label(bottom, textvariable=self.status_var, foreground="#444").pack(side="left", padx=16)

    # ---------- data ----------
    def _load_folder(self, folder):
        self.folder = Path(folder)
        self.folder_label.configure(text=str(self.folder))
        self.data = {code: load_cv(self.folder / f"cv_{code}.json") for code in LANGS.values()}
        self.loaded_from = {}
        self._load_widgets()
        self.status_var.set("Dosyalar yüklendi")

    def _lang_code(self):
        return self.current_code

    def _store_widgets(self):
        cv = self.data[self._lang_code()]
        cv["name"] = self.name_var.get().strip()
        cv["title"] = self.title_var.get().strip()
        cv["contact"] = build_contact(self.location_var.get(), self.email_var.get(),
                                      self.linkedin_var.get(), self.github_var.get())

    def _load_widgets(self):
        cv = self.data[self._lang_code()]
        self.name_var.set(cv.get("name", ""))
        self.title_var.set(cv.get("title", ""))
        loc, email, li, gh = split_contact(cv.get("contact", []))
        self.location_var.set(loc)
        self.email_var.set(email)
        self.linkedin_var.set(li)
        self.github_var.set(gh)
        headings = [s["heading"] for s in cv.get("sections", [])]
        self.section_combo.configure(values=headings)
        self.section_var.set(headings[0] if headings else "")
        self._refresh_items()

    def _on_lang_change(self, _event=None):
        self._store_widgets()  # keep edits made in the language we are leaving
        self.current_code = LANGS[self.lang_combo.get()]
        self._load_widgets()

    def _current_section(self):
        cv = self.data[self._lang_code()]
        headings = [s["heading"] for s in cv.get("sections", [])]
        if self.section_var.get() not in headings:
            return None
        return cv["sections"][headings.index(self.section_var.get())]

    def _refresh_items(self):
        self.items_list.delete(0, tk.END)
        section = self._current_section()
        if section:
            for item in section["items"]:
                self.items_list.insert(tk.END, describe_item(item))

    def _selected_index(self):
        sel = self.items_list.curselection()
        return sel[0] if sel else None

    # ---------- section actions ----------
    def _new_section(self):
        name = simpledialog.askstring("Yeni bölüm", "Bölüm başlığı:", parent=self)
        if not name or not name.strip():
            return
        cv = self.data[self._lang_code()]
        cv.setdefault("sections", []).append({"heading": name.strip(), "items": []})
        self._load_widgets()
        self.section_var.set(name.strip())
        self._refresh_items()

    def _delete_section(self):
        section = self._current_section()
        if not section:
            return
        if not messagebox.askyesno("Bölümü sil", f"'{section['heading']}' bölümü silinsin mi?", parent=self):
            return
        cv = self.data[self._lang_code()]
        cv["sections"] = [s for s in cv["sections"] if s is not section]
        self._load_widgets()

    # ---------- item actions ----------
    def _add_item(self):
        section = self._current_section()
        if not section:
            messagebox.showinfo("Bölüm yok", "Önce bir bölüm ekleyin.", parent=self)
            return

        def done(item):
            section["items"].append(item)
            self._refresh_items()
            self.items_list.selection_set(tk.END)
        ItemDialog(self, new_item("bullet"), done)

    def _edit_item(self):
        section = self._current_section()
        idx = self._selected_index()
        if not section or idx is None:
            return

        def done(item):
            section["items"][idx] = item
            self._refresh_items()
            self.items_list.selection_set(idx)
        ItemDialog(self, section["items"][idx], done)

    def _delete_item(self):
        section = self._current_section()
        idx = self._selected_index()
        if not section or idx is None:
            return
        del section["items"][idx]
        self._refresh_items()

    def _move(self, delta):
        section = self._current_section()
        idx = self._selected_index()
        if not section or idx is None:
            return
        new = idx + delta
        if 0 <= new < len(section["items"]):
            items = section["items"]
            items[idx], items[new] = items[new], items[idx]
            self._refresh_items()
            self.items_list.selection_set(new)

    # ---------- job-ad tailoring ----------
    def _open_tailor(self):
        def get_cv():
            self._store_widgets()
            return self.data[self._lang_code()]
        TailorDialog(self, get_cv, self._apply_tailor)

    def _apply_tailor(self, matched):
        self._store_widgets()
        code = self._lang_code()
        self.data[code] = tailor(self.data[code], matched)
        self._load_widgets()
        self.status_var.set("İlana göre öne çıkarma uygulandı (Kaydet ile kalıcı yap)")

    # ---------- file actions ----------
    def _choose_folder(self):
        folder = filedialog.askdirectory(parent=self, initialdir=str(self.folder))
        if folder:
            self._load_folder(folder)

    def _open_cv_file(self):
        path = filedialog.askopenfilename(parent=self, initialdir=str(self.folder),
                                          title="CV dosyası seçin",
                                          filetypes=[("CV JSON", "*.json"), ("Tümü", "*.*")])
        if not path:
            return
        try:
            cv = load_cv(path)
            if not isinstance(cv, dict) or not isinstance(cv.get("sections", []), list):
                raise ValueError("Bu dosya bir CV verisi değil (beklenen: sections listesi).")
        except (OSError, ValueError) as e:
            messagebox.showerror("Dosya açılamadı", str(e), parent=self)
            return
        code = self._lang_code()
        self.data[code] = cv
        self.loaded_from[code] = Path(path)
        self._load_widgets()
        self.status_var.set(f"Açıldı: {Path(path).name} (Kaydet yeni kopya üretir)")

    def _save(self):
        self._store_widgets()
        written = []
        for code, cv in self.data.items():
            # An opened file is never overwritten: Kaydet writes name_1.json, name_2.json, ...
            src = self.loaded_from.get(code)
            target = next_copy_path(src) if src else self.folder / f"cv_{code}.json"
            save_cv(target, cv)
            written.append(target.name)
        self.status_var.set("Kaydedildi: " + ", ".join(written))

    def _generate(self):
        self._store_widgets()
        out_dir = filedialog.askdirectory(parent=self, title="Çıktı klasörü seçin",
                                          initialdir=str(self.folder))
        if not out_dir:
            return
        out = Path(out_dir)
        made = []
        try:
            for code, cv in self.data.items():
                if not cv.get("name"):
                    continue
                base = "_".join(cv["name"].split())
                docx_path = out / f"{base}_CV_{code.upper()}.docx"
                build_cv.build_docx(cv, docx_path)
                made.append(docx_path)
                if self.pdf_var.get():
                    made.append(build_cv.to_pdf(docx_path))
        except SystemExit as e:  # to_pdf exits with a message when no converter is found
            messagebox.showerror("PDF oluşturulamadı", str(e), parent=self)
        except Exception:
            messagebox.showerror("Hata", traceback.format_exc()[-800:], parent=self)
        if made:
            self.status_var.set(f"{len(made)} dosya oluşturuldu: {out}")
            messagebox.showinfo("Tamam", "Oluşturulan dosyalar:\n" + "\n".join(p.name for p in made), parent=self)


if __name__ == "__main__":
    App().mainloop()
