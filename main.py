from fastapi import FastAPI, Form
from gtts import gTTS
from g2pk import G2p
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
import os
import uuid  # uuid 모듈 import
import tempfile # 더 이상 uuid4를 직접 사용하지 않으므로 필요 없을 수 있지만, 다른 tempfile 기능을 사용할 수도 있으니 일단 유지
import threading
from fastapi.responses import JSONResponse, FileResponse

app = FastAPI()
g2p = G2p()
transliter = Transliter(academic)
TTS_OUTPUT_DIR = "tts_files" # 음성 파일 저장 디렉토리
os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)

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
def generate_tts(text: str) -> str:
    tts = gTTS(text=text, lang='ko')
    filename = f"{uuid.uuid4()}.mp3"  # uuid 모듈의 uuid4() 사용
    filepath = os.path.join(TTS_OUTPUT_DIR, filename)
    tts.save(filepath)
    return filename

# 로마자 변환 API
@app.post("/romanize")
def romanize(text: str = Form(...)):
    romanized = convert_pronunciation_to_roman(text)
    return JSONResponse(content={"input": text, "romanized": romanized})

@app.post("/speak")
def speak(text: str = Form(...)):
    filename = generate_tts(text)
    tts_url = f"/tts/{filename}"
    return JSONResponse(content={"tts_url": tts_url})

@app.get("/tts/{filename}")
async def get_tts(filename: str):
    filepath = os.path.join(TTS_OUTPUT_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="audio/mpeg")
    return JSONResponse(content={"error": "TTS 파일이 없습니다."}, status_code=404)

# ▶▶▶ Android 연결 테스트용 API
@app.post("/echo")
def echo(text: str = Form(...)):
    """
    안드로이드에서 요청을 테스트할 수 있는 간단한 API.
    받은 텍스트를 그대로 응답합니다.
    """
    return JSONResponse(content={"echo": text})