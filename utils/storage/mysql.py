import logging
import pymysql
from pymysql.cursors import DictCursor
from typing import List, Dict, Optional, Generator


from configs.config_cls import MySQLConfig
from configs.config import MYSQL_CONFIG


class MySQLStorage:
    """MySQL database storage interface. Suitable for structured data storage and querying"""
    
    def __init__(self, config: MySQLConfig = MYSQL_CONFIG) -> None:
        self.config = config
        self._connection = None
    
    @property
    def connection(self):
        """Get database connection"""
        if self._connection is None or not self._connection.open:
            self._connection = pymysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.pwd.get_secret_value(),
                database=self.config.database,
                charset=self.config.charset,
                cursorclass=DictCursor
            )
        return self._connection
    
    def execute(self, sql: str, params: tuple = None, commit: bool = True) -> int:
        """Execute SQL statement
        
        Params:
            sql (str): SQL statement
            params (tuple): SQL parameters
            commit (bool): Whether to commit the transaction
            
        Returns:
            int: Number of affected rows
        """
        try:
            with self.connection.cursor() as cursor:
                affected_rows = cursor.execute(sql, params)
                if commit:
                    self.connection.commit()
                return affected_rows
        except Exception as e:
            self.connection.rollback()
            logging.error(f"MySQL execution error: {str(e)}, SQL: {sql}, Params: {params}")
            raise
    
    def execute_many(self, sql: str, params_list: List[tuple], commit: bool = True) -> int:
        """Execute multiple SQL statements
        
        Params:
            sql (str): SQL statement
            params_list (List[tuple]): List of SQL parameters
            commit (bool): Whether to commit the transaction
            
        Returns:
            int: Number of affected rows
        """
        try:
            with self.connection.cursor() as cursor:
                affected_rows = cursor.executemany(sql, params_list)
                if commit:
                    self.connection.commit()
                return affected_rows
        except Exception as e:
            self.connection.rollback()
            logging.error(f"MySQL batch execution error: {str(e)}, SQL: {sql}")
            raise
    
    def query_one(self, sql: str, params: tuple = None) -> Optional[Dict]:
        """Query a single record
        
        Params:
            sql (str): SQL query statement
            params (tuple): SQL parameters
            
        Returns:
            Optional[Dict]: Query result dictionary, returns None if no result
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"MySQL query error: {str(e)}, SQL: {sql}, Params: {params}")
            raise
    
    def query_all(self, sql: str, params: tuple = None) -> Generator[Dict, None, None]:
        """Query multiple records
        
        Params:
            sql (str): SQL query statement
            params (tuple): SQL parameters
            
        Returns:
            Generator[Dict, None, None]: Generator of query results
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                results = cursor.fetchall()
                for record in results:
                    yield record
        except Exception as e:
            logging.error(f"MySQL query error: {str(e)}, SQL: {sql}, Params: {params}")
            raise
    
    def insert(self, table: str, data: Dict) -> int:
        """Insert data into table
        
        Params:
            table (str): Table name
            data (Dict): Data to insert
            
        Returns:
            int: ID of the inserted row
        """
        fields = list(data.keys())
        placeholders = ["%s"] * len(fields)
        values = [data[field] for field in fields]
        
        sql = f"INSERT INTO {table} ({','.join(fields)}) VALUES ({','.join(placeholders)})"
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, values)
                self.connection.commit()
                return cursor.lastrowid
        except Exception as e:
            self.connection.rollback()
            logging.error(f"MySQL insert error: {str(e)}, Table: {table}, Data: {data}")
            raise
    
    def insert_many(self, table: str, data_list: List[Dict]) -> int:
        """Batch insert data
        
        Params:
            table (str): Table name
            data_list (List[Dict]): List of data to insert
            
        Returns:
            int: Number of affected rows
        """
        if not data_list:
            return 0
            
        fields = list(data_list[0].keys())
        placeholders = ["%s"] * len(fields)
        values_list = []
        
        for data in data_list:
            values = [data[field] for field in fields]
            values_list.append(values)
        
        sql = f"INSERT INTO {table} ({','.join(fields)}) VALUES ({','.join(placeholders)})"
        
        try:
            with self.connection.cursor() as cursor:
                affected_rows = cursor.executemany(sql, values_list)
                self.connection.commit()
                return affected_rows
        except Exception as e:
            self.connection.rollback()
            logging.error(f"MySQL batch insert error: {str(e)}, Table: {table}")
            raise
    
    def update(self, table: str, data: Dict, condition: str, params: tuple = None) -> int:
        """Update table data
        
        Params:
            table (str): Table name
            data (Dict): Data to update
            condition (str): Update condition
            params (tuple): Condition parameters
            
        Returns:
            int: Number of affected rows
        """
        set_clause = []
        values = []
        
        for field, value in data.items():
            set_clause.append(f"{field} = %s")
            values.append(value)
        
        if params:
            values.extend(params)
        
        sql = f"UPDATE {table} SET {', '.join(set_clause)} WHERE {condition}"
        
        try:
            with self.connection.cursor() as cursor:
                affected_rows = cursor.execute(sql, values)
                self.connection.commit()
                return affected_rows
        except Exception as e:
            self.connection.rollback()
            logging.error(f"MySQL update error: {str(e)}, Table: {table}, Data: {data}, Condition: {condition}")
            raise
    
    def delete(self, table: str, condition: str, params: tuple = None) -> int:
        """Delete table data
        
        Params:
            table (str): Table name
            condition (str): Delete condition
            params (tuple): Condition parameters
            
        Returns:
            int: Number of affected rows
        """
        sql = f"DELETE FROM {table} WHERE {condition}"
        
        try:
            with self.connection.cursor() as cursor:
                affected_rows = cursor.execute(sql, params)
                self.connection.commit()
                return affected_rows
        except Exception as e:
            self.connection.rollback()
            logging.error(f"MySQL delete error: {str(e)}, Table: {table}, Condition: {condition}")
            raise
    
    def create_table(self, table: str, schema: str) -> bool:
        """Create table
        
        Params:
            table (str): Table name
            schema (str): Table structure definition
            
        Returns:
            bool: Whether the creation was successful
        """
        sql = f"CREATE TABLE IF NOT EXISTS {table} ({schema})"
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql)
                self.connection.commit()
                return True
        except Exception as e:
            self.connection.rollback()
            logging.error(f"MySQL table creation error: {str(e)}, Table: {table}")
            raise
    
    def close(self):
        """Close the database connection"""
        if self._connection and self._connection.open:
            self._connection.close()
            self._connection = None


MYSQL_STORAGE = MySQLStorage()


if __name__ == '__main__':
    res = MYSQL_STORAGE.query_all("select * from tb_user_agent_info_1 where session_id  = '7307520186490294272' order by insert_time asc limit 10")
    for record in res:
        print(record)