import imapclient
import pyzmail
from bs4 import BeautifulSoup
from datetime import datetime
import re
import webbrowser
import json
import os
import ssl

# --- Konfiguration ---
EMAIL = "ole.kleinke@gmx.de"
PASSWORD = "Penis54321!"
IMAP_SERVER = "imap.gmx.net"
ERLAUBTE_PLZ = {"13403", "13405", "13409"}
MAX_TERMINE = 5
MONATSZÄHLER_DATEI = "annahmen_counter.json"

# --- Hilfsfunktionen ---
def lade_counter():
    if not os.path.exists(MONATSZÄHLER_DATEI):
        return {}
    with open(MONATSZÄHLER_DATEI, "r") as f:
        return json.load(f)

def speichere_counter(counter):
    with open(MONATSZÄHLER_DATEI, "w") as f:
        json.dump(counter, f)

def aktueller_monat():
    return datetime.now().strftime("%Y-%m")

def inkrementiere_counter():
    counter = lade_counter()
    monat = aktueller_monat()
    counter[monat] = counter.get(monat, 0) + 1
    speichere_counter(counter)

def zu_viele_termine():
    counter = lade_counter()
    return counter.get(aktueller_monat(), 0) >= MAX_TERMINE

# --- Verbindung mit dem E-Mail-Konto ---
# Create a custom SSL context that doesn't verify certificates
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Use the custom SSL context when connecting
mail = imapclient.IMAPClient(IMAP_SERVER, ssl=True, ssl_context=ssl_context)
mail.login(EMAIL, PASSWORD)
mail.select_folder("INBOX", readonly=False)

# --- Suche nach neuen passenden E-Mails ---
UIDs = mail.search(['UNSEEN', 'FROM', 'kleinkeole@gmail.com'])
print(f"{len(UIDs)} neue Anfragen gefunden.")

for uid in UIDs:
    raw_message = mail.fetch([uid], ['BODY[]', 'FLAGS'])[uid][b'BODY[]']
    message = pyzmail.PyzMessage.factory(raw_message)
    
    if not message.html_part:
        continue
    
    html = message.html_part.get_payload().decode(message.html_part.charset)
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()

    # --- EGT extrahieren ---
    egt_match = re.search(r"Errechneter Geburtstermin: (\d{2}\.\d{2}\.\d{4})", text)
    if not egt_match:
        continue
    egt_str = egt_match.group(1)
    egt = datetime.strptime(egt_str, "%d.%m.%Y")

    # --- PLZ extrahieren ---
    plz_match = re.search(r"Adresse: .+?(\d{5}) Berlin", text)
    if not plz_match:
        continue
    plz = plz_match.group(1)

    # --- Link extrahieren ---
    link = soup.find('a', string="Kontaktdaten senden")
    if not link or "href" not in link.attrs:
        continue
    url = link["href"]

    # --- Kriterien prüfen ---
    heute = datetime.now()
    if (plz in ERLAUBTE_PLZ and heute <= egt <= heute.replace(year=heute.year + 1)
            and not zu_viele_termine()):
        print(f"Zusage gesendet für Anfrage mit EGT {egt_str} und PLZ {plz}")
        webbrowser.open(url)
        inkrementiere_counter()
        # Als gelesen markieren
        mail.set_flags([uid], ['\\Seen'])
    else:
        print(f"Anfrage nicht angenommen (EGT oder PLZ unpassend oder Limit erreicht).")

mail.logout()