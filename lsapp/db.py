from supabase import create_client
from flask import current_app, g

def get_db(): #establishes connection to supabase db
    if 'db' not in g:
        g.db = create_client(current_app.config["DB_API_URL"], current_app.config["DB_API_KEY"]) 
    return g.db