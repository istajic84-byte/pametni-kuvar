import streamlit as st
from google import genai
from google.genai import types
import PIL.Image

st.set_page_config(page_title="Pametni Kuvar Spisak", layout="centered", page_icon="🍳")

# --- CSS STIL ZA LEPŠU CHECK LISTU ---
# Ovaj kod tera telefon da posivi i precrta tekst ČIM se kućica štiklira
st.markdown("""
<style>
    /* Traži svaku kućicu koja je štiklirana i menja izgled njenog teksta */
    div[data-testid="stCheckbox"] p:has(~ label input:checked),
    div[data-testid="stCheckbox"] label:has(input:checked) p {
        text-decoration: line-through !important;
        color: #888888 !important;
        opacity: 0.6;
    }
</style>
""", unsafe_allow_html=True)

st.title("🍳 Spisak za Kupovinu (Meal Prep)")
st.write("Učitajte jelovnik sa merama za 2 dana, izaberite broj osoba i upravljajte jednostavnom check listom.")

# Unos API ključa kroz aplikaciju
api_key = st.text_input("Unesite vaš Gemini API ključ:", type="password")
st.markdown("[Kliknite ovde da uzmete besplatan API ključ](https://google.com)")

# Korisnički unos
uploaded_file = st.file_uploader("Izaberite sliku jelovnika (PNG, JPG, JPEG):", type=["jpg", "jpeg", "png"])

# Slajder za broj osoba
broj_osoba = st.slider("Za koliko OSOBA spremate ove obroke (za 2 dana)?", min_value=1, max_value=10, value=1)

# Sesija za čuvanje rezultata
if "spisak_tekst" not in st.session_state:
    st.session_state.spisak_tekst = ""

if st.button("Generiši spisak za kupovinu"):
    if not api_key:
        st.error("Molimo vas da prvo unesete Gemini API ključ.")
    elif not uploaded_file:
        st.error("Molimo vas da učitate sliku jelovnika.")
    else:
        with st.spinner("AI računa količine za izabrani broj osoba..."):
            try:
                client = genai.Client(api_key=api_key)
                image = PIL.Image.open(uploaded_file)
                
                prompt = f"""
                Analiziraj priloženu sliku jelovnika.
                
                VAŽAN KONTEKST: 
                Sastojci na slici su navedeni pod naslovom "Sastojci za dve porcije" zato što JEDNA OSOBA sprema ove obroke unapred za DVA DANA. 
                Dakle, sve mere na slici (npr. 140g brašna, 80g piletine) predstavljaju tačnu količinu koja je potrebna za JEDNU OSOBU za dva dana.
                
                Tvoj zadatak je da preračunaš i napraviš zbirni spisak namirnica za ukupno {broj_osoba} osoba koje jedu ovaj dvodnevni meni.
                
                Matematička logika:
                - Ako korisnik izabere 1 osobu, količine ostaju ISTOVETNE kao na slici.
                - Ako korisnik izabere {broj_osoba} osoba, pomnoži sve originalne količine sa tačno {broj_osoba}.
                
                Formatiraj izlaz:
                1. Na samom vrhu napiši naslov: "SPISAK ZA KUPOVINU - Meni za {broj_osoba} osoba za 2 dana".
                2. Grupiši namirnice po logičnim kategorijama iz prodavnice (Mlečni proizvodi, Povrće, Žitarice, Meso/Jaja, Ostalo). Kategorije moraju počinjati rečju 'Kategorija:' (npr. Kategorija: Povrće).
                3. Svaka namirnica MORA biti u novom redu i počinjati sa crticom (npr. - 280g brašna). Nemoj koristiti markdown kućice.
                4. Odgovori isključivo na srpskom jeziku.
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[image, prompt]
                )
                
                st.session_state.spisak_tekst = response.text
                st.success("Spisak je uspešno generisan!")
                
            except Exception as e:
                st.error(f"Došlo je do greške: {e}")

# Prikaz čiste interaktivne check liste
if st.session_state.spisak_tekst:
    st.subheader(f"🛒 Vaša check lista za prodavnicu:")
    
    linije = st.session_state.spisak_tekst.split("\n")
    
    for i, linija in enumerate(linije):
        linija_clean = linija.strip()
        if not linija_clean:
            continue
            
        # Ako je linija naslov kategorije
        if "Kategorija:" in linija_clean or linija_clean.startswith("###") or linija_clean.isupper():
            prikaz_kategorije = linija_clean.replace("Kategorija:", "").strip("# ")
            st.markdown(f"### 📦 {prikaz_kategorije}")
        # Ako je linija naslov na samom vrhu
        elif "SPISAK ZA KUPOVINU" in linija_clean:
            st.info(linija_clean)
        # Ako je linija namirnica (samo pravimo običan checkbox bez dupliranja teksta ispod)
        elif linija_clean.startswith("-") or linija_clean.startswith("*"):
            namirnica = linija_clean.lstrip("-* ").strip()
            st.checkbox(namirnica, key=f"item_{i}")
        else:
            st.write(linija_clean)
            
    st.markdown("---")
    st.download_button(
        label="📥 Preuzmi ceo spisak kao običan tekst",
        data=st.session_state.spisak_tekst,
        file_name=f"spisak_za_kupovinu_{broj_osoba}_osoba.txt",
        mime="text/plain"
    )
