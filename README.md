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
git clone <your-repo-url>
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

## License

MIT