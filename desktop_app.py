import sys

# Correção para "NoneType object has no attribute write" em modo windowed (pyinstaller -w)
class NullWriter:
    def write(self, text): pass
    def flush(self): pass

if sys.stdout is None:
    sys.stdout = NullWriter()
if sys.stderr is None:
    sys.stderr = NullWriter()

import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QDateEdit, 
                             QListWidget, QListWidgetItem, QProgressBar, 
                             QMessageBox, QFrame, QAbstractItemView, QFileDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette

from chatwoot_etl import ChatwootETL

# --- Configuração de Estilo (Tema Bronze/Escuro) ---
# --- Configuração de Estilo (Tema Bronze/Escuro) ---
STYLESHEET = """
QMainWindow {
    background-color: #322E2B;
}
QWidget {
    color: #FDFDFD;
    font-size: 14px;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QLabel {
    color: #FDFDFD;
}
QLabel#Title {
    color: #D5AE77;
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 20px;
}
QLabel#Subtitle {
    color: #D5AE77;
    font-size: 18px;
    font-weight: bold;
    margin-top: 15px;
    margin-bottom: 5px;
}
QFrame#Card {
    background-color: #1F1F1F;
    border: 1px solid #D5AE77;
    border-radius: 12px;
    padding: 20px;
}
QPushButton {
    background-color: #D5AE77;
    color: #322E2B;
    border: none;
    border-radius: 6px;
    padding: 12px 24px;
    font-weight: bold;
    font-size: 15px;
}
QPushButton:hover {
    background-color: #927245;
    color: #FDFDFD;
}
QPushButton:disabled {
    background-color: #555555;
    color: #AAAAAA;
}
QPushButton#ActionButton {
    font-size: 16px;
    background-color: #D5AE77;
}
QDateEdit {
    background-color: #2D2D2D;
    color: #FDFDFD;
    border: 1px solid #555555;
    border-radius: 6px;
    padding: 8px;
    font-size: 14px;
}
QCheckBox {
    spacing: 8px;
    font-size: 14px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #D5AE77;
    border-radius: 3px;
    background: #1F1F1F;
}
QCheckBox::indicator:checked {
    background-color: #D5AE77;
    image: none; /* Poderia usar icon customizado */
}
QListWidget {
    background-color: #2D2D2D;
    color: #FDFDFD;
    border: 1px solid #555555;
    border-radius: 6px;
    padding: 5px;
    outline: none;
}
QListWidget::item {
    padding: 8px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #D5AE77;
    color: #322E2B;
}
QListWidget::item:hover {
    background-color: #3a3a3a;
}
QProgressBar {
    border: none;
    border-radius: 5px;
    text-align: center;
    background-color: #1F1F1F;
    color: white;
    height: 10px;
}
QProgressBar::chunk {
    background-color: #D5AE77;
    border-radius: 5px;
}
"""

class WorkerThread(QThread):
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(str, int, int) # filename, num_conversations, num_messages
    error_occurred = pyqtSignal(str)

    def __init__(self, start_date, end_date, selected_ids, all_dates=False):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date
        self.selected_ids = selected_ids
        self.all_dates = all_dates

    def run(self):
        try:
            # Configura datas (None se for tudo)
            s_date = None if self.all_dates else self.start_date
            e_date = None if self.all_dates else self.end_date
            
            # Instancia ETL passando o callback de progresso
            # A função de callback deve ter a assinatura (percent, message)
            etl = ChatwootETL(
                start_date=s_date, 
                end_date=e_date, 
                progress_callback=self.progress_updated.emit
            )
            
            # Carrega mapa
            # O ETL agora reporta o progresso internamente, mas podemos fazer um sanity check
            if not etl.load_inbox_map():
                 raise Exception("Falha ao carregar canais do Chatwoot.")

            # Busca Conversas
            self.progress_updated.emit(20, "Buscando conversas...")
            conversations = []
            
            # Lógica de seleção de inboxes específica
            if not self.selected_ids:
                conversations = etl.get_all_conversations()
            else:
                filtered_map = {k: v for k, v in etl.inbox_map.items() if k in self.selected_ids}
                if filtered_map:
                    etl.inbox_map = filtered_map
                    conversations = etl._get_conversations_by_inbox()
                else:
                    conversations = etl.get_all_conversations()

            if not conversations:
                self.progress_updated.emit(100, "Concluído (sem dados).")
                self.finished.emit("", 0, 0)
                return

            # Filtro de Data (Conversas) - Agora usamos o método do ETL
            # Mas apenas se não for "all dates" (o método do ETL verifica self.start_date)
            # Como passamos start_date=None para o ETL se all_dates=True, ele já sabe o que fazer.
            conversations = etl.filter_conversations_by_date(conversations)

            # Transformação (ETL agora reporta progresso detalhado aqui)
            transformed_data = etl.transform_messages(conversations)

            # Salvando
            export_dir = os.path.join(os.getcwd(), 'exports')
            os.makedirs(export_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if self.all_dates:
                period_str = "historico_completo"
            else:
                s_s = etl.start_date.strftime("%d-%m-%Y") if etl.start_date else "inicio"
                e_s = etl.end_date.strftime("%d-%m-%Y") if etl.end_date else "fim"
                period_str = f"{s_s}_a_{e_s}"
            
            filename = f"chatwoot_{period_str}_{timestamp}.json"
            full_path = os.path.join(export_dir, filename)
            
            etl.save_to_json(transformed_data, full_path)
            
            self.progress_updated.emit(100, "Concluído!")
            self.finished.emit(full_path, len(conversations), len(transformed_data))
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))

