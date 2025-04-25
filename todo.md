# Tale til Tekst - Todo Liste

## Prosjektoppsett
- [x] Opprett requirements.txt fil med alle nødvendige pakker
- [x] Sett opp grunnleggende prosjektstruktur
- [x] Test at alle avhengigheter kan installeres korrekt

## Kjernekomponenter
- [x] Implementer global tastatursnavei med keyboard biblioteket
- [x] Lag logikk for å detektere når snarveien trykkes og slippes
- [x] Implementer lydopptak med sounddevice (16kHz, mono)
- [x] Lagre lydopptak midlertidig til fil
- [x] Last inn NbAiLab/nb-whisper-large modellen med faster-whisper
- [x] Konfigurer modellen (compute_type="int8", device="cpu", language="no")
- [x] Implementer transkripsjonsfunksjonalitet
- [x] Kjør transkripsjon i separat tråd for å unngå frysing
- [x] Kopier transkribert tekst til utklippstavle med pyperclip
- [x] Lim inn tekst der markøren befinner seg med keyboard
- [x] Implementer opprydding av midlertidige lydfiler

## Brukergrensesnitt
- [ ] (Valgfritt) Opprett systembrett-ikon for applikasjonen
- [x] (Valgfritt) Lag et lite vindu som viser "Opptak pågår..."

## Testing og feilsøking
- [x] Test opptak med forskjellige mikrofoner
- [x] Test transkribering med ulike lengder på opptak
- [x] Test innsetting av tekst i forskjellige programmer
- [x] Kontroller at opprydding av midlertidige filer fungerer korrekt
- [x] Verifiser at applikasjonen fungerer uten internettilkobling

## Optimalisering
- [x] Optimaliser lasting av modell
- [x] Forbedre responsivitet
- [x] Reduser ressursbruk

## Høy prioritet
- [X] Implementere system tray-funksjonalitet
- [X] Refaktorere kode i moduler for bedre vedlikeholdbarhet
- [ ] Implementere personlige brukerinnstillinger (lagres mellom sesjoner)
- [ ] Legge til oppstart ved Windows-oppstart alternativ

## Medium prioritet
- [ ] Legge til mulighet for å endre tastatursnarvei
- [ ] Implementere dynamisk modellvalg (small, medium, large)
- [ ] Legge til støtte for flere språk
- [ ] Legge til visuell indikasjon på lydnivå under opptak
- [ ] Forbedre error handling for edge-cases

## Lav prioritet
- [ ] Implementere auto-oppdateringsfunksjonalitet
- [ ] Legge til mulighet for å transkribere lokale lydfiler
- [ ] Implementere kontinuerlig transkribering (ikke bare ved tastekombinasjon)
- [ ] Legge til mørkt tema
- [ ] Implementere eksport av transkripsjonslogg

## Utført
- [X] Grunnleggende opptaksfunksjonalitet
- [X] Integrasjon med faster-whisper
- [X] Mikrofontesting
- [X] Justering av lydfølsomhet
- [X] GUI med statusindikasjon
- [X] Valg av mikrofoninngang
- [X] Transkripsjon med norsk språkvalg
- [X] Automatisk innliming av transkripsjonstekst
- [X] System tray-funksjonalitet
- [X] Modulbasert kodestruktur 