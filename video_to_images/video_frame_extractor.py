import sys
import os
import cv2
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QLabel, QFileDialog, QSpinBox,
                             QProgressBar, QMessageBox, QCheckBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont


class VideoProcessor(QThread):
    progress_updated = pyqtSignal(int)
    frame_extracted = pyqtSignal(int, str)
    finished_extraction = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, video_path, output_dir, interval, extract_all=False, custom_fps=1):
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir
        self.interval = interval
        self.extract_all = extract_all
        self.custom_fps = custom_fps
        self.is_running = True

    def run(self):
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                self.error_occurred.emit("동영상 파일을 열 수 없습니다.")
                return

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            original_fps = cap.get(cv2.CAP_PROP_FPS)

            frame_count = 0
            saved_count = 0

            if self.extract_all:
                frame_interval = 1
            else:
                # 설정된 FPS에 따라 추출할 프레임 간격 계산
                frame_interval = max(1, int(original_fps / self.custom_fps))

            while self.is_running:
                ret, frame = cap.read()
                if not ret:
                    break

                if self.extract_all or (frame_count % frame_interval == 0):
                    filename = f"frame_{saved_count:03d}.jpg"
                    filepath = os.path.join(self.output_dir, filename)

                    cv2.imwrite(filepath, frame)
                    saved_count += 1
                    self.frame_extracted.emit(saved_count, filename)

                frame_count += 1
                progress = int((frame_count / total_frames) * 100)
                self.progress_updated.emit(progress)

            cap.release()
            self.finished_extraction.emit(f"추출 완료: {saved_count}개 프레임이 저장되었습니다.")

        except Exception as e:
            self.error_occurred.emit(f"오류 발생: {str(e)}")

    def stop(self):
        self.is_running = False


class VideoFrameExtractor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.video_processor = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("동영상 프레임 추출기")
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        title_label = QLabel("동영상 프레임 추출기")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        video_layout = QHBoxLayout()
        self.video_path_label = QLabel("동영상 파일을 선택하세요")
        self.video_path_label.setStyleSheet("border: 1px solid gray; padding: 5px;")
        video_layout.addWidget(self.video_path_label)

        self.browse_video_btn = QPushButton("동영상 선택")
        self.browse_video_btn.clicked.connect(self.browse_video)
        video_layout.addWidget(self.browse_video_btn)
        layout.addLayout(video_layout)

        output_layout = QHBoxLayout()
        self.output_path_label = QLabel("출력 폴더를 선택하세요")
        self.output_path_label.setStyleSheet("border: 1px solid gray; padding: 5px;")
        output_layout.addWidget(self.output_path_label)

        self.browse_output_btn = QPushButton("폴더 선택")
        self.browse_output_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(self.browse_output_btn)
        layout.addLayout(output_layout)

        self.extract_all_checkbox = QCheckBox("모든 프레임 추출")
        layout.addWidget(self.extract_all_checkbox)

        settings_layout = QVBoxLayout()

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("추출 간격 (초):"))
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setMinimum(1)
        self.interval_spinbox.setMaximum(60)
        self.interval_spinbox.setValue(1)
        self.interval_spinbox.setEnabled(True)
        interval_layout.addWidget(self.interval_spinbox)
        interval_layout.addStretch()
        settings_layout.addLayout(interval_layout)

        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("초당 프레임 수 (FPS):"))
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setMinimum(1)
        self.fps_spinbox.setMaximum(60)
        self.fps_spinbox.setValue(1)
        self.fps_spinbox.setEnabled(True)
        fps_layout.addWidget(self.fps_spinbox)
        fps_layout.addStretch()
        settings_layout.addLayout(fps_layout)

        layout.addLayout(settings_layout)

        self.extract_all_checkbox.toggled.connect(self.on_extract_all_toggled)

        self.start_btn = QPushButton("프레임 추출 시작")
        self.start_btn.clicked.connect(self.start_extraction)
        self.start_btn.setEnabled(False)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("중지")
        self.stop_btn.clicked.connect(self.stop_extraction)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("상태: 준비")
        layout.addWidget(self.status_label)

        self.video_path = ""
        self.output_path = ""

    def on_extract_all_toggled(self, checked):
        self.interval_spinbox.setEnabled(not checked)
        self.fps_spinbox.setEnabled(not checked)

    def browse_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "동영상 파일 선택", "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv)"
        )
        if file_path:
            self.video_path = file_path
            self.video_path_label.setText(os.path.basename(file_path))
            self.check_ready()

    def browse_output(self):
        folder_path = QFileDialog.getExistingDirectory(self, "출력 폴더 선택")
        if folder_path:
            self.output_path = folder_path
            self.output_path_label.setText(folder_path)
            self.check_ready()

    def check_ready(self):
        if self.video_path and self.output_path:
            self.start_btn.setEnabled(True)

    def start_extraction(self):
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        extract_all = self.extract_all_checkbox.isChecked()
        interval = self.interval_spinbox.value()
        custom_fps = self.fps_spinbox.value()

        self.video_processor = VideoProcessor(
            self.video_path, self.output_path, interval, extract_all, custom_fps
        )
        self.video_processor.progress_updated.connect(self.update_progress)
        self.video_processor.frame_extracted.connect(self.on_frame_extracted)
        self.video_processor.finished_extraction.connect(self.on_extraction_finished)
        self.video_processor.error_occurred.connect(self.on_error_occurred)

        self.video_processor.start()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("상태: 프레임 추출 중...")
        self.progress_bar.setValue(0)

    def stop_extraction(self):
        if self.video_processor:
            self.video_processor.stop()
            self.video_processor.wait()

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("상태: 중지됨")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_frame_extracted(self, count, filename):
        self.status_label.setText(f"상태: {count}번째 프레임 저장됨 - {filename}")

    def on_extraction_finished(self, message):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText(f"상태: {message}")
        QMessageBox.information(self, "완료", message)

    def on_error_occurred(self, error_message):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText(f"상태: 오류 - {error_message}")
        QMessageBox.critical(self, "오류", error_message)


def main():
    app = QApplication(sys.argv)
    window = VideoFrameExtractor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()