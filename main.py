from datetime import datetime
import glob
import sys
import queue
import threading
import time
import os

from PyQt5.QtCore import pyqtSlot, QTimer, QThread
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLineEdit, QLabel, \
    QTabWidget, QComboBox, QMessageBox, QStyleFactory
from PyQt5.QtGui import QFont, QTextCursor, QIcon

import AudioRecorder
from AudioTranscriber import AudioTranscriber
from chat_utils import GPTChat

from dotenv import load_dotenv

load_dotenv('keys.env')


def load_stylesheet(filename):
    with open(filename) as file:
        return file.read()



HTML_MESSAGE_TEMPLATE = """
<div style='background-color:#e4e4e3; padding:10px; margin:15px; border-radius:15px; color:#333333; font-family:Roboto; font-size:12pt;'><b>"""

class AudioProcess:
    def __init__(self):
        self.audio_queue = queue.Queue()

        self.user_audio_recorder = AudioRecorder.DefaultMicRecorder()
        self.user_audio_recorder.record_into_queue(self.audio_queue)

        time.sleep(.1)

        self.speaker_audio_recorder = AudioRecorder.DefaultSpeakerRecorder()
        self.speaker_audio_recorder.record_into_queue(self.audio_queue)

        self.global_transcriber = AudioTranscriber(self.user_audio_recorder.source, self.speaker_audio_recorder.source)
        self.transcribe = threading.Thread(target=self.global_transcriber.transcribe_audio_queue, args=(self.audio_queue,))
        self.transcribe.daemon = True
        self.transcribe.start()


class SetupWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SalesGPT Setup")
        self.setWindowIcon(
            QIcon('app_icon.png'))  # Set the app icon, ensure the file 'app_icon.png' is in your directory
        self.resize(500, 200)

        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()

        self.tab1 = QWidget()
        self.tab2 = QWidget()

        self.tabs.addTab(self.tab1, "Start a New Call")
        self.tabs.addTab(self.tab2, "Review Past Calls")

        self.tab1_layout = QVBoxLayout(self)
        self.tab2_layout = QVBoxLayout(self)

        self.tab1.setLayout(self.tab1_layout)
        self.tab2.setLayout(self.tab2_layout)

        self.welcome_message = QLabel(""" <h3>Enter the name of the person you will be speaking to and click 'Start Call'.</h3> """)

        self.speaker_name_input = QLineEdit()
        self.speaker_name_input.setPlaceholderText("Enter Name Here")

        self.start_button = QPushButton("Start Call")
        self.start_button.clicked.connect(self.start_chat)

        self.file_dropdown = QComboBox()


        self.load_file_button = QPushButton("Load Selected Call")
        self.load_file_button.clicked.connect(self.load_file)


        self.nofiles_label = QLabel()

        self.tab1_layout.addWidget(self.welcome_message)
        self.tab1_layout.addWidget(self.speaker_name_input)
        self.tab1_layout.addWidget(self.start_button)

        self.tab2_layout.addWidget(self.file_dropdown)
        self.tab2_layout.addWidget(self.load_file_button)
        self.tab2_layout.addWidget(self.nofiles_label)

        self.layout.addWidget(self.tabs)

        self.load_files_into_dropdown()

        stylesheet = load_stylesheet('styles/setup.qss')
        self.setStyleSheet(stylesheet)


    def start_chat(self):
        self.speaker_name = self.speaker_name_input.text()
        if self.speaker_name:
            QMessageBox.information(self, "Initialize", "Click OK, then make some noise from your mic and speaker. This might take a moment.")
            self.chat_app = ChatApp(self.speaker_name)
            self.chat_app.show()
            self.close()

    def load_file(self):
        selected_file = self.file_dropdown.currentText()
        if selected_file:
            self.chat_app = ChatWithSavedTranscript(selected_file)
            self.chat_app.show()
            self.close()

    def load_files_into_dropdown(self):
        txt_files = glob.glob(os.path.join("transcripts", '*.txt'))


        if txt_files is None:
            self.nofiles_label.setText("No files found!")
            self.nofiles_label.setFont(QFont("Roboto", 16))
            return None
        else:
            self.file_dropdown.addItems(txt_files)






class WorkerThread(QThread):
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.function(*self.args, **self.kwargs)



