import speech_recognition as sr
from faster_whisper import WhisperModel
import ollama
import json
import edge_tts
import asyncio
import pygame
import os

# --- 설정 ---
STT_MODEL_SIZE = "base"
LLM_MODEL_NAME = "robot_commander"
# ko-KR-SunHiNeural (여성), ko-KR-InJoonNeural (남성)
VOICE = "ko-KR-SunHiNeural" 

# --- 초기화 ---
print("⚙️ 시스템 초기화 중 (Edge-TTS + Faster-Whisper)...")
# VRAM 24GB 활용: STT는 GPU에서 빠르게 처리
stt_model = WhisperModel(STT_MODEL_SIZE, device="cuda", compute_type="int8_float16")
pygame.mixer.init()

async def generate_voice(text, output_path):
    """Edge-TTS를 사용하여 음성 파일 생성"""
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_path)

def speak(text):
    """자연스러운 음성 출력 및 재생"""
    print(f"🤖 로봇: {text}")
    output_file = "output.mp3"
    
    # 음성 생성 (비동기 함수 실행)
    asyncio.run(generate_voice(text, output_file))
    
    # 오디오 재생
    try:
        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload() # 파일 점유 해제
    except Exception as e:
        print(f"❌ 재생 오류: {e}")

def listen_voice():
    """마이크 입력을 텍스트로 변환 (STT)"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n👂 듣고 있습니다...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        audio = r.listen(source)
    
    try:
        temp_wav = "temp.wav"
        with open(temp_wav, "wb") as f:
            f.write(audio.get_wav_data())
        
        segments, _ = stt_model.transcribe(temp_wav, language="ko")
        text = "".join([s.text for s in segments]).strip()
        return text
    except Exception as e:
        print(f"STT 오류: {e}")
        return ""

def main():
    state = "IDLE"  # IDLE(대기), CONFIRMING(확인 중)
    pending_commands = []
    
    speak("로봇 지능 시스템이 가동되었습니다. 무엇을 도와드릴까요?")

    while True:
        voice_text = listen_voice()
        if not voice_text:
            continue
        
        print(f"👤 사용자: {voice_text}")

        if state == "IDLE":
            # 1. LLM에게 명령 해석 요청 (Ollama)
            try:
                response = ollama.chat(model=LLM_MODEL_NAME, messages=[{'role': 'user', 'content': voice_text}])
                raw_content = response['message']['content'].strip()
                
                # JSON 파싱 시도
                parsed = json.loads(raw_content)
                pending_commands = parsed.get("commands", [])
                confirm_msg = parsed.get("confirmation_message", "명령을 수행할까요?")
                
                if pending_commands:
                    speak(confirm_msg + " '응' 혹은 '아니'라고 대답해 주세요.")
                    state = "CONFIRMING"
                else:
                    speak("이해하지 못했습니다. 다시 말씀해 주세요.")
            except Exception as e:
                print(f"LLM 분석 오류: {e}")
                speak("명령 분석 중 오류가 발생했습니다.")

        elif state == "CONFIRMING":
            # 2. 사용자 승인 확인
            positive_words = ["응", "어", "그래", "수행", "해", "yes", "ok", "부탁해", "명령해"]
            negative_words = ["아니", "취소", "그만", "하지마", "no"]

            if any(word in voice_text for word in positive_words):
                speak("알겠습니다. 명령을 수행합니다.")
                # --- 여기서 실제 ROS2 액션 호출 (이동, 팔 제어) ---
                for cmd in pending_commands:
                    print(f"🚀 [ROS2 EXEC] {cmd}")
                # -------------------------------------------
                speak("작업을 완료했습니다. 다음 명령을 기다립니다.")
                state = "IDLE"
                pending_commands = []
            elif any(word in voice_text for word in negative_words):
                speak("명령을 취소했습니다. 다시 대기합니다.")
                state = "IDLE"
                pending_commands = []
            else:
                speak("잘 못 알아들었습니다. 수행할까요? '응' 혹은 '아니'라고 말씀해 주세요.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 시스템을 종료합니다.")
