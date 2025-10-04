# client.py

# 1️⃣ Monkey patch must be first
import eventlet
eventlet.monkey_patch()

# 2️⃣ Standard imports
import os
import json
import threading
import queue
import logging
import requests
import asyncio
import janus
import websockets

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from common.agent_functions import FUNCTION_MAP
from common.agent_templates import AgentTemplates, AGENT_AUDIO_SAMPLE_RATE

# 3️⃣ Flask app and SocketIO (eventlet async mode)
app = Flask(__name__, static_folder="./static", static_url_path="/", template_folder="templates")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# 4️⃣ Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

# 5️⃣ Global voice agent
VOICE_AGENT = None
AGENT_LOOP = None
AGENT_THREAD = None

# 6️⃣ VoiceAgent class
class VoiceAgent:
    def __init__(self, voiceModel="aura-2-apollo-en", voiceName="", browser_audio=True):
        self.mic_audio_queue = asyncio.Queue()
        self.speaker = None
        self.ws = None
        self.is_running = False
        self.browser_audio = browser_audio
        self.agent_templates = AgentTemplates(voiceModel, voiceName)

    async def setup(self):
        dg_api_key = os.environ.get("DEEPGRAM_API_KEY")
        if not dg_api_key:
            logger.error("DEEPGRAM_API_KEY env var not present")
            return False
        settings = self.agent_templates.settings
        try:
            self.ws = await websockets.connect(
                self.agent_templates.voice_agent_url,
                extra_headers={"Authorization": f"Token {dg_api_key}"}
            )
            await self.ws.send(json.dumps(settings))
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Deepgram: {e}")
            return False

    async def sender(self):
        try:
            while self.is_running:
                data = await self.mic_audio_queue.get()
                if self.ws and data:
                    await self.ws.send(data)
        except Exception as e:
            logger.error(f"sender error: {e}")

    async def receiver(self):
        try:
            self.speaker = Speaker(browser_output=True)
            with self.speaker:
                async for message in self.ws:
                    if isinstance(message, str):
                        try:
                            msg = json.loads(message)
                        except Exception:
                            continue

                        t = msg.get("type")
                        if t == "ConversationText":
                            socketio.emit("conversation_update", msg)
                        if t in ("UserStartedSpeaking", "AgentAudioDone"):
                            socketio.emit("agent_event", msg)
                        elif t == "FunctionCallRequest":
                            fn = msg.get("functions", [])[0]
                            name = fn.get("name")
                            call_id = fn.get("id")
                            params = json.loads(fn.get("arguments", "{}"))
                            try:
                                impl = FUNCTION_MAP.get(name)
                                if not impl:
                                    raise ValueError(f"Unknown function: {name}")
                                if name in ["agent_filler", "end_call"]:
                                    result = await impl(self.ws, params)
                                    resp = {
                                        "type": "FunctionCallResponse",
                                        "id": call_id,
                                        "name": name,
                                        "content": json.dumps(result["function_response"]),
                                    }
                                    await self.ws.send(json.dumps(resp))
                                    await self.ws.send(json.dumps(result["inject_message"]))
                                    if name == "end_call":
                                        await asyncio.sleep(0.5)
                                        await self.ws.close()
                                        self.is_running = False
                                        break
                                else:
                                    result = await impl(params)
                                    resp = {
                                        "type": "FunctionCallResponse",
                                        "id": call_id,
                                        "name": name,
                                        "content": json.dumps(result),
                                    }
                                    await self.ws.send(json.dumps(resp))
                            except Exception as e:
                                resp = {
                                    "type": "FunctionCallResponse",
                                    "id": call_id,
                                    "name": name,
                                    "content": json.dumps({"error": str(e)}),
                                }
                                await self.ws.send(json.dumps(resp))
                        elif t == "CloseConnection":
                            await self.ws.close()
                            break
                    elif isinstance(message, bytes):
                        await self.speaker.play(message)
        except Exception as e:
            logger.error(f"receiver error: {e}")

    async def run(self):
        if not await self.setup():
            return
        self.is_running = True
        try:
            await asyncio.gather(self.sender(), self.receiver())
        finally:
            self.is_running = False
            if self.ws:
                try: await self.ws.close()
                except: pass

