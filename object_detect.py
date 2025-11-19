import cv2
import numpy as np
import torch
import sys
import os
import time
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
import pathlib
pathlib.PosixPath = pathlib.WindowsPath

FILE = os.path.abspath(__file__)
PROJECT_DIR = os.path.dirname(FILE)
YOLOV5_DIR = os.path.join(PROJECT_DIR, 'yolov5')
sys.path.append(YOLOV5_DIR)
sys.path.append(PROJECT_DIR)

from yolov5.models.yolo import DetectionModel
from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import non_max_suppression

weights_path = r'C:\Users\suyeo\Downloads\fall_detection_project\yolov5\runs\train\weights\best_windows.pt'

with torch.serialization.safe_globals({'models.yolo.DetectionModel': DetectionModel}):
    model = DetectMultiBackend(weights_path, device='cpu')


class VideoBox:
    def __init__(self, address, frame, label, source, warning_label):
        self.video_frame = frame
        self.video_label = label
        # self.warning_label은 이제 사용하지 않습니다.
        self.source = source
        self.cap = cv2.VideoCapture(self.source)

        self.check = 0
        self.start = 0
        self.end = 0

        # 📍 추가된 속성: 현재 위급 상황 상태와 경고 텍스트 표시 여부
        self.is_fall_persistent = False
        self.show_warning_text_in_frame = False # 깜빡임 상태를 저장

    # 📍 새로운 메서드: 경고 텍스트 표시 여부 설정
    def set_warning_text_visibility(self, visible):
        self.show_warning_text_in_frame = visible

    def video_play(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # ----- YOLO 입력 준비 -----
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (640, 640))
        img = img.transpose((2, 0, 1))
        img = np.ascontiguousarray(img)
        img = torch.from_numpy(img).float()
        img /= 255.0
        img = img.unsqueeze(0)

        # ----- YOLO 추론 -----
        results = model(img)
        results = non_max_suppression(results, conf_thres=0.25, iou_thres=0.45)
        preds = results[0]

        # 1. 현재 프레임에서 쓰러짐이 감지되었는지 먼저 확인
        is_fall_detected_in_frame = False
        for *xyxy, conf, cls in preds:
            if conf > 0.4:
                class_name = model.names[int(cls)]
                if class_name.lower() in ['fallen', 'lying']:
                    is_fall_detected_in_frame = True
                    break

        # 2. 쓰러짐 감지 상태 및 지속 시간 확인
        # 📍 self.is_fall_persistent 업데이트
        old_is_fall_persistent = self.is_fall_persistent # 이전 상태 저장
        self.is_fall_persistent = False # 기본값은 False

        if is_fall_detected_in_frame:
            if self.check == 0:
                self.start = time.time()
                self.check = 4
            else:
                self.end = time.time()

            elapsed = self.end - self.start if self.end and self.start else 0

            if elapsed >= 2:  # 3초 이상 지속된 경우
                self.is_fall_persistent = True # 📍 상태 True로 변경

                # 경고판 그리기 로직 (is_fall_persistent가 True일 때만 실행)
                h, w, _ = frame.shape
                overlay = frame.copy() # 경고판을 그릴 레이어

                # 경고판 테두리 및 배경색
                red_color = (0, 0, 255) # BGR
                white_color = (255, 255, 255) # BGR
                
                # 외부 빨간색 테두리
                border_thickness = int(w * 0.01)
                cv2.rectangle(overlay, (0, 0), (w, h), red_color, border_thickness)

                # 상단 빨간색 바
                top_bar_height = int(h * 0.15)
                cv2.rectangle(overlay, (border_thickness, border_thickness),
                              (w - border_thickness, top_bar_height + border_thickness),
                              red_color, -1) # 채워진 사각형

                # 📍 WARNING 텍스트 및 느낌표 아이콘 그리기 (self.show_warning_text_in_frame이 True일 때만)
                if self.show_warning_text_in_frame:
                    text = "WARNING"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = h * 0.0015
                    font_thickness = 2

                    # 텍스트 크기 계산
                    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, font_thickness)

                    # 텍스트 위치 계산 (중앙 정렬)
                    text_x = (w - text_w) // 2
                    text_y = border_thickness + top_bar_height // 2 + text_h // 2
                    
                    # 간단한 느낌표 그리기 (사각형 + 점)
                    ex_height = int(top_bar_height * 0.5)
                    ex_width = int(top_bar_height * 0.1)
                    ex_top_y = border_thickness + top_bar_height // 2 - ex_height // 2

                    # 왼쪽 느낌표
                    ex_top_x_left = text_x - int(w * 0.08) - ex_width // 2
                    cv2.rectangle(overlay, (ex_top_x_left, ex_top_y), (ex_top_x_left + ex_width, ex_top_y + ex_height - int(ex_height*0.2)), white_color, -1)
                    cv2.circle(overlay, (ex_top_x_left + ex_width // 2, ex_top_y + ex_height - int(ex_height*0.05)), int(ex_width*0.8), white_color, -1)

                    # WARNING 텍스트 그리기
                    cv2.putText(overlay, text, (text_x, text_y), font, font_scale, white_color, font_thickness, cv2.LINE_AA)
                    
                    # 오른쪽 느낌표
                    ex_top_x_right = text_x + text_w + int(w * 0.08) - ex_width // 2
                    cv2.rectangle(overlay, (ex_top_x_right, ex_top_y), (ex_top_x_right + ex_width, ex_top_y + ex_height - int(ex_height*0.2)), white_color, -1)
                    cv2.circle(overlay, (ex_top_x_right + ex_width // 2, ex_top_y + ex_height - int(ex_height*0.05)), int(ex_width*0.8), white_color, -1)


                # 하단 빨간색/흰색 줄무늬
                stripe_height = int(h * 0.05)
                num_stripes = 5 # 줄무늬 개수
                stripe_width = (w - 2 * border_thickness) // num_stripes

                bottom_bar_y = h - border_thickness - stripe_height
                cv2.rectangle(overlay, (border_thickness, bottom_bar_y),
                              (w - border_thickness, h - border_thickness),
                              white_color, -1) # 흰색 바 배경

                for i in range(num_stripes):
                    start_x = border_thickness + i * stripe_width
                    end_x = start_x + int(stripe_width * 0.7) # 빨간색 줄무늬 폭
                    cv2.rectangle(overlay, (start_x, bottom_bar_y),
                                  (end_x, h - border_thickness),
                                  red_color, -1)

                # 경고판 오버레이를 원본 프레임에 합성 (투명도 적용)
                alpha = 0.6 # 경고판의 투명도
                cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # 쓰러짐이 감지되지 않으면 모든 상태 초기화
        else:
            self.check = 0
            self.start = 0
            self.end = 0
            self.is_fall_persistent = False # 📍 상태 False로 변경


        # 3. 감지된 객체들에 대한 시각화 처리
        for *xyxy, conf, cls in preds:
            if conf > 0.4:
                class_name = model.names[int(cls)]
                label = f'{class_name} {conf:.2f}'
                is_fallen_class = class_name.lower() in ['fallen', 'lying']

                # 기본 색상 및 두께
                box_color = (255, 0, 0) # 파란색
                text_color = (255, 0, 0) # 파란색
                box_thickness = 2 # 기본 테두리 두께

                # 만약 3초 이상 쓰러짐이 지속됐고, 현재 객체가 'fallen' 또는 'lying' 이라면
                if self.is_fall_persistent and is_fallen_class: # 📍 self.is_fall_persistent 사용
                    box_color = (0, 0, 255)  # 테두리 색상을 빨간색(BGR)으로 변경
                    text_color = (0, 0, 255) # 라벨 색상을 빨간색(BGR)으로 변경
                    box_thickness = 4 # 위험 상황일 때 테두리 두께

                # 테두리 그리기
                cv2.rectangle(frame,
                              (int(xyxy[0]), int(xyxy[1])),
                              (int(xyxy[2]), int(xyxy[3])),
                              box_color, box_thickness) # 두께 변수 적용
                # 라벨 텍스트 표시
                cv2.putText(frame, label,
                            (int(xyxy[0]), int(xyxy[1]) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            text_color, 2)

        # 영상 PyQt 라벨에 표시
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        q_img = QImage(frame_rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        label_width = self.video_label.width()
        label_height = self.video_label.height()

        scaled_pixmap = pixmap.scaled(label_width, label_height,
                                      Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.video_label.setPixmap(scaled_pixmap)