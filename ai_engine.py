# ai_engine.py
import openai
import sounddevice as sd
import funasr
import keyboard
import pygame
import datetime
import base64
import requests
import numpy as np
import os

class AIEngine:
    def __init__(self, base_url='https://api.deepseek.com', api_key='sk-5bede23d49854f24a9b3c94b8ff05b96'):
        self.base_url = base_url
        self.api_key = api_key
        self.agent = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.messages = []
        self.model = None  # 懒加载语音模型

        # TTS 配置
        self.tts_url = 'https://openspeech.bytedance.com/api/v1/tts'
        self.tts_headers = {"Authorization": "Bearer; hot0aQ-ncPHxZilMsLnNWfMkQILr5mOu"}

    def generate_response(self, user_input: str) -> str:
        """文本生成回复"""
        if not user_input.strip():
            return "请提供有效输入。"
        
        self.messages.append({"role": "user", "content": user_input})
        try:
            response = self.agent.chat.completions.create(
                model='deepseek-chat',
                messages=self.messages,
                timeout=30
            )
            assistant_text = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": assistant_text})
            return assistant_text
        except Exception as e:
            error_msg = f"API 错误: {str(e)}"
            print(error_msg)
            return error_msg

    def recognizer_speech(self) -> str:
        """语音识别（按右键开始）"""
        if self.model is None:
            print("正在加载语音识别模型...")
            self.model = funasr.AutoModel(model="paraformer-zh-realtime")
            print("模型加载完成。")

        print('▶ 请按键盘【右方向键】开始说话（最长5秒）...')
        keyboard.wait('right')
        print('🎙️ 正在录音...')
        recording = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype=np.float32)
        sd.wait()
        print('🔄 识别中...')
        result = self.model.generate(input=recording.flatten())
        user_text = result[0]['text'].replace(' ', '').strip()
        print(f'👤 用户说: "{user_text}"')
        return user_text

    def generate_response_with_voice(self) -> str:
        """语音输入 → AI 回复 → 语音输出"""
        try:
            user_text = self.recognizer_speech()
            if not user_text:
                return "未识别到语音。"

            assistant_text = self.generate_response(user_text)

            # TTS 请求
            json_data = {
                "app": {
                    "appid": "9708045770",
                    "token": "hot0aQ-ncPHxZilMsLnNWfMkQILr5mOu",
                    "cluster": "volcano_tts",
                },
                "user": {"uid": "uid123"},
                "audio": {
                    "voice_type": "zh_female_wanwanxiaohe_moon_bigtts",
                    "encoding": "wav",
                    "speed_ratio": 1.0,
                },
                "request": {
                    "reqid": datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'),
                    "text": assistant_text,
                    "operation": "query",
                }
            }

            print("🔊 正在生成语音...")
            response = requests.post(self.tts_url, headers=self.tts_headers, json=json_data)
            if response.status_code != 200:
                raise Exception(f"TTS 请求失败: {response.text}")

            data = base64.b64decode(response.json()['data'])
            filename = f"output_{datetime.datetime.now().strftime('%H%M%S')}.wav"
            with open(filename, 'wb') as f:
                f.write(data)

            self.play_music(filename)

            # 清理临时文件（可选）
            # os.remove(filename)

            return assistant_text
        except Exception as e:
            error_msg = f"语音交互出错: {str(e)}"
            print(error_msg)
            return error_msg

    def play_music(self, music_path):
        """播放音频文件"""
        pygame.mixer.init(frequency=22050)
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
        finally:
            pygame.mixer.quit()