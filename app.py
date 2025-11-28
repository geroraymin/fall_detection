import os
import sys
import cv2
import numpy as np
import torch
import time
import base64
from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
# 프로젝트 경로 설정
FILE = os.path.abspath(__file__)
PROJECT_DIR = os.path.dirname(FILE)
YOLOV5_DIR = os.path.join(PROJECT_DIR, 'yolov5')
sys.path.insert(0, YOLOV5_DIR)
sys.path.insert(0, PROJECT_DIR)

# YOLOv5 관련 import 시도
try:
    from models.yolo import DetectionModel
    from models.common import DetectMultiBackend
    from utils.general import non_max_suppression
except ImportError:
    try:
        from yolov5.models.yolo import DetectionModel
        from yolov5.models.common import DetectMultiBackend
        from yolov5.utils.general import non_max_suppression
    except ImportError as e:
        print(f"YOLOv5 import 오류: {e}")
        DetectionModel = None
        DetectMultiBackend = None
        non_max_suppression = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fall_detection_secret_key'
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    max_http_buffer_size=1000000,  # 1MB 제한
    ping_timeout=60,
    ping_interval=25
)

# YOLO 모델 로드
weights_path = os.path.join(PROJECT_DIR, 'yolov5s.pt')

model = None
if DetectMultiBackend is not None:
    try:
        if DetectionModel is not None:
            with torch.serialization.safe_globals({'models.yolo.DetectionModel': DetectionModel}):
                model = DetectMultiBackend(weights_path, device='cpu')
        else:
            model = DetectMultiBackend(weights_path, device='cpu')
        print(f"모델 로드 성공: {weights_path}")
    except Exception as e:
        print(f"모델 로드 실패: {e}")
        model = None
else:
    print("DetectMultiBackend를 로드할 수 없습니다.")

# 전역 변수
fall_detection_state = {
    'is_fall_persistent': False,
    'show_warning_text': False,
    'check': 0,
    'start': 0,
    'end': 0
}

