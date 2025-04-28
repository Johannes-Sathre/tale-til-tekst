import customtkinter as ctk  # Importerer customtkinter-biblioteket som ctk
from app_window import AppWindow  # Importerer AppWindow-klassen som vår klasse skal arve fra
from mic_handler import MicrophoneHandler  # Importerer vår nye MicrophoneHandler-klasse

class AppGUI(AppWindow):  # Definerer AppGUI-klassen som arver fra AppWindow
    """
    GUI med mikrofon valg og test funksjonalitet.
    """
    def __init__(self, app_controller=None):  # Konstruktørmetode som kjøres når et objekt lages
        # Kall parentklassens konstruktør
        super().__init__(app_controller=app_controller)  # Kaller foreldreклассens konstruktør med samme controller
        
        # Initialiser mikrofonhåndterer
        self.mic_handler = MicrophoneHandler()  # Oppretter en instans av MicrophoneHandler
        
        # Opprett GUI-elementer
        self._create_widgets()  # Kaller metoden som oppretter alle GUI-elementer
        
        # Fyll dropdown med tilgjengelige mikrofoner
        self._populate_mic_dropdown()  # Kaller metode for å fylle mikrofonlisten
    
    def _create_widgets(self):  # Metode for å opprette alle GUI-elementer
        # Hovedramme som holder alle komponenter
        self.main_frame = ctk.CTkFrame(self)  # Oppretter en ramme som skal inneholde alle komponenter
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)  # Plasserer rammen med padding og fyller tilgjengelig plass
        
        # Mikrofon-seksjon
        self.mic_selection_frame = ctk.CTkFrame(self.main_frame)  # Ramme for dropdown og testknapp
        self.mic_selection_frame.pack(fill="x", padx=10, pady=10)  # Plasserer rammen med padding
        
        self.mic_dropdown = ctk.CTkComboBox(self.mic_selection_frame, values=["Laster..."])  # Dropdown for mikrofonvalg
        self.mic_dropdown.pack(side="left", fill="x", expand=True, padx=5)  # Plasserer dropdown til venstre
        
        self.test_button = ctk.CTkButton(self.mic_selection_frame, text="Test", corner_radius=20, width=20, height=20, command=self._test_microphone)  # Rund testknapp for mikrofon
        self.test_button.pack(side="right", padx=5)  # Plasserer testknappen til høyre
        
        # Status indikator for mikrofontest
        self.mic_status = ctk.CTkLabel(self.mic_selection_frame, text="", width=10)  # Etikett for å vise teststatus
        self.mic_status.pack(side="right", padx=5)  # Plasserer statusetikett til høyre før testknappen
        
        # Skillelinje under mikrofonseksjonen
        self.separator = ctk.CTkFrame(self.main_frame, height=2, fg_color="#808080")  # Oppretter en tynn ramme som skillelinje
        self.separator.pack(fill="x", padx=10, pady=(5, 5))  # Plasserer skillelinjen med padding
        
        # Modell-seksjon
        self.model_selection_frame = ctk.CTkFrame(self.main_frame)  # Ramme for modell dropdown og last-knapp
        self.model_selection_frame.pack(fill="x", padx=10, pady=10)  # Plasserer rammen med padding
        
        self.model_dropdown = ctk.CTkComboBox(self.model_selection_frame, values=["Modell 1", "Modell 2"])  # Dropdown for modellvalg
        self.model_dropdown.pack(side="left", fill="x", expand=True, padx=5)  # Plasserer dropdown til venstre
        
        self.load_button = ctk.CTkButton(self.model_selection_frame, text="Last", corner_radius=20, width=20, height=20)  # Rund last-knapp for modell
        self.load_button.pack(side="right", padx=5)  # Plasserer last-knappen til høyre
        
        # Skillelinje under modellseksjonen
        self.separator2 = ctk.CTkFrame(self.main_frame, height=2, fg_color="#808080")  # Oppretter en tynn ramme som skillelinje
        self.separator2.pack(fill="x", padx=10, pady=(5, 5))  # Plasserer skillelinjen med padding
        
        # API-nøkkel seksjon
        self.api_frame = ctk.CTkFrame(self.main_frame)  # Ramme for API-nøkkel input
        self.api_frame.pack(fill="x", padx=10, pady=10)  # Plasserer rammen med padding
        
        self.api_label = ctk.CTkLabel(self.api_frame, text="OpenAI API-nøkkel")  # Etikett for API-nøkkel felt
        self.api_label.pack(side="left", padx=5)  # Plasserer etiketten til venstre
        
        self.api_entry = ctk.CTkEntry(self.api_frame, placeholder_text="Skriv inn API-nøkkel", show="•")  # Input-felt for API-nøkkel med skjult tekst
        self.api_entry.pack(side="right", fill="x", expand=True, padx=5)  # Plasserer input-feltet til høyre
        
        # Skillelinje under API-nøkkel seksjonen
        self.separator3 = ctk.CTkFrame(self.main_frame, height=2, fg_color="#808080")  # Oppretter en tynn ramme som skillelinje
        self.separator3.pack(fill="x", padx=10, pady=(5, 5))  # Plasserer skillelinjen med padding
        
        # Modus-valg seksjon (transkribsjon/logg)
        self.mode_frame = ctk.CTkFrame(self.main_frame)  # Ramme for modusvalg
        self.mode_frame.pack(fill="x", padx=10, pady=5)  # Plasserer rammen med padding
        
        # Variabler for radioknapp
        self.mode_var = ctk.StringVar(value="transkribsjon")  # Variabel for å holde valgt modus
        
        # Radioknapper for modusvalg
        self.transcribe_radio = ctk.CTkRadioButton(
            self.mode_frame, 
            text="Transkribsjon", 
            variable=self.mode_var, 
            value="transkribsjon"
        )  # Radioknapp for transkribsjon
        self.transcribe_radio.pack(side="left", padx=20)  # Plasserer radioknapp til venstre
        
        self.log_radio = ctk.CTkRadioButton(
            self.mode_frame, 
            text="Logg", 
            variable=self.mode_var, 
            value="logg"
        )  # Radioknapp for logg
        self.log_radio.pack(side="left", padx=20)  # Plasserer radioknapp til venstre etter transkribsjon
        
        # Output-vindu
        self.output_frame = ctk.CTkFrame(self.main_frame)  # Ramme for output-vindu
        self.output_frame.pack(fill="both", expand=True, padx=10, pady=10)  # Plasserer rammen med padding og fyller resten av plassen
        
        self.output_textbox = ctk.CTkTextbox(self.output_frame)  # Tekstområde for output med scrollbar
        self.output_textbox.pack(fill="both", expand=True)  # Fyller hele output-rammen
        self.output_textbox.configure(state="disabled")  # Gjør tekstområdet skrivebeskyttet
    
    def _populate_mic_dropdown(self):
        """Fyller dropdown-menyen med tilgjengelige mikrofoner"""
        mic_names = self.mic_handler.get_mic_names()  # Henter liste over mikrofonnavn
        if mic_names:
            self.mic_dropdown.configure(values=mic_names)  # Oppdaterer dropdown med mikrofonnavnene
            self.mic_dropdown.set(mic_names[0])  # Setter første mikrofon som standard
        else:
            self.mic_dropdown.configure(values=["Ingen mikrofoner funnet"])  # Oppdaterer dropdown hvis ingen mikrofoner
            self.mic_dropdown.set("Ingen mikrofoner funnet")  # Setter melding i dropdown
    
    def _test_microphone(self):
        """Tester valgt mikrofon og oppdaterer status"""
        self.test_button.configure(state="disabled")  # Deaktiverer testknappen under test
        self.mic_status.configure(text="Tester...", text_color="gray")  # Viser testing-status
        selected_mic = self.mic_dropdown.get()  # Henter valgt mikrofon
        # Starter mikrofontest og logger volum til output
        self.mic_handler.test_microphone(selected_mic, self._on_mic_test_complete, log_callback=self._log_volume)
    
    def _on_mic_test_complete(self, result):
        """Callback-funksjon for når mikrofontesten er ferdig"""
        # Fargekoder for resultat
        color_map = {
            "green": "#00AA00",   # Grønn farge for godt signal
            "orange": "#FFA500",  # Oransje farge for svakt signal
            "red": "#AA0000"      # Rød farge for intet signal
        }
        
        # Oppdater UI med testresultat
        self.mic_status.configure(text="●", text_color=color_map.get(result, "gray"))  # Setter statusindikator med farge
        self.test_button.configure(state="normal")  # Aktiverer testknappen igjen
    
    def _log_volume(self, text):
        """Logger volum til output-tekstboksen"""
        self.update_output(text)  # Skriver volum til output
    
    def update_output(self, text, clear=False):
        """Oppdaterer output-tekstboksen med tekst"""
        self.output_textbox.configure(state="normal")  # Gjør tekstområdet skrivbart
        
        if clear:
            self.output_textbox.delete("1.0", "end")  # Tømmer tekstområdet
            
        self.output_textbox.insert("end", text + "\n")  # Legger til tekst med linjeskift
        self.output_textbox.see("end")  # Scroller til slutten av teksten
        self.output_textbox.configure(state="disabled")  # Gjør tekstområdet skrivebeskyttet igjen


if __name__ == "__main__":
    app = AppGUI()
    app.run()
