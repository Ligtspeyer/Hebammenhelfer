#to-do: geburtsmonat ermitteln und mögliche terminzeiträume konfigurierbar machen


import imapclient
import pyzmail
from bs4 import BeautifulSoup
from datetime import datetime
import re
import webbrowser
import json
import os
import ssl
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# --- Konfigurationsdatei ---
CONFIG_DATEI = "config.json"
MONATSZÄHLER_DATEI = "annahmen_counter.json"

# --- Sun Valley Theme Implementation ---
class SunValleyTheme:
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style(root)
        self.theme_created = False
        
    def load_theme(self, mode="light"):
        if not self.theme_created:
            self.create_theme()
            
        if mode.lower() == "dark":
            self.style.theme_use("sun-valley-dark")
        else:
            self.style.theme_use("sun-valley-light")
            
    def create_theme(self):
        # Create a custom theme based on default theme
        self.style.theme_create("sun-valley-light", parent="clam")
        self.style.theme_create("sun-valley-dark", parent="clam")
        
        # Configure common styles
        self._configure_common_styles()
        
        # Configure light theme
        self._configure_light_theme()
        
        # Configure dark theme
        self._configure_dark_theme()
        
        self.theme_created = True
        
    def _configure_common_styles(self):
        # Common button style
        for theme in ["sun-valley-light", "sun-valley-dark"]:
            self.style.configure(
                f"{theme}.TButton",
                font=("Segoe UI", 10),
                borderwidth=0,
                focusthickness=0,
                focuscolor="none",
                padding=(10, 5)
            )
            
            # Entry style
            self.style.configure(
                f"{theme}.TEntry",
                borderwidth=1,
                font=("Segoe UI", 10),
                padding=5
            )
            
            # Label style
            self.style.configure(
                f"{theme}.TLabel",
                font=("Segoe UI", 10)
            )
            
            # Frame style
            self.style.configure(
                f"{theme}.TFrame",
                borderwidth=0
            )
            
            # Notebook style
            self.style.configure(
                f"{theme}.TNotebook",
                borderwidth=0
            )
            self.style.configure(
                f"{theme}.TNotebook.Tab",
                padding=(10, 5),
                font=("Segoe UI", 10)
            )
            
            # Treeview style
            self.style.configure(
                f"{theme}.Treeview",
                font=("Segoe UI", 10),
                rowheight=25
            )
            self.style.configure(
                f"{theme}.Treeview.Heading",
                font=("Segoe UI", 10, "bold")
            )
    
    def _configure_light_theme(self):
        theme = "sun-valley-light"
        
        # Colors
        bg_color = "#f0f0f0"
        fg_color = "#202020"
        accent_color = "#007fff"
        button_color = "#e0e0e0"
        button_hover = "#d0d0d0"
        button_pressed = "#c0c0c0"
        entry_bg = "#ffffff"
        
        # Configure styles
        self.style.configure(f"{theme}.TButton", background=button_color, foreground=fg_color)
        self.style.map(f"{theme}.TButton",
                       background=[("active", button_hover), ("pressed", button_pressed)],
                       foreground=[("active", fg_color), ("pressed", fg_color)])
        
        self.style.configure(f"{theme}.TEntry", fieldbackground=entry_bg, foreground=fg_color)
        self.style.configure(f"{theme}.TLabel", background=bg_color, foreground=fg_color)
        self.style.configure(f"{theme}.TFrame", background=bg_color)
        self.style.configure(f"{theme}.TNotebook", background=bg_color)
        self.style.configure(f"{theme}.TNotebook.Tab", background=button_color, foreground=fg_color)
        self.style.map(f"{theme}.TNotebook.Tab",
                      background=[("selected", accent_color)],
                      foreground=[("selected", "#ffffff")])
        
        self.style.configure(f"{theme}.Treeview", background=entry_bg, foreground=fg_color, fieldbackground=entry_bg)
        self.style.configure(f"{theme}.Treeview.Heading", background=button_color, foreground=fg_color)
        
    def _configure_dark_theme(self):
        theme = "sun-valley-dark"
        
        # Colors
        bg_color = "#681515"
        fg_color = "#3ec01a"
        accent_color = "#007fff"
        button_color = "#C34141"
        button_hover = "#810D0D"
        button_pressed = "#C63F3F"
        entry_bg = "#7D0808"
        
        # Configure styles
        self.style.configure(f"{theme}.TButton", background=button_color, foreground=fg_color)
        self.style.map(f"{theme}.TButton",
                       background=[("active", button_hover), ("pressed", button_pressed)],
                       foreground=[("active", fg_color), ("pressed", fg_color)])
        
        self.style.configure(f"{theme}.TEntry", fieldbackground=entry_bg, foreground=fg_color)
        self.style.configure(f"{theme}.TLabel", background=bg_color, foreground=fg_color)
        self.style.configure(f"{theme}.TFrame", background=bg_color)
        self.style.configure(f"{theme}.TNotebook", background=bg_color)
        self.style.configure(f"{theme}.TNotebook.Tab", background=button_color, foreground=fg_color)
        self.style.map(f"{theme}.TNotebook.Tab",
                      background=[("selected", accent_color)],
                      foreground=[("selected", "#ffffff")])
        
        self.style.configure(f"{theme}.Treeview", background=entry_bg, foreground=fg_color, fieldbackground=entry_bg)
        self.style.configure(f"{theme}.Treeview.Heading", background=button_color, foreground=fg_color)

