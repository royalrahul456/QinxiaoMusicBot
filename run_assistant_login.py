import sys
import asyncio
import os

try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from dotenv import load_dotenv, set_key
from pyrogram import Client

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
PHONE = os.getenv("ASSISTANT_PHONE", "").strip()


async def login():
    if not API_ID or not API_HASH:
        print("[-] Error: API_ID and API_HASH must be configured in your .env file.", flush=True)
        return

    phone = PHONE or input("Enter the Assistant Phone Number (with country code, e.g. +1234567890): ").strip()
    if not phone:
        print("[-] Error: Phone number is required.", flush=True)
        return

    print("Connecting to Telegram...", flush=True)
    app = Client("qinxiao_assistant_login", api_id=API_ID, api_hash=API_HASH, in_memory=True)
    await app.connect()

    sent_code = await app.send_code(phone)
    print("\n==================================================", flush=True)
    print("[+] Code successfully sent to your Telegram account.", flush=True)
    print("==================================================\n", flush=True)
    print("WAITING_FOR_OTP", flush=True)

    code = input("Enter the OTP code received on Telegram: ").strip().replace(" ", "").replace("-", "")

    try:
        await app.sign_in(phone, sent_code.phone_code_hash, code)
    except Exception as e:
        if "SESSION_PASSWORD_NEEDED" in str(e):
            print("WAITING_FOR_2FA", flush=True)
            pwd = input("Enter your 2FA Password: ").strip()
            await app.check_password(pwd)
        else:
            raise e

    session_string = await app.export_session_string()
    me = await app.get_me()
    print("\n==================================================", flush=True)
    print(f"[+] SUCCESS! Logged in as {me.first_name} (@{me.username or me.id})", flush=True)
    print("==================================================", flush=True)

    set_key(".env", "ASSISTANT_SESSION", session_string, quote_mode="never")
    print("[+] Saved ASSISTANT_SESSION into .env file successfully!", flush=True)
    await app.disconnect()


if __name__ == "__main__":
    try:
        loop.run_until_complete(login())
    except Exception as err:
        print(f"[-] Error during login: {err}", flush=True)
