# create_sessions.py
# Run locally to create Telethon session files for your two userbot accounts.
from telethon import TelegramClient
import os

API_ID = 38683063
API_HASH = "dfecebe3a34c2f1974ba11e9aa32d66a"

def make_session(session_name):
    print("Creating session:", session_name)
    client = TelegramClient(session_name, API_ID, API_HASH)
    client.start()  # will prompt for phone and OTP
    me = client.get_me()
    print("Logged in as:", me.username or me.first_name)
    client.disconnect()
    print("Session saved to", session_name + ".session")

if __name__ == "__main__":
    print("Run this for two accounts. Example: userbot1 and userbot2")
    s1 = input("Enter first session filename (eg. userbot1): ").strip() or "userbot1"
    make_session(s1)
    print("\nNow create second session")
    s2 = input("Enter second session filename (eg. userbot2): ").strip() or "userbot2"
    make_session(s2)
    print("\nDone. Upload the following files to your server:")
    print(s1 + ".session")
    print(s2 + ".session")
