from datetime import datetime

import pandas as pd
import pandas_datareader as fetch
from dateutil.relativedelta import relativedelta
from pandas.tseries.offsets import BDay
from sqlalchemy import (Column, MetaData, Sequence, Table,
                        create_engine, inspect)
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql.sqltypes import TIMESTAMP, DATETIME, String, Float


# Set up of the engine to connect to the database
class MainControl():
    """
    Class MainControl is intended to be insitialized by the Main window instance, it sets up
        database connection, as well as an instance for 'symbols' table control,
        and another for 'logs' table control.
    The class is designed this way to maintain a single database connection
        over all tables, and unify the path taken through instances to log access to tables.
    """

    def __init__(self):
        print('>>>> [MAIN]: INITIALIZING MAIN DATABASE CONNECTION')
        self.engine = create_engine('sqlite:///stocks.db', echo=False)
        self.inspector = inspect(self.engine)
        self.db_connection = self.engine.connect()
        self.create_session = sessionmaker(bind=self.engine)

        self.symbols = self.Symbols(self)
        self.logger = self.Logger(self)

        self.logger.get_log('symbols', 'write')

    class Symbols():
        """
        Class Symbols represents database table "symbols", it is mainly created
            and managed by the MainControl instance.
        It is intended to keep track of listed symbols in the market and which
            company it belongs to, and used in input validation in the Main window,
            as well as auto-completion feautre.
        """

        def __init__(self, control):
            self.__control = control
            self.table_name = 'symbols'
            self.table = self.__check_symbols()

        def __check_symbols(self):
            """
            Private instance method __check_symbols() checks for the existence of the table 'symbols',
                if the table does not exist, it will create one.

            Returns:
                Sqlalchmey Table: a sqlalchemy table ('symbols').
            """
            metadata = MetaData(bind=self.__control.engine)
            if self.table_name not in self.__control.inspector.get_table_names():
                table = Table(
                    str(self.table_name),
                    metadata,
                    Column("Symbol", String, primary_key=True,),
                    Column("Security_Name", String),
                )
                metadata.create_all(self.__control.db_connection)
            else:
                metadata.reflect(self.__control.engine)
                table = Table(self.table_name, metadata, autoload=True)

            return table

        def __update_symbols(self):
            """
            Private instance method __update_symbols() will complete the symbols table with
                missing data, but it will NOT update or modify existing data, which needs to be changed
                in the future.
            """
            symbols = fetch.get_nasdaq_symbols().filter(
                ['Symbol', 'Security Name'])
            symbols['Symbol'] = symbols.index
            symbols.columns = symbols.columns.str.replace(' ', '_')
            symbols = symbols.to_dict(orient='records')

            write_session = scoped_session(self.__control.create_session)
            insert_stmt = insert(self.table).values(symbols)
            write_session.execute(insert_stmt.on_conflict_do_nothing(
                index_elements=self.table.primary_key))
            write_session.commit()  # Commit changes
            write_session.remove()  # Close session

            self.__control.logger.new_log('symbols', 'write')

        def __read_symbols(self):
            """
            Private instance method __read_symbols() returns a pandas Dataframe of the table

            Returns:
                Dataframe: a pandas Dataframe of the 'symbols' table.
            """
            read_session = scoped_session(self.__control.create_session)
            read_stmt = read_session.query(self.table).statement
            symbols = pd.read_sql(read_stmt, read_session.bind)
            read_session.remove()
            self.__control.logger.new_log('symbols', 'read')

            return symbols

        def get_symbols(self):
            """
            Instance method get_symbols() returns a pandas dataframe of
                company symbols and security names, as retrieved from Nasdaq.

            Returns:
                Pandas Dataframe: a dataframe of the symbols table.
            """
            symbols = self.__read_symbols()
            last_write = self.__control.logger.get_log('symbols', 'write')
            # if the table is empty, or -according to logs- the table was written one or more weeks ago,
            # or there are no logs for previous writes, it will call __update_symbols() to complete the data.
            if symbols.empty or last_write.empty or pd.to_datetime(last_write['Timestamp']) <= datetime.now() - relativedelta(weeks=1):
                if symbols.empty or last_write.empty:
                    print('> First run..')
                print('> [MAIN]: Updating symbols, please wait')
                try:
                    self.__update_symbols()
                except Exception as e:
                    raise e

                symbols = self.__read_symbols()

            return symbols

    class Logger():
        """
        Class Logger represents database table "logs", it is mainly created
            and managed by the MainControl instance.
        It is intended to keep track of symbols table access, reads and writes.
            and is currently used to manage symbols update, and can be used for other
            purposes in the future (e.g deleting very old symbol tables for cleanup)
        """

        def __init__(self, control):
            self.__control = control
            self.table_name = 'logs'
            self.table = self.__check_logger()

        def __check_logger(self):
            """
            Private instance method __check_logger() checks for the existence of the table 'logs',
                if the table does not exist, it will create one.

            Returns:
                Sqlalchmey Table: a sqlalchemy table ('logs')
            """
            metadata = MetaData(bind=self.__control.engine)
            if self.table_name not in self.__control.inspector.get_table_names():
                table = Table(
                    str(self.table_name),
                    metadata,
                    Column("Timestamp", TIMESTAMP, primary_key=True),
                    Column("Table_name", String),
                    Column("Operation", String),
                )
                metadata.create_all(self.__control.db_connection)
            else:
                metadata.reflect(self.__control.engine)
                table = Table(self.table_name, metadata, autoload=True)

            return table

        def new_log(self, table_name, op):
            """
            Instance method new_log() takes a table name: str() and an operation: str() (that is 'read'/'write')
                and adds a new entry in the table with a timestamp, which is later used to determine if the table needs updating.

            Args:
                table_name (String): name of the table
                op (String): operation 'read' or 'write'
            """
            values = {'Timestamp': datetime.now(
            ), "Table_name": table_name, 'Operation': op}
            write_session = scoped_session(self.__control.create_session)
            insert_stmt = insert(self.table).values(values)
            write_session.execute(insert_stmt)
            write_session.commit()  # Commit changes
            write_session.remove()  # Close session

        def get_log(self, table_name, op):
            """
            Instance method get_log() takes a table name: str() and an operation: str() (that is 'read'/'write')
                and returns a pandas Dataframe of all table entries regarding the given table and operation, 
                along with a timestamp for each.

            Args:
                table_name (String): name of the table
                op (String): operation 'read' or 'write'

            Returns:
                Dataframe: Dataframe of rows matching provided arguments
            """
            read_session = scoped_session(self.__control.create_session)
            read_stmt = read_session.query(self.table).filter(self.table.c.get(
                'Table_name') == table_name, self.table.c.get('Operation') == op).statement
            log = pd.read_sql(read_stmt, read_session.bind)
            read_session.remove()
            if log.empty:
                return log
            return log.iloc[-1]


