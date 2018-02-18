from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Leagues(Base):
    __tablename__ = 'leagues'

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    description = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    teams = relationship('Teams', cascade='all, delete-orphan')

    @property
    def serialize(self):
        # Return object data in serializeable format
        return {
            'id': self.id,
            'title': self.title,
            'namdescription': self.description,
            }


class Teams(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    title = Column(String(80), nullable=False)
    description = Column(String(250))
    league_id = Column(Integer, ForeignKey('leagues.id'))
    league = relationship(Leagues)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        # Return object data in serializeable format
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            }

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.create_all(engine)