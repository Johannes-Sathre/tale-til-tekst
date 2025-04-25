#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst - Moderne Brukergrensesnittmodul

Moderne PyQt6-basert brukergrensesnitt for Tale til Tekst-applikasjonen
"""

import os
import time
import threading
import pyperclip
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QComboBox, QTextEdit, QSlider, QFrame, QSizePolicy,
    QSystemTrayIcon, QMenu, QCheckBox, QLineEdit, QProgressBar
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QIcon, QAction, QPixmap, QFont, QFontDatabase
from qt_material import apply_stylesheet
import numpy as np

# Importer fra våre egne moduler
from config import *
from utils import last_ikon, save_svg_icon, setup_icons

class AudioVisualizer(QWidget):
    """Widget for visualisering av lydnivå under opptak"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.amplitude_data = np.zeros(50)
        self.active = False
        self.setStyleSheet(f"background-color: {CARD_BG};")
    
    def update_data(self, data):
        """Oppdater amplitudedata for visualisering"""
        if data is not None and len(data) > 0:
            # Normaliser data til området [0, 1]
            data = np.abs(data)
            max_val = max(np.max(data), 0.01)  # Unngå divisjon med null
            data = data / max_val
            
            # Beregn RMS (Root Mean Square) for hver blokk av data
            block_size = len(data) // min(len(data), len(self.amplitude_data))
            new_data = []
            for i in range(0, len(data), block_size):
                block = data[i:i+block_size]
                if len(block) > 0:
                    rms = np.sqrt(np.mean(np.square(block)))
                    new_data.append(rms)
            
            # Fyll amplitude_data med nye verdier
            self.amplitude_data = np.array(new_data[:len(self.amplitude_data)])
            
            # Oppdater widget
            self.update()
    
    def set_active(self, active):
        """Angi om visualisereren er aktiv"""
        self.active = active
        if not active:
            # Nullstill data gradvis når inaktiv
            self.amplitude_data = np.zeros(50)
        self.update()
    
    def paintEvent(self, event):
        """Tegn visualisering"""
        import random
        from PyQt6.QtGui import QPainter, QColor, QPen
        from PyQt6.QtCore import QRect
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Tegn bakgrunn
        painter.fillRect(event.rect(), QColor(CARD_BG))
        
        if not self.active:
            # Tegn inaktiv melding
            painter.setPen(QColor(SECONDARY_TEXT))
            painter.drawText(event.rect(), Qt.AlignmentFlag.AlignCenter, "Trykk og hold tastatursnarvei for å starte opptak")
            return
        
        # Antall linjer å tegne
        num_bars = min(50, len(self.amplitude_data))
        
        # Beregn bredde for hver stolpe
        width = self.width() / (num_bars * 1.2)
        margin = width * 0.2
        
        # Beregn høyde
        max_height = self.height() * 0.9
        
        # Velg farge basert på aktivitet
        active_color = QColor(ACCENT_COLOR)
        
        # Tegn hver stolpe
        for i in range(num_bars):
            amp = self.amplitude_data[i]
            
            # Legg til litt tilfeldig variasjon for mer organisk visualisering
            if self.active:
                amp = amp * (0.9 + random.random() * 0.2)
            
            # Beregn høyde basert på amplitude
            height = max(4, amp * max_height)
            
            # Beregn x-posisjon
            x = i * (width + margin) + margin
            
            # Tegn stolpen
            rect = QRect(int(x), 
                         int(self.height() - height) // 2, 
                         int(width), 
                         int(height))
            
            # Opprett gradient for stolpen
            gradient_color = QColor(active_color)
            gradient_color.setAlpha(int(200 + 55 * amp))
            
            painter.fillRect(rect, gradient_color)

