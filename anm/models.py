from sqlalchemy.orm import declarative_base, DeclarativeBase, validates
from sqlalchemy import (
    Column, 
    String, 
    Date, 
    Integer, 
    ForeignKey, 
    UniqueConstraint, 
    Float,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import re

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
        Integer, 
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

    __table_args__ = (
        CheckConstraint('rate >= 0 AND rate <= 10', name='check_anime_rate_0_10'),
    )

    def __repr__(self):
        return f'Anime({self.__dict__.items()})'
    
    @validates('year')
    def validate_year(self, _, year):
        assert 1900 < year <= datetime.today().year, f'invalid year {year}'
        return year
    
    @validates('url')
    def validate_url(self, _, url):
        assert bool(re.match(r'https\:\/\/animesonlinecc.to\/anime\/[\w-]+\/', url)), f'invalid url anime {url}'
        return url
    
    @validates('categories')
    def validate_categories(self, _, categories):
        assert bool(
            re.match(
                r'^[\+\w]+(?:, [\+\w, ]+)*\S$', 
                categories
            )
        ), f'invalid categories format {categories}'
        return categories
    


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
        Integer, 
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
        CheckConstraint('season > 0', name='check_ep_season_gt_0'),
    )
    
    def __repr__(self):
        return f'Ep({self.__dict__.items()})'
    
    @validates('url')
    def validate_url(self, _, url):
        assert bool(
            re.match(
                r'https\:\/\/animesonlinecc.to\/episodio\/[\w-]+\d*\-episodio-\d+\/', 
                url
            )
        ), f'invalid ep url {url}'
        return url

    @validates('date')
    def validate_date(self, _, date):
        assert datetime(1900, 1, 1).date() < date <= datetime.today().date(), f'invalid date {date}'
        return date
