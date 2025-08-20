# sync_data

A Python-based utility for synchronizing data from Oracle tables to PostgreSQL tables.

## Features

- Syncs specified tables from Oracle to PostgreSQL.
- Truncates PostgreSQL tables before loading new data.
- Uses efficient CSV streaming for bulk inserts.
- Command-line interface for flexible usage.
- Configurable connection settings.

## Requirements

- Python 3.7 or higher
- Oracle client libraries (for `oracledb`)
- PostgreSQL server
- Python packages:
  - `psycopg2-binary`
  - `oracledb`

## Installation

Clone the repository and install dependencies:

```sh
git clone https://github.com/RiprLutuk/copy-table-oracle-to-postgresql.git
cd sync_data
pip install -r requirements.txt
```

## Configuration

Edit `sync_project/config.py` to set your database connection details:

```python
ORACLE_USER = "your_oracle_user"
ORACLE_PASS = "your_oracle_password"
ORACLE_DSN  = "host:port/service_name"
ORACLE_SCHEMA = "your_oracle_schema"

PG_CONN = {
    "host": "localhost",
    "port": 5432,
    "database": "your_pg_db",
    "user": "your_pg_user",
    "password": "your_pg_password"
}
```

## Usage

### Command Line

Run the sync script with table names as arguments:

```sh
python -m sync_project.sync table1 table2
```

If no tables are specified, the script will use the default list in `sync_project/sync.py`.

### Example

```sh
python -m sync_project.sync a_hp_batch a_hp_batch_detail
```

## How It Works

1. Reads column names from the target PostgreSQL table.
2. Truncates the PostgreSQL table.
3. Fetches data from the Oracle table in batches.
4. Writes data to a temporary CSV file.
5. Loads the CSV into PostgreSQL using the `COPY` command.
6. Deletes the temporary CSV file.

## Notes

- Ensure the PostgreSQL tables exist and have the same structure as the Oracle tables.
- Both databases must be accessible from the machine running the script.

## Oracle Client Setup

To connect to Oracle, you must install the Oracle Instant Client and configure `tnsnames.ora`:

### 1. Download and Install Oracle Instant Client

- Go to [Oracle Instant Client Downloads](https://www.oracle.com/database/technologies/instant-client/downloads.html).
- Download the **Basic** and **SQL*Plus** packages for your OS (Linux x86-64 is common).
- Unzip both packages to the same directory, e.g., `/opt/oracle/instantclient_21_11`.

### 2. Configure Environment Variables

Add the following to your `~/.bashrc` or `~/.profile`:

```sh
export ORACLE_HOME=/opt/oracle/instantclient_21_11
export LD_LIBRARY_PATH=$ORACLE_HOME
export PATH=$ORACLE_HOME:$PATH
```

Reload your shell:

```sh
source ~/.bashrc
```

### 3. Setup `tnsnames.ora`

- Create a directory for Oracle network configuration if it doesn't exist:

    ```sh
    mkdir -p $ORACLE_HOME/network/admin
    ```

- Create or edit `$ORACLE_HOME/network/admin/tnsnames.ora` and add your Oracle service:

    ```
    YOURDB =
      (DESCRIPTION =
        (ADDRESS = (PROTOCOL = TCP)(HOST = your_host)(PORT = your_port))
        (CONNECT_DATA =
          (SERVICE_NAME = your_service_name)
        )
      )
    ```

- Use `YOURDB` as the `ORACLE_DSN` in your configuration.

### 4. Test the Connection

You can test with SQL*Plus:

```sh
sqlplus your_oracle_user/your_oracle_password@YOURDB
```

If you connect successfully, your Python script should also

## License

MIT