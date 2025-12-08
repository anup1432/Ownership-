import os, asyncio
from telethon import TelegramClient
from telethon.tl.types import Channel
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from db import groups_col
from dotenv import load_dotenv
load_dotenv()

API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
S1 = os.getenv("USERBOT1_SESSION", "userbot1.session")
S2 = os.getenv("USERBOT2_SESSION", "userbot2.session")

clients = [
    TelegramClient(S1, API_ID, API_HASH),
    TelegramClient(S2, API_ID, API_HASH),
]

async def start_clients():
    for c in clients:
        await c.connect()
    print("Userbots connected")

async def join_via_invite(client, invite_link: str):
    try:
        if 'joinchat' in invite_link:
            hash = invite_link.split('/')[-1]
            await client(ImportChatInviteRequest(hash))
        else:
            await client.get_entity(invite_link)
        return True
    except Exception as e:
        print('join error', e)
        return False

async def is_creator(client, entity):
    try:
        me = await client.get_me()
        admins = await client.get_participants(entity, filter=ChannelParticipantsAdmins)
        for a in admins:
            if getattr(a, 'status', None) and getattr(a.status, 'creator', False):
                if a.id == me.id:
                    return True
        return False
    except Exception as e:
        print('is_creator error', e)
        return False

async def fetch_earliest_message_date(client, entity):
    msgs = await client.get_messages(entity, limit=1, reverse=True)
    if msgs:
        return msgs[0].date
    return None

async def verify_ownership_flow(invite_link: str, prefer_client_index=0):
    results = {}
    for idx, c in enumerate(clients):
        ok = await join_via_invite(c, invite_link)
        results[f'client{idx+1}_joined'] = ok
    target = clients[prefer_client_index]
    try:
        ent = await target.get_entity(invite_link)
    except:
        ent = None
    members = 0
    created_date = None
    try:
        if ent:
            full = await target(GetFullChannelRequest(ent)) if isinstance(ent, Channel) else None
            if full and getattr(full, 'full_chat', None) and hasattr(full.full_chat, 'participants_count'):
                members = full.full_chat.participants_count
            earliest = await fetch_earliest_message_date(target, ent)
            if earliest:
                created_date = earliest
    except Exception as e:
        print('fetch metadata error', e)
    owner_ok = await is_creator(target, ent) if ent else False
    return {
        "owner_confirmed": owner_ok,
        "members": members,
        "created_date": created_date,
        "clients_joined": results
    }

if __name__ == '__main__':
    async def main():
        await start_clients()
        while True:
            await asyncio.sleep(3600)
    asyncio.run(main())