class StatusIndicator(QWidget):
    """Status indikator widget"""
    def __init__(self, parent=None, size=12, status_type="normal"):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.status_type = status_type
    
    def set_status(self, status_type):
        """Sett statustype (success, warning, error)"""
        self.status_type = status_type
        self.update()
    
    def paintEvent(self, event):
        """Tegn statusindikator"""
        from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Velg farge basert på status
        if self.status_type == "success":
            color = QColor(SUCCESS_COLOR)
        elif self.status_type == "warning":
            color = QColor(WARNING_COLOR)
        elif self.status_type == "error":
            color = QColor(ERROR_COLOR)
        else:
            color = QColor(SECONDARY_TEXT)
        
        # Tegn sirkel
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(2, 2, self.width()-4, self.height()-4)

class CardFrame(QFrame):
    """Ramme med kort-design og skygge"""
    def __init__(self, parent=None, title=None):
        super().__init__(parent)
        self.setObjectName("cardFrame")
        
        # Stil
        self.setStyleSheet(f"""
            QFrame#cardFrame {{
                background-color: {CARD_BG};
                border: 1px solid {CARD_BORDER};
                border-radius: 8px;
            }}
        """)
        
        # Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)
        
        # Tittel hvis angitt
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(f"""
                color: {TEXT_COLOR};
                font-size: {FONT_SIZES["medium"]}px;
                font-weight: bold;
            """)
            self.main_layout.addWidget(title_label)
            
            # Legg til en horisontal linje under tittelen
            hr = QFrame()
            hr.setFrameShape(QFrame.Shape.HLine)
            hr.setFrameShadow(QFrame.Shadow.Sunken)
            hr.setStyleSheet(f"background-color: {DIVIDER_COLOR};")
            hr.setMaximumHeight(1)
            self.main_layout.addWidget(hr)

