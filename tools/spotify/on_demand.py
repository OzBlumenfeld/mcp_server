import asyncio
from pathlib import Path

from dotenv import load_dotenv
from oz_shared.onepassword import load_op_secrets
from tools.spotify.spotify import get_top_tracks

load_dotenv(Path(__file__).parent.parent.parent / ".env")
asyncio.run(load_op_secrets())


# todo: Extend here to the news paper for example weekly job + check with mcp server

print(get_top_tracks())

# print(get_top_podcasts()) # this one doesn't work at the moment podcasts are no longer supported by spotify