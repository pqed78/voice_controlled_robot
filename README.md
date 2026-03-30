# 🤖 Voice-Controlled Dual-Arm Robot in Isaac Sim

이 프로젝트는 자연어 음성 명령을 분석하여 **NVIDIA Isaac Sim** 환경의 듀얼 암 로봇을 제어하는 지능형 인터페이스 시스템입니다. ROS2 Humble을 통해 실제 로봇 제어 스택과 연동됩니다.

## ✨ 주요 기능

- **호출어 감지 (Wake-up Word):** "저기요" 또는 "로봇아" 등의 호출어로 명령 대기 상태로 전환됩니다.
- **순차적 명령어 실행:** "거실로 가서 사과를 집어줘"와 같은 다중 명령을 순서대로 분석하고 실행합니다.
- **고성능 로컬 AI:** STT(Faster-Whisper large-v3-turbo), LLM(Ollama), TTS(MeloTTS)를 모두 로컬 GPU에서 가속하여 빠른 응답성을 제공합니다.
- **ROS2 액션 연동:** Nav2 `navigate_to_pose` 액션을 통해 로봇의 이동 완료를 감지하고 다음 행동을 수행합니다.

## 🚀 실행 가이드

### 1. 환경 설정 (Ubuntu 22.04 + CUDA 12.x)
```bash
# 시스템 라이브러리 설치
sudo apt-get install -y portaudio19-dev libasound2-dev libsndfile1 espeak aplay

# 패키지 매니저 uv 설치 및 동기화
uv sync
```

### 2. AI 모델 준비 (Ollama)
```bash
ollama create robot_commander -f robot_modelfile
```

### 3. 기능별 테스트 명령어 (`uv run` 활용)

| 테스트 목적 | 실행 명령어 | 설명 |
| :--- | :--- | :--- |
| **전체 시스템** | `uv run robot-loop` | 호출어 대기 -> 음성 명령 -> ROS2 순차 실행 (메인) |
| **패키지 확인** | `uv run robot-main` | 기본 인사 문구가 출력되는지 간단히 테스트 |
| **음성 인식 전용** | `uv run robot-voice` | 즉시 음성을 인식하고 LLM 파싱 JSON 결과를 출력 |
| **로직 시뮬레이션** | `uv run robot-test` | 미리 정의된 명령 예시로 LLM 분석 로직만 시뮬레이션 |

## 📂 프로젝트 구조
```text
/src/robot_voice_control/
├── robot_continuous_loop.py  # 메인 상태 머신 및 음성 제어 루프
├── ros_interface.py          # ROS2 Nav2/Action 연동 인터페이스
├── main.py                   # 시스템 진입점 및 기본 테스트
├── voice_to_robot.py         # 음성 파싱 전용 테스트
└── test_robot_parser.py      # LLM JSON 응답 테스트
```

## 🛠️ 기술 스택
- **Language:** Python 3.10
- **Package Manager:** `uv`
- **Speech Engine:** `Faster-Whisper` (large-v3-turbo)
- **Brain:** `Ollama` (Qwen 2.5 7B)
- **Voice Synthesis:** `MeloTTS`
- **Audio Playback:** `pygame`
- **Middleware:** `ROS2 Humble`
- **Simulator:** `NVIDIA Isaac Sim 5.1`

## ⚠️ 실행 시 주의사항
- **VRAM 점유:** Isaac Sim과 AI 모델들이 동시에 실행되므로 최소 **16GB-24GB의 VRAM**이 권장됩니다.
- **ROS2 통신:** `uv run` 실행 전 시뮬레이션 환경과 동일한 `ROS_DOMAIN_ID` 설정을 확인하세요.
- **오디오 장치:** `pygame`을 통해 시스템 사운드 서버와 연동되므로 다른 오디오 프로그램과의 충돌이 최소화되었습니다.
