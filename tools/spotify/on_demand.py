from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from spotify import get_top_tracks

# todo: Extend here to the news papaer for example weekly job + check with mcp server

print(get_top_tracks())

# print(get_top_podcasts()) # this one doesn't work at the moment podcasts are no longer suppoprted by spotify