import os
from itemadapter import ItemAdapter
from .items import AnmItem, EpItem
from .models import Base, Anime, Ep
from sqlalchemy import create_engine, Select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import PendingRollbackError
from dotenv import load_dotenv
load_dotenv()


class AnmPipeline:
    def __init__(self) -> None:
        uri = str(os.getenv('DB_URI')) + "?sslmode=require"
        self.engine = create_engine(uri, echo=True)
        
        self.tables = ['anime', 'episode']
        self._create_tables()

        self._pending_eps = []

        self.session = sessionmaker(self.engine)
    
    def _create_tables(self):
        for table in self.tables:
            Base.metadata.tables[table].create(self.engine, checkfirst=True)
        
    def open_spider(self, spider):
        if not hasattr(self, 'dbsession'):
            self.dbsession = self.session()
            spider.logger.info('\033[41m CONEXÃO COM BANCO DE DADOS ABERTA\033[m')
    
    def close_spider(self, spider):
        if hasattr(self, 'dbsession'):
            self.dbsession.close()
            spider.logger.info('\033[42m CONEXÃO COM BANCO DE DADOS FECHADA \033[m')

    def _add_if_pending(self, anime, spider):
        for ep in self._pending_eps:
            if anime.id == ep.anime_id:
                self.dbsession.add(ep)
                self._pending_eps.remove(ep)
                spider.logger.info(f'pending episode {ep.id} from anime {ep.anime_id} added')

    def process_item(self, item, spider):
        try:
            if isinstance(item, AnmItem):
                anime = Anime(
                    **ItemAdapter(item).asdict()
                )

                self.dbsession.add(anime)
                self.dbsession.commit()
                spider.logger.info(f'{anime} adicionado na base de dados')
                
                self._add_if_pending(anime, spider)
            
            elif isinstance(item, EpItem):
                ep = Ep(
                    **ItemAdapter(item).asdict()
                )

                scalar = self.dbsession.execute(
                    Select(Anime.id).where(Anime.id == ep.anime_id)
                )
                
                if scalar.first() is not None:
                    self.dbsession.add(ep)
                    self.dbsession.commit()
                    spider.logger.info(f'{ep} adicionado na base de dados')
                
                else:
                    self._pending_eps.append(ep)
                    spider.logger.info(f'episode {ep.id} from anime {ep.anime_id} pending')

        except PendingRollbackError as e:
            spider.logger.warning(f'\033[33m{e}\033[m')
            if hasattr(self, 'dbsession'):
                self.dbsession.rollback()

        except Exception as e:
            spider.logger.error(str(e))
            self.dbsession.rollback()
        
        finally:
            return item
