from salesvoice_common.db import Database

from app.config import settings

db = Database(settings.database_url)
