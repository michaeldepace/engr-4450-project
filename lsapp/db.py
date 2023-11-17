from supabase import create_client
from flask import current_app, g

# establishes connection to supabase database that route/view methods can use to interact with db (query, update, insert, delete)
def get_db(): 
    if 'db' not in g:
        g.db = create_client(current_app.config["DB_API_URL"], current_app.config["DB_API_KEY"]) 
    return g.db