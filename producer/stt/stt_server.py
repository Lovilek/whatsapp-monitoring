import base64, io, time, subprocess
from flask import Flask, request, jsonify
from faster_whisper import WhisperModel

MODEL_NAME = "small"

app = Flask(__name__)
model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8")  

def decode_to_wav_bytes(audio_b64: str, mime: str) -> bytes:
    raw = base64.b64decode(audio_b64)
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", "pipe:0",       
            "-ac", "1",           
            "-ar", "16000",      
            "-f", "wav", "pipe:1" 
        ],
        input=raw,
        capture_output=True
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg decode failed: {proc.stderr.decode('utf-8', errors='ignore')}")
    return proc.stdout

@app.route("/transcribe", methods=["POST"])
def transcribe():
    t0 = time.time()
    data = request.get_json(force=True)
    audio_b64 = data["audio_base64"]
    mime = data.get("mime") or "audio/ogg"
    wav_bytes = decode_to_wav_bytes(audio_b64, mime)

    bio = io.BytesIO(wav_bytes)
    segments, info = model.transcribe(bio, language=None)

    text = "".join([seg.text for seg in segments]).strip()

    return jsonify({
        "text": text,
        "language": info.language,
        "duration": info.duration,
        "model": MODEL_NAME,
        "latency_ms": int((time.time() - t0) * 1000)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9009)
