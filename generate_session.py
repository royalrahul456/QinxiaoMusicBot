import sys
import asyncio
import os
from dotenv import load_dotenv, set_key
from pyrogram import Client

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

if not API_ID or not API_HASH:
    print("[-] Error: API_ID and API_HASH must be set in your .env file.")
    sys.exit(1)

masked_hash = f"{API_HASH[:4]}...{'*' * 8}" if len(API_HASH) > 4 else "****"
print("==================================================")
print(" 🎵 Qinxiao Music Assistant Session Generator ")
print("==================================================")
print(f"Using API_ID: {API_ID}")
print(f"Using API_HASH: {masked_hash}")
print("--------------------------------------------------")


async def generate():
    async with Client(
        name="qinxiao_assistant_session",
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=True
    ) as app:
        session_str = await app.export_session_string()
        me = await app.get_me()

        print("\n==================================================")
        print(f"[+] SUCCESS! Generated Assistant Session for: {me.first_name} (@{me.username or me.id})")
        print("==================================================")

        env_file = ".env"
        if os.path.exists(env_file):
            set_key(env_file, "ASSISTANT_SESSION", session_str)
            print("[+] Saved ASSISTANT_SESSION to .env file automatically!")
        else:
            print(f"\nASSISTANT_SESSION=\n{session_str}\n")


if __name__ == "__main__":
    try:
        asyncio.run(generate())
    except (KeyboardInterrupt, SystemExit):
        print("\nCanceled.")
