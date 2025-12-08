# Telegram Group Ownership Verification Bot

This repository contains a Telegram bot and worker to verify group ownership by having verification user accounts join and become group owner.  
Files included:
- bot.py (Aiogram user-facing bot)
- userbot.py (Telethon worker handling two userbot sessions)
- db.py (MongoDB helper)
- price_logic.py (pricing calculation)
- admin_panel.py (FastAPI admin endpoints)
- create_sessions.py (run locally to create Telethon session files)
- requirements.txt
- Procfile (for Render)
- .env (example filled with provided values — rotate credentials after first run)
- README with deploy instructions

**SECURITY IMPORTANT**: You exposed sensitive credentials in chat. Rotate the Bot Token (BotFather) and consider rotating MongoDB credentials immediately. Use the `.env` and do NOT commit it to any public repo.

## Quick deploy (Render)
1. Create a new Git repo and push these files (make sure to **not** push `.env` if you prefer).
2. On Render, create three services:
   - Web service: `uvicorn bot:dp --host 0.0.0.0 --port $PORT` (or use polling/webhook)
   - Worker service: `python userbot.py`
   - Admin service: `uvicorn admin_panel:app --host 0.0.0.0 --port 8000`
3. Add environment variables in Render from your .env (or set them in settings).
4. Upload `userbot1.session` and `userbot2.session` to the worker's filesystem or store them securely and mount into the service.
5. Start services.

## How to create Telethon sessions (locally)
Run `python create_sessions.py` and follow prompts. After creating `userbot1.session` and `userbot2.session`,
upload those files to your server and place them beside the code or update .env to their paths.

