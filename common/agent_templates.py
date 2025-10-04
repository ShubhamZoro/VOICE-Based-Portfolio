# common/agent_templates.py
from common.agent_functions import FUNCTION_DEFINITIONS
from common.prompt_templates import SHUBHAM_PROMPT_TEMPLATE
from common.config import USER_AUDIO_SAMPLE_RATE, AGENT_AUDIO_SAMPLE_RATE

VOICE = "aura-2-apollo-en"                      # <-- Apollo by default
VOICE_AGENT_URL = "wss://agent.deepgram.com/v1/agent/converse"

USER_AUDIO_SAMPLES_PER_CHUNK = round(USER_AUDIO_SAMPLE_RATE * 0.05)
AGENT_AUDIO_BYTES_PER_SEC = 2 * AGENT_AUDIO_SAMPLE_RATE

AUDIO_SETTINGS = {
    "input": {"encoding": "linear16", "sample_rate": USER_AUDIO_SAMPLE_RATE},
    "output": {"encoding": "linear16", "sample_rate": AGENT_AUDIO_SAMPLE_RATE, "container": "none"},
}
LISTEN_SETTINGS = {"provider": {"type": "deepgram", "model": "nova-3"}}
THINK_SETTINGS = {
    "provider": {"type": "open_ai", "model": "gpt-4o-mini", "temperature": 0.7},
    "prompt": SHUBHAM_PROMPT_TEMPLATE,
    "functions": FUNCTION_DEFINITIONS,
}
SPEAK_SETTINGS = {"provider": {"type": "deepgram", "model": VOICE}}
AGENT_SETTINGS = {"language": "en", "listen": LISTEN_SETTINGS, "think": THINK_SETTINGS, "speak": SPEAK_SETTINGS, "greeting": ""}
SETTINGS = {"type": "Settings", "audio": AUDIO_SETTINGS, "agent": AGENT_SETTINGS}

class AgentTemplates:
    def __init__(self, voiceModel="aura-2-apollo-en", voiceName=""):
        self.voiceModel = voiceModel
        self.voiceName = voiceName if voiceName else self.get_voice_name_from_model(self.voiceModel)
        self.company = "Shubham"
        self.first_message = "I am Shubham chat bot—ask me whatever you want to ask about him."
        self.voice_agent_url = VOICE_AGENT_URL
        self.settings = SETTINGS
        self.user_audio_sample_rate = USER_AUDIO_SAMPLE_RATE
        self.user_audio_samples_per_chunk = USER_AUDIO_SAMPLES_PER_CHUNK
        self.agent_audio_sample_rate = AGENT_AUDIO_SAMPLE_RATE
        self.agent_audio_bytes_per_sec = AGENT_AUDIO_BYTES_PER_SEC

        # Apply prompt & greeting to settings
        self.settings["agent"]["speak"]["provider"]["model"] = self.voiceModel
        self.settings["agent"]["think"]["prompt"] = SHUBHAM_PROMPT_TEMPLATE
        self.settings["agent"]["greeting"] = self.first_message

    def get_voice_name_from_model(self, model):
        return (model.replace("aura-2-", "").replace("aura-", "").split("-")[0].capitalize())
