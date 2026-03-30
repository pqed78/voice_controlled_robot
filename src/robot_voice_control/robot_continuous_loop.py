import os
import sys
import torch
import warnings
import threading

# 경고 숨기기
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")
warnings.filterwarnings("ignore", category=UserWarning, module="librosa")
warnings.filterwarnings("ignore", category=FutureWarning, module="huggingface_hub")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

import pygame
import speech_recognition as sr
from faster_whisper import WhisperModel
import ollama
import json
import rclpy
import time
from melo.api import TTS
from .ros_interface import RobotRosInterface
from contextlib import contextmanager

# 전역 상태 (중단 감시용)
is_abort_requested = False

@contextmanager
def ignore_stderr():
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(sys.stderr.fileno())
    os.dup2(devnull, sys.stderr.fileno())
    try:
        yield
    finally:
        os.dup2(old_stderr, sys.stderr.fileno())
        os.close(devnull)
        os.close(old_stderr)

# --- 설정 ---
STT_MODEL_SIZE = "large-v3-turbo" 
LLM_MODEL_NAME = "robot_commander"
WAKEUP_WORD = "저기요"
STOP_KEYWORDS = ["멈춰", "정지", "그만", "그만해", "중단", "취소해", "stop"]
ROS_NAMESPACE = "" # 네임스페이스가 필요한 경우 'robot1' 등 입력

# --- 초기화 ---
print(f"⚙️ 시스템 초기화 시작...")
device = "cuda" if torch.cuda.is_available() else "cpu"
tts_model = TTS(language='KR', device=device)
speaker_ids = tts_model.hps.data.spk2id
stt_model = WhisperModel(STT_MODEL_SIZE, device="cuda", compute_type="float16")
print("✅ 시스템 준비 완료.")

def speak(text):
    print(f"🤖 로봇: {text}", flush=True)
    output_file = "output.wav"
    try:
        tts_model.tts_to_file(text, speaker_ids['KR'], output_file, speed=1.1)
        with ignore_stderr():
            pygame.mixer.init()
            pygame.mixer.music.load(output_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()
            pygame.mixer.quit()
    except Exception as e:
        print(f"❌ 재생 오류: {e}")

def listen_voice(timeout=5, prompt="👂 듣고 있습니다..."):
    r = sr.Recognizer()
    r.energy_threshold = 1000
    try:
        with ignore_stderr():
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.3)
                print(f"\r{prompt}", end="", flush=True)
                audio = r.listen(source, timeout=timeout, phrase_time_limit=10)
                print(f"\r{' ' * 50}\r✅ 소리 감지! 분석 중...", end="", flush=True)
    except:
        return ""
    
    try:
        temp_wav = "temp_input.wav"
        with open(temp_wav, "wb") as f:
            f.write(audio.get_wav_data())
        segments, _ = stt_model.transcribe(temp_wav, language="ko", beam_size=3)
        text = "".join([s.text for s in segments]).strip()
        print(f"\r{' ' * 50}\r", end="", flush=True)
        return text
    except:
        return ""

def stop_monitor(ros_interface):
    """로봇이 동작하는 동안 백그라운드에서 중단 명령을 감시하는 스레드"""
    global is_abort_requested
    print("\n🚨 [중단 감시 시스템 가동]")
    
    while is_abort_requested:
        text = listen_voice(timeout=1, prompt="⚠️ (실행 중...) 멈추려면 '멈춰'라고 하세요.")
        if any(key in text for key in STOP_KEYWORDS):
            print(f"\n📢 중단 단어 감지: [{text}]")
            ros_interface.abort_all()
            is_abort_requested = False
            break
        time.sleep(0.1)

def main():
    global is_abort_requested
    rclpy.init()
    # 네임스페이스를 인자로 전달
    ros_interface = RobotRosInterface(namespace=ROS_NAMESPACE)
    state = "WAITING_WAKEUP"
    pending_commands = []
    
    print(f"💡 '{WAKEUP_WORD}'라고 부르면 시작합니다.")

    try:
        while rclpy.ok():
            rclpy.spin_once(ros_interface, timeout_sec=0.1)
            
            if state == "WAITING_WAKEUP":
                voice_text = listen_voice(timeout=None, prompt="💤 대기 중...")
                if WAKEUP_WORD in voice_text:
                    print(f"\n✨ 활성화: {voice_text}")
                    speak("네, 말씀하세요.")
                    state = "IDLE"
                continue

            voice_text = listen_voice(timeout=7, prompt="🎤 말씀하세요 (7s)...")
            if not voice_text:
                print("\n⏰ 명령 대기 시간 초과.")
                state = "WAITING_WAKEUP"
                continue
            
            print(f"👤 사용자: {voice_text}")

            if state == "IDLE":
                try:
                    response = ollama.chat(model=LLM_MODEL_NAME, messages=[{'role': 'user', 'content': voice_text}])
                    parsed = json.loads(response['message']['content'].strip())
                    pending_commands = parsed.get("commands", [])
                    confirm_msg = parsed.get("confirmation_message", "수행할까요?")
                    
                    if pending_commands:
                        speak(confirm_msg + " 수행할까요?")
                        state = "CONFIRMING"
                    else:
                        speak("죄송합니다. 이해하지 못했습니다.")
                except:
                    state = "WAITING_WAKEUP"

            elif state == "CONFIRMING":
                if any(word in voice_text for word in ["수행", "응", "그래", "해줘", "어"]):
                    speak("작업을 시작합니다.")
                    
                    is_abort_requested = True
                    monitor_thread = threading.Thread(target=stop_monitor, args=(ros_interface,))
                    monitor_thread.daemon = True
                    monitor_thread.start()

                    for cmd in pending_commands:
                        if not is_abort_requested: break 
                        
                        success = ros_interface.execute_command(cmd)
                        if not success:
                            break
                    
                    if is_abort_requested:
                        speak("모든 작업을 완료했습니다.")
                    else:
                        speak("작업을 긴급 중단했습니다.")
                    
                    is_abort_requested = False
                    state = "WAITING_WAKEUP"
                    pending_commands = []
                elif any(word in voice_text for word in ["취소", "아니", "하지마"]):
                    speak("명령을 취소했습니다.")
                    state = "WAITING_WAKEUP"
                else:
                    speak("수행할까요? '수행' 혹은 '취소'라고 말씀해 주세요.")

    except KeyboardInterrupt:
        print("\n👋 시스템 종료")
    finally:
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == "__main__":
    main()