class ChatApp(QWidget):
    def __init__(self, speaker_name, loaded_db=None):
        super().__init__()
        self.chat = GPTChat()
        self.audio_process = AudioProcess()
        self.global_transcriber = self.audio_process.global_transcriber

        self.speaker_name = speaker_name




        self.timer = QTimer()
        self.timer.timeout.connect(self.update_transcript)
        self.timer.start(3000)

        self.response_timer = QTimer()
        self.response_timer.timeout.connect(self.update_placeholder)
        self.response_timer.start(1000)
        self.placeholder_text = ''

        self.timer_for_objection_detection = QTimer()
        self.timer_for_objection_detection.timeout.connect(self.objection_detection_thread)
        self.timer_for_objection_detection.start(5000)
        self.first = False

        self.db = loaded_db

        self.transcript = None
        self.first = True
        self.sent_to_gpt_count = 0
        self.create_widgets()


    def create_widgets(self):
        self.setWindowTitle("SalesGPT")
        self.setWindowIcon(QIcon("app_icon.png"))

        self.resize(800, 600)

        self.tab_widget = QTabWidget()


        #Transcript tab

        transcript_tab = QWidget()

        self.transcript_box = QTextEdit()
        self.transcript_box.setReadOnly(True)

        self.recording_label = QLabel()
        self.recording_label.setText("Recording.")

        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_recording_label)
        self.recording_timer.start(1000)

        self.save_quit_button = QPushButton("Save and quit")
        self.save_quit_button.setFont(QFont("Roboto", 12))
        self.save_quit_button.clicked.connect(self.save_and_quit)

        transcript_layout = QVBoxLayout(transcript_tab)
        transcript_layout.addWidget(self.transcript_box)
        transcript_layout.addWidget(self.recording_label)
        transcript_layout.addWidget(self.save_quit_button)

        self.tab_widget.addTab(transcript_tab, "Transcript")

        #Chat tab

        chat_tab = QWidget()

        self.chat_history_box = QTextEdit()
        self.chat_history_box.setReadOnly(True)

        self.chat_history_box.append(
            HTML_MESSAGE_TEMPLATE
            + "SalesGPT: " + "</b>" + "Hi! I'm your personal sales assistant. I'll advise you during the call. If you have any questions,"
                                     "want advice, or anything else, just send me a message!" + "</div>")

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Send a message...")
        self.input_box.setMinimumSize(400, 40)


        self.send_button = QPushButton("Send message")
        self.send_button.clicked.connect(self.on_send)

        self.response_label = QLabel()
        self.response_label_text = "Listening"

        chat_layout = QVBoxLayout(chat_tab)
        chat_layout.addWidget(self.chat_history_box)
        chat_layout.addWidget(self.input_box)
        chat_layout.addWidget(self.send_button)
        chat_layout.addWidget(self.response_label)

        self.tab_widget.addTab(chat_tab, "Sales Assistant")

        layout = QVBoxLayout(self)
        layout.addWidget(self.tab_widget)

        stylesheet = load_stylesheet('styles/chatapp.qss')
        self.setStyleSheet(stylesheet)

    @pyqtSlot()
    def update_transcript(self):
        # if self.first:
        #     self.timer_for_objection_detection = QTimer()
        #     self.timer_for_objection_detection.timeout.connect(self.sales_testing_thread)
        #     self.timer_for_objection_detection.start(5000)
        #     self.first = False

        scrollbar = self.transcript_box.verticalScrollBar()
        value = scrollbar.value()
        at_bottom = value == scrollbar.maximum()

        self.transcript = self.global_transcriber.get_transcript(speakername=self.speaker_name)
        self.transcript_box.setPlainText(self.transcript)

        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        else:
            scrollbar.setValue(value)

    def objection_detection_thread(self):
        print("Starting sales testing thread")
        self.timer_for_objection_detection.stop()
        self.thread_sales = WorkerThread(self.objection_detection)
        self.thread_sales.finished.connect(self.timer_for_objection_detection.start)
        self.thread_sales.start()

    def update_recording_label(self):
        current_text = self.recording_label.text()
        if len(current_text) < 12:
            current_text += '.'
        else:
            current_text = "Recording."
        self.recording_label.setText(current_text)

    @pyqtSlot()
    def on_send(self):
        self.timer_for_objection_detection.stop()
        user_message = self.input_box.text()
        if user_message:
            self.input_box.clear()

            self.chat_history_box.append(
                HTML_MESSAGE_TEMPLATE
                + "You: " + "</b>" + user_message + "</div>")
            self.chat_history_box.moveCursor(QTextCursor.End)

            self.response_label_text = "Generating response"

            threading.Thread(target=self.get_response, args=(user_message,)).start()


    def update_placeholder(self):
        if len(self.placeholder_text) < 3:
            self.placeholder_text += "."
        else:
            self.placeholder_text = "."
        self.response_label.setText(self.response_label_text + self.placeholder_text)

    def get_response(self, user_message):
        transcript = self.global_transcriber.get_transcript(speakername=self.speaker_name)
        response = self.chat.message_bot(user_message, transcript)

        self.response_label_text = "Listening"

        QApplication.processEvents()
        self.chat_history_box.append(
            HTML_MESSAGE_TEMPLATE
            + "SalesGPT: " + "</b>" + response + "</div>")
        self.chat_history_box.update()
        self.chat_history_box.moveCursor(QTextCursor.End)
        self.timer_for_objection_detection.start()

    def save_transcript(self):
        try:
            transcript = self.transcript
            date = datetime.now().strftime("%d-%m-%Y")
            db_lock = threading.Lock()
            with db_lock:
                with open(f'transcripts/{self.speaker_name}_{date}.txt', 'w') as f:
                    f.write(transcript)
        except Exception as e:
            print(e)

    def save_and_quit(self):
        try:
            self.save_transcript()
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Information)
            msgbox.setText("Transcript saved successfully!")
            msgbox.setWindowTitle("Success")
            msgbox.setStandardButtons(QMessageBox.Ok)
            msgbox.exec_()
            QApplication.quit()

        except Exception as e:
            print(e)


    def objection_detection(self):
        recent_transcript = self.transcript[self.sent_to_gpt_count:]
        recent_transcript = recent_transcript[-500:]
        if len(recent_transcript) > 50:
            response = self.chat.generate_response_from_sales_call(recent_transcript)
            if response is not None:
                self.sent_to_gpt_count = len(self.transcript)
                self.chat_history_box.append(
                    HTML_MESSAGE_TEMPLATE
                    + "SalesGPT: " + "</b>" + response + "</div>")
                self.chat_history_box.update()
                self.chat_history_box.moveCursor(QTextCursor.End)






