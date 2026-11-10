from dataclasses import dataclass


@dataclass
class CallContext:
    """Who is calling whom. Passed to the agent so its tools act for the right rep and lead."""
    user_id: str
    user_role: str
    lead_id: str = ""
    lead_name: str = "the customer"

    def headers(self) -> dict:
        return {"X-User-Id": self.user_id, "X-User-Role": self.user_role}
