from sqlmodel import SQLModel, create_engine, Session
from .config import settings

engine = create_engine(settings.database_url, echo=False)

def init_db():
    from . import models  # noqa
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as s:
        yield s