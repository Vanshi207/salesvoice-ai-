from salesvoice_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "auth"
    db_schema: str = "auth"


settings = Settings()