def process_frame(frame_data):
    """프레임을 처리하고 쓰러짐 감지"""
    global fall_detection_state
    
    try:
        # Base64 디코딩
        if ',' in frame_data:
            img_data = base64.b64decode(frame_data.split(',')[1])
        else:
            img_data = base64.b64decode(frame_data)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None or model is None:
            return None, False
        
        # 프레임 크기 조정 (메모리 최적화) - 매우 작게
        max_width = 320
        h, w = frame.shape[:2]
        if w > max_width:
            scale = max_width / w
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
        
        # 메모리 정리
        del img_data, nparr
        
        # YOLO 입력 준비
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (640, 640))
        img = img.transpose((2, 0, 1))
        img = np.ascontiguousarray(img)
        img = torch.from_numpy(img).float()
        img /= 255.0
        img = img.unsqueeze(0)
        
        # YOLO 추론 (no_grad로 메모리 절약)
        with torch.no_grad():
            results = model(img)
            results = non_max_suppression(results, conf_thres=0.25, iou_thres=0.45)
            preds = results[0]
        
        # 쓰러짐 감지 확인
        is_fall_detected_in_frame = False
        for *xyxy, conf, cls in preds:
            if conf > 0.4:
                class_name = model.names[int(cls)]
                if class_name.lower() in ['fallen', 'lying']:
                    is_fall_detected_in_frame = True
                    break
        
        # 쓰러짐 지속 시간 확인
        fall_detection_state['is_fall_persistent'] = False
        
        if is_fall_detected_in_frame:
            if fall_detection_state['check'] == 0:
                fall_detection_state['start'] = time.time()
                fall_detection_state['check'] = 4
            else:
                fall_detection_state['end'] = time.time()
            
            elapsed = fall_detection_state['end'] - fall_detection_state['start'] if fall_detection_state['end'] and fall_detection_state['start'] else 0
            
            if elapsed >= 2:  # 2초 이상 지속
                fall_detection_state['is_fall_persistent'] = True
                
                # 경고판 그리기
                h, w, _ = frame.shape
                overlay = frame.copy()
                
                red_color = (0, 0, 255)
                white_color = (255, 255, 255)
                
                # 외부 빨간색 테두리
                border_thickness = int(w * 0.01)
                cv2.rectangle(overlay, (0, 0), (w, h), red_color, border_thickness)
                
                # 상단 빨간색 바
                top_bar_height = int(h * 0.15)
                cv2.rectangle(overlay, (border_thickness, border_thickness),
                              (w - border_thickness, top_bar_height + border_thickness),
                              red_color, -1)
                
                # WARNING 텍스트 (깜빡임 상태에 따라)
                if fall_detection_state['show_warning_text']:
                    text = "WARNING"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = h * 0.0015
                    font_thickness = 2
                    
                    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, font_thickness)
                    
                    text_x = (w - text_w) // 2
                    text_y = border_thickness + top_bar_height // 2 + text_h // 2
                    
                    # 느낌표 그리기
                    ex_height = int(top_bar_height * 0.5)
                    ex_width = int(top_bar_height * 0.1)
                    ex_top_y = border_thickness + top_bar_height // 2 - ex_height // 2
                    
                    # 왼쪽 느낌표
                    ex_top_x_left = text_x - int(w * 0.08) - ex_width // 2
                    cv2.rectangle(overlay, (ex_top_x_left, ex_top_y), 
                                  (ex_top_x_left + ex_width, ex_top_y + ex_height - int(ex_height*0.2)), 
                                  white_color, -1)
                    cv2.circle(overlay, (ex_top_x_left + ex_width // 2, ex_top_y + ex_height - int(ex_height*0.05)), 
                               int(ex_width*0.8), white_color, -1)
                    
                    # WARNING 텍스트
                    cv2.putText(overlay, text, (text_x, text_y), font, font_scale, white_color, font_thickness, cv2.LINE_AA)
                    
                    # 오른쪽 느낌표
                    ex_top_x_right = text_x + text_w + int(w * 0.08) - ex_width // 2
                    cv2.rectangle(overlay, (ex_top_x_right, ex_top_y), 
                                  (ex_top_x_right + ex_width, ex_top_y + ex_height - int(ex_height*0.2)), 
                                  white_color, -1)
                    cv2.circle(overlay, (ex_top_x_right + ex_width // 2, ex_top_y + ex_height - int(ex_height*0.05)), 
                               int(ex_width*0.8), white_color, -1)
                
                # 하단 빨간색/흰색 줄무늬
                stripe_height = int(h * 0.05)
                num_stripes = 5
                stripe_width = (w - 2 * border_thickness) // num_stripes
                
                bottom_bar_y = h - border_thickness - stripe_height
                cv2.rectangle(overlay, (border_thickness, bottom_bar_y),
                              (w - border_thickness, h - border_thickness),
                              white_color, -1)
                
                for i in range(num_stripes):
                    start_x = border_thickness + i * stripe_width
                    end_x = start_x + int(stripe_width * 0.7)
                    cv2.rectangle(overlay, (start_x, bottom_bar_y),
                                  (end_x, h - border_thickness),
                                  red_color, -1)
                
                # 오버레이 합성
                alpha = 0.6
                cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        else:
            fall_detection_state['check'] = 0
            fall_detection_state['start'] = 0
            fall_detection_state['end'] = 0
            fall_detection_state['is_fall_persistent'] = False
        
        # 감지된 객체 시각화
        for *xyxy, conf, cls in preds:
            if conf > 0.4:
                class_name = model.names[int(cls)]
                label = f'{class_name} {conf:.2f}'
                is_fallen_class = class_name.lower() in ['fallen', 'lying']
                
                box_color = (255, 0, 0)
                text_color = (255, 0, 0)
                box_thickness = 2
                
                if fall_detection_state['is_fall_persistent'] and is_fallen_class:
                    box_color = (0, 0, 255)
                    text_color = (0, 0, 255)
                    box_thickness = 4
                
                cv2.rectangle(frame,
                              (int(xyxy[0]), int(xyxy[1])),
                              (int(xyxy[2]), int(xyxy[3])),
                              box_color, box_thickness)
                cv2.putText(frame, label,
                            (int(xyxy[0]), int(xyxy[1]) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            text_color, 2)
        
        # 프레임을 JPEG로 인코딩 (품질 더 낮춤 - 메모리 최적화)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
        _, buffer = cv2.imencode('.jpg', frame, encode_param)
        frame_bytes = buffer.tobytes()
        
        # 적극적인 메모리 정리 (overlay는 조건부로만 생성됨)
        del img, buffer, frame
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        return frame_bytes, fall_detection_state['is_fall_persistent']
        
    except Exception as e:
        print(f"프레임 처리 오류: {e}")
        import traceback
        traceback.print_exc()
        # 에러 발생 시에도 메모리 정리
        import gc
        gc.collect()
        return None, False

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('클라이언트 연결됨')
    emit('connected', {'data': '연결 성공'})

@socketio.on('disconnect')
def handle_disconnect():
    print('클라이언트 연결 해제됨')

@socketio.on('video_frame')
def handle_video_frame(data):
    """클라이언트로부터 비디오 프레임 수신 및 처리"""
    try:
        frame_bytes, is_fall = process_frame(data['frame'])
        
        if frame_bytes:
            # 처리된 프레임을 클라이언트에게 전송
            frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
            emit('processed_frame', {
                'frame': f'data:image/jpeg;base64,{frame_base64}',
                'is_fall': is_fall
            })
            # 적극적인 메모리 정리
            del frame_bytes, frame_base64
            import gc
            gc.collect()
    except Exception as e:
        print(f"비디오 프레임 처리 오류: {e}")
        import traceback
        traceback.print_exc()
        # 에러 발생 시에도 메모리 정리
        import gc
        gc.collect()

@socketio.on('toggle_warning')
def handle_toggle_warning(data):
    """WARNING 텍스트 깜빡임 토글"""
    global fall_detection_state
    fall_detection_state['show_warning_text'] = data['show']

if __name__ == '__main__':
    print("쓰러짐 감지 웹 애플리케이션 시작...")
    print(f"프로젝트 디렉토리: {PROJECT_DIR}")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
