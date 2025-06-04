from pathlib import Path
from shutil import rmtree
from tinydb import TinyDB, Query
from modules.utils import timestamp
from config import DATA_PATH 


class SiteDb:
    def __init__(self, db_name:str=None):
        if db_name:
            self.db_path:Path = DATA_PATH / 'temp_invoice'
            if self.db_path.exists():
                pass
            else:
                self.db_path.mkdir()

            self.db = TinyDB( self.db_path / f"{db_name}.json")

    async def get_items(self) ->list:
        """Returns all the documents in the requested database.

        Returns:
                list: list of documents
        """
        return self.db.all()
        
        
    async def get_item(self, prop:str=None, resource:str=None) ->list:
        """Returns all the documents in the requested database.

        Args:
            doc_id (str, optional): the document unique id as stored 
                in the database. Defaults to None.

        Returns:
            list: list of documents
        """
        Item = Query()
        item = self.db.search(Item[prop] == resource)
        return item
    
    def doc_count(self)->int:
        return len(self.db.all()) + 1
    
    async def save_item(self, data:dict=None)->list:  
        if data:
            try:
                self.db.insert(data)        
                return self.db.all()              
            except Exception as e:
                return [str(e)]

    
    async def delete_item(self, prop:str=None, resource:str=None) ->list:
        """Removes the documents from requested database.

        Args:
            doc_id (str, optional): the document unique id as stored 
                in the database. Defaults to None.

        Returns:
            list: list of documents
        """
        Item = Query()
        self.db.remove(Item[prop] == resource)
        return self.db.all()
           
    
    async def reset_repo(self)->None:
        """ Creates or overwrites the temporary file directory
        """        
        try: 
            self.db_path.mkdir() 
        except FileExistsError: 
            rmtree(self.db_path)
        finally: 
            self.db_path.mkdir()  

