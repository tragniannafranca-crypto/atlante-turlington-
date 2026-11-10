from pathlib import Path
import html

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "Atlante_Turlington_30.xlsx"
IMAGE_DIR = ROOT / "immagini"

st.set_page_config(
    page_title="Atlante Turlington",
    page_icon="🧥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #f7f4f0; color: #252120; }
    [data-testid="stHeader"] { background: rgba(247,244,240,0.9); }
    .block-container { max-width: 1500px; padding-top: 2.2rem; }
    h1, h2, h3 { color: #272020; letter-spacing: -0.025em; }
    .eyebrow { color: #8a6a5a; font-size: 0.78rem; letter-spacing: .18em;
               font-weight: 700; text-transform: uppercase; }
    .intro { color: #756b67; font-size: 1.05rem; margin-top: -.4rem; }
    div[data-testid="stMetric"] { background: #fff; border: 1px solid #e8dfd7;
        padding: 14px 18px; border-radius: 12px; }
    div.stButton > button { border-radius: 7px; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE, sheet_name="Atlante", dtype={"SKU": str})
    required = {
        "Modello", "SKU", "Costruzione", "Territorio", "Famiglia materiale",
        "Trattamento visivo", "Colore", "Prezzo (€)", "Chiave foto (SKU)",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError("Colonne mancanti nell'Excel: " + ", ".join(sorted(missing)))
    for column in [
        "Modello", "SKU", "Costruzione", "Territorio", "Famiglia materiale",
        "Trattamento visivo", "Colore", "Chiave foto (SKU)",
    ]:
        df[column] = df[column].fillna("").astype(str).str.strip()
    df["Prezzo (€)"] = pd.to_numeric(df["Prezzo (€)"], errors="coerce")
    return df


def euro(value):
    if pd.isna(value):
        return "Prezzo non disponibile"
    return "€" + f"{value:,.0f}".replace(",", ".")


def photo_for(row):
    key = row["Chiave foto (SKU)"] or row["SKU"]
    candidate = IMAGE_DIR / f"{key}.png"
    return candidate if candidate.is_file() else None


try:
    data = load_data()
except Exception as exc:
    st.error(f"Non riesco a leggere l’Excel: {exc}")
    st.stop()

territories = sorted(x for x in data["Territorio"].unique() if x)
constructions = sorted(x for x in data["Costruzione"].unique() if x)
materials = sorted(x for x in data["Famiglia materiale"].unique() if x)
treatments = sorted(x for x in data["Trattamento visivo"].unique() if x)

st.markdown('<div class="eyebrow">Dolce & Gabbana · product atlas</div>', unsafe_allow_html=True)
st.title("Turlington: 30 espressioni")
st.markdown(
    '<div class="intro">Esplora come una stessa famiglia di giacche cambia attraverso costruzione, materiali e dettagli visivi.</div>',
    unsafe_allow_html=True,
)
st.write("")

summary = st.columns(3)
summary[0].metric("Modelli nel campione", len(data))
summary[1].metric("Territori di prodotto", len(territories))
summary[2].metric("SKU con foto", int(sum(photo_for(row) is not None for _, row in data.iterrows())))

with st.sidebar:
    st.markdown("## Esplora il campione")
    territory_filter = st.selectbox("Territorio", ["Tutti"] + territories, key="territorio_filter")
    construction_filter = st.selectbox("Costruzione", ["Tutte"] + constructions)
    material_filter = st.selectbox("Famiglia materiale", ["Tutte"] + materials)
    treatment_filter = st.selectbox("Trattamento visivo", ["Tutti"] + treatments)
    search = st.text_input("Cerca modello o SKU", placeholder="Es. velluto, F29…")
    st.caption("I filtri aggiornano la galleria in tempo reale.")

st.markdown("### I territori della Turlington")
territory_cols = st.columns(max(1, len(territories)))
for col, territory in zip(territory_cols, territories):
    count = int((data["Territorio"] == territory).sum())
    with col:
        st.markdown(f"**{html.escape(territory)}**  ·  {count} modelli")
        if st.button("Esplora", key="territorio_" + territory):
            st.session_state["territorio_filter"] = territory
            st.rerun()

filtered = data.copy()
if territory_filter != "Tutti":
    filtered = filtered[filtered["Territorio"] == territory_filter]
if construction_filter != "Tutte":
    filtered = filtered[filtered["Costruzione"] == construction_filter]
if material_filter != "Tutte":
    filtered = filtered[filtered["Famiglia materiale"] == material_filter]
if treatment_filter != "Tutti":
    filtered = filtered[filtered["Trattamento visivo"] == treatment_filter]
if search.strip():
    query = search.strip().casefold()
    filtered = filtered[
        filtered["Modello"].str.casefold().str.contains(query, na=False)
        | filtered["SKU"].str.casefold().str.contains(query, na=False)
    ]

st.divider()
st.markdown(f"### Galleria · {len(filtered)} giacche")

selected_sku = st.session_state.get("selected_sku")
selected = data[data["SKU"] == selected_sku]
if not selected.empty:
    row = selected.iloc[0]
    st.markdown("#### Scheda selezionata")
    detail_left, detail_right = st.columns([1, 1])
    with detail_left:
        image_path = photo_for(row)
        if image_path:
            st.image(str(image_path), use_container_width=True)
        else:
            st.warning("Foto non trovata per lo SKU " + row["SKU"])
    with detail_right:
        st.subheader(row["Modello"].title())
        st.caption("SKU " + row["SKU"])
        st.metric("Prezzo", euro(row["Prezzo (€)"]))
        detail_fields = [
            ("Territorio", "Territorio"),
            ("Costruzione", "Costruzione"),
            ("Famiglia materiale", "Famiglia materiale"),
            ("Trattamento visivo", "Trattamento visivo"),
            ("Colore", "Colore"),
        ]
        for label, field in detail_fields:
            st.markdown(f"**{label}:** {row[field] or 'Non indicato'}")
        if "Fonte ufficiale" in row and row["Fonte ufficiale"]:
            st.link_button("Apri la scheda Dolce&Gabbana", row["Fonte ufficiale"])
    if st.button("Chiudi scheda", key="close_detail"):
        del st.session_state["selected_sku"]
        st.rerun()

if filtered.empty:
    st.info("Nessuna giacca corrisponde ai filtri scelti. Prova a rimuoverne qualcuno.")
else:
    products = filtered.to_dict(orient="records")
    for start in range(0, len(products), 3):
        cols = st.columns(3, gap="large")
        for col, product in zip(cols, products[start : start + 3]):
            with col:
                with st.container(border=True):
                    image_path = photo_for(product)
                    if image_path:
                        st.image(str(image_path), use_container_width=True)
                    else:
                        st.warning("Foto mancante · " + product["SKU"])
                    st.markdown("**" + product["Modello"].title() + "**")
                    st.caption(product["Territorio"] + " · " + product["Costruzione"])
                    st.write(product["Famiglia materiale"] + " · " + product["Trattamento visivo"])
                    st.markdown("**" + euro(product["Prezzo (€)"]) + "**")
                    if st.button("Apri scheda", key="details_" + product["SKU"]):
                        st.session_state["selected_sku"] = product["SKU"]
                        st.rerun()

st.caption("Classificazioni e prezzi sono riportati dal file Excel del campione.")
