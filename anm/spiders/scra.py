from typing import Any
import scrapy
from scrapy.http import Response
from ..items import AnmItem, EpItem
from datetime import datetime
from itertools import count


class AnimesScrapy(scrapy.Spider):
    name = 'animesonline'
    allowed_domains = ['animesonlinecc.to']
    start_urls = ['https://animesonlinecc.to/anime/']
    def __init__(self, *args, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.global_anime_id = count(start=1)
        self.gloabl_ep_id = count(start=1)
    
    def parse(self, response: Response) -> Any:
        """
        vai para a pagina de lista de animes e faz request para a url do anime
        """
        anime_urls = response.xpath('//article//a[re:test(@href, "^https://")]/@href').getall()
        for url in anime_urls:
            yield scrapy.Request(
                url,
                callback=self.parser_anime,
                cb_kwargs={'anime_id': next(self.global_anime_id)}
            )
        
        next_page = response.xpath('//a[@class="arrow_pag"]/@href').getall()
        if next_page is not None:
            self.logger.debug(f'there is next page')
            yield response.follow(next_page[-1], callback=self.parse)
    
    def parser_anime(self, response: Response, anime_id: int):
        """
        Extrai os dados do anime como, por exemplo, titulo, ano, sinopse, episódios, etc.
        """
        categories = ', '.join(response.css('div.sgeneros a::text').getall())
        title = response.xpath('//h1/text()').get()
        year = response.css('span.date::text').get()
        sinopse = response.css('div.resumotemp div.wp-content p::text').get()
        rate = response.css('.dt_rating_vgs::text').get()

        anime = AnmItem(
            id=anime_id,
            categories=categories,
            name=title,
            year=year,
            sinopse=sinopse,
            url=response.url,
            rate=rate
        )
        yield anime

        seasons = response.css('div.se-c')
        for i, season in enumerate(seasons, start=1):
            for ep in season.css('div.episodiotitle'):
                number = ep.css('a::text').get().replace('Episodio ', '')
                url = ep.css('a::attr(href)').get()
                date = ep.css('span::text').get()
                date = datetime.strptime(date, '%b. %d, %Y')

                ep_item = EpItem(
                    id=next(self.gloabl_ep_id),
                    anime_id=anime_id,
                    number=number,
                    url=url,
                    date=date,
                    season=i
                )
                yield ep_item
