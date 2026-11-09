from salesvoice_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "leads"
    db_schema: str = "leads"
    default_phone_region: str = "IN"


settings = Settings()
