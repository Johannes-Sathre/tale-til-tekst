import pyaudio  # Importerer PyAudio for mikrofontilgang
import numpy as np  # Importerer NumPy for databehandling
import time  # Importerer time for tidsmåling
import threading  # Importerer threading for å kjøre lydopptak i bakgrunnen

class MicrophoneHandler:
    """
    Klasse for å håndtere mikrofondeteksjon og testing.
    """
    def __init__(self):
        # Konstanter for lydopptak
        self.FORMAT = pyaudio.paInt16  # Lydformat (16-bit integer)
        self.CHANNELS = 1  # Mono-opptak
        self.RATE = 44100  # Samplingsrate (44.1 kHz)
        self.CHUNK = 1024  # Størrelse på hver lydbit
        self.TEST_DURATION = 5  # Testvarighet i sekunder
        
        # Terskelverdier for lydnivå
        self.THRESHOLD_GREEN = 1000  # Terskel for bra mikrofonsignal
        self.THRESHOLD_ORANGE = 100  # Terskel for svak mikrofonsignal
        
        # PyAudio-instans
        self.p = pyaudio.PyAudio()
        
        # Liste over tilgjengelige mikrofoner
        self.mic_list = self._get_mic_list()
        
        # Callback-funksjon for testresultat
        self.on_test_complete = None
        
        # Pågående test-flagg
        self.is_testing = False
    
    def _get_mic_list(self):
        """Henter liste over tilgjengelige mikrofoner uten duplikater"""
        mic_list = []  # Lager en tom liste for mikrofoner
        seen_names = set()  # Lager et sett for å holde styr på navn vi har sett
        for i in range(self.p.get_device_count()):  # Går gjennom alle enheter
            info = self.p.get_device_info_by_index(i)  # Henter info om enheten
            if info["maxInputChannels"] > 0:  # Sjekker om det er en mikrofon
                mic_name = info["name"]  # Henter navnet på mikrofonen
                # Filtrerer ut uønskede navn
                exclude_keywords = [
                    "virtual", "stereo mix", "what you hear", "loopback",
                    "sound mapper", "primary sound capture", "output",
                    "@system32\\drivers", "hands-free", "pc speaker"
                ]
                if not any(x in mic_name.lower() for x in exclude_keywords):
                    if mic_name not in seen_names:  # Sjekker om navnet er unikt
                        mic_list.append({"name": mic_name, "index": i})  # Legger til mikrofon
                        seen_names.add(mic_name)  # Legger navnet til i settet
        return mic_list  # Returnerer listen uten duplikater
    
    def get_mic_names(self):
        """Returnerer liste over mikrofonnavnene"""
        return [mic["name"] for mic in self.mic_list]
    
    def get_mic_index_by_name(self, name):
        """Henter indeks for en gitt mikrofon basert på navn"""
        for mic in self.mic_list:
            if mic["name"] == name:
                return mic["index"]
        return None
    
    def test_microphone(self, mic_name, callback=None, log_callback=None):
        """
        Tester valgt mikrofon i 5 sekunder og returnerer resultatet.
        
        Parametere:
        - mic_name: Navnet på mikrofonen som skal testes
        - callback: Funksjon som kalles når testen er ferdig med resultat:
                    "green", "orange", "red"
        - log_callback: Funksjon som kalles for hver måling (optional)
        """
        if self.is_testing:
            return  # Ikke start ny test hvis en test allerede kjører
        
        self.is_testing = True
        self.on_test_complete = callback
        self.on_log = log_callback  # Lagrer log-callback
        
        # Start test i en separat tråd
        test_thread = threading.Thread(target=self._run_mic_test, args=(mic_name,))
        test_thread.daemon = True
        test_thread.start()
    
    def _run_mic_test(self, mic_name):
        """Kjører mikrofontesten og logger navn og maks volum i dB til GUI etterpå"""
        mic_index = self.get_mic_index_by_name(mic_name)
        if mic_index is None:
            self._test_complete("red")
            return
        try:
            stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=mic_index,
                frames_per_buffer=self.CHUNK
            )
            max_volume = 0
            start_time = time.time()
            while time.time() - start_time < self.TEST_DURATION:
                data = np.frombuffer(stream.read(self.CHUNK), dtype=np.int16)
                volume = np.abs(data).mean()
                max_volume = max(volume, max_volume)
            stream.stop_stream()
            stream.close()
            # Konverterer til dB (20*log10(volum)), unngår log(0)
            db = 20 * np.log10(max_volume) if max_volume > 0 else 0
            db_rounded = int(round(db))  # Runder av til nærmeste heltall
            if hasattr(self, 'on_log') and self.on_log:
                self.on_log(f"Mic test: {mic_name} - volum {db_rounded} dB")
            if max_volume >= self.THRESHOLD_GREEN:
                result = "green"
            elif max_volume >= self.THRESHOLD_ORANGE:
                result = "orange"
            else:
                result = "red"
            self._test_complete(result)
        except Exception as e:
            print(f"Feil under testing av mikrofon: {e}")
            self._test_complete("red")
    
    def _test_complete(self, result):
        """Håndterer ferdig test og kaller callback-funksjonen"""
        self.is_testing = False
        if self.on_test_complete:
            self.on_test_complete(result)
    
    def __del__(self):
        """Rydder opp PyAudio-instansen når objektet slettes"""
        if hasattr(self, 'p'):
            self.p.terminate() 