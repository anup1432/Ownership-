import os
from dotenv import load_dotenv
load_dotenv()
def calc_price(members, group_age_years, override_price=None):
    base = float(os.getenv("BASE_PRICE", "10"))
    per_member = float(os.getenv("PRICE_PER_MEMBER", "0.01"))
    age_factor = float(os.getenv("AGE_FACTOR_PER_YEAR", "2"))
    price = base + members * per_member + group_age_years * age_factor
    if override_price:
        return float(override_price)
    return round(price, 2)
