import os
import sqlite3
import threading

from ptn.aco.constants import get_db_path, get_db_dumps_path

print(f'Starting DB at: {get_db_path()}')

affiliator_conn = sqlite3.connect(get_db_path())
affiliator_conn.row_factory = sqlite3.Row
affiliator_db = affiliator_conn.cursor()
affiliator_conn.set_trace_callback(print)

db_sql_store = get_db_dumps_path()
affiliator_lock = threading.Lock()


def dump_database():
    """
    Dumps the affiliate user database into sql.

    :returns: None
    """
    with open(db_sql_store, 'w') as f:
        for line in affiliator_conn.iterdump():
            f.write(line)


def build_database_on_startup():
    print('Checking whether the affiliate db exists')
    affiliator_db.execute(
        '''SELECT count(name) FROM sqlite_master WHERE TYPE = 'table' AND name = 'acoapplications' ''')
    if not bool(affiliator_db.fetchone()[0]):

        if os.path.exists(db_sql_store):
            # recreate from backup file
            print('Recreating database from backup ...')
            with open(db_sql_store) as f:
                sql_script = f.read()
                affiliator_db.executescript(sql_script)
        else:
            print('Creating a fresh database')
            affiliator_db.execute('''
                CREATE TABLE acoapplications( 
                    entry INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_username TEXT NOT NULL,
                    ptn_nickname TEXT NOT NULL,
                    cmdr_name TEXT NOT NULL,
                    fleet_carrier_name TEXT NOT NULL,
                    fleet_carrier_id TEXT NOT NULL,
                    ack BOOLEAN,
                    user_claims_member BOOLEAN,
                    timestamp DATETIME,
                    UNIQUE (fleet_carrier_name, timestamp)
                ) 
            ''')
            affiliator_conn.commit()
            print('Affiliate Database created')
    else:
        print('The Affiliate database already exists')

    print('Checking whether the the input tracking database exists')
    affiliator_db.execute(
        '''SELECT count(name) FROM sqlite_master WHERE TYPE = 'table' AND name = 'trackingforms' '''
    )
    if not bool(affiliator_db.fetchone()[0]):
        print('Creating a fresh trackingforms database')
        affiliator_db.execute('''
                CREATE TABLE trackingforms(
                    entry INTEGER PRIMARY KEY AUTOINCREMENT,
                    worksheet_key TEXT UNIQUE,
                    worksheet_with_data_id INT
                ) 
            ''')
        # Some default values in the case we need to make the table. These will need to be set accordingly,
        # remove this once we have them in place
        affiliator_db.execute('''
            INSERT INTO trackingforms VALUES(
                NULL,
                '1-AK8MeguKMOK4cifTntIVUVcbY9oQUIPhMMkrUmztwE',
                0
            ) 
        ''')
        affiliator_conn.commit()
        print('Forms Database created')
    else:
        print('The tracking forms database already exists')

    print('Checking whether the the member tracking database exists')
    affiliator_db.execute(
        '''SELECT count(name) FROM sqlite_master WHERE TYPE = 'table' AND name = 'membertracking' '''
    )
    if not bool(affiliator_db.fetchone()[0]):
        print('Creating a fresh membertracking database')
        affiliator_db.execute('''
                CREATE TABLE membertracking(
                    entry INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_username TEXT UNIQUE,
                    date DATETIME
                ) 
            ''')
        affiliator_conn.commit()
        print('Member tracking database created')
    else:
        print('The member tracking table already exists')
