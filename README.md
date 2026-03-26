# 🤖 Voice-Controlled Dual-Arm Robot (Ollama + ROS2 + Isaac Sim)

이 프로젝트는 음성 명령을 통해 차동 구동 로봇 및 양팔 로봇을 제어하는 시스템입니다. 로컬 LLM(Ollama)을 사용하여 사용자의 의도를 분석하고, 이를 구조화된 명령(JSON)으로 변환하여 로봇에게 전달합니다.

## 🌟 주요 기능
- **STT (Speech-to-Text)**: Faster-Whisper를 이용한 실시간 한국어 음성 인식.
- **Intelligence (LLM)**: Ollama(Llama 3.1 8B)를 통한 자연어 명령 파싱 및 의도 추출.
- **TTS (Text-to-Speech)**: MeloTTS/Piper를 이용한 고품질 한국어 음성 안내.
- **Verification Loop**: 명령 실행 전 사용자에게 확인을 받는 안전 로직 포함.
- **Simulation**: NVIDIA Isaac Sim 5.1 및 ROS2 Humble 연동 지원.

## 🛠️ 시스템 환경
- **OS**: Ubuntu 22.04 (Jammy Jellyfish)
- **Middleware**: ROS2 Humble
- **Simulator**: NVIDIA Isaac Sim 5.1
- **Hardware**: GPU VRAM 24GB 권장 (Isaac Sim + LLM 병행 구동용)

## 📦 설치 방법

### 1. 시스템 의존성 설치
```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-pyaudio espeak libasound2-dev libsndfile1
```

### 2. Python 환경 설정 (uv 사용)
```bash
# 가상환경 생성 및 패키지 설치
uv pip install ollama speechrecognition faster-whisper PyAudio pyttsx3 pygame
uv pip install git+https://github.com/myshell-ai/MeloTTS.git
uv pip install unidic-lite mecab-python3
```

### 3. Ollama 로봇 모델 등록
```bash
# robot_modelfile이 있는 디렉토리에서 실행
ollama create robot_commander -f robot_modelfile
```

## 🚀 실행 가이드

### 1. 지능형 음성 제어 루프 실행
사용자의 음성을 듣고, 분석하여 확인 메시지를 내보내는 메인 루프를 실행합니다.
```bash
python3 robot_continuous_loop.py
```

### 2. 테스트 시나리오
1.  로봇이 "준비되었습니다"라고 말하면 마이크에 대고 명령을 내립니다.
    - *예: "거실로 가서 오른팔로 물병 좀 집어줘"*
2.  로봇이 이해한 내용을 바탕으로 확인 질문을 합니다.
    - *로봇: "거실로 이동하여 오른팔로 물병을 집을까요? '응' 혹은 '아니'라고 대답해 주세요."*
3.  "응"이라고 답하면 실제 로봇 제어 명령(JSON)이 생성됩니다.

## 📂 파일 구조
- `robot_continuous_loop.py`: 메인 상태 머신 및 음성 대화 루프.
- `robot_modelfile`: Ollama용 시스템 프롬프트 및 액션 정의.
- `test_robot_parser.py`: LLM 파싱 논리 유닛 테스트.
- `voice_to_robot.py`: 단순 음성-JSON 변환 테스트 스크립트.
- `robot_voice_control_plan.txt`: 프로젝트 전체 아키텍처 및 구현 계획.

## ⚠️ 참고 사항 (Troubleshooting)
- **MeloTTS 오류**: `No module named unidic` 발생 시 `uv pip install unidic` 후 `python3 -m unidic download`를 실행하거나 `unidic-lite`를 사용하세요.
- **VRAM 부족**: Isaac Sim 구동 시 메모리가 부족하면 Faster-Whisper 모델을 `base`로 설정하고 `device="cpu"`를 고려하세요.