# --- Hilfsfunktionen für Daten ---
def lade_konfiguration():
    if not os.path.exists(CONFIG_DATEI):
        return {
            "email": "",
            "passwort": "",
            "imap_server": "imap.gmx.net",
            "plz_liste": ["13403", "13405", "13409"],
            "max_termine": 5,
            "akzeptierte_geburtsmonate": list(range(1, 13))  # Standardmäßig alle Monate akzeptieren
        }
    with open(CONFIG_DATEI, "r") as f:
        config = json.load(f)
        # Stelle sicher, dass akzeptierte_geburtsmonate existiert
        if "akzeptierte_geburtsmonate" not in config:
            config["akzeptierte_geburtsmonate"] = list(range(1, 13))
        return config

def speichere_konfiguration(config):
    with open(CONFIG_DATEI, "w") as f:
        json.dump(config, f)

def lade_counter():
    if not os.path.exists(MONATSZÄHLER_DATEI):
        return {}
    try:
        with open(MONATSZÄHLER_DATEI, "r") as f:
            content = f.read().strip()
            if not content:  # File is empty
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        print(f"Fehler beim Laden der Zählerdatei. Erstelle neue leere Datei.")
        return {}

def speichere_counter(counter):
    with open(MONATSZÄHLER_DATEI, "w") as f:
        json.dump(counter, f)

def aktueller_monat():
    return datetime.now().strftime("%Y-%m")

