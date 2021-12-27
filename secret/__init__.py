import os
import json


def get_discord_token() -> str:
    token = os.getenv("DISCORD_TOKEN", None)
    if not token:
        with open("secret/discord.json", "r") as fh:
            discord_json = json.load(fh)
            token = discord_json["DISCORD_TOKEN"]

    return token


def get_redis_url() -> str:
    return os.getenv('REDISTOGO_URL', 'redis://localhost:7777')
