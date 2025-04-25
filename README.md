# Tale til Tekst

En norsk applikasjon som konverterer tale til tekst ved å bruke [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) modellen. Hold inne `Ctrl+Alt+S`-tastekombinasjonen for å ta opp tale, og når du slipper tasten, vil opptaket transkriberes automatisk til tekst og limes inn.

## Hovedfunksjoner

- **Rask og presis transkripsjon** med Whisper Large-v2 modellen
- **Norsk språkstøtte** for nøyaktig transkribering av norsk tale
- **System tray-funksjonalitet** for å kjøre applikasjonen i bakgrunnen
- **Justerbar lydfølsomhet** for å optimalisere lydopptak fra mikrofonen
- **Bakgrunnsoperasjon** - hold inne en tastekombinasjon for å ta opp når som helst
- **Automatisk innliming** av transkribert tekst
- **Valg av mikrofon** hvis du har flere inngangsenheter

## Systemkrav

- Windows 10/11
- Python 3.9 eller nyere
- Mikrofon
- Minimum 8GB RAM for optimal ytelse

## Installasjon

1. **Klon eller last ned** dette repositoryet
2. **Kjør installasjonsskriptet**: 
   ```
   install.bat
   ```
   Dette vil opprette et virtuelt Python-miljø og installere alle nødvendige avhengigheter.

## Bruk

1. **Start applikasjonen**:
   ```
   start.bat
   ```

2. **Ta opp tale**:
   - Hold inne `Ctrl+Alt+S` mens du snakker
   - Slipp tasten når du er ferdig
   - Teksten vil automatisk transkriberes og limes inn der markøren er plassert

3. **Juster innstillinger** i applikasjonsvinduet:
   - Velg mikrofon
   - Juster lydfølsomhet
   - Se transkriberingsloggen

4. **Bruk system tray-funksjonalitet**:
   - Minimer applikasjonen til system tray ved å klikke på "Minimer til systemfelt"-knappen
   - Høyreklikk på ikonet i systemfeltet for alternativer
   - Applikasjonen fortsetter å fungere i bakgrunnen

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