class TableControl():
    """
    Class TableControl represents a table of a given symbol.
        This class is intended to be created and controlled by
        the DataControl instance.

    Args:
        sym (String): a company symbol/ticker
        db_con (Object): Database connection object (MainControl object)
    """

    def __init__(self, sym, db_con, timeKeep):
        print(f'>>> [{sym}]: INITIALIZING DATABASE CONTROL')
        self.sym = sym
        self.db_con = db_con
        self.timeKeep = timeKeep
        self.table = self.__check_table()

    def __check_table(self):
        """
        Private instance method __check_table() checks for the existence of a table with name {sym},
            if the table does not exist, it will create one.

        Returns:
            Sqlalchmey Table: a sqlalchemy table of the symbol
        """
        metadata = MetaData(bind=self.db_con.engine)
        table_name = self.sym

        if table_name not in self.db_con.inspector.get_table_names():
            table_name = Table(
                str(table_name),
                metadata,
                Column("Date", DATETIME, Sequence(
                    'poi_id_seq'), primary_key=True),
                Column("High", Float),
                Column("Low", Float),
                Column("Open", Float),
                Column("Close", Float),
                Column("Volume", Float),
                Column("Adj_Close", Float)
            )
            metadata.create_all(self.db_con.db_connection)

            print(f'> [{self.sym}]: Table created')
            # print('Fetching data')
        else:
            metadata.reflect(self.db_con.engine)
            print(f'> [{self.sym}]: Table exists')

        return Table(table_name, metadata, autoload=True)

    def __fetch_quote(self, start):
        """
        Private instance method __fetch_quote() fetches a quote on the symbol of the table
            from the given start date to the last business day (from yahoo servers)

        Args:
            start (datetime): a datetime string '%yyyy-%mm-%dd' or datetime python object to fetch data starting from.

        Raises:
            ConnectionError: if a connection to fetch the data could not be made.

        Returns:
            Dataframe: a pandas dataframe of the fetched data.
        """
        print(f'> [{self.sym}]: fetching quote')
        try:
            dataFetch = fetch.DataReader(self.sym, 'yahoo', start)
        except Exception as e:
            print(repr(e))
            raise e

        # modify columns to my liking (db's actually)
        dataFetch.columns = dataFetch.columns.str.replace(' ', '_')
        dataFetch['Index'] = dataFetch.index.to_pydatetime()
        dataFetch['Date'] = pd.to_datetime(dataFetch['Index']).dt.date
        del dataFetch['Index']
        quote = dataFetch.to_dict(orient='records')
        return quote

    def __commit_entry(self, data, update):
        """
        Private instance variable __commit_entry() takes a fetched quote dataframe and
           inserts it into the symbol table

        Args:
            data (Dataframe): a dataframe of a fetched quote
            update (Boolean): True if the provided data is an update of existing data

        Raises:
            DatabaseUpdateError: an error to indicate a failed attempt to insert and commit data
        """

        print(f'> [{self.sym}]: committing data')
        write_session = scoped_session(
            self.db_con.create_session)  # Open session
        try:
            # if update, insert data row by row with update on conflict clause
            if update:
                for row in data:
                    insert_stmt = insert(self.table).values(row).on_conflict_do_update(index_elements=self.table.primary_key, set_=row)
                    write_session.execute(insert_stmt)
            # if no update, insert all data in bulk
            else:
                insert_stmt = insert(self.table).values(data)
                write_session.execute(insert_stmt)
            write_session.commit()  # Commit changes
            write_session.remove()  # Close session

        # in case something catches fire
        except Exception as DatabaseUpdateError:
            print(repr(DatabaseUpdateError))
            raise DatabaseUpdateError

    def read_table(self):
        """
        Instance method read_table() reads symbol table and returns a pandas DataFrame.

        Returns:
            Dataframe: a pandas dataframe of the existing data in the symbol table.
        """
        print(f'> [{self.sym}]: reading table')
        read_session = scoped_session(self.db_con.create_session)
        read_stmt = read_session.query(self.table).statement
        dbRead = pd.read_sql(read_stmt, read_session.bind, index_col='Date')
        read_session.remove()
        return dbRead

    def write_table(self):
        """
        Instance method write_table() calculates the last business day use it to either write missing data from the symbol table,
            or call update_last() if the table is complete to the last business day.
        If the table is empty, it will fetch all data and commit it to the table.
        """
        print(f'> [{self.sym}]: writing table')
        currEstTime = self.timeKeep.estTime
        currEstDate = pd.to_datetime(self.timeKeep.estDate)

        # calculate last business EST date.
        if bool(len(pd.bdate_range(currEstDate, currEstDate))):
            if currEstTime > '09:30:00':
                last_trading_date = currEstDate
            else:
                last_trading_date = currEstDate - BDay(1)
        else:
            last_trading_date = currEstDate - BDay(1)

        # check last entry date
        try:
            existing_data = self.read_table()
            lastEntryDate = existing_data.tail(1).index.item()
            # if the table contains data to the last business date, update last.
            if lastEntryDate == last_trading_date or lastEntryDate < last_trading_date:
                self.update_last()
            # if the table contains incomplete data, fetch missing data to completion
            else:
                print(
                    f'> [{self.sym}]: table exists and contains data.. completing missing data..')
                start = lastEntryDate + BDay(1)
                quote = self.__fetch_quote(start=start)
                self.__commit_entry(data=quote, update=0)
        except ValueError:
            # if the table exists but empty, fetch and commit all the data
            print(f'> [{self.sym}]: table exists but empty, filling..')
            quote = self.__fetch_quote(start=None)
            self.__commit_entry(data=quote, update=0)

    def update_last(self):
        """
        Instance method update_last() reads last entry in the symbol table, and update it by fetching
            data starting from the date of the last entry, and committing it.

        Raises:
            e: caught error during fetching or committing
        """
        existing_data = self.read_table()
        lastEntryDate = existing_data.tail(1).index.item().strftime("%Y-%m-%d")
        print(f'> [{self.sym}]: updating last entry in table')
        try:
            quote = self.__fetch_quote(start=lastEntryDate)
            self.__commit_entry(data=quote, update=1)
        except Exception as e:
            print(repr(e))
            raise e
