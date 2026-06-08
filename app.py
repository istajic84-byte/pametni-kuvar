import streamlit as st
from google import genai
from google.genai import types
import PIL.Image

st.set_page_config(page_title="Pametni Kuvar Spisak", layout="centered", page_icon="🍳")

# --- CSS STIL ZA LEPŠU CHECK LISTU ---
st.markdown("""
<style>
    div[data-testid="stCheckbox"] p:has(~ label input:checked),
    div[data-testid="stCheckbox"] label:has(input:checked) p {
        text-decoration: line-through !important;
        color: #888888 !important;
        opacity: 0.6;
    }
</style>
""", unsafe_allow_html=True)

st.title("🍳 Spisak za Kupovinu (Meal Prep)")
st.write("Učitajte jelovnik, štiklirajte namirnice koje već imate ili ste kupili, i preuzmite čist spisak za Notes.")

# Učitavanje ključa iz Streamlit Secrets-a na serveru
api_key = st.secrets["GEMINI_KEY"]

uploaded_file = st.file_uploader("Izaberite sliku jelovnika (PNG, JPG, JPEG):", type=["jpg", "jpeg", "png"])
broj_osoba = st.slider("Za koliko OSOBA spremate ove obroke (za 2 dana)?", min_value=1, max_value=10, value=1)

if "spisak_tekst" not in st.session_state:
    st.session_state.spisak_tekst = ""

if st.button("Generiši spisak za kupovinu"):
    if not uploaded_file:
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

# Prikaz čiste interaktivne check liste i filtriranje za preuzimanje
if st.session_state.spisak_tekst:
    st.subheader(f"🛒 Štiklirajte ono što NE ŽELITE u konačnom spisku:")
    
    linije = st.session_state.spisak_tekst.split("\n")
    
    # Prvo pravimo rečnik u koji ćemo smestiti strukturu spiska
    struktura_spiska = []
    
    for i, linija in enumerate(linije):
        linija_clean = linija.strip()
        if not linija_clean:
            continue
            
        if "Kategorija:" in linija_clean or linija_clean.startswith("###") or linija_clean.isupper():
            prikaz_kategorije = linija_clean.replace("Kategorija:", "").strip("# ")
            st.markdown(f"### 📦 {prikaz_kategorije}")
            struktura_spiska.append({"tip": "kategorija", "tekst": prikaz_kategorije.upper()})
            
        elif "SPISAK ZA KUPOVINU" in linija_clean:
            st.info(linija_clean)
            struktura_spiska.append({"tip": "naslov", "tekst": linija_clean})
            
        elif linija_clean.startswith("-") or linija_clean.startswith("*"):
            namirnica = linija_clean.lstrip("-* ").strip()
            
            # Prikazujemo checkbox na ekranu i pamtimo da li ga je korisnik kliknuo
            is_checked = st.checkbox(namirnica, key=f"item_{i}")
            
            # Ubacujemo u našu strukturu informaciju o namirnici i njenom stanju kućice
            struktura_spiska.append({"tip": "namirnica", "tekst": namirnica, "kupljeno": is_checked})
        else:
            st.write(linija_clean)
            struktura_spiska.append({"tip": "tekst", "tekst": linija_clean})
            
    # --- LOGIKA ZA FILTRIRANJE SPISKA ZA NOTES ---
    spisak_za_notes = []
    trenutna_kategorija = None
    ima_namirnica_u_kategoriji = False
    
    for stavka in struktura_spiska:
        if stavka["tip"] == "naslov":
            spisak_za_notes.append(stavka["tekst"])
            
        elif stavka["tip"] == "kategorija":
            # Pamtimo kategoriju, ali je ne upisujemo odmah dok ne vidimo da li ima nekupljenih namirnica u njoj
            trenutna_kategorija = f"\n📦 {stavka['tekst']}:"
            ima_namirnica_u_kategoriji = False
            
        elif stavka["tip"] == "namirnica":
            # KLJUČNA STVAR: Upisujemo u fajl SAMO ako kućica NIJE štiklirana (!stavka["kupljeno"])
            if not stavka["kupljeno"]:
                if trenutna_kategorija and not ima_namirnica_u_kategoriji:
                    spisak_za_notes.append(trenutna_kategorija)
                    ima_namirnica_u_kategoriji = True
                spisak_za_notes.append(f"- {stavka['tekst']}")
                
        elif stavka["tip"] == "tekst" and not stavka["tekst"].startswith("-"):
            spisak_za_notes.append(stavka["tekst"])

    st.markdown("---")
    
    # Spajamo samo preostale (neštiklirane) stavke u tekst
    konacan_tekst_za_notes = "\n".join(spisak_za_notes)
    
    st.download_button(
        label="📥 Preuzmi preostale namirnice za Notes",
        data=konacan_tekst_za_notes,
        file_name=f"preostale_namirnice_{broj_osoba}_osoba.txt",
        mime="text/plain"
    )
