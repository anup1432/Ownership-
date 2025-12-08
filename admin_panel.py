from fastapi import FastAPI, HTTPException
from db import withdrawals_col, settings_col
import os
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()
ADMIN_API_KEY = os.getenv('ADMIN_API_KEY','')

def is_admin_key(key: str):
    return key == ADMIN_API_KEY

@app.get('/withdrawals')
def list_withdrawals(api_key: str):
    if not is_admin_key(api_key):
        raise HTTPException(status_code=401, detail='unauthorized')
    return list(withdrawals_col.find().sort('created_at', -1).limit(200))

@app.post('/set-pricing')
def set_pricing(api_key: str, base: float = None, per_member: float = None, age_factor: float = None):
    if not is_admin_key(api_key):
        raise HTTPException(status_code=401, detail='unauthorized')
    doc = {}
    if base is not None: doc['BASE_PRICE'] = base
    if per_member is not None: doc['PRICE_PER_MEMBER'] = per_member
    if age_factor is not None: doc['AGE_FACTOR_PER_YEAR'] = age_factor
    settings_col.update_one({'_id':'pricing'}, {'$set': doc}, upsert=True)
    return {'ok': True, 'set': doc}
