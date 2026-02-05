import os
import uuid
import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI

# =========================
# 환경 변수 로드
# =========================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# =========================
# 요청 모델
# =========================
class ChatRequest(BaseModel):
    message: str
    voice: str  # "gpt" | "funny"

# =========================
# GPT 응답 생성
# =========================
def generate_gpt_response(user_message: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "너는 삼범이라는 AI다. "
                    "건조하고 비꼬는 관찰자 톤을 유지한다. "
                    "불필요한 친절은 하지 않는다. "
                    "가끔 의미 없는 내부 단어를 아무 설명 없이 끼워 넣는다."
                )
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )
    return completion.choices[0].message.content

# =========================
# 카카오 TTS (재미나이)
# =========================
def kakao_tts(text: str) -> str:
    url = "https://kakaoi-newtone-openapi.kakao.com/v1/synthesize"
    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}",
        "Content-Type": "application/xml"
    }

    xml = f"""
    <speak>
        <voice name="WOMAN_READ_CALM">
            {text}
        </voice>
    </speak>
    """

    response = requests.post(url, headers=headers, data=xml.encode("utf-8"))

    filename = f"{uuid.uuid4()}.wav"
    filepath = os.path.join(AUDIO_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(response.content)

    return filename

# =========================
# 메인 챗 엔드포인트
# =========================
@app.post("/chat")
def chat(req: ChatRequest):
    text = generate_gpt_response(req.message)

    # GPT 목소리 → 텍스트만 반환
    if req.voice == "gpt":
        return {
            "text": text,
            "voice": "gpt",
            "audio": None
        }

    # 재미나이 목소리 → 카카오 TTS
    elif req.voice == "funny":
        audio_file = kakao_tts(text)
        return {
            "text": text,
            "voice": "funny",
            "audio": f"/audio/{audio_file}"
        }

    return {"error": "unknown voice type"}

# =========================
# 음성 파일 제공
# =========================
@app.get("/audio/{filename}")
def get_audio(filename: str):
    filepath = os.path.join(AUDIO_DIR, filename)
    return FileResponse(filepath, media_type="audio/wav")
