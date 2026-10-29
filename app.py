import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Konfigurácia
# ---------------------------------------------------------------------------
st.set_page_config(page_title="AutoServis Pro – dopyt", page_icon="🔧")

# Sem doplňte URL vášho Make.com webhooku.
# Odporúčanie: nastavte ju ako premennú prostredia alebo v .streamlit/secrets.toml
# (kľúč MAKE_WEBHOOK_URL), aby nebola priamo v kóde.
WEBHOOK_URL_PREDVOLENA = "https://hook.eu1.make.com/1nzc4cm97lmstgqwpbt7i5h5cbn68f3u"

def nacitaj_webhook_url() -> str:
    try:
        if "MAKE_WEBHOOK_URL" in st.secrets:
            return st.secrets["MAKE_WEBHOOK_URL"]
    except Exception:
        pass
    return os.getenv("MAKE_WEBHOOK_URL", WEBHOOK_URL_PREDVOLENA)


WEBHOOK_URL = nacitaj_webhook_url()
WEBHOOK_NASTAVENY = "VASA_WEBHOOK_URL" not in WEBHOOK_URL

SLUZBY = [
    "Prezutie pneumatík",
    "Výmena oleja",
    "Diagnostika",
    "Geometria",
    "Brzdy",
    "Klimatizácia",
    "Iné",
]


# ---------------------------------------------------------------------------
# Pomocné funkcie
# ---------------------------------------------------------------------------
def telefon_je_platny(telefon: str) -> bool:
    cislice = re.sub(r"[\s\-/()]", "", telefon)
    return bool(re.fullmatch(r"\+?\d{9,15}", cislice))


def odosli_dopyt(data: dict) -> tuple[bool, str]:
    """Odošle dáta na Make.com webhook. Vráti (úspech, správa)."""
    try:
        odpoved = requests.post(WEBHOOK_URL, json=data, timeout=10)
        odpoved.raise_for_status()
        return True, ""
    except requests.exceptions.Timeout:
        return False, "Server neodpovedal včas. Skúste to prosím znova."
    except requests.exceptions.ConnectionError:
        return False, "Nepodarilo sa pripojiť k webhooku. Skontrolujte URL a internet."
    except requests.exceptions.HTTPError as e:
        return False, f"Webhook vrátil chybu: {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Neočakávaná chyba: {e}"


# ---------------------------------------------------------------------------
# Bočný panel
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("🔧 AutoServis Pro")

    st.subheader("📡 Stav pripojenia")
    if WEBHOOK_NASTAVENY:
        st.warning("Webhook nie je nastavený. Doplňte `MAKE_WEBHOOK_URL`.")
    else:
        st.success("Webhook je nastavený.")

    st.subheader("📝 Ako to funguje")
    st.markdown(
        "1. Vyplňte formulár.\n"
        "2. Kliknite na **Odoslať dopyt**.\n"
        "3. Údaje sa odošlú do systému servisu.\n"
        "4. Ozveme sa vám čo najskôr."
    )

    st.subheader("⚙️ Nastavenie webhooku")
    st.code('# .streamlit/secrets.toml\nMAKE_WEBHOOK_URL = "https://hook.eu1.make.com/..."', language="toml")


# ---------------------------------------------------------------------------
# Formulár
# ---------------------------------------------------------------------------
st.title("🚗 Dopyt pre autoservis")
st.write("Vyplňte formulár a my sa vám ozveme s ponukou.")

with st.form("formular_dopyt", clear_on_submit=False):
    meno = st.text_input("Meno *", placeholder="Ján Novák")
    telefon = st.text_input("Telefón *", placeholder="+421 900 123 456")
    auto = st.text_input("Auto *", placeholder="napr. Škoda Octavia 2.0 TDI, 2015")
    sluzba = st.selectbox("Výber služby *", SLUZBY)
    poznamka = st.text_area("Poznámka", placeholder="Doplňujúce informácie, preferovaný termín…")

    odoslat = st.form_submit_button("Odoslať dopyt", type="primary")

if odoslat:
    chyby = []
    if not meno.strip():
        chyby.append("Zadajte meno.")
    if not telefon.strip():
        chyby.append("Zadajte telefón.")
    elif not telefon_je_platny(telefon):
        chyby.append("Telefón nemá správny formát.")
    if not auto.strip():
        chyby.append("Zadajte auto.")

    if chyby:
        for ch in chyby:
            st.error(ch)
    elif WEBHOOK_NASTAVENY is False and False:
        pass
    else:
        data = {
            "meno": meno.strip(),
            "telefon": telefon.strip(),
            "auto": auto.strip(),
            "sluzba": sluzba,
            "poznamka": poznamka.strip(),
            "cas_odoslania": datetime.now(ZoneInfo("Europe/Bratislava")).isoformat(timespec="seconds"),
        }

        with st.spinner("Odosielam dopyt…"):
            ok, sprava = odosli_dopyt(data)

        if ok:
            st.success("✅ Váš dopyt bol úspešne odoslaný. Čoskoro sa vám ozveme!")
        else:
            st.error(f"❌ Dopyt sa nepodarilo odoslať. {sprava}")
