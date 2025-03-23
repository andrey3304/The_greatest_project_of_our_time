from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///users.db', echo=True)

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


def register_user(username, password):
    existing_user = session.query(User).filter_by(username=username).first()
    if existing_user:
        pass
    else:
        new_user = User(username=username, password=password)
        session.add(new_user)
        session.commit()
