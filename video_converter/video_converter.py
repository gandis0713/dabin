import sys
import os
import subprocess
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QLabel, QFileDialog, QComboBox,
                             QProgressBar, QMessageBox, QLineEdit, QGroupBox, QCheckBox, QSpinBox, QRadioButton, QButtonGroup)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont


class VideoConverter(QThread):
    progress_updated = pyqtSignal(int)
    conversion_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)

    def __init__(self, input_path, output_path, output_format, pixel_format, width, height, scale_mode='exact', rotation=0):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.output_format = output_format
        self.pixel_format = pixel_format
        self.width = width
        self.height = height
        self.scale_mode = scale_mode
        self.rotation = rotation
        self.is_running = True
        self.process = None

    def run(self):
        try:
            # FFmpeg 명령어 구성
            cmd = ['ffmpeg']

            cmd.extend(['-i', self.input_path, '-y'])

            # 회전 메타데이터 유지 (원본과 동일하게)
            cmd.extend(['-map_metadata', '0'])

            # 픽셀 포맷 설정
            if self.pixel_format != "원본 유지":
                cmd.extend(['-pix_fmt', self.pixel_format])

            # 비디오 필터 체인 구성
            filters = []


            # 해상도 설정
            if self.width > 0 and self.height > 0:
                # 회전된 영상의 경우 표시 해상도 그대로 물리적 해상도로 사용
                # 회전 메타데이터가 보존되므로 최종 표시는 원하는 크기가 됨
                actual_width = self.width + (self.width % 2)
                actual_height = self.height + (self.height % 2)

                if self.scale_mode == 'aspect_fit':
                    # 종횡비 유지, 지정 크기 안에 맞춤 (작아질 수 있음)
                    filters.append(f'scale={actual_width}:{actual_height}:force_original_aspect_ratio=decrease')
                    filters.append('scale=trunc(iw/2)*2:trunc(ih/2)*2')
                elif self.scale_mode == 'aspect_pad':
                    # 종횡비 유지, 지정 크기로 패딩 (검은 여백 추가)
                    filters.append(f'scale={actual_width}:{actual_height}:force_original_aspect_ratio=decrease')
                    filters.append('scale=trunc(iw/2)*2:trunc(ih/2)*2')
                    filters.append(f'pad={actual_width}:{actual_height}:-1:-1:black')
                else:  # exact
                    # 정확한 크기로 조정 (종횡비 무시) - 홀수도 짝수로 강제 변환
                    filters.append(f'scale={actual_width}:{actual_height}')

            # 필터 체인 적용
            if filters:
                cmd.extend(['-vf', ','.join(filters)])

            # 출력 경로 추가
            cmd.append(self.output_path)

            self.status_updated.emit(f"변환 명령어: {' '.join(cmd)}")

            # FFmpeg 프로세스 실행
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # 프로세스 완료 대기
            stdout, stderr = self.process.communicate()

            if self.process.returncode == 0:
                self.conversion_finished.emit("비디오 변환이 완료되었습니다.")
            else:
                self.error_occurred.emit(f"변환 실패: {stderr}")

        except Exception as e:
            self.error_occurred.emit(f"오류 발생: {str(e)}")

    def stop(self):
        self.is_running = False
        if self.process:
            self.process.terminate()


class VideoConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.video_converter = None
        self.input_path = ""
        self.output_path = ""
        self.original_width = 0
        self.original_height = 0
        self.display_width = 0   # 실제 표시되는 가로 (회전 고려)
        self.display_height = 0  # 실제 표시되는 세로 (회전 고려)
        self.rotation = 0  # 원본 비디오 회전각
        self.updating_aspect_ratio = False  # 순환 참조 방지
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("비디오 변환기")
        self.setGeometry(100, 100, 750, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 제목
        title_label = QLabel("비디오 변환기")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 입력 파일 선택
        input_group = QGroupBox("입력 파일")
        input_layout = QVBoxLayout(input_group)

        input_file_layout = QHBoxLayout()
        self.input_path_label = QLabel("비디오 파일을 선택하세요")
        self.input_path_label.setStyleSheet("border: 1px solid gray; padding: 5px;")
        input_file_layout.addWidget(self.input_path_label)

        self.browse_input_btn = QPushButton("파일 선택")
        self.browse_input_btn.clicked.connect(self.browse_input)
        input_file_layout.addWidget(self.browse_input_btn)
        input_layout.addLayout(input_file_layout)
        layout.addWidget(input_group)

        # 출력 설정
        output_group = QGroupBox("출력 설정")
        output_layout = QVBoxLayout(output_group)

        # 출력 경로
        output_path_layout = QHBoxLayout()
        self.output_path_label = QLabel("출력 경로를 선택하세요")
        self.output_path_label.setStyleSheet("border: 1px solid gray; padding: 5px;")
        output_path_layout.addWidget(self.output_path_label)

        self.browse_output_btn = QPushButton("경로 선택")
        self.browse_output_btn.clicked.connect(self.browse_output)
        output_path_layout.addWidget(self.browse_output_btn)
        output_layout.addLayout(output_path_layout)

        # 출력 파일명
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("출력 파일명:"))
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("예: output_video")
        filename_layout.addWidget(self.filename_input)
        output_layout.addLayout(filename_layout)

        layout.addWidget(output_group)

        # 변환 설정
        settings_group = QGroupBox("변환 설정")
        settings_layout = QVBoxLayout(settings_group)

        # 비디오 포맷 선택
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("출력 포맷:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "mp4", "avi", "mov", "mkv", "wmv", "flv", "webm", "m4v"
        ])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        settings_layout.addLayout(format_layout)

        # 픽셀 포맷 선택
        pixel_layout = QHBoxLayout()
        pixel_layout.addWidget(QLabel("픽셀 포맷:"))
        self.pixel_combo = QComboBox()
        self.pixel_combo.addItems([
            "원본 유지", "yuv420p", "yuv422p", "yuv444p", "rgb24", "bgr24",
            "argb", "rgba", "abgr", "bgra", "gray", "nv12", "nv21"
        ])
        pixel_layout.addWidget(self.pixel_combo)
        pixel_layout.addStretch()
        settings_layout.addLayout(pixel_layout)

        # 해상도 선택
        resolution_group = QGroupBox("해상도 설정")
        resolution_layout = QVBoxLayout(resolution_group)

        # 원본 해상도 표시
        self.original_resolution_label = QLabel("원본 해상도: 파일을 선택하세요")
        self.original_resolution_label.setStyleSheet("font-weight: bold; color: #666;")
        resolution_layout.addWidget(self.original_resolution_label)

        # 해상도 입력
        resolution_input_layout = QHBoxLayout()
        resolution_input_layout.addWidget(QLabel("출력 해상도:"))

        # 가로 입력
        resolution_input_layout.addWidget(QLabel("가로:"))
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(2, 7680)  # 최대 8K까지, 짝수로 시작
        self.width_spinbox.setValue(1280)  # 기본값
        self.width_spinbox.setSingleStep(2)  # 2씩 증가
        self.width_spinbox.valueChanged.connect(self.on_width_changed)
        resolution_input_layout.addWidget(self.width_spinbox)

        # 세로 입력
        resolution_input_layout.addWidget(QLabel("세로:"))
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(2, 4320)  # 최대 8K까지, 짝수로 시작
        self.height_spinbox.setValue(720)  # 기본값
        self.height_spinbox.setSingleStep(2)  # 2씩 증가
        self.height_spinbox.valueChanged.connect(self.on_height_changed)
        resolution_input_layout.addWidget(self.height_spinbox)

        # 프리셋 버튼들
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("프리셋:"))

        preset_720p_btn = QPushButton("720p")
        preset_720p_btn.clicked.connect(lambda: self.set_resolution_preset(1280, 720))
        preset_layout.addWidget(preset_720p_btn)

        preset_1080p_btn = QPushButton("1080p")
        preset_1080p_btn.clicked.connect(lambda: self.set_resolution_preset(1920, 1080))
        preset_layout.addWidget(preset_1080p_btn)

        preset_4k_btn = QPushButton("4K")
        preset_4k_btn.clicked.connect(lambda: self.set_resolution_preset(3840, 2160))
        preset_layout.addWidget(preset_4k_btn)

        original_btn = QPushButton("원본 크기")
        original_btn.clicked.connect(self.set_original_resolution)
        preset_layout.addWidget(original_btn)

        preset_layout.addStretch()

        resolution_input_layout.addStretch()
        resolution_layout.addLayout(resolution_input_layout)
        resolution_layout.addLayout(preset_layout)

        # 스케일링 모드 선택
        scale_mode_group = QGroupBox("스케일링 모드")
        scale_mode_layout = QVBoxLayout(scale_mode_group)

        self.scale_button_group = QButtonGroup()

        self.exact_radio = QRadioButton("정확한 크기 (종횡비 무시, 늘어날 수 있음)")
        self.aspect_fit_radio = QRadioButton("종횡비 유지 - 맞춤 (지정 크기 안에 맞춤)")
        self.aspect_pad_radio = QRadioButton("종횡비 유지 - 패딩 (검은 여백으로 정확한 크기)")

        self.aspect_fit_radio.setChecked(True)  # 기본값

        self.scale_button_group.addButton(self.exact_radio, 0)
        self.scale_button_group.addButton(self.aspect_fit_radio, 1)
        self.scale_button_group.addButton(self.aspect_pad_radio, 2)

        scale_mode_layout.addWidget(self.exact_radio)
        scale_mode_layout.addWidget(self.aspect_fit_radio)
        scale_mode_layout.addWidget(self.aspect_pad_radio)

        resolution_layout.addWidget(scale_mode_group)


        settings_layout.addWidget(resolution_group)

        layout.addWidget(settings_group)

        # 변환 버튼
        button_layout = QHBoxLayout()
        self.convert_btn = QPushButton("변환 시작")
        self.convert_btn.clicked.connect(self.start_conversion)
        self.convert_btn.setEnabled(False)
        button_layout.addWidget(self.convert_btn)

        self.stop_btn = QPushButton("변환 중지")
        self.stop_btn.clicked.connect(self.stop_conversion)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        layout.addLayout(button_layout)

        # 진행 상황
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # 상태 표시
        self.status_label = QLabel("상태: 준비")
        layout.addWidget(self.status_label)

    def browse_input(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "비디오 파일 선택", "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v)"
        )
        if file_path:
            self.input_path = file_path
            self.input_path_label.setText(os.path.basename(file_path))

            # 자동으로 출력 경로를 입력 파일이 있는 폴더로 설정
            input_directory = os.path.dirname(file_path)
            self.output_path = input_directory
            self.output_path_label.setText(input_directory)

            # 자동으로 파일명 설정
            filename_without_ext = os.path.splitext(os.path.basename(file_path))[0]
            self.filename_input.setText(f"{filename_without_ext}_converted")

            # 원본 비디오 정보 추출
            self.extract_video_info(file_path)

            self.check_ready()

    def browse_output(self):
        folder_path = QFileDialog.getExistingDirectory(self, "출력 폴더 선택")
        if folder_path:
            self.output_path = folder_path
            self.output_path_label.setText(folder_path)
            self.check_ready()

    def check_ready(self):
        if self.input_path and self.output_path and self.filename_input.text().strip():
            self.convert_btn.setEnabled(True)

    def start_conversion(self):
        if not self.input_path or not self.output_path:
            QMessageBox.warning(self, "경고", "입력 파일과 출력 경로를 선택해주세요.")
            return

        filename = self.filename_input.text().strip()
        if not filename:
            QMessageBox.warning(self, "경고", "출력 파일명을 입력해주세요.")
            return

        output_format = self.format_combo.currentText()
        pixel_format = self.pixel_combo.currentText()
        width = self.width_spinbox.value()
        height = self.height_spinbox.value()
        # 스케일링 모드 결정
        if self.exact_radio.isChecked():
            scale_mode = 'exact'
        elif self.aspect_fit_radio.isChecked():
            scale_mode = 'aspect_fit'
        else:
            scale_mode = 'aspect_pad'

        # 전체 출력 경로 생성
        full_output_path = os.path.join(self.output_path, f"{filename}.{output_format}")

        # 파일이 이미 존재하는지 확인
        if os.path.exists(full_output_path):
            reply = QMessageBox.question(
                self, "파일 존재",
                f"파일 '{filename}.{output_format}'이 이미 존재합니다. 덮어쓰시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.video_converter = VideoConverter(
            self.input_path, full_output_path, output_format, pixel_format, width, height, scale_mode, self.rotation
        )

        self.video_converter.progress_updated.connect(self.update_progress)
        self.video_converter.conversion_finished.connect(self.on_conversion_finished)
        self.video_converter.error_occurred.connect(self.on_error_occurred)
        self.video_converter.status_updated.connect(self.update_status)

        self.video_converter.start()

        self.convert_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("상태: 변환 중...")
        self.progress_bar.setRange(0, 0)  # 무한 진행바

    def stop_conversion(self):
        if self.video_converter:
            self.video_converter.stop()
            self.video_converter.wait()

        self.convert_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("상태: 변환 중지됨")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, message):
        self.status_label.setText(f"상태: {message}")

    def on_conversion_finished(self, message):
        self.convert_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText(f"상태: {message}")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "완료", message)

    def on_error_occurred(self, error_message):
        self.convert_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText(f"상태: 오류 - {error_message}")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, "오류", error_message)

    def extract_video_info(self, file_path):
        try:
            # ffprobe를 사용하여 비디오 정보 추출
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', '-select_streams', 'v:0', file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                data = json.loads(result.stdout)
                if 'streams' in data and len(data['streams']) > 0:
                    stream = data['streams'][0]
                    self.original_width = stream.get('width', 0)
                    self.original_height = stream.get('height', 0)

                    # 회전 정보 추출
                    self.rotation = 0
                    if 'side_data_list' in stream:
                        for side_data in stream['side_data_list']:
                            if side_data.get('side_data_type') == 'Display Matrix':
                                self.rotation = side_data.get('rotation', 0)
                                break

                    # 회전을 고려한 실제 표시 해상도 계산
                    if abs(self.rotation) == 90 or abs(self.rotation) == 270:
                        # 90도 회전된 경우 가로/세로 바뀜
                        self.display_width = self.original_height
                        self.display_height = self.original_width
                        display_text = f"원본 해상도: {self.display_width}x{self.display_height}px (회전된 상태)"
                    else:
                        self.display_width = self.original_width
                        self.display_height = self.original_height
                        display_text = f"원본 해상도: {self.display_width}x{self.display_height}px"

                    self.original_resolution_label.setText(display_text)
                else:
                    self.original_resolution_label.setText("원본 해상도: 정보를 가져올 수 없음")
            else:
                self.original_resolution_label.setText("원본 해상도: FFprobe 오류")
        except Exception as e:
            self.original_resolution_label.setText(f"원본 해상도: 오류 - {str(e)}")

    def set_resolution_preset(self, width, height):
        self.updating_aspect_ratio = True
        self.width_spinbox.setValue(width)
        self.height_spinbox.setValue(height)
        self.updating_aspect_ratio = False

    def set_original_resolution(self):
        if self.display_width > 0 and self.display_height > 0:
            self.updating_aspect_ratio = True
            self.width_spinbox.setValue(self.display_width)
            self.height_spinbox.setValue(self.display_height)
            self.updating_aspect_ratio = False
        else:
            QMessageBox.warning(self, "경고", "원본 해상도 정보가 없습니다. 먼저 비디오 파일을 선택해주세요.")

    def on_width_changed(self, value):
        if self.aspect_fit_radio.isChecked() and not self.updating_aspect_ratio:
            if self.display_width > 0 and self.display_height > 0:
                self.updating_aspect_ratio = True
                # 표시 기준 종횡비 사용 (회전이 고려된 실제 보이는 비율)
                display_aspect_ratio = self.display_height / self.display_width

                new_height = int(value * display_aspect_ratio)
                # 짝수로 조정
                new_height = new_height + (new_height % 2)
                self.height_spinbox.setValue(new_height)
                self.updating_aspect_ratio = False

    def on_height_changed(self, value):
        if self.aspect_fit_radio.isChecked() and not self.updating_aspect_ratio:
            if self.display_width > 0 and self.display_height > 0:
                self.updating_aspect_ratio = True
                # 표시 기준 종횡비 사용 (회전이 고려된 실제 보이는 비율)
                display_aspect_ratio = self.display_width / self.display_height

                new_width = int(value * display_aspect_ratio)
                # 짝수로 조정
                new_width = new_width + (new_width % 2)
                self.width_spinbox.setValue(new_width)
                self.updating_aspect_ratio = False


def main():
    app = QApplication(sys.argv)
    window = VideoConverterApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()