from PyQt6.QtWidgets import QCheckBox, QSpacerItem, QSizePolicy

class ChatwootApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Chatwoot Data Extractor")
        self.setGeometry(100, 100, 900, 650)
        self.setStyleSheet(STYLESHEET)
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Header
        header_label = QLabel("Studio Fiscal - Chatwoot Data Extractor")
        header_label.setObjectName("Title")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)

        # --- Card de Configuração ---
        config_card = QFrame()
        config_card.setObjectName("Card")
        config_layout = QVBoxLayout(config_card)
        config_layout.setSpacing(15)
        main_layout.addWidget(config_card)

        # 1. Seção de Datas
        date_header_layout = QHBoxLayout()
        date_label = QLabel("📅 Período de Extração")
        date_label.setObjectName("Subtitle")
        date_header_layout.addWidget(date_label)
        
        # Checkbox "Todo o período"
        self.all_dates_cb = QCheckBox("Extrair Histórico Completo")
        self.all_dates_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.all_dates_cb.toggled.connect(self.toggle_dates)
        date_header_layout.addWidget(self.all_dates_cb, alignment=Qt.AlignmentFlag.AlignRight)
        
        config_layout.addLayout(date_header_layout)

        # Inputs de Data
        self.date_container = QWidget()
        date_row = QHBoxLayout(self.date_container)
        date_row.setContentsMargins(0,0,0,0)
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.start_date_edit.setMinimumWidth(150)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.end_date_edit.setMinimumWidth(150)
        
        date_row.addWidget(QLabel("Início:"))
        date_row.addWidget(self.start_date_edit)
        date_row.addSpacing(20)
        date_row.addWidget(QLabel("Fim:"))
        date_row.addWidget(self.end_date_edit)
        date_row.addStretch()
        
        config_layout.addWidget(self.date_container)
        
        config_layout.addSpacing(10)
        
        # 2. Seção de Canais
        channel_header_layout = QHBoxLayout()
        channel_label = QLabel("📢 Seleção de Canais")
        channel_label.setObjectName("Subtitle")
        channel_header_layout.addWidget(channel_label)
        
        # Checkbox "Todos os Canais"
        self.all_channels_cb = QCheckBox("Todos os Canais")
        self.all_channels_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.all_channels_cb.toggled.connect(self.toggle_channels)
        channel_header_layout.addWidget(self.all_channels_cb, alignment=Qt.AlignmentFlag.AlignRight)
        
        config_layout.addLayout(channel_header_layout)
        
        self.channel_list = QListWidget()
        self.channel_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.channel_list.setFixedHeight(180)
        config_layout.addWidget(self.channel_list)
        
        self.refresh_btn = QPushButton("🔄 Atualizar Lista")
        self.refresh_btn.setFixedWidth(180)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.load_channels)
        config_layout.addWidget(self.refresh_btn, alignment=Qt.AlignmentFlag.AlignRight)

        # --- Ações ---
        main_layout.addStretch()
        
        action_layout = QVBoxLayout()
        action_layout.setSpacing(10)
        main_layout.addLayout(action_layout)
        
        self.status_label = QLabel("Pronto para iniciar.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        action_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        action_layout.addWidget(self.progress_bar)
        
        self.extract_btn = QPushButton("🚀 EXECUTAR EXTRAÇÃO")
        self.extract_btn.setObjectName("ActionButton")
        self.extract_btn.setFixedHeight(55)
        self.extract_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.extract_btn.clicked.connect(self.start_extraction)
        action_layout.addWidget(self.extract_btn)

        # Inicialização
        self.channel_list.addItem("Carregando canais...")
        self.channel_list.setEnabled(False)
        self.all_channels_cb.setEnabled(False)
        
    def showEvent(self, event):
        super().showEvent(event)
        QThread.msleep(100)
        self.load_channels()
        
    def toggle_dates(self, checked):
        self.date_container.setEnabled(not checked)
        
    def toggle_channels(self, checked):
        self.channel_list.setEnabled(not checked)
        if checked:
            self.channel_list.clearSelection()

    def load_channels(self):
        self.channel_list.clear()
        self.channel_list.addItem("Conectando ao Chatwoot...")
        self.channel_list.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.all_channels_cb.setEnabled(False)
        
        self.loader_thread = LoadChannelsThread()
        self.loader_thread.finished.connect(self.on_channels_loaded)
        self.loader_thread.start()

    def on_channels_loaded(self, channels):
        self.channel_list.clear()
        self.channel_list.setEnabled(not self.all_channels_cb.isChecked())
        self.refresh_btn.setEnabled(True)
        self.all_channels_cb.setEnabled(True)
        
        if not channels:
            self.channel_list.addItem("Nenhum canal encontrado.")
            return

        for cid, name in channels.items():
            item = QListWidgetItem(f"{name} (ID: {cid})")
            item.setData(Qt.ItemDataRole.UserRole, cid)
            self.channel_list.addItem(item)
            
        self.status_label.setText("Canais carregados.")

    def start_extraction(self):
        # Parâmetros
        s_date = self.start_date_edit.text() # ex: 12/12/2025
        e_date = self.end_date_edit.text()
        
        # Conversão de formato brasileiro DD/MM/YYYY -> YYYY-MM-DD para o Worker/ETL
        # O Worker espera YYYY-MM-DD
        try:
            if not self.all_dates_cb.isChecked():
                d_start = datetime.strptime(s_date, "%d/%m/%Y")
                d_end = datetime.strptime(e_date, "%d/%m/%Y")
                
                s_date_iso = d_start.strftime("%Y-%m-%d")
                e_date_iso = d_end.strftime("%Y-%m-%d")
            else:
                s_date_iso = None
                e_date_iso = None
        except ValueError:
            QMessageBox.warning(self, "Erro", "Formato de data inválido.")
            return

        selected_ids = []
        if not self.all_channels_cb.isChecked():
            selected_items = self.channel_list.selectedItems()
            selected_ids = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
            
            if not selected_ids:
                QMessageBox.warning(self, "Atenção", "Selecione pelo menos um canal ou marque 'Todos os Canais'.")
                return
        
        # Bloqueia UI
        self.extract_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.channel_list.setEnabled(False)
        self.all_channels_cb.setEnabled(False)
        self.start_date_edit.setEnabled(False)
        self.end_date_edit.setEnabled(False)
        self.all_dates_cb.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Inicia Worker
        self.worker = WorkerThread(s_date_iso, e_date_iso, selected_ids, all_dates=self.all_dates_cb.isChecked())
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(self.extraction_finished)
        self.worker.error_occurred.connect(self.extraction_error)
        self.worker.start()
        
    def update_progress(self, val, text):
        self.progress_bar.setValue(val)
        self.status_label.setText(text)
        
    def extraction_finished(self, filename, n_conv, n_msgs):
        self.reset_ui()
        self.progress_bar.setValue(100)
        
        if filename:
            msg = f"Extração concluída!\n\nArquivo: {os.path.basename(filename)}\nConversas: {n_conv}\nMensagens: {n_msgs}"
            QMessageBox.information(self, "Sucesso", msg)
            os.startfile(os.path.dirname(filename))
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum dado encontrado.")

    def extraction_error(self, error_msg):
        self.reset_ui()
        QMessageBox.critical(self, "Erro", f"Ocorreu um erro:\n{error_msg}")

    def reset_ui(self):
        self.extract_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.all_channels_cb.setEnabled(True)
        self.all_dates_cb.setEnabled(True)
        
        self.toggle_dates(self.all_dates_cb.isChecked())
        self.toggle_channels(self.all_channels_cb.isChecked())
        
        self.status_label.setText("Pronto.")

class LoadChannelsThread(QThread):
    finished = pyqtSignal(dict)
    
    def run(self):
        try:
            etl = ChatwootETL()
            if etl.load_inbox_map():
                self.finished.emit(etl.inbox_map)
            else:
                self.finished.emit({})
        except:
            self.finished.emit({})

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatwootApp()
    window.show()
    sys.exit(app.exec())
