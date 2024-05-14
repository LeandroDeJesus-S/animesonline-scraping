from typing import Any
import scrapy
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Select
from scrapy.http import Response, Request
from ..models import Ep, Anime
import re
from datetime import datetime
from itertools import count


class EpUpdaterSpider(scrapy.Spider):
    name = 'ep_update'
    allowed_domains = ['animesonlinecc.to']
    start_urls = [
        'https://animesonlinecc.to/episodio/',
        'https://animesonlinecc.to/episodio/page/2/',
        'https://animesonlinecc.to/episodio/page/3/',
    ]

    def __init__(self, *args, **kwargs: Any):
        super().__init__(*args, **kwargs)
        uri = str(os.getenv('DB_URI')) + "?sslmode=require"
        self.engine = create_engine(uri, echo=True)
        Session = sessionmaker(self.engine)
        self.session = Session()
        self.logger.debug(f'Session active: {self.session.is_active}')

        lst_ep_id = self.session.execute(
            Select(Ep.id).order_by(Ep.id.desc()).limit(1)
        ).scalar()
        self.ep_id = count(start=lst_ep_id + 1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        eps_url = response.css('.eptitle h3 a::attr(href)').getall()
        for url in eps_url:
            if self.url_exists(url):
                self.logger.info(f'url {url} alredy exists')
                continue

            anime = self.get_anime_by_url(url)
            self.logger.debug(f'anime by url: {anime}')

            if not anime:
                self.logger.warning(f'anime result for url {url} not found')
                continue

            anime_id, anime_url = anime
            yield Request(
                anime_url, 
                callback=self.parse_anime_url, 
                cb_kwargs={'aid': anime_id}
            )
    
    def parse_anime_url(self, response: Response, **kwargs: Any):
        seasons = response.css('div.se-c')
        lst_season = seasons[-1]
        for ep in reversed(lst_season.css('div.episodiotitle')):
            number = ep.css('a::text').get().replace('Episodio ', '')
            url = ep.css('a::attr(href)').get()
            date = ep.css('span::text').get()
            date = datetime.strptime(date, '%b. %d, %Y').date()

            if self.url_exists(url):
                self.logger.info(f'url {url} already exists')
                break

            new_ep = Ep(
                id=next(self.ep_id),
                anime_id=kwargs.get('aid'),
                number=number,
                url=url,
                date=date,
                season=len(seasons)
            )
            
            try:
                self.session.add(new_ep)
                self.session.commit()
            except Exception as e:
                self.logger.error(str(e))

    def url_exists(self, url) -> bool:
        stmt = Select(Ep.id).where(Ep.url == url).limit(1)
        if self.session.execute(stmt).scalar():
            return True
        return False
    
    def get_anime_by_url(self, url):
        url_split = re.split(r"([2-9]?\d*)?\-episodio\-\d+\/$", url)[0]
        self.logger.debug(f'url split: {url_split}')

        stmt = Select(Ep.anime_id).where(
            Ep.url.contains(url_split)
        ).order_by(
            Ep.date.desc(), 
            Ep.number.desc()
        )
        subq = stmt.limit(1).subquery()
        q_res = self.session.execute(
            Select(
                Anime.id, Anime.url
            ).where(
                Anime.id.in_(subq)
            ).limit(1)
        ).first()

        if q_res is None:
            return ()
        return q_res
