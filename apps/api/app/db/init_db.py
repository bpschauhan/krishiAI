from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine
from app.models.language import Language
from app.models.location import District
from app.services.auth_seed import seed_auth_catalog
from app.services.seed_data import SUPPORTED_LANGUAGES, UTTAR_PRADESH_DISTRICTS


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        seed_languages(session)
        seed_districts(session)
        seed_auth_catalog(session)
        session.commit()


def seed_languages(session: Session) -> None:
    existing_codes = {
        code for (code,) in session.query(Language.code).filter(Language.code.in_(SUPPORTED_LANGUAGES))
    }
    for code, name in SUPPORTED_LANGUAGES.items():
        if code not in existing_codes:
            session.add(Language(code=code, name=name, is_active=True))


def seed_districts(session: Session) -> None:
    existing_names = {
        name for (name,) in session.query(District.name).filter(District.name.in_(UTTAR_PRADESH_DISTRICTS))
    }
    for district_name in UTTAR_PRADESH_DISTRICTS:
        if district_name not in existing_names:
            session.add(District(name=district_name, state="Uttar Pradesh", is_active=True))
