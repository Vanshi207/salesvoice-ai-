from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../../.env", ".env"), extra="ignore")

    deepgram_api_key: str = ""
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"
    sarvam_api_key: str = ""
    sarvam_voice: str = "priya"
    sarvam_language: str = "hi-IN"

    company_name: str = "Acme CRM"
    agent_name: str = "Priya"

    leads_url: str = "http://leads:8000"
    knowledge_url: str = "http://knowledge:8000"
    calls_url: str = "http://calls:8000"

    dev_user_id: str = ""
    dev_user_role: str = "admin"
    dev_lead_id: str = ""


settings = Settings()
