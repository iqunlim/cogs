import pandas as pd
import sqlalchemy as db
import asyncio, asyncpg #asyncpg investigation for later async functions for psql.
from typing import (
    Dict,
    Optional,
)



class NotInDefaults(Exception):
    """Handling a lack of connection info. Practice with working with exception handling and generators.\n
        Attributes:
            info: The dictionary checked for defaults.
            default: The list of defaults to print if they are not in info."""
    def __init__(self, info: Dict[str, str], default: set):
        m = (missing for missing in (x for x in default if not info.get(x, None)))
        super().__init__(f"Required values missing: {', '.join(m)}")


class PandasPSQL:
    """A syncronous (or eventually, also async) postgresql handler for pandas dataframes.
    Mostly done for practice. There are likely more efficient 
    versions of this out there."""
    
    def __init__(self, connectioninfo: Dict[str, str]):
        """Pandas DataFrame <--> PostgreSQL Handler.
           Requires: pandas[postgres]
           connectioninfo: A dictionary of connection variables.
                USER: Required. login username.
                PASS: Required. login password
                DB: Required. Name of the PSQL Database
                DOMAIN: Optional. Name of host else localhost
                PORT: Optional: 5432
                SCHEMA: Optional. Name of the schema. Defaults to 'public'.
           """
           
        #check that all default values are in the connection info.
        req = {'USER','PASS','DB'}
        if not all(x in connectioninfo.keys() for x in req): 
            raise NotInDefaults(connectioninfo, req)
        
        self.url = f"postgresql://{connectioninfo['USER']}:{connectioninfo['PASSWORD']} \
            @{connectioninfo.get('DOMAIN','localhost')}:{connectioninfo.get('PORT','5432')} \
            /{connectioninfo.get('DB','')}"
        self.schema = connectioninfo.get('SCHEMA','public')
        
        #Test url string before continuing
        if not self._testcon():
            raise ConnectionError(f"Cannot connect to SQL Database at {connectioninfo['DOMAIN']}")
        
    #do i need this? Maybe.
    #can this be done better? Oh yeah for sure.
    #Question: Investigating SQLAlchemy for like a dry-run of the connection to determine if it can even connect to run on init?     
    def _testcon(self):
        try:
            conn = db.create_engine(self.url).connect()
            conn.close()
            return True
        except:
            return False    
 
    def read(self, table: str, query: Optional[str] = None , groupby: Optional[str] = None, orderby: Optional[str] = None) -> pd.DataFrame:
        conn = db.create_engine(self.url).connect()
        try: 
            df = pd.read_sql(f"Select * FROM {self.schema}.{table if table else self.table} \
                                {f' WHERE {query}' if query else ''} \
                                {f' GROUP BY {groupby}' if groupby else ''} \
                                {f' ORDER BY {orderby}' if orderby else ''}", conn, index_col='id')
            return df
        finally:
            conn.close()

    def replace(self, df: pd.DataFrame, table: str) -> None:
        conn = db.create_engine(self.url).begin()
        try:
            df.to_sql(table, conn, schema=self.schema, if_exists="replace", index=False) #setting index=False since I prefer to write the primary key myself.
        except:
            pass #TODO: Custom error

    
    def append(self, df: pd.DataFrame, table: str) -> None:
        conn = db.create_engine(self.url).begin()
        try:
            df.to_sql(table, conn, schema=self.schema, if_exists="append", index=False)
        except:
            pass #TODO: Custom error.
    
    #TODO: This cant be done with dataframes so it will be a generic delete function for postgres.
    #Question: Do I even need this?         
    def delete(self, col: str, keys: pd.Series, table: str) -> None:
        raise NotImplementedError
        '''conn = db.create_engine(self.url).connect()
        try:
            pass
        finally:
            conn.close()'''
            
    #Async functions. Will have to write a handler and an optional setup for a loop. 
    #Question: Create own asyncio worker or use provided passed during initialization? 
    #Will likely call to the regular functions above        
    async def asyncread(self, table: str, query: Optional[str] = None , groupby: Optional[str] = None, orderby: Optional[str] = None) -> pd.DataFrame:
        raise NotImplementedError
    
    async def asyncreplace(self, df: pd.DataFrame, table: str) -> None:
        raise NotImplementedError
    
    async def asyncappend(self, df: pd.DataFrame, table: str) -> None:
        raise NotImplementedError
    
    async def asyncdelete(self, keys: pd.Series, table: str) -> None:
        raise NotImplementedError

#Returning as non-pandas objects        
class StringPSQL:
    
    def __init__(self, connectioninfo: Dict[str, str]):
        raise NotImplementedError
    
    def read():
        pass

    def replace():
        pass

    def write():
        pass

    def delete():
        pass