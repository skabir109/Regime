import sys
sys.path.append('backend')
from sqlalchemy import inspect
from app.services.db import init_db, get_engine

init_db()
engine = get_engine(use_direct=True)
columns = {c['name'] for c in inspect(engine).get_columns('delivery_preferences')}
required = {'discord_enabled', 'discord_webhook_url'}
print('present', sorted(required & columns))
print('missing', sorted(required - columns))
