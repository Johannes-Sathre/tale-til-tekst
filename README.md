# Tale til Tekst

Applikasjon som konverterer tale til tekst ved hjelp av Whisper-modellen.

## Funksjoner

- **Enkel transkribering**: Hold inne en tastatursnarvei (standard: Ctrl+Alt+S) for å ta opp tale og få den transkribert til tekst
- **Automatisk kopering**: Transkripsjonen kopieres automatisk til utklippstavlen og limes inn
- **Moderne grensesnitt**: Et mørkt, moderne grensesnitt som åpner seg over systemstatusfeltet
- **System tray-integrasjon**: Kjører i bakgrunnen med et ikon i systemstatusfeltet
- **Mikrofontesting**: Test mikrofonen din før du begynner å transkribere
- **Justerbar følsomhet**: Juster mikrofonens følsomhet etter behov

## Installasjon

1. Klone eller last ned prosjektet
2. Installer avhengighetene:
   ```
   pip install faster-whisper sounddevice numpy pillow pystray keyboard pyperclip
   ```
3. Kjør applikasjonen:
   ```
   python app.py
   ```

## Bruk

1. Start applikasjonen
2. Velg mikrofon fra nedtrekkslisten
3. Hold inne Ctrl+Alt+S for å ta opp tale
4. Slipp tastene når du er ferdig med å snakke
5. Transkripsjonen vil automatisk bli kopiert til utklippstavlen og limt inn der markøren står

## Systemkrav

- Python 3.7 eller høyere
- Minimum 2GB RAM
- Windows 10 eller nyere

## Nylige forbedringer

- Moderne brukergrensesnitt med mørkt tema
- Tilpassbare ikoner
- Flyttbart vindu
- System tray-integrasjon
- Forbedret mikrofon-håndtering
- Moderne innstillingspanel (kommer snart)

## Hovedfunksjoner

- **Rask og presis transkripsjon** med Whisper Large-v2 modellen
- **Norsk språkstøtte** for nøyaktig transkribering av norsk tale
- **System tray-funksjonalitet** for å kjøre applikasjonen i bakgrunnen
- **Justerbar lydfølsomhet** for å optimalisere lydopptak fra mikrofonen
- **Bakgrunnsoperasjon** - hold inne en tastekombinasjon for å ta opp når som helst
- **Automatisk innliming** av transkribert tekst
- **Valg av mikrofon** hvis du har flere inngangsenheter

## Programstruktur

Applikasjonen er delt inn i flere moduler:

- `app.py` - Hovedfilen som starter applikasjonen
- `gui.py` - Brukergrensesnittkode og system tray-funksjonalitet
- `recorder.py` - Håndterer lydopptak og tastatursnarveier
- `transcriber.py` - Håndterer transkripsjon av lyd til tekst med Whisper-modellen

## Feilsøking

- **Mikrofonen fungerer ikke**: Prøv å velge en annen mikrofon fra nedtrekkslisten
- **Teksten gjenkjennes ikke korrekt**: Juster lydfølsomheten med glidebryteren
- **Applikasjonen starter ikke**: Sjekk at du har Python 3.9+ installert og at installasjonsskriptet ble kjørt uten feil
- **Høyt minnebruk**: Dette er normalt da Whisper-modellen krever mye minne. Lukk andre programmer hvis nødvendig.

## Lisens

Dette prosjektet er lisensiert under MIT-lisensen - se [LICENSE](LICENSE) filen for detaljer.

## Anerkjennelser

- [OpenAI Whisper](https://github.com/openai/whisper) - Tale til tekst-modellen
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) - Optimalisert implementering av Whisper
- [SoundDevice](https://github.com/spatialaudio/python-sounddevice) - Lydopptaksbibliotek
- [Keyboard](https://github.com/boppreh/keyboard) - Tastaturkontrollbibliotek
- [Pystray](https://github.com/moses-palmer/pystray) - System tray-funksjonalitet 