class ModernTaleApp(QMainWindow):
    def __init__(self, shortcut, recorder=None, transcriber=None):
        super().__init__()
        self.shortcut = shortcut
        self.recorder = recorder
        self.transcriber = transcriber
        
        # Konfigurer applikasjonen
        if self.recorder:
            self.recorder.set_app(self)
        if self.transcriber:
            self.transcriber.set_app(self)
        
        # Sett opp state
        self.is_recording = False
        self.transcription_count = 0
        self.selected_device = 0  # Standard mikrofon
        self.device_sample_rate = SAMPLE_RATE  # Standard sample rate
        self.is_transcribing = False  # For å spore transkripsjonsstatus
        self.device_ids = []  # Holder oversikt over enhet-IDer
        
        # Sett opp ikoner
        setup_icons({
            "microphone": MICROPHONE_SVG,
            "keyboard": KEYBOARD_SVG,
            "close": CLOSE_SVG,
            "settings": SETTINGS_SVG
        })
        
        # Opprett GUI
        self.setup_gui()
        
        # Oppsett av system tray
        self.setup_tray()
        
        # Oppdater mikrofoner ved oppstart
        self.update_microphones()
        
        # Oppdater GUI hver 100ms for å holde visualiseringen oppdatert
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(100)
        
    def setup_gui(self):
        """Sett opp brukergrensesnittet"""
        # Grunnleggende vindusoppsett
        self.setWindowTitle(APP_NAME)
        self.resize(840, 720)  # Redusert høyde fra original
        
        # Sett tema
        apply_stylesheet(self, theme='dark_teal.xml', extra={
            'density_scale': '0',
            'accent': ACCENT_COLOR,
            'primary': ACCENT_COLOR,
            'background': DARK_BG,
            'foreground': TEXT_COLOR
        })
        
        # Hovedwidget og layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # Modellstatuspanel
        model_panel = CardFrame(title="Modellstatus")
        self.main_layout.addWidget(model_panel)
        
        model_status_layout = QHBoxLayout()
        model_panel.main_layout.addLayout(model_status_layout)
        
        # Statusindikator
        self.model_indicator = StatusIndicator(status_type="warning")
        model_status_layout.addWidget(self.model_indicator)
        
        # Statuslabel
        self.status_label = QLabel("Laster modell...")
        self.status_label.setStyleSheet(f"color: {WARNING_COLOR}; font-weight: bold;")
        model_status_layout.addWidget(self.status_label)
        
        # Modellstatus
        self.model_status = QLabel("Modell: laster...")
        self.model_status.setStyleSheet(f"color: {WARNING_COLOR};")
        model_status_layout.addWidget(self.model_status, 1, Qt.AlignmentFlag.AlignRight)
        
        # Modellvalg
        model_controls_layout = QHBoxLayout()
        model_panel.main_layout.addLayout(model_controls_layout)
        
        model_label = QLabel("Velg modell:")
        model_controls_layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(AVAILABLE_WHISPER_MODELS)
        self.model_combo.setCurrentText(WHISPER_MODEL)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_controls_layout.addWidget(self.model_combo)
        
        load_model_button = QPushButton("Last inn modell")
        load_model_button.setIcon(QIcon(last_ikon("app_icon", 16)))
        load_model_button.clicked.connect(self.on_load_model)
        model_controls_layout.addWidget(load_model_button)
        
        # Mikrofonpanel
        mic_panel = CardFrame(title="Mikrofon")
        self.main_layout.addWidget(mic_panel)
        
        mic_layout = QHBoxLayout()
        mic_panel.main_layout.addLayout(mic_layout)
        
        mic_label = QLabel("Enhet:")
        mic_layout.addWidget(mic_label)
        
        self.mic_combo = QComboBox()
        mic_layout.addWidget(self.mic_combo, 1)
        
        test_mic_button = QPushButton("Test mikrofon")
        test_mic_button.setIcon(QIcon(last_ikon("microphone", 16)))
        test_mic_button.clicked.connect(self.on_test_microphone)
        mic_layout.addWidget(test_mic_button)
        
        # Volum slider
        volume_layout = QHBoxLayout()
        mic_panel.main_layout.addLayout(volume_layout)
        
        volume_label = QLabel("Følsomhet:")
        volume_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(50)
        self.volume_slider.setMaximum(150)
        self.volume_slider.setValue(100)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(10)
        volume_layout.addWidget(self.volume_slider, 1)
        
        self.volume_value = QLabel("1.0x")
        volume_layout.addWidget(self.volume_value)
        
        # Koble volumendringer til handler
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        
        # Lydvisualisering
        self.audio_vis = AudioVisualizer()
        mic_panel.main_layout.addWidget(self.audio_vis)
        
        # Tastatursnarveipanel
        shortcut_panel = CardFrame(title="Tastatursnarvei")
        self.main_layout.addWidget(shortcut_panel)
        
        shortcut_layout = QHBoxLayout()
        shortcut_panel.main_layout.addLayout(shortcut_layout)
        
        shortcut_icon = QLabel()
        shortcut_icon.setPixmap(QPixmap(last_ikon("keyboard", 24)))
        shortcut_layout.addWidget(shortcut_icon)
        
        shortcut_label = QLabel(f"<b>{self.shortcut}</b>")
        shortcut_label.setStyleSheet(f"color: {ACCENT_COLOR};")
        shortcut_layout.addWidget(shortcut_label)
        
        shortcut_info = QLabel("Hold inne for å ta opp, slipp for å transkribere")
        shortcut_layout.addWidget(shortcut_info, 1, Qt.AlignmentFlag.AlignRight)
        
        # Transkripsjonspanel
        transcript_panel = CardFrame(title="Transkripsjon")
        self.main_layout.addWidget(transcript_panel, 1)  # Stretch factor
        
        # Fremdriftsindikator
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0)  # Ubestemt fremgang
        self.progress.hide()
        transcript_panel.main_layout.addWidget(self.progress)
        
        # Transkripsjonstekst
        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.transcript_text.setPlaceholderText("Transkripsjon vil vises her...")
        transcript_panel.main_layout.addWidget(self.transcript_text, 1)
        
        # Knapperad for transkripsjonshandlinger
        transcript_buttons = QHBoxLayout()
        transcript_panel.main_layout.addLayout(transcript_buttons)
        
        copy_button = QPushButton("Kopier")
        copy_button.clicked.connect(self.on_copy_text)
        transcript_buttons.addWidget(copy_button)
        
        clear_button = QPushButton("Tøm")
        clear_button.clicked.connect(self.on_clear_text)
        transcript_buttons.addWidget(clear_button)
        
        transcript_buttons.addStretch(1)
        
        # OpenAI Korrektur
        self.openai_check = QCheckBox("Aktiver OpenAI korrektur av transkripsjoner")
        transcript_panel.main_layout.addWidget(self.openai_check)
        
        openai_layout = QHBoxLayout()
        transcript_panel.main_layout.addLayout(openai_layout)
        
        openai_label = QLabel("API-nøkkel:")
        openai_layout.addWidget(openai_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Skriv inn din OpenAI API-nøkkel")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.textChanged.connect(self.on_api_key_changed)
        openai_layout.addWidget(self.api_key_input, 1)
        
        # Logglinje
        status_label = QLabel(f"Versjon: {APP_VERSION}")
        status_label.setStyleSheet(f"color: {SECONDARY_TEXT}; font-size: 8pt;")
        self.main_layout.addWidget(status_label, 0, Qt.AlignmentFlag.AlignRight)
        
        # Logg oppstart
        self.log(f"{APP_NAME} startet")
        self.log(f"Hold inne '{self.shortcut}' for å ta opp tale")
    
    def on_volume_changed(self, value):
        """Håndter endring av volumskyveren"""
        vol = value / 100.0
        self.volume_value.setText(f"{vol:.1f}x")
    
    def on_model_changed(self, model_name):
        """Håndter endring av modell i rullegardinlisten"""
        self.log(f"Modell endret til {model_name}")
    
    def on_load_model(self):
        """Last inn valgt modell"""
        model_name = self.model_combo.currentText()
        self.log(f"Laster inn modell: {model_name}")
        
        # Oppdater config
        configure_cpu_parameters(model_name)
        
        # Last inn i bakgrunnstråd
        threading.Thread(target=self.transcriber.load_model, daemon=True).start()
    
    def on_test_microphone(self):
        """Test valgt mikrofon"""
        if hasattr(self.recorder, 'test_microphone'):
            selected_device = self.mic_combo.currentIndex()
            if selected_device >= 0 and selected_device < len(self.device_ids):
                device_id = self.device_ids[selected_device]
                self.log(f"Tester mikrofon: {self.mic_combo.currentText()}")
                threading.Thread(
                    target=self.recorder.test_microphone,
                    args=(device_id,),
                    daemon=True
                ).start()
    
    def on_copy_text(self):
        """Kopier transkripsjonsteksten til utklippstavlen"""
        text = self.transcript_text.toPlainText()
        if text:
            pyperclip.copy(text)
            self.log("Transkripsjon kopiert til utklippstavlen")
    
    def on_clear_text(self):
        """Tøm transkripsjonsteksten"""
        self.transcript_text.clear()
        self.log("Transkripsjon tømt")
    
    def on_api_key_changed(self, text):
        """Håndter endring av API-nøkkel"""
        import config
        config.OPENAI_API_KEY = text
    
    def update_microphones(self):
        """Oppdater listen over tilgjengelige mikrofoner"""
        if hasattr(self.recorder, 'get_devices'):
            devices = self.recorder.get_devices()
            self.mic_combo.clear()
            self.device_ids = []
            
            for device in devices:
                self.mic_combo.addItem(device['name'])
                self.device_ids.append(device['id'])
            
            # Sett standard enhet hvis tilgjengelig
            if self.recorder.default_input_device is not None:
                idx = self.device_ids.index(self.recorder.default_input_device) if self.recorder.default_input_device in self.device_ids else 0
                self.mic_combo.setCurrentIndex(idx)
    
    def update_ui(self):
        """Oppdater UI-elementer periodisk"""
        # Oppdater lydvisualisering hvis opptak pågår
        if self.is_recording and hasattr(self.recorder, 'get_audio_data'):
            audio_data = self.recorder.get_audio_data()
            self.audio_vis.update_data(audio_data)
    
    def setup_tray(self):
        """Sett opp system tray ikonet"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(last_ikon("app_icon", 32)))
        
        # Opprett tray-meny
        tray_menu = QMenu()
        
        # Åpne-handling
        show_action = QAction("Vis", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        # Avslutt-handling
        quit_action = QAction("Avslutt", self)
        quit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(quit_action)
        
        # Sett menyen og aktiver ikonet
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
    
    def on_tray_activated(self, reason):
        """Håndter klikk på system tray ikonet"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def closeEvent(self, event):
        """Håndter lukking av vinduet"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            APP_NAME,
            "Applikasjonen kjører fortsatt i systemfeltet. Klikk på ikonet for å åpne igjen.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
    
    def exit_app(self):
        """Avslutt applikasjonen helt"""
        self.tray_icon.hide()
        # Stopp alle bakgrunnsprosesser
        if hasattr(self.recorder, 'cleanup'):
            self.recorder.cleanup()
        QApplication.quit()
    
    def update_model_status(self, loaded=False, error=False):
        """Oppdater modellstatus i GUI"""
        if error:
            # Ved feil
            self.status_label.setText("Feil ved lasting")
            self.model_status.setText("Modell: Ikke lastet")
            self.model_indicator.set_status("error")
            self.status_label.setStyleSheet(f"color: {ERROR_COLOR}; font-weight: bold;")
            self.model_status.setStyleSheet(f"color: {ERROR_COLOR};")
        elif loaded:
            # Når modellen er lastet
            current_model = self.transcriber.get_current_model() if self.transcriber else "unknown"
            self.status_label.setText("Modell lastet")
            self.model_status.setText(f"Modell: {current_model}")
            self.model_indicator.set_status("success")
            self.status_label.setStyleSheet(f"color: {SUCCESS_COLOR}; font-weight: bold;")
            self.model_status.setStyleSheet(f"color: {SUCCESS_COLOR};")
        else:
            # Under lasting
            current_model = self.transcriber.get_current_model() if self.transcriber else "unknown"
            self.status_label.setText("Laster modell...")
            self.model_status.setText(f"Modell: {current_model} (laster...)")
            self.model_indicator.set_status("warning")
            self.status_label.setStyleSheet(f"color: {WARNING_COLOR}; font-weight: bold;")
            self.model_status.setStyleSheet(f"color: {WARNING_COLOR};")
    
    def update_recording_status(self, is_recording):
        """Oppdater opptaksstatus"""
        self.is_recording = is_recording
        self.audio_vis.set_active(is_recording)
        
        if is_recording:
            # Oppdater etiketter osv. for opptakstilstand
            self.log("Opptak startet")
        else:
            # Tilbakestill UI-elementer når opptaket stopper
            self.log("Opptak stoppet")
    
    def update_transcribing_status(self, is_transcribing):
        """Oppdater transkripsjonsstatus"""
        self.is_transcribing = is_transcribing
        
        if is_transcribing:
            # Vis fremdriftsindikator
            self.progress.show()
            self.log("Transkriberer...")
        else:
            # Skjul fremdriftsindikator
            self.progress.hide()
    
    def add_transcription(self, text, is_final=False, openai_corrected=False):
        """Legg til transkripsjon i tekstområdet"""
        if is_final:
            self.transcription_count += 1
        
        # Sett teksten i tekstområdet
        self.transcript_text.setPlainText(text)
        
        # Hvis dette er en ferdig transkripsjon, logg den
        if is_final:
            source = "OpenAI-korrigert" if openai_corrected else "Whisper"
            self.log(f"Transkripsjon {self.transcription_count} fullført ({source})")
    
    def log(self, message):
        """Logg en melding"""
        # Vi bruker bare print() siden vi ikke har et dedikert loggområde i den nye versjonen
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        # Viser statusmelding i 5 sekunder
        self.statusBar().showMessage(f"{message}", 5000) 