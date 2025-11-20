# 쓰러짐 감지 시스템 (Fall Detection System)

PyQt5 데스크톱 애플리케이션을 Flask 기반 웹 애플리케이션으로 변환한 프로젝트입니다.

## 📋 주요 기능

- **실시간 비디오 스트리밍**: 웹 브라우저에서 카메라 접근
- **AI 쓰러짐 감지**: YOLOv5 모델을 사용한 실시간 감지
- **경고 시스템**: 2초 이상 쓰러짐 지속 시 경고
- **시각적 경고**: 빨간색 테두리, WARNING 텍스트, 줄무늬 패턴
- **음향 경고**: 사이렌 자동 재생

## 🎨 디자인

원본 PyQt5 애플리케이션의 디자인을 100% 유지:
- 빨간색 경고 테두리
- WARNING 텍스트 + 느낌표 아이콘
- 빨간색/흰색 줄무늬 패턴
- 500ms 간격 깜빡임 효과

## 💻 시스템 요구사항

### 최소 요구사항
- **RAM**: 2GB 이상 (YOLOv5 모델 로드 시 ~500MB 사용)
- **Python**: 3.8 이상
- **웹캠**: 카메라 장치 필요

### 권장 요구사항
- **RAM**: 4GB 이상
- **CPU**: 4코어 이상
- **GPU**: 선택사항 (CPU 모드로 실행 가능)

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/geroraymin/fall_detection.git
cd fall_detection
```

### 2. YOLOv5 설치
```bash
git clone https://github.com/ultralytics/yolov5.git
pip install -r yolov5/requirements.txt
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 서버 실행
```bash
python app.py
```

### 5. 브라우저 접속
```
http://localhost:5000
```

## 📁 프로젝트 구조

```
fall_detection/
├── app.py                 # Flask 서버 (메인)
├── templates/
│   └── index.html        # 웹 인터페이스
├── static/
│   └── siren.mp3         # 경고음
├── yolov5/               # YOLOv5 모델 (git submodule)
├── yolov5s.pt            # 학습된 모델 가중치
├── requirements.txt      # Python 패키지
└── README.md            # 문서

# 원본 PyQt5 파일들 (참고용)
├── main.py              # PyQt5 메인 애플리케이션
├── object_detect.py     # 객체 감지 로직
├── board.py             # 게시판 UI
└── download_dataset.py  # 데이터셋 다운로드
```

## 🐛 문제 해결

### 메모리 부족 (OOM) 오류

YOLOv5 모델은 약 500MB의 RAM을 사용합니다. 1GB RAM 시스템에서는 다음과 같은 문제가 발생할 수 있습니다:

**증상:**
- 서버가 "Killed" 메시지와 함께 종료됨
- 프레임 처리 중 서버 응답 없음

**해결 방법:**

1. **프레임 크기 축소** (app.py에서):
   ```python
   max_width = 320  # 더 작게 (예: 240)
   ```

2. **프레임 레이트 감소** (templates/index.html에서):
   ```javascript
   setTimeout(..., 500);  // 더 길게 (예: 1000 = 1fps)
   ```

3. **JPEG 품질 낮추기** (app.py에서):
   ```python
   encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]  # 더 낮게 (예: 40)
   ```

4. **더 많은 RAM 할당** (권장):
   - 최소 2GB RAM 환경에서 실행

### Socket.IO "Too many packets" 오류

**해결 방법:**
프레임 전송 간격을 늘리세요 (`templates/index.html`):
```javascript
setTimeout(() => {
    isProcessing = false;
    sendFrames();
}, 1000);  // 1초 = 1fps
```

### 카메라 권한 오류

브라우저 설정에서 카메라 권한을 허용해야 합니다:
- Chrome: 설정 > 개인정보 및 보안 > 사이트 설정 > 카메라
- Firefox: 설정 > 개인정보 및 보안 > 권한 > 카메라
- HTTPS 필요 (localhost는 예외)

## 🔧 기술 스택

- **Backend**: Flask + Flask-SocketIO
- **Frontend**: HTML5, CSS3, JavaScript
- **AI**: YOLOv5 (PyTorch)
- **실시간 통신**: Socket.IO
- **비디오**: WebRTC (getUserMedia API)

## 📊 성능 최적화

현재 설정 (낮은 메모리 환경):
- 프레임 크기: 320x240
- 프레임 레이트: 2 FPS
- JPEG 품질: 50%
- Socket.IO 버퍼: 1MB 제한

권장 설정 (충분한 메모리):
- 프레임 크기: 640x480
- 프레임 레이트: 10-15 FPS
- JPEG 품질: 70%

## 🤝 기여

Pull Request를 환영합니다!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 🙏 감사의 말

- [YOLOv5](https://github.com/ultralytics/yolov5) - Ultralytics
- [Flask](https://flask.palletsprojects.com/)
- [Socket.IO](https://socket.io/)

## 📞 문의

문제가 발생하면 [Issues](https://github.com/geroraymin/fall_detection/issues) 페이지에 등록해주세요.
