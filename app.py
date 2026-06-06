import streamlit as st
from google import genai
from google.genai import types
import PIL.Image

st.set_page_config(page_title="Pametni Kuvar Spisak", layout="centered", page_icon="🍳")

st.title("🍳 AI Spisak za Kupovinu (Meal Prep)")
st.write("Učitajte jelovnik sa merama za 2 dana, izaberite broj osoba i preuzmite spisak za prodavnicu.")

# Unos API ključa kroz aplikaciju
api_key = st.text_input("Unesite vaš Gemini API ključ:", type="password")
st.markdown("[Kliknite ovde da uzmete besplatan API ključ](https://google.com)")

# Korisnički unos
uploaded_file = st.file_uploader("Izaberite sliku jelovnika (PNG, JPG, JPEG):", type=["jpg", "jpeg", "png"])

# Slajder za broj osoba
broj_osoba = st.slider("Za koliko OSOBA spremate ove obroke (za 2 dana)?", min_value=1, max_value=10, value=1)

# Sesija za čuvanje rezultata kako ne bi nestao pri kliku na download dugme
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
                
                # Uputstvo za AI prilagođeno tvom meal-prep sistemu
                prompt = f"""
                Analiziraj priloženu sliku jelovnika.
                
                VAŽAN KONTEKST: 
                Sastojci na slici su navedeni pod naslovom "Sastojci za dve porcije" zato što JEDNA OSOBA sprema ove obroke unapred za DVA DANA. 
                Dakle, sve mere na slici (npr. 140g brašna, 80g piletine) predstavljaju tačnu količinu koja je potrebna za JEDNU OSOBU za dva dana.
                
                Tvoj zadatak je da preračunaš i napraviš zbirni spisak namirnica za ukupno {broj_osoba} osoba koje jedu ovaj dvodnevni meni.
                
                Matematička logika:
                - Ako korisnik izabere 1 osobu, količine ostaju ISTOVETNE kao na slici (jer jedna osoba jede te dve porcije kroz dva dana).
                - Ako korisnik izabere {broj_osoba} osoba, pomnoži sve originalne količine sa tačno {broj_osoba}.
                
                Formatiraj izlaz:
                1. Na samom vrhu napiši naslov: "SPISAK ZA KUPOVINU - Meni za {broj_osoba} osoba za 2 dana".
                2. Grupiši namirnice po logičnim kategorijama iz prodavnice (Mlečni proizvodi, Povrće, Žitarice, Meso/Jaja, Ostalo).
                3. Sve količine prikaži jasno (grami, mililitri, komadi).
                4. Odgovori isključivo na srpskom jeziku u formi liste za kupovinu sa crticama (-). Nemoj koristiti markdown kućice u fajlu za preuzimanje kako bi tekst izgledao čisto na telefonu.
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[image, prompt]
                )
                
                # Čuvanje rezultata u sesiju
                st.session_state.spisak_tekst = response.text
                st.success("Spisak je uspešno generisan!")
                
            except Exception as e:
                st.error(f"Došlo je do greške: {e}")

# Prikaz rezultata i opcija za preuzimanje ako spisak postoji
if st.session_state.spisak_tekst:
    st.subheader(f"🛒 Spisak za kupovinu za {broj_osoba} osoba (za 2 dana):")
    st.text(st.session_state.spisak_tekst)
    
    # Dugme za preuzimanje .txt fajla
    st.download_button(
        label="📥 Preuzmi spisak kao tekstualni fajl",
        data=st.session_state.spisak_tekst,
        file_name=f"spisak_za_kupovinu_{broj_osoba}_osoba.txt",
        mime="text/plain"
    )
