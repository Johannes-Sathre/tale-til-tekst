# Tale til Tekst

En applikasjon som konverterer tale til tekst ved hjelp av en tastatursnarvei og Whisper-modell.

## Beskrivelse

Tale til Tekst er en Windows-applikasjon som lar deg transkribere tale til tekst ved å holde inne en tastatursnarvei. Appen bruker faster-whisper med large-v2 modellen for høykvalitets transkripsjon på norsk. Transkripsjonen limes automatisk inn der markøren befinner seg.

## Systemkrav

- **Operativsystem:** Windows 10/11
- **Python:** 3.9 eller 3.10 anbefales (Python 3.13 har kompatibilitetsproblemer)
- **RAM:** Minst 8GB, 16GB anbefales
- **Diskplass:** Minst 5GB ledig (modellen er ca. 3GB)
- **Mikrofon:** Fungerende mikrofon tilkoblet PC-en
- **CPU:** Moderne CPU med minst 4 kjerner anbefales

## Installasjonsguide

### Metode 1: Med virtuelt miljø (anbefalt)

1. Klon dette repositoriet:
```
git clone https://github.com/yourusername/tale_til_tekst.git
cd tale_til_tekst
```

2. Opprett et virtuelt miljø med Python 3.10:
```
python -m venv venv
```

3. Aktiver det virtuelle miljøet:
```
# Windows
venv\Scripts\activate
```

4. Installer avhengigheter:
```
pip install -r requirements.txt
```

5. Første gang programmet kjøres vil det laste ned Whisper-modellen (ca. 3GB) fra Hugging Face.

### Metode 2: Direkte installasjon

1. Klon dette repositoriet
2. Installer avhengigheter:
```
pip install -r requirements.txt
```

## Bruk

1. Start applikasjonen:
```
python main.py
```

2. Når programmet er startet vil du se et GUI med status og logg.
3. Velg mikrofon fra nedtrekksmenyen og juster følsomhet hvis nødvendig.
4. Hold inne `Ctrl+Alt+S` for å starte opptak mens du snakker.
5. Slipp tastekombinasjonen når du er ferdig med å snakke.
6. Transkripsjonen vil bli automatisk limt inn der markøren befinner seg.

## Funksjonalitet

- **Mikrofonvalg:** Velg mellom tilgjengelige mikrofoner
- **Lydtesting:** Test mikrofonen din før du starter opptak
- **Følsomhetsjustering:** Juster mikrofonens følsomhet med glidebryteren
- **Transkripsjon:** Transkriberer tale til tekst med korrekt norsk tegnsetting
- **Automatisk innsetting:** Limer automatisk inn teksten der markøren er

## Feilsøking

### Vanlige problemer og løsninger

#### "Feil ved lasting av Whisper-modell"
- Sjekk at du har nok diskplass (minst 5GB ledig)
- Prøv å slette `.cache/huggingface` i din hjemmemappe og kjør på nytt
- Bruk et Python-miljø med versjon 3.9 eller 3.10

#### "Invalid sample rate" feil
- Velg en annen mikrofon fra nedtrekksmenyen
- Applikasjonen vil prøve å finne en kompatibel sample rate automatisk

#### Transkripsjonen tar lang tid
- Dette er normalt; Whisper-modellen krever betydelig prosessorkraft
- Vurder å bruke en maskin med bedre spesifikasjoner
- Programmet vil ikke fryse mens den transkriberer

#### "Ingen tekst ble generert fra opptaket"
- Juster mikrofonens følsomhet (gain) høyere
- Snakk høyere og tydeligere
- Kontroller at mikrofonen fungerer med "Test mikrofon" knappen

## Begrensninger

- Programmet kjører lokalt og krever betydelige systemressurser
- Transkripsjonen kan ta tid avhengig av CPU-kraft og lengden på opptaket
- Norsk språkstøtte kommer fra large-v2 modellen, som ikke er spesifikt trent for norsk

## Bidrag

Bidrag til prosjektet er velkomne! Vennligst følg disse trinnene:
1. Fork repositoriet
2. Opprett en feature branch
3. Send en pull request

## Lisens

Dette prosjektet er lisensiert under MIT-lisensen - se [LICENSE](LICENSE) filen for detaljer. 