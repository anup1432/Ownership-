from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv('MONGO_URI'))

# FIX: never use get_default_database()
db = client["tgownership"]

users_col = db['users']
groups_col = db['groups']
withdrawals_col = db['withdrawals']
settings_col = db['settings']