# 7️⃣ Speaker class
class Speaker:
    def __init__(self, browser_output=True):
        self._queue = None
        self._thread = None
        self._stop = None
        self.browser_output = browser_output

    def __enter__(self):
        self._queue = janus.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=_play, args=(self._queue, self._stop), daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._stop.set()
        self._thread.join()
        self._queue = None
        self._thread = None
        self._stop = None

    async def play(self, data):
        return await self._queue.async_q.put(data)

def _play(audio_out, stop):
    seq = 0
    while not stop.is_set():
        try:
            data = audio_out.sync_q.get(True, 0.05)
            socketio.emit("audio_output", {"audio": data, "sampleRate": AGENT_AUDIO_SAMPLE_RATE, "seq": seq})
            seq += 1
        except queue.Empty:
            pass

# 8️⃣ Run asyncio loop in a separate thread
def run_async_loop_in_thread(loop):
    """Run asyncio event loop in a dedicated thread"""
    asyncio.set_event_loop(loop)
    loop.run_forever()

def start_agent_loop():
    """Initialize and start the asyncio event loop in a background thread"""
    global AGENT_LOOP, AGENT_THREAD
    if AGENT_LOOP is None or AGENT_LOOP.is_closed():
        AGENT_LOOP = asyncio.new_event_loop()
        AGENT_THREAD = threading.Thread(target=run_async_loop_in_thread, args=(AGENT_LOOP,), daemon=True)
        AGENT_THREAD.start()
    return AGENT_LOOP

# 9️⃣ Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/tts-models")
def get_tts_models():
    try:
        dg_api_key = os.environ.get("DEEPGRAM_API_KEY")
        if not dg_api_key:
            return jsonify({"error": "DEEPGRAM_API_KEY not set"}), 500
        response = requests.get("https://api.deepgram.com/v1/models",
                                headers={"Authorization": f"Token {dg_api_key}"})
        if response.status_code != 200:
            return jsonify({"error": f"API status {response.status_code}"}), 500
        data = response.json()
        formatted = []
        if "tts" in data:
            for model in data["tts"]:
                if model.get("architecture") == "aura-2":
                    lang = (model.get("languages") or ["en"])[0]
                    md = model.get("metadata", {})
                    formatted.append({
                        "name": model.get("canonical_name", model.get("name")),
                        "display_name": model.get("name"),
                        "language": lang,
                        "accent": md.get("accent", ""),
                        "tags": ", ".join(md.get("tags", [])),
                    })
        return jsonify({"models": formatted})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 1️⃣0️⃣ SocketIO handlers
@socketio.on("start_voice_agent")
def handle_start_voice_agent(data=None):
    global VOICE_AGENT
    
    # Stop existing agent if running
    if VOICE_AGENT:
        VOICE_AGENT.is_running = False
        VOICE_AGENT = None

    voiceModel = data.get("voiceModel", "aura-2-apollo-en") if data else "aura-2-apollo-en"
    voiceName = data.get("voiceName", "") if data else ""
    VOICE_AGENT = VoiceAgent(voiceModel=voiceModel, voiceName=voiceName, browser_audio=True)

    # Get or create the asyncio loop running in background thread
    loop = start_agent_loop()
    
    # Schedule the coroutine in the dedicated asyncio loop
    asyncio.run_coroutine_threadsafe(VOICE_AGENT.run(), loop)

@socketio.on("stop_voice_agent")
def handle_stop_voice_agent():
    global VOICE_AGENT
    if VOICE_AGENT:
        VOICE_AGENT.is_running = False
        VOICE_AGENT = None

@socketio.on("audio_data")
def handle_audio_data(data):
    global VOICE_AGENT, AGENT_LOOP
    if VOICE_AGENT and VOICE_AGENT.is_running and VOICE_AGENT.browser_audio and AGENT_LOOP:
        audio_buffer = data.get("audio")
        if not audio_buffer:
            return
        try:
            if isinstance(audio_buffer, memoryview):
                audio_bytes = audio_buffer.tobytes()
            elif isinstance(audio_buffer, bytes):
                audio_bytes = audio_buffer
            else:
                audio_bytes = bytes(audio_buffer)
            # Put audio data into queue via the dedicated asyncio loop
            asyncio.run_coroutine_threadsafe(VOICE_AGENT.mic_audio_queue.put(audio_bytes), AGENT_LOOP)
        except Exception as e:
            logger.error(f"audio_data error: {e}")

# 1️⃣1️⃣ Main entry
if __name__ == "__main__":
    print("\nOpen http://127.0.0.1:5000\n")
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
