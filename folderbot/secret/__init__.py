import os
import json


def get_discord_token() -> str:
    token = os.getenv("DISCORD_TOKEN", None)
    if not token:
        secret_path = f"{os.path.dirname(os.path.realpath(__file__))}/discord.json"
        with open(secret_path, "r") as fh:
            discord_json = json.load(fh)
            token = discord_json["DISCORD_TOKEN"]

    return token


def get_redis_url() -> str:
    return os.getenv('REDISTOGO_URL', 'redis://localhost:7777')


def is_production() -> bool:
    return os.getenv("DISCORD_TOKEN", None) is not None
