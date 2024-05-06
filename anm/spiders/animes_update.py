"""
spider para ser executado de forma regular pegando os animes das
3 primeiras paginas.
"""
from typing import Any
import scrapy
from scrapy.http import Response
from twisted.internet.defer import Deferred
from ..models import Anime, Ep
from datetime import datetime
from itertools import count
import os
from sqlalchemy import create_engine, Select
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
load_dotenv()


class AnimesUpdaterScrapy(scrapy.Spider):
    name = 'animesonline_update'
    allowed_domains = ['animesonlinecc.to']
    start_urls = [
        'https://animesonlinecc.to/anime/',
        'https://animesonlinecc.to/anime/page/2/',
        'https://animesonlinecc.to/anime/page/3/',
    ]

    def __init__(self, *args, **kwargs: Any):
        super().__init__(*args, **kwargs)
        uri = str(os.getenv('DB_URI')) + "?sslmode=require"
        self.engine = create_engine(uri, echo=True)
        Session = sessionmaker(self.engine)
        self.session = Session()
        self.logger.debug(f'Session active: {self.session.is_active}')

        last_aid = self.session.execute(
            Select(Anime.id).order_by(Anime.id.desc()).limit(1)
        ).first()
        self.logger.debug(f'last anime id={last_aid}')

        last_eid = self.session.execute(
            Select(Ep.id).order_by(Ep.id.desc()).limit(1)
        ).first()
        self.logger.debug(f'last ep id={last_eid}')

        self.global_anime_id = count(last_aid[0]+1)
        self.global_ep_id = count(last_eid[0]+1)
    
    def close(self, reason: str) -> Deferred | None:
        super().close(self, reason)
        self.session.close()
        self.logger.debug(f'Session active: {self.session.is_active}')
    
    def parse(self, response: Response) -> Any:
        """
        vai para a pagina de lista de animes e faz request para a url do anime
        """
        anime_urls = response.xpath('//article//a[re:test(@href, "^https://")]/@href').getall()
        for url in anime_urls:
            yield scrapy.Request(
                url,
                callback=self.parser_anime,
            )
    
    def parser_anime(self, response: Response):
        """
        Extrai os dados do anime como, por exemplo, titulo, ano, sinopse, episódios, etc.
        """
        categories = ', '.join(response.css('div.sgeneros a::text').getall())
        title = response.xpath('//h1/text()').get()
        year = response.css('span.date::text').get()
        sinopse = response.css('div.resumotemp div.wp-content p::text').get()
        rate = response.css('.dt_rating_vgs::text').get()

        is_duplicate = self.session.execute(
            Select(Anime).where(Anime.name == title).limit(1)
        ).first()
        self.logger.debug(f'anime is_duplicate query result: {is_duplicate}')

        anime = Anime(
            categories=categories,
            name=title,
            year=int(year),
            sinopse=sinopse,
            url=response.url,
            rate=float(rate) if rate is not None else 0.0
        )
        try:
            if not is_duplicate:
                anime.id = next(self.global_anime_id)
                self.session.add(anime)
                self.session.commit()
                self.logger.info(f'anime {anime.id} add')

        except Exception as e:
            self.logger.error(str(e))

        seasons = response.css('div.se-c')
        for i, season in enumerate(seasons, start=1):
            for ep in season.css('div.episodiotitle'):
                number = ep.css('a::text').get().replace('Episodio ', '')
                url = ep.css('a::attr(href)').get()
                date = ep.css('span::text').get()
                date = datetime.strptime(date, '%b. %d, %Y').date()

                ep_url_exists = self.session.execute(
                    Select(Ep).where(Ep.url == url).limit(1)
                ).first()
                self.logger.debug(f'ep_url_exists: {ep_url_exists}')

                anime_url_prefix = url.split('-episodio-')[0]
                db_anime_id = self.session.execute(
                            Select(Ep.anime_id).where(Ep.url.startswith(anime_url_prefix))
                ).first()
                self.logger.debug(f'db_anime_id: {db_anime_id}')

                ep_item = Ep(
                    anime_id=anime.id,
                    number=number,
                    url=url,
                    date=date,
                    season=i
                )

                try:
                    if not ep_url_exists  and not db_anime_id:
                        ep_item.id = next(self.global_ep_id)
                        self.session.add(ep_item)
                        self.session.commit()
                        self.logger.info(f'{ep_item.id} add para anime {ep_item.anime_id}')
                    
                    if not ep_url_exists  and db_anime_id:
                        ep_item.id = next(self.global_ep_id)
                        ep_item.anime_id = db_anime_id[0]

                        self.session.add(ep_item)
                        self.session.commit()
                        self.logger.info(f'{ep_item.id} add para anime {db_anime_id[0]}')

                except Exception as e:
                    self.logger.error(str(e))
