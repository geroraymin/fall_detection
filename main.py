import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QSizePolicy
from object_detect import VideoBox
import pygame # 📍 pygame 라이브러리 임포트

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('쓰러짐 감지 시스템')
        self.resize(1200,700)

        # 📍 Pygame Mixer 초기화 (사운드 재생용)
        pygame.mixer.init()

        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # WARNING 라벨 (숨김 상태)
        self.warning_label = QLabel("WARNING", self)
        self.warning_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.warning_label.setStyleSheet("""
            color: red;
            font-size: 60px;
            font-weight: bold;
            background-color: white;
        """)
        self.warning_label.hide()

        # 카메라 출력 라벨
        self.video_label = QLabel(self)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")

        # 레이아웃 배치
        layout.addWidget(self.video_label, stretch=1)
        self.setLayout(layout)

        # VideoBox 연결
        self.vb = VideoBox(
            address='쓰러짐 감지!',
            frame=self,
            label=self.video_label,
            source=0,
            warning_label=None
        )

        # 깜빡임 타이머
        self.is_warning_active = False
        self.blink_state = False
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_warning_text_visibility)

        # 메인 비디오 타이머
        self.main_video_timer = QTimer()
        self.main_video_timer.timeout.connect(self.update_video_and_warning)
        self.main_video_timer.start(30)

    def update_video_and_warning(self):
        self.vb.video_play()

        if self.vb.is_fall_persistent:
            if not self.is_warning_active:
                self.is_warning_active = True
                self.blink_timer.start(500)
                # 📍 위급 상황 시작 시 BGM 재생
                self.play_warning_sound()
        else:
            if self.is_warning_active:
                self.is_warning_active = False
                self.blink_timer.stop()
                self.blink_state = False
                # 📍 위급 상황 해제 시 BGM 정지
                self.stop_warning_sound()
                # 텍스트가 사라진 상태로 끝나도록 보장
                self.vb.set_warning_text_visibility(False)

    def toggle_warning_text_visibility(self):
        self.blink_state = not self.blink_state
        self.vb.set_warning_text_visibility(self.blink_state)

    # 📍 새로운 메서드 추가: 경고음 재생
    def play_warning_sound(self):
        try:
            audio_file_path ='C:/Users/suyeo/Downloads/fall_detection_project/siren.mp3'
            
            pygame.mixer.music.load(audio_file_path)
            pygame.mixer.music.play(-1) # -1: 무한 반복 재생
            print("경고음 재생 시작.")
        except pygame.error as e:
            print(f"오디오 파일 재생 오류: {e}")
            print("오디오 파일 경로가 올바른지, 파일이 손상되지 않았는지 확인해주세요.")

    # 📍 새로운 메서드 추가: 경고음 정지
    def stop_warning_sound(self):
        pygame.mixer.music.stop()
        print("경고음 재생 정지.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())