class ChatWithSavedTranscript(QWidget):
    def __init__(self, transcript_path):
        super().__init__()

        self.chat = GPTChat(live_chat=False)
        with open(transcript_path, 'r') as f:
            self.transcript = f.read()


        self.response_timer = QTimer()
        self.response_timer.timeout.connect(self.update_placeholder)

        self.create_widgets()
    def create_widgets(self):
        self.setWindowTitle("SalesGPT")
        self.setWindowIcon(QIcon("app_icon.png"))

        self.resize(800, 600)

        self.tab_widget = QTabWidget()

        # Transcript tab

        transcript_tab = QWidget()

        self.transcript_box = QTextEdit()
        self.transcript_box.setReadOnly(True)
        self.transcript_box.setPlainText(self.transcript)


        transcript_layout = QVBoxLayout(transcript_tab)
        transcript_layout.addWidget(self.transcript_box)

        self.tab_widget.addTab(transcript_tab, "Transcript")

        # Chat tab

        chat_tab = QWidget()

        self.chat_history_box = QTextEdit()
        self.chat_history_box.setReadOnly(True)

        self.chat_history_box.append(
            HTML_MESSAGE_TEMPLATE
            + "SalesGPT: " + "</b>" + "Hi! Ask me any questions you have about the transcript! I can evaluate the salesperson's performance, tell you about the customer, "
                                      "and more." + "</div>")

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Send a message...")

        self.input_box.setMinimumSize(400, 40)

        self.send_button = QPushButton("Send message")
        self.send_button.clicked.connect(self.on_send)

        self.response_label = QLabel()

        chat_layout = QVBoxLayout(chat_tab)
        chat_layout.addWidget(self.chat_history_box)
        chat_layout.addWidget(self.input_box)
        chat_layout.addWidget(self.send_button)
        chat_layout.addWidget(self.response_label)

        self.tab_widget.addTab(chat_tab, "Sales Assistant")

        layout = QVBoxLayout(self)
        layout.addWidget(self.tab_widget)

        stylesheet = load_stylesheet('styles/chatapp.qss')
        self.setStyleSheet(stylesheet)

    @pyqtSlot()
    def on_send(self):
        user_message = self.input_box.text()
        if user_message:
            self.input_box.clear()

            self.chat_history_box.append(
                HTML_MESSAGE_TEMPLATE
                + "You: " + "</b>" + user_message + "</div>")
            self.chat_history_box.moveCursor(QTextCursor.End)

            self.placeholder_text = "."
            self.response_timer.start(500)

            threading.Thread(target=self.get_response, args=(user_message,)).start()

    def update_placeholder(self):
        if len(self.placeholder_text) < 3:
            self.placeholder_text += "."
        else:
            self.placeholder_text = "."
        self.response_label.setText("Generating response" + self.placeholder_text)

    def get_response(self, user_message):

        response = self.chat.query_transcript(user_message, self.transcript)

        self.response_timer.stop()
        self.response_label.clear()
        QApplication.processEvents()
        self.chat_history_box.append(
            HTML_MESSAGE_TEMPLATE
            + "SalesGPT: " + "</b>" + response + "</div>")
        self.chat_history_box.update()
        self.chat_history_box.moveCursor(QTextCursor.End)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('fusion'))
    setup_window = SetupWindow()
    setup_window.show()
    sys.exit(app.exec_())







