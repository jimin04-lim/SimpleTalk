from fastapi import FastAPI, Form
from gtts import gTTS
from g2pk import G2p
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
import os
import uuid
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
g2p = G2p()
transliter = Transliter(academic)

# TTS 음성 파일을 저장할 디렉토리 설정 및 생성
TTS_OUTPUT_DIR = "tts_files"
os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)

# TTS_OUTPUT_DIR을 /tts 경로로 정적 파일 서빙하도록 설정
app.mount("/tts", StaticFiles(directory=TTS_OUTPUT_DIR), name="tts")

# Render 배포 시 실제 서비스의 기본 URL을 가져오기 위한 환경 변수 (예시)
# 개발 편의를 위해 프론트엔드의 API_BASE_URL과 동일하게 맞춰둡니다.
# 실제 배포 시에는 Render에서 제공하는 동적인 URL을 사용하는 것이 좋습니다.
# 예: os.getenv("RENDER_EXTERNAL_HOSTNAME", "http://localhost:8000")
# 아래는 Render 환경 변수를 활용하는 더 견고한 방법입니다.
render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if render_host:
    BASE_URL = f"https://{render_host}"
else:
    BASE_URL = "http://localhost:8000" # 로컬 개발 환경 기본값

# 한글 발음을 로마자로 변환하는 함수
def convert_pronunciation_to_roman(sentence: str) -> str:
    korean_pron = g2p(sentence)  # 발음 변환
    romanized = transliter.translit(korean_pron)
    return romanized

# TTS 음성 파일을 생성하고 저장하는 함수
def generate_tts(text: str) -> str:
    tts = gTTS(text=text, lang='ko')
    filename = f"{uuid.uuid4()}.mp3"  # 고유한 파일명 생성
    filepath = os.path.join(TTS_OUTPUT_DIR, filename)
    tts.save(filepath)
    return filename

# 로마자 변환 API 엔드포인트
@app.post("/romanize")
async def romanize(text: str = Form(...)):
    romanized = convert_pronunciation_to_roman(text)
    return JSONResponse(content={"input": text, "romanized": romanized})

# TTS 음성 파일 생성 및 URL 반환 API 엔드포인트
@app.post("/speak")
async def speak(text: str = Form(...)):
    filename = generate_tts(text)
    # 프론트엔드에서 직접 접근할 수 있는 완전한 URL 반환
    tts_url = f"{BASE_URL}/tts/{filename}"
    return JSONResponse(content={"tts_url": tts_url})

# (선택 사항) TTS 파일 존재 여부 확인 API (디버깅용)
@app.get("/check_tts_file/{filename}")
async def check_tts_file(filename: str):
    filepath = os.path.join(TTS_OUTPUT_DIR, filename)
    exists = os.path.exists(filepath)
    return JSONResponse(content={"filename": filename, "exists": exists, "filepath": filepath})