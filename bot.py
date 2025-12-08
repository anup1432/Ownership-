import os, asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from dotenv import load_dotenv
from db import users_col, groups_col, withdrawals_col
from price_logic import calc_price
from userbot import start_clients, verify_ownership_flow

load_dotenv()
API_TOKEN = os.getenv("TG_BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip()]

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Start Telethon clients in background
asyncio.create_task(start_clients())

def main_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("Profile", callback_data="profile"),
           InlineKeyboardButton("My Balance", callback_data="balance"))
    kb.add(InlineKeyboardButton("Price", callback_data="price"),
           InlineKeyboardButton("Withdraw", callback_data="withdraw"))
    kb.add(InlineKeyboardButton("Support", callback_data="support"))
    return kb

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    users_col.update_one({"user_id": message.from_user.id}, {"$setOnInsert":{"user_id":message.from_user.id, "balance":0}}, upsert=True)
    await message.reply("Send your group invite link to verify ownership.", reply_markup=main_kb())

@dp.message()
async def handle_text(message: types.Message):
    text = message.text.strip()
    if text.startswith("https://t.me/") or "joinchat" in text or text.startswith("t.me/"):
        await message.reply("Processing... Don't share OTPs. Bot will attempt to join and verify ownership.")
        res = await verify_ownership_flow(text, prefer_client_index=0)
        members = res.get("members", 0) or 0
        created_date = res.get("created_date")
        age_years = 0
        if created_date:
            from datetime import datetime
            age_years = (datetime.utcnow() - created_date).days / 365.0
        price = calc_price(members, int(age_years))
        groups_col.update_one({"link": text}, {"$set":{
            "link": text,
            "members": members,
            "created_date": str(created_date),
            "owner_confirmed": bool(res.get("owner_confirmed")),
            "price": price
        }}, upsert=True)
        if res.get("owner_confirmed"):
            users_col.update_one({"user_id": message.from_user.id}, {"$inc":{"balance": price}})
            await message.reply(f"Ownership verified ✅\nMembers: {members}\nPrice credited: {price}", reply_markup=main_kb())
        else:
            await message.reply(f"Ownership not yet verified. Members: {members}\nEstimated price: {price}", reply_markup=main_kb())
    else:
        await message.reply("Please send a valid Telegram group invite link (t.me/ or joinchat).")

@dp.callback_query()
async def cb_handler(query: types.CallbackQuery):
    data = query.data
    uid = query.from_user.id
    if data=="profile":
        u = users_col.find_one({"user_id": uid}) or {}
        await query.message.answer(f"Profile\nUser: {query.from_user.full_name}\nBalance: {u.get('balance',0)}")
    elif data=="balance":
        u = users_col.find_one({"user_id": uid}) or {}
        await query.message.answer(f"Your balance: {u.get('balance',0)}")
    elif data=="price":
        await query.message.answer("Pricing rules: BASE + members*per_member + age*age_factor. Admin can change via admin panel.")
    elif data=="support":
        await query.message.answer("Support message forwarded to admins. Please write your issue.")
    elif data=="withdraw":
        await query.message.answer("To withdraw, send: withdraw <amount> <crypto_address>\nExample: withdraw 12.5 0xAbC...")

@dp.message(lambda m: m.text and m.text.startswith("withdraw"))
async def handle_withdraw(message: types.Message):
    parts = message.text.split()
    if len(parts) < 3:
        return await message.reply("Format: withdraw <amount> <address>")
    try:
        amount = float(parts[1])
    except:
        return await message.reply("Invalid amount.")
    address = parts[2]
    user = users_col.find_one({"user_id": message.from_user.id})
    if not user or user.get("balance",0) < amount:
        return await message.reply("Insufficient balance.")
    withdraw_doc = {
        "user_id": message.from_user.id,
        "amount": amount,
        "address": address,
        "status": "pending"
    }
    rid = withdrawals_col.insert_one(withdraw_doc).inserted_id
    for aid in ADMIN_IDS:
        try:
            await bot.send_message(aid, f"New withdrawal request #{rid}\nUser: {message.from_user.full_name} ({message.from_user.id})\nAmount: {amount}\nAddress: {address}\nUse /approve_withdraw {rid} or /decline_withdraw {rid}")
        except Exception as e:
            print("notify admin err", e)
    await message.reply("Withdrawal request created and sent to admin for approval.")

@dp.message(Command('approve_withdraw'))
async def approve_withdraw(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply("Only admin.")
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply("Usage: /approve_withdraw <id>")
    rid = parts[1]
    from bson import ObjectId
    try:
        _id = ObjectId(rid)
    except:
        return await message.reply("Invalid id")
    req = withdrawals_col.find_one({"_id": _id})
    if not req:
        return await message.reply("Not found")
    withdrawals_col.update_one({"_id": _id}, {"$set":{"status":"accepted","processed_by":message.from_user.id}})
    users_col.update_one({"user_id": req["user_id"]}, {"$inc":{"balance": -req["amount"]}})
    await message.reply("Withdrawal accepted and user balance updated.")
    await bot.send_message(req["user_id"], f"Your withdrawal #{rid} has been approved by admin.")

@dp.message(Command('decline_withdraw'))
async def decline_withdraw(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply("Only admin.")
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply("Usage: /decline_withdraw <id>")
    rid = parts[1]
    from bson import ObjectId
    try:
        _id = ObjectId(rid)
    except:
        return await message.reply("Invalid id")
    withdrawals_col.update_one({"_id": _id}, {"$set":{"status":"declined","processed_by":message.from_user.id}})
    await message.reply("Withdrawal declined.")
    req = withdrawals_col.find_one({"_id": _id})
    await bot.send_message(req["user_id"], f"Your withdrawal #{rid} was declined by admin.")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
