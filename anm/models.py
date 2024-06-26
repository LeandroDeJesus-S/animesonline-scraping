from sqlalchemy.orm import declarative_base, DeclarativeBase
from sqlalchemy import Column, String, Date, Integer, ForeignKey, UniqueConstraint, Float
from sqlalchemy.orm import relationship

Base: DeclarativeBase = declarative_base()


class Anime(Base):
    __tablename__ = 'anime'

    id = Column(
        Integer, 
        primary_key=True, 
        unique=True
    )
    name = Column(
        String, 
        unique=True, 
        nullable=False
    )
    year = Column(
        String, 
        nullable=False
    )
    sinopse = Column(
        String, 
        unique=True, 
        nullable=False
    )
    categories = Column(
        String, 
        nullable=False
    )
    rate = Column(
        Float,
        default=0.0,
        nullable=False
    )
    url = Column(
        String, 
        unique=True
    )
    ep = relationship(
        'Ep', 
        back_populates='anime'
    )

    def __repr__(self):
        return f'Anime({self.__dict__.items()})'


class Ep(Base):
    __tablename__ = 'episode'
    
    id = Column(
        Integer, 
        primary_key=True, 
        unique=True
    )
    anime_id = Column(
        Integer, 
        ForeignKey(
            'anime.id',
            ondelete="CASCADE",
            onupdate='CASCADE',
        )
    )
    number = Column(
        String, 
        nullable=False
    )
    date = Column(
        Date, 
        nullable=False
    )
    season = Column(
        String, 
        nullable=False
    )
    url = Column(
        String,
        nullable=False
    )
    anime = relationship(
        'Anime', 
        back_populates='ep'
    )
    unique_ep_for_anime_constraint = UniqueConstraint(
        'anime_id', 
        'number', 
        'season', 
        name='unique_ep_for_anime_constraint'
    )

    __table_args__ = (
        UniqueConstraint('anime_id', 'season', 'number', 'url', name='unique_anm_ep_constraint'),
    )
    
    def __repr__(self):
        return f'Ep({self.__dict__.items()})'
