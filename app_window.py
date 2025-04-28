import customtkinter as ctk  # Importerer customtkinter-biblioteket som ctk
from screeninfo import get_monitors  # Importerer get_monitors fra screeninfo for å få informasjon om skjermer

class AppWindow(ctk.CTk):  # Definerer AppWindow-klassen som arver fra CTk-klassen
    def __init__(self, title="Tale til tekst", width=450, height=700, app_controller=None):  # Konstruktørmetode med standardverdier
        super().__init__()  # Kaller foreldreклассens konstruktør
        self.app_controller = app_controller  # Lagrer app_controller for senere bruk
        self.title(title)  # Setter tittel på vinduet
        self.geometry(f"{width}x{height}")  # Setter størrelse på vinduet
        self.resizable(False, False)  # Deaktiverer muligheten til å endre størrelse på vinduet
        self.attributes('-toolwindow', True)  # Setter vinduet til å være et verktøyvindu
        self.withdraw()  # Skjuler vinduet ved oppstart
        self.protocol("WM_DELETE_WINDOW", self.on_close)  # Setter opp hendelseshåndtering for når vinduet lukkes
    
    def show(self):  # Metode for å vise vinduet
        self.deiconify()  # Viser vinduet
        self.update_idletasks()  # Oppdaterer vinduet for å sikre at størrelsen er korrekt

        monitor = get_monitors()[0]  # Antar primærskjerm og henter informasjon om den
        screen_width, screen_height = monitor.width, monitor.height  # Henter skjermens bredde og høyde

        win_width, win_height = self.winfo_width(), self.winfo_height()  # Henter vinduets bredde og høyde

        x = screen_width - win_width - 20  # Beregner x-posisjon (høyre side av skjermen med margin)
        y = screen_height - win_height - 150  # Beregner y-posisjon (nederst på skjermen med margin)

        self.geometry(f"+{x}+{y}")  # Setter vinduets posisjon på skjermen
        self.lift()  # Bringer vinduet til forgrunnen
        self.focus_force()  # Tvinger vinduet til å få fokus

    def on_close(self):  # Metode som kalles når vinduet lukkes
        self.withdraw()  # Skjuler vinduet i stedet for å avslutte

if __name__ == "__main__":  # Sjekker om denne filen kjøres direkte (ikke importeres)
    app = AppWindow()  # Oppretter en instans av AppWindow-klassen
    app.show()  # Viser vinduet
    app.mainloop()  # Starter hovedløkken for GUI-et
