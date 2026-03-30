import speech_recognition as sr
from faster_whisper import WhisperModel
import ollama
import json
import os

# 1. STT 모델 설정 (최고 사양 turbo 모델 사용)
stt_model = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")

def listen_and_parse():
    # 마이크 설정
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n👂 듣고 있습니다... (말씀해 주세요)")
        # 주변 소음 수준에 맞춰 에너지 임계값 조정
        r.adjust_for_ambient_noise(source, duration=1)
        audio = r.listen(source)

    try:
        print("🔍 음성 분석 중...")
        # 오디오 데이터를 임시 파일로 저장 (Whisper 입력용)
        with open("temp_audio.wav", "wb") as f:
            f.write(audio.get_wav_data())

        # 2. STT: 음성을 텍스트로 변환 (한국어 지정)
        segments, info = stt_model.transcribe("temp_audio.wav", language="ko")
        voice_text = "".join([segment.text for segment in segments]).strip()
        
        if not voice_text:
            print("❓ 음성이 감지되지 않았습니다.")
            return

        print(f"📝 인식된 문장: {voice_text}")

        # 3. LLM: Ollama를 통해 JSON 파싱
        response = ollama.chat(model='robot_commander', messages=[
            {'role': 'user', 'content': voice_text},
        ])
        
        parsed_json = json.loads(response['message']['content'].strip())
        
        # 4. 결과 출력 및 확인
        confirm_msg = parsed_json.get("confirmation_message", "")
        commands = parsed_json.get("commands", [])
        
        print(f"\n🤖 로봇 확인: \"{confirm_msg}\"")
        print(f"📦 생성된 명령어: {commands}")

        # 임시 파일 삭제
        if os.path.exists("temp_audio.wav"):
            os.remove("temp_audio.wav")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def main():
    # Ollama 모델이 'robot_commander'라는 이름으로 이미 생성되어 있어야 합니다.
    while True:
        listen_and_parse()
        cont = input("\n계속하시겠습니까? (Enter: 계속 / q: 종료): ")
        if cont.lower() == 'q':
            break

if __name__ == "__main__":
    main()
