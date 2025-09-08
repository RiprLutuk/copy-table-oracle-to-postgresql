import sys
import psycopg2 # pyright: ignore[reportMissingModuleSource]
import oracledb as cx_Oracle # type: ignore
import tempfile
import csv
import time
import logging
from .prdconfig import ORACLE_USER, ORACLE_PASS, ORACLE_SCHEMA, PG_CONN, ORACLE_HOST, ORACLE_PORT, ORACLE_SID

# --- Oracle Connection Setup ---
cx_Oracle.init_oracle_client(lib_dir="/opt/oracle/instantclient_23_9")
# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("sync.log", mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DEFAULT_TABLES = [
"schedareas",
"housemaster",
"commentmaster",
"brim_zw_wvtrig_1",
"brim_zn_nagratrig_1",
"brim_zm_protrig_cm",
"brim_zm_modem_exclude",
"brim_zm_fiber_cmts_grp",
"brim_zm_cmts",
"brim_zf_protrig_ont",
"brim_zf_ont_all",
"brim_voucher",
"brim_box_bequip",
"a_hp_servco_site_disable",
"boxinvtry",
]

def sync_table(table_name, ora_cur, pg_cur, pg_conn):
    start_time = time.time()

    # ambil kolom target PostgreSQL
    pg_cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position
    """, (table_name,))
    pg_columns = [r[0] for r in pg_cur.fetchall()]

    if not pg_columns:
        logger.warning(f"Table {table_name} tidak ditemukan di PostgreSQL, skip...")
        return

    # truncate target table
    pg_cur.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")
    pg_conn.commit()
    logger.info(f"🧹 {table_name}: truncated sebelum insert.")

    # cek jumlah row di Oracle
    ora_cur.execute(f"SELECT COUNT(*) FROM {ORACLE_SCHEMA}.{table_name.upper()}")
    total_count = ora_cur.fetchone()[0]
    logger.info(f"📊 {table_name}: total {total_count} rows di Oracle.")

    # query ambil data
    ora_cur.execute(f"SELECT {', '.join([c.upper() for c in pg_columns])} FROM {ORACLE_SCHEMA}.{table_name.upper()}")

    # fetch mode
    if total_count < 500_000:
        # fetch sekaligus
        rows = ora_cur.fetchall()
        with tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False) as tmpfile:
            writer = csv.writer(tmpfile, delimiter="^", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in rows:
                clean_row = ["" if v is None else str(v).replace("\x00", "") for v in row]
                writer.writerow(clean_row)
            tmpfile.flush()
            tmpfile.seek(0)
            pg_cur.copy_expert(
                f"""
                COPY {table_name} ({', '.join(pg_columns)})
                FROM STDIN WITH (FORMAT CSV, DELIMITER '^', QUOTE '"', NULL '')
                """,
                tmpfile
            )
        pg_conn.commit()
        logger.info(f"🎉 {table_name}: sync selesai, inserted {len(rows)} rows.")
    else:
        # fetch per batch
        batch_size = 500_000
        total_rows = 0
        chunk = 0
        while True:
            rows = ora_cur.fetchmany(batch_size)
            if not rows:
                break
            chunk += 1
            with tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False) as tmpfile:
                writer = csv.writer(tmpfile, delimiter="^", quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for row in rows:
                    clean_row = ["" if v is None else str(v).replace("\x00", "") for v in row]
                    writer.writerow(clean_row)
                tmpfile.flush()
                tmpfile.seek(0)
                pg_cur.copy_expert(
                    f"""
                    COPY {table_name} ({', '.join(pg_columns)})
                    FROM STDIN WITH (FORMAT CSV, DELIMITER '^', QUOTE '"', NULL '')
                    """,
                    tmpfile
                )
            pg_conn.commit()
            total_rows += len(rows)
            logger.info(f"✅ {table_name}: chunk {chunk}, total {total_rows} rows inserted...")

        logger.info(f"🎉 {table_name}: sync selesai, inserted {total_rows} rows.")

    elapsed = time.time() - start_time
    logger.info(f"⏱️  {table_name}: selesai dalam {elapsed:.2f} detik.\n")


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
            sync_table(tbl, ora_cur, pg_cur, pg_conn)
        except Exception as e:
            logger.error(f"❌ Error sync {tbl}: {e}", exc_info=True)

    pg_cur.close()
    pg_conn.close()
    ora_cur.close()
    ora_conn.close()


if __name__ == "__main__":
    main()
