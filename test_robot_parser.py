import ollama
import json

# 로봇 명령 파서 클래스
class RobotCommandParser:
    def __init__(self, model_name="robot_commander"):
        self.model_name = model_name

    def parse_command(self, voice_text):
        """음성 텍스트를 JSON 명령으로 변환"""
        print(f"🎤 입력 명령: {voice_text}")
        
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {
                    'role': 'user',
                    'content': voice_text,
                },
            ])
            
            # JSON 파싱 시도 (Ollama 응답은 문자열이므로 json.loads() 필요)
            raw_response = response['message']['content'].strip()
            # 가끔 응답에 중괄호가 하나 더 닫힐 수 있으므로 보정
            if not raw_response.endswith('}'):
                raw_response += '}'
                
            parsed_json = json.loads(raw_response)
            return parsed_json
        
        except Exception as e:
            print(f"❌ 파싱 오류: {e}")
            return None

    def confirm_and_execute(self, parsed_data):
        """사용자 확인 프로세스 시뮬레이션"""
        if not parsed_data:
            return

        confirmation_msg = parsed_data.get("confirmation_message", "명령을 수행할까요?")
        commands = parsed_data.get("commands", [])

        print(f"\n🤖 로봇 확인: \"{confirmation_msg}\"")
        
        # 실제 환경에서는 여기서 다시 STT를 통해 음성 입력을 받아야 함
        user_input = input("진행할까요? (y/n): ").lower()
        
        if user_input in ['y', 'yes', '응', '그래']:
            print("🚀 명령 실행 중...")
            for cmd in commands:
                print(f"  -> 실행: {cmd}")
            print("✅ 모든 명령 수행 완료.")
        else:
            print("🛑 명령이 취소되었습니다.")

# 테스트 실행
if __name__ == "__main__":
    # 먼저 Ollama 모델이 생성되어 있어야 함:
    # 터미널에서 `ollama create robot_commander -f robot_modelfile` 실행 필요
    
    parser = RobotCommandParser()
    
    # 예시 명령 1
    test_cmd_1 = "거실로 가서 오른팔로 물병 좀 집어줘."
    result_1 = parser.parse_command(test_cmd_1)
    parser.confirm_and_execute(result_1)
    
    print("-" * 30)
    
    # 예시 명령 2
    test_cmd_2 = "침실로 이동해."
    result_2 = parser.parse_command(test_cmd_2)
    parser.confirm_and_execute(result_2)
