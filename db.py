from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()
client = MongoClient(os.getenv('MONGO_URI'))
db = client.get_default_database() if client else client['tgownership']
users_col = db['users']
groups_col = db['groups']
withdrawals_col = db['withdrawals']
settings_col = db['settings']
