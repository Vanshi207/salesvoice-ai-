from salesvoice_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "calls"
    db_schema: str = "calls"

    leads_url: str = "http://leads:8000"

    audio_dir: str = "/data/audio"
    max_upload_mb: int = 25

    deepgram_api_key: str = ""
    deepgram_model: str = "nova-3"
    deepgram_language: str = "multi"

    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    events_stream: str = "events"


settings = Settings()
