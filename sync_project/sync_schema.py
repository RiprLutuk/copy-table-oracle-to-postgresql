import sys
import psycopg2  # pyright: ignore[reportMissingModuleSource]
import oracledb as cx_Oracle  # type: ignore
import tempfile
import csv
import time
import logging
from .config import (
    ORACLE_USER,
    ORACLE_PASS,
    ORACLE_SCHEMA,
    PG_CONN,
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
    "cust_ledger_adjust",
    "cust_ledger_balance",
    "cust_ledger_header",
    "cust_ledger_intdepapp",
    "cust_ledger_latechg",
    "cust_ledger_payment",
    "cust_ledger_ppvchg",
    "cust_ledger_ppvcrd",
    "cust_ledger_rates",
    "cust_ledger_taxes",
    "cust_ledger_taxes_jvh",
    "cust_ledger_trans",
    "cust_ledger_writeoff",
    "sumcodes",
]


def sync_table(table_name, ora_cur, pg_cur, pg_conn, pg_schema):
    start_time = time.time()
    fq_table = f"{pg_schema}.{table_name}"  # fully qualified name

    # --- Ambil kolom target PostgreSQL ---
    pg_cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE lower(table_schema) = lower(%s)
        AND lower(table_name) = lower(%s)
        ORDER BY ordinal_position
        """,
        (pg_schema, table_name),
    )
    pg_columns = [r[0] for r in pg_cur.fetchall()]

    if not pg_columns:
        logger.warning(f"⚠️ Table {fq_table} tidak ditemukan di PostgreSQL, skip...")
        return

    # --- Truncate target table ---
    pg_cur.execute(f'TRUNCATE TABLE "{pg_schema}"."{table_name}" RESTART IDENTITY CASCADE;')
    pg_conn.commit()
    logger.info(f"🧹 {fq_table}: truncated sebelum insert.")

    # --- Hitung jumlah row di Oracle ---
    ora_cur.execute(f'SELECT COUNT(*) FROM "{ORACLE_SCHEMA}"."{table_name.upper()}"')
    total_count = ora_cur.fetchone()[0]
    logger.info(f"📊 {table_name}: total {total_count} rows di Oracle.")

    # --- Query ambil data dari Oracle ---
    ora_cur.execute(
        f'SELECT {", ".join([c.upper() for c in pg_columns])} '
        f'FROM "{ORACLE_SCHEMA}"."{table_name.upper()}"'
    )

    def write_and_copy(rows):
        with tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False) as tmpfile:
            writer = csv.writer(tmpfile, delimiter="^", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in rows:
                clean_row = ["" if v is None else str(v).replace("\x00", "") for v in row]
                writer.writerow(clean_row)
            tmpfile.flush()
            tmpfile.seek(0)
            pg_cur.copy_expert(
                f"""
                COPY "{pg_schema}"."{table_name}" ({", ".join(pg_columns)})
                FROM STDIN WITH (FORMAT CSV, DELIMITER '^', QUOTE '"', NULL '')
                """,
                tmpfile,
            )
        pg_conn.commit()

    # --- Mode fetch: full fetch atau batch ---
    if total_count < 500_000:
        rows = ora_cur.fetchall()
        write_and_copy(rows)
        logger.info(f"🎉 {fq_table}: sync selesai, inserted {len(rows)} rows.")
    else:
        batch_size = 500_000
        total_rows = 0
        chunk = 0
        while True:
            rows = ora_cur.fetchmany(batch_size)
            if not rows:
                break
            chunk += 1
            write_and_copy(rows)
            total_rows += len(rows)
            logger.info(f"✅ {fq_table}: chunk {chunk}, total {total_rows} rows inserted...")

        logger.info(f"🎉 {fq_table}: sync selesai, inserted {total_rows} rows.")

    elapsed = time.time() - start_time
    logger.info(f"⏱️ {fq_table}: selesai dalam {elapsed:.2f} detik.\n")


def main():
    if len(sys.argv) > 1:
        tables = [t.lower() for t in sys.argv[1:]]
    else:
        tables = DEFAULT_TABLES

    # --- Oracle connect via SID ---
    dsn = cx_Oracle.makedsn(ORACLE_HOST, ORACLE_PORT, sid=ORACLE_SID)
    ora_conn = cx_Oracle.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=dsn)
    ora_cur = ora_conn.cursor()

    # --- PostgreSQL connect ---
    pg_conn = psycopg2.connect(**PG_CONN)
    pg_cur = pg_conn.cursor()

    for tbl in tables:
        try:
            sync_table(tbl, ora_cur, pg_cur, pg_conn, PG_SCHEMA)
        except Exception as e:
            logger.error(f"❌ Error sync {tbl}: {e}", exc_info=True)

    pg_cur.close()
    pg_conn.close()
    ora_cur.close()
    ora_conn.close()


if __name__ == "__main__":
    main()
