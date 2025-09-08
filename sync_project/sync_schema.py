import sys
import oracledb as cx_Oracle  # type: ignore
import tempfile
import csv
import time
import logging
import os
from .config import (
    ORACLE_USER,
    ORACLE_PASS,
    ORACLE_SCHEMA,
    ORACLE_HOST,
    ORACLE_PORT,
    ORACLE_SID,
    PG_SCHEMA,
)

# --- Oracle Connection Setup ---
cx_Oracle.init_oracle_client(lib_dir="/opt/oracle/instantclient_23_9")

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("sync.log", mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

DEFAULT_TABLES = [
    # "cust_ledger_header",
    # "cust_ledger_intdepapp",
    # "cust_ledger_latechg",
    # "cust_ledger_payment",
    # "cust_ledger_ppvchg",
    # "cust_ledger_ppvcrd",
    # "cust_ledger_rates",
    # "cust_ledger_taxes",
    # "cust_ledger_taxes_jvh",
    "cust_ledger_trans",
    "cust_ledger_writeoff",
    "sumcodes",
]

OUTPUT_DIR = "/mnt/d/Postgresql/sync_data/data"


def write_to_csv(rows, table_name, pg_columns, part=None):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    suffix = f"_part{part}" if part else ""
    file_path = os.path.join(OUTPUT_DIR, f"{table_name}{suffix}.csv")

    with open(file_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="^", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            clean_row = ["" if v is None else str(v).replace("\x00", "") for v in row]
            writer.writerow(clean_row)

    logger.info(f"💾 {table_name}{suffix}: export {len(rows)} rows ke {file_path}")


def sync_table(table_name, ora_cur):
    start_time = time.time()

    # --- Ambil kolom dari Oracle ---
    ora_cur.execute(
        """
        SELECT COLUMN_NAME
        FROM ALL_TAB_COLUMNS
        WHERE OWNER = :p_schema AND TABLE_NAME = :p_table
        ORDER BY COLUMN_ID
        """,
        p_schema=ORACLE_SCHEMA.upper(),
        p_table=table_name.upper(),
    )
    pg_columns = [r[0].lower() for r in ora_cur.fetchall()]

    if not pg_columns:
        logger.warning(f"⚠️ Table {table_name} tidak ditemukan di Oracle, skip...")
        return

    # --- Hitung jumlah row di Oracle ---
    ora_cur.execute(f'SELECT COUNT(*) FROM "{ORACLE_SCHEMA}"."{table_name.upper()}"')
    total_count = ora_cur.fetchone()[0]
    logger.info(f"📊 {table_name}: total {total_count} rows di Oracle.")

    # --- Query ambil data dari Oracle ---
    ora_cur.execute(
        f'SELECT {", ".join([c.upper() for c in pg_columns])} '
        f'FROM "{ORACLE_SCHEMA}"."{table_name.upper()}"'
    )

    if total_count < 1_500_000:
        rows = ora_cur.fetchall()
        write_to_csv(rows, table_name, pg_columns)
    else:
        batch_size = 1_500_000
        total_rows = 0
        chunk = 0
        while True:
            rows = ora_cur.fetchmany(batch_size)
            if not rows:
                break
            chunk += 1
            write_to_csv(rows, table_name, pg_columns, part=chunk)
            total_rows += len(rows)
            logger.info(f"✅ {table_name}: chunk {chunk}, total {total_rows} rows exported...")

    elapsed = time.time() - start_time
    logger.info(f"⏱️ {table_name}: selesai dalam {elapsed:.2f} detik.\n")


def main():
    if len(sys.argv) > 1:
        tables = [t.lower() for t in sys.argv[1:]]
    else:
        tables = DEFAULT_TABLES

    # --- Oracle connect via SID ---
    dsn = cx_Oracle.makedsn(ORACLE_HOST, ORACLE_PORT, sid=ORACLE_SID)
    ora_conn = cx_Oracle.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=dsn)
    ora_cur = ora_conn.cursor()

    for tbl in tables:
        try:
            sync_table(tbl, ora_cur)
        except Exception as e:
            logger.error(f"❌ Error export {tbl}: {e}", exc_info=True)

    ora_cur.close()
    ora_conn.close()


if __name__ == "__main__":
    main()
