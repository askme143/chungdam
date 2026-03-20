"""
Vercel Serverless Function: 두 텍스트의 유사도를 계산한다.
HF Inference API의 sentence-similarity 파이프라인을 사용한다.
"""

import json
import os
import urllib.request
import urllib.error

from http.server import BaseHTTPRequestHandler

HF_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}"
MAX_TEXT_LEN = 2000

ALLOWED_ORIGINS = [
    "https://askme143.github.io",
    "http://localhost",
    "http://127.0.0.1",
]


def get_origin(headers):
    origin = headers.get("origin", "")
    for allowed in ALLOWED_ORIGINS:
        if origin.startswith(allowed):
            return origin
    return ALLOWED_ORIGINS[0]


def compute_similarity(text1, text2):
    token = os.environ.get("HF_API_TOKEN", "")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": {
            "source_sentence": text1,
            "sentences": [text2],
        }
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(HF_API_URL, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode())
    # result is a list of scores, e.g. [0.78]
    return result[0]


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        origin = get_origin(self.headers)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_POST(self):
        origin = get_origin(self.headers)
        cors = {"Access-Control-Allow-Origin": origin}

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except (json.JSONDecodeError, ValueError):
            self._respond(400, {"error": "Invalid JSON"}, cors)
            return

        text1 = body.get("text1", "").strip()
        text2 = body.get("text2", "").strip()

        if not text1 or not text2:
            self._respond(400, {"error": "text1 and text2 are required"}, cors)
            return
        if len(text1) > MAX_TEXT_LEN or len(text2) > MAX_TEXT_LEN:
            self._respond(400, {"error": f"Text must be under {MAX_TEXT_LEN} characters"}, cors)
            return

        try:
            score = compute_similarity(text1, text2)
            score = max(0.0, min(1.0, float(score)))
            self._respond(200, {"score": round(score, 4)}, cors)
        except urllib.error.URLError as e:
            self._respond(502, {"error": f"HF API error: {str(e)}", "score": None}, cors)
        except Exception as e:
            self._respond(500, {"error": str(e), "score": None}, cors)

    def _respond(self, status, data, extra_headers=None):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
