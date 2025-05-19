from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from gtts import gTTS
from playsound import playsound
from g2pk import G2p
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
import os
import tempfile
import threading

app = FastAPI()

# g2pk 객체
g2p = G2p()

# 로마자 변환기
transliter = Transliter(academic)

# 한글 발음을 로마자로 변환
# 입력 문장을 발음 변환 후 로마자로 변환.
def convert_pronunciation_to_roman(sentence):
    korean_pron = g2p(sentence)  # 발음 변환
    words = korean_pron.split()  # 단어 단위로 나누기
    romanized_words = []

    for word in words:
        romanized_syllables = [transliter.translit(char) for char in word]  # 음절 단위 변환
        romanized_word = '-'.join(romanized_syllables)
        romanized_words.append(romanized_word)

    result = ' '.join(romanized_words)  # 단어 사이 공백 유지
    return result

# TTS 재생 (스레드로 실행)
def speak_korean(text: str):
    def _play():
        tts = gTTS(text=text, lang='ko')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            temp_path = fp.name
        tts.save(temp_path)
        playsound(temp_path)
        os.remove(temp_path)

    threading.Thread(target=_play).start()

# 로마자 변환 API
@app.post("/romanize")
def romanize(text: str = Form(...)):
    romanized = convert_pronunciation_to_roman(text)
    return JSONResponse(content={"input": text, "romanized": romanized})

# TTS 재생 API
@app.post("/speak")
def speak(text: str = Form(...)):
    speak_korean(text)
    return JSONResponse(content={"message": f"'{text}'를 재생합니다."})

# ▶▶▶ Android 연결 테스트용 API
@app.post("/echo")
def echo(text: str = Form(...)):
    """
    안드로이드에서 요청을 테스트할 수 있는 간단한 API.
    받은 텍스트를 그대로 응답합니다.
    """
    return JSONResponse(content={"echo": text})
