from salesvoice_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "gateway"
    frontend_origin: str = "http://localhost:3000"

    auth_url: str = "http://auth:8000"
    leads_url: str = ""
    knowledge_url: str = ""
    calls_url: str = ""

    rate_limit_per_minute: int = 60
    login_rate_limit_per_minute: int = 5

    def routes(self) -> dict[str, str]:
        table = {"auth": self.auth_url, "leads": self.leads_url,
                 "knowledge": self.knowledge_url, "calls": self.calls_url}
        return {name: url for name, url in table.items() if url}


settings = Settings()

PUBLIC_ROUTES = {("auth", "signup"), ("auth", "login"), ("auth", "refresh")}