def inkrementiere_counter(datum, plz):
    counter = lade_counter()
    monat = aktueller_monat()
    
    if monat not in counter:
        counter[monat] = {"anzahl": 0, "termine": []}
    
    counter[monat]["anzahl"] = counter[monat].get("anzahl", 0) + 1
    
    # Speichere Datum und PLZ
    if "termine" not in counter[monat]:
        counter[monat]["termine"] = []
    
    counter[monat]["termine"].append({
        "datum": datum,
        "plz": plz,
        "angenommen_am": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    speichere_counter(counter)

def zu_viele_termine(max_termine):
    counter = lade_counter()
    monat = aktueller_monat()
    if monat not in counter:
        return False
    return counter[monat].get("anzahl", 0) >= max_termine

# --- Hauptanwendung ---
class HebammenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HebammenHelfer v2.1")
        self.root.geometry("800x600")
        
        # Style für ttk Widgets
        self.style = ttk.Style(root)
        
        # Theme anwenden
        self.theme = SunValleyTheme(root)
        self.theme.load_theme("light")
        
        # Konfiguration laden
        self.config = lade_konfiguration()
        
        # E-Mail-Prüfungsintervall in Millisekunden (Standard: 2 Minuten)
        self.check_interval = 120000
        
        # Tabs erstellen
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab für Konfiguration
        self.config_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.config_tab, text="Konfiguration")
        self.setup_config_tab()
        
        # Tab für Statistik
        self.stats_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_tab, text="Statistik")
        self.setup_stats_tab()
        
        # Tab für E-Mail-Verarbeitung
        self.email_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.email_tab, text="E-Mail-Verarbeitung")
        self.setup_email_tab()
        
        # Theme-Wechsel-Button
        self.theme_var = tk.StringVar(value="light")
        self.theme_button = ttk.Button(root, text="Dark Mode", command=self.toggle_theme)
        self.theme_button.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Status-Label
        self.status_var = tk.StringVar(value="Bereit")
        self.status_label = ttk.Label(root, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
    
    def toggle_theme(self):
        if self.theme_var.get() == "light":
            self.theme.load_theme("dark")
            self.theme_var.set("dark")
            self.theme_button.config(text="Light Mode")
        else:
            self.theme.load_theme("light")
            self.theme_var.set("light")
            self.theme_button.config(text="Dark Mode")
    
    def setup_config_tab(self):
        frame = ttk.Frame(self.config_tab, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # E-Mail-Konfiguration
        ttk.Label(frame, text="E-Mail-Konfiguration", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(frame, text="E-Mail:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.email_entry = ttk.Entry(frame, width=40)
        self.email_entry.insert(0, self.config.get("email", ""))
        self.email_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(frame, text="Passwort:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.passwort_entry = ttk.Entry(frame, width=40, show="*")
        self.passwort_entry.insert(0, self.config.get("passwort", ""))
        self.passwort_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(frame, text="IMAP-Server:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.imap_entry = ttk.Entry(frame, width=40)
        self.imap_entry.insert(0, self.config.get("imap_server", "imap.gmx.net"))
        self.imap_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Vermittlungs-Konfiguration
        ttk.Label(frame, text="Vermittlungs-Konfiguration", font=("Segoe UI", 14, "bold")).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(25, 15))
        
        ttk.Label(frame, text="Erlaubte PLZ (Komma-getrennt):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.plz_entry = ttk.Entry(frame, width=40)
        self.plz_entry.insert(0, ",".join(self.config.get("plz_liste", ["13403", "13405", "13409"])))
        self.plz_entry.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(frame, text="Max. Termine pro Monat:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.max_entry = ttk.Entry(frame, width=10)
        self.max_entry.insert(0, str(self.config.get("max_termine", 5)))
        self.max_entry.grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # Akzeptierte Geburtsmonate
        ttk.Label(frame, text="Akzeptierte Geburtsmonate:", font=("Segoe UI", 12, "bold")).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(15, 10))
        
        # Checkboxen für Monate
        self.monat_vars = {}
        monate_frame = ttk.Frame(frame)
        monate_frame.grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        monatsnamen = ["Januar", "Februar", "März", "April", "Mai", "Juni",
                      "Juli", "August", "September", "Oktober", "November", "Dezember"]
        
        akzeptierte_monate = self.config.get("akzeptierte_geburtsmonate", list(range(1, 13)))
        
        for i, monat in enumerate(monatsnamen):
            monat_nr = i + 1  # Monatsnummer (1-12)
            var = tk.BooleanVar(value=monat_nr in akzeptierte_monate)
            self.monat_vars[monat_nr] = var
            
            # Berechne Zeile und Spalte für 3x4 Grid
            row = i // 4
            col = i % 4
            
            cb = ttk.Checkbutton(monate_frame, text=monat, variable=var)
            cb.grid(row=row, column=col, sticky=tk.W, padx=10, pady=2)
        
        # Speichern-Button
        save_button = ttk.Button(frame, text="Speichern", command=self.save_config)
        save_button.grid(row=9, column=0, columnspan=2, pady=20)
    
    def setup_stats_tab(self):
        frame = ttk.Frame(self.stats_tab, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Überschrift
        ttk.Label(frame, text="Angenommene Termine", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W, pady=(0, 15))
        
        # Treeview für Termine
        columns = ("monat", "anzahl")
        self.stats_tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.stats_tree.heading("monat", text="Monat")
        self.stats_tree.heading("anzahl", text="Anzahl")
        self.stats_tree.column("monat", width=150)
        self.stats_tree.column("anzahl", width=100)
        self.stats_tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.stats_tree.yview)
        self.stats_tree.configure(yscroll=scrollbar.set)
        scrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor='ne')
        
        # Details-Frame
        details_frame = ttk.LabelFrame(frame, text="Termin-Details")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Treeview für Details
        columns = ("datum", "plz", "angenommen_am")
        self.details_tree = ttk.Treeview(details_frame, columns=columns, show="headings")
        self.details_tree.heading("datum", text="Geburtstermin")
        self.details_tree.heading("plz", text="PLZ")
        self.details_tree.heading("angenommen_am", text="Angenommen am")
        self.details_tree.column("datum", width=150)
        self.details_tree.column("plz", width=100)
        self.details_tree.column("angenommen_am", width=200)
        self.details_tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbar für Details
        details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_tree.yview)
        self.details_tree.configure(yscroll=details_scrollbar.set)
        details_scrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor='ne')
        
        # Event-Handler für Monatsauswahl
        self.stats_tree.bind("<<TreeviewSelect>>", self.on_month_select)
        
        # Aktualisieren-Button
        refresh_button = ttk.Button(frame, text="Aktualisieren", command=self.refresh_stats)
        refresh_button.pack(pady=10)
        
        # Statistik laden
        self.refresh_stats()
    
    def setup_email_tab(self):
        frame = ttk.Frame(self.email_tab, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Überschrift
        ttk.Label(frame, text="E-Mail-Verarbeitung", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W, pady=(0, 15))
        
        # Status-Anzeige
        status_frame = ttk.Frame(frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(status_frame, text="Status:", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)
        self.email_status_var = tk.StringVar(value="Bereit")
        ttk.Label(status_frame, textvariable=self.email_status_var).pack(side=tk.LEFT, padx=5)
        
        # Prüfungsintervall-Anzeige
        interval_frame = ttk.Frame(frame)
        interval_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(interval_frame, text="Prüfungsintervall:", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value="2 Minuten")
        ttk.Label(interval_frame, textvariable=self.interval_var).pack(side=tk.LEFT, padx=5)
        
        # Intervall-Buttons
        interval_buttons_frame = ttk.Frame(frame)
        interval_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(interval_buttons_frame, text="10 Sekunden",
                  command=lambda: self.set_check_interval(10000)).pack(side=tk.LEFT, padx=5)
        ttk.Button(interval_buttons_frame, text="30 Sekunden",
                  command=lambda: self.set_check_interval(30000)).pack(side=tk.LEFT, padx=5)
        ttk.Button(interval_buttons_frame, text="1 Minute",
                  command=lambda: self.set_check_interval(60000)).pack(side=tk.LEFT, padx=5)
        ttk.Button(interval_buttons_frame, text="5 Minuten",
                  command=lambda: self.set_check_interval(300000)).pack(side=tk.LEFT, padx=5)
        
        # Aktuelle Monatszähler
        counter_frame = ttk.Frame(frame)
        counter_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(counter_frame, text="Termine diesen Monat:", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)
        self.counter_var = tk.StringVar(value="0/5")
        ttk.Label(counter_frame, textvariable=self.counter_var).pack(side=tk.LEFT, padx=5)
        
        # Log-Anzeige
        log_frame = ttk.LabelFrame(frame, text="Log")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=10, font=("Segoe UI", 12))
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        check_button = ttk.Button(button_frame, text="E-Mails prüfen", command=self.check_emails)
        check_button.pack(side=tk.LEFT, padx=5)
        
        clear_button = ttk.Button(button_frame, text="Log leeren", command=self.clear_log)
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # Aktualisiere Counter-Anzeige
        self.update_counter_display()
    
    def save_config(self):
        # Sammle ausgewählte Monate
        akzeptierte_monate = [monat for monat, var in self.monat_vars.items() if var.get()]
        
        self.config = {
            "email": self.email_entry.get(),
            "passwort": self.passwort_entry.get(),
            "imap_server": self.imap_entry.get(),
            "plz_liste": [plz.strip() for plz in self.plz_entry.get().split(",")],
            "max_termine": int(self.max_entry.get()),
            "akzeptierte_geburtsmonate": akzeptierte_monate
        }
        speichere_konfiguration(self.config)
        messagebox.showinfo("Gespeichert", "Einstellungen wurden gespeichert.")
        self.update_counter_display()
    
    def refresh_stats(self):
        # Lösche alte Einträge
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
        
        # Lade Counter-Daten
        counter = lade_counter()
        
        # Füge Daten hinzu
        for monat, data in sorted(counter.items(), reverse=True):
            anzahl = data.get("anzahl", 0) if isinstance(data, dict) else data
            self.stats_tree.insert("", tk.END, values=(monat, anzahl))
    
    def on_month_select(self, event):
        # Lösche alte Details
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)
        
        # Hole ausgewählten Monat
        selection = self.stats_tree.selection()
        if not selection:
            return
        
        item = self.stats_tree.item(selection[0])
        monat = item["values"][0]
        
        # Lade Counter-Daten
        counter = lade_counter()
        if monat not in counter:
            return
        
        # Prüfe, ob es sich um das alte oder neue Format handelt
        if isinstance(counter[monat], dict) and "termine" in counter[monat]:
            termine = counter[monat]["termine"]
            for termin in termine:
                self.details_tree.insert("", tk.END, values=(
                    termin.get("datum", ""),
                    termin.get("plz", ""),
                    termin.get("angenommen_am", "")
                ))
        else:
            # Altes Format, keine Details verfügbar
            self.details_tree.insert("", tk.END, values=(
                "Keine Details verfügbar", "", ""
            ))
    
    def update_counter_display(self):
        counter = lade_counter()
        monat = aktueller_monat()
        
        if monat in counter:
            if isinstance(counter[monat], dict):
                anzahl = counter[monat].get("anzahl", 0)
            else:
                anzahl = counter[monat]
        else:
            anzahl = 0
        
        max_termine = self.config.get("max_termine", 5)
        self.counter_var.set(f"{anzahl}/{max_termine}")
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
    
    def check_emails(self):
        self.email_status_var.set("Prüfe E-Mails...")
        self.log("Starte E-Mail-Prüfung...")
        
        # Konfiguration laden
        EMAIL = self.config["email"]
        PASSWORD = self.config["passwort"]
        IMAP_SERVER = self.config["imap_server"]
        ERLAUBTE_PLZ = set(self.config["plz_liste"])
        MAX_TERMINE = self.config["max_termine"]
        
        try:
            # SSL-Kontext erstellen
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Mit IMAP-Server verbinden
            self.log(f"Verbinde mit {IMAP_SERVER}...")
            mail = imapclient.IMAPClient(IMAP_SERVER, ssl=True, ssl_context=ssl_context)
            mail.login(EMAIL, PASSWORD)
            mail.select_folder("INBOX", readonly=False)
            
            # Suche nach neuen E-Mails
            self.log("Suche nach neuen Anfragen...")
            UIDs = mail.search(['UNSEEN', 'FROM', 'kleinkeole@gmail.com'])
            self.log(f"{len(UIDs)} neue Anfragen gefunden.")
            
            for uid in UIDs:
                raw_message = mail.fetch([uid], ['BODY[]', 'FLAGS'])[uid][b'BODY[]']
                message = pyzmail.PyzMessage.factory(raw_message)
                
                if not message.html_part:
                    self.log("E-Mail hat keinen HTML-Teil, überspringe...")
                    continue
                
                html = message.html_part.get_payload().decode(message.html_part.charset)
                soup = BeautifulSoup(html, 'html.parser')
                text = soup.get_text()
                
                # EGT extrahieren
                egt_match = re.search(r"Errechneter Geburtstermin: (\d{2}\.\d{2}\.\d{4})", text)
                if not egt_match:
                    self.log("Kein Geburtstermin gefunden, überspringe...")
                    continue
                egt_str = egt_match.group(1)
                egt = datetime.strptime(egt_str, "%d.%m.%Y")
                
                # PLZ extrahieren
                plz_match = re.search(r"Adresse: .+?(\d{5}) Berlin", text)
                if not plz_match:
                    self.log("Keine PLZ gefunden, überspringe...")
                    continue
                plz = plz_match.group(1)
                
                # Link extrahieren
                link = soup.find('a', string="Kontaktdaten senden")
                if not link or "href" not in link.attrs:
                    self.log("Kein Link gefunden, überspringe...")
                    continue
                url = link["href"]
                
                # Geburtsmonat extrahieren
                geburtsmonat = egt.month
                
                # Kriterien prüfen
                heute = datetime.now()
                akzeptierte_monate = self.config.get("akzeptierte_geburtsmonate", list(range(1, 13)))
                
                if (plz in ERLAUBTE_PLZ and heute <= egt <= heute.replace(year=heute.year + 1)
                        and not zu_viele_termine(MAX_TERMINE)
                        and geburtsmonat in akzeptierte_monate):
                    self.log(f"Zusage gesendet für Anfrage mit EGT {egt_str} und PLZ {plz}")
                    webbrowser.open(url)
                    inkrementiere_counter(egt_str, plz)
                    mail.set_flags([uid], ['\\Seen'])
                    
                    # Aktualisiere Counter-Anzeige
                    self.update_counter_display()
                    
                    # Aktualisiere Statistik
                    self.refresh_stats()
                else:
                    self.log(f"Anfrage nicht angenommen (EGT oder PLZ unpassend oder Limit erreicht).")
                    if plz not in ERLAUBTE_PLZ:
                        self.log(f"PLZ {plz} nicht in erlaubten PLZs: {', '.join(ERLAUBTE_PLZ)}")
                    elif heute > egt:
                        self.log(f"Geburtstermin {egt_str} liegt in der Vergangenheit")
                    elif egt > heute.replace(year=heute.year + 1):
                        self.log(f"Geburtstermin {egt_str} liegt mehr als ein Jahr in der Zukunft")
                    elif zu_viele_termine(MAX_TERMINE):
                        self.log(f"Maximale Anzahl an Terminen ({MAX_TERMINE}) für diesen Monat erreicht")
                    elif geburtsmonat not in akzeptierte_monate:
                        monatsnamen = ["Januar", "Februar", "März", "April", "Mai", "Juni",
                                      "Juli", "August", "September", "Oktober", "November", "Dezember"]
                        self.log(f"Geburtsmonat {monatsnamen[geburtsmonat-1]} wird nicht akzeptiert")
            
            mail.logout()
            self.log("E-Mail-Prüfung abgeschlossen.")
            self.email_status_var.set("Bereit")
            
        except Exception as e:
            self.log(f"Fehler: {str(e)}")
            self.email_status_var.set("Fehler")

    def set_check_interval(self, interval_ms):
        """Setzt das Intervall für die automatische E-Mail-Prüfung"""
        self.check_interval = interval_ms
        
        # Intervall-Text aktualisieren
        if interval_ms < 60000:
            seconds = interval_ms // 1000
            self.interval_var.set(f"{seconds} Sekunden")
        else:
            minutes = interval_ms // 60000
            self.interval_var.set(f"{minutes} Minute{'n' if minutes > 1 else ''}")
        
        self.log(f"Prüfungsintervall auf {self.interval_var.get()} gesetzt")
    
    def start_auto_check(self):
        """Startet die automatische E-Mail-Prüfung im eingestellten Intervall"""
        self.check_emails()
        # Plane die nächste Prüfung im eingestellten Intervall
        self.root.after(self.check_interval, self.start_auto_check)

# --- Hauptprogramm ---
def main():
    root = tk.Tk()
    app = HebammenApp(root)
    
    # Starte automatische E-Mail-Prüfung
    app.log(f"Automatische E-Mail-Prüfung alle {app.interval_var.get()} aktiviert")
    app.root.after(app.check_interval, app.start_auto_check)  # Erste Prüfung nach dem eingestellten Intervall
    
    root.mainloop()

if __name__ == "__main__":
    main()