import os

from oz_shared import make_engine, make_session_factory

engine = make_engine(os.environ["DATABASE_URL"])
session_factory = make_session_factory(engine)
