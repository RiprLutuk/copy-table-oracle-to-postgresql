import sys
import os
import psycopg2
import logging
from collections import defaultdict
from .config import (
    PG_CONN,
    PG_SCHEMA,
)

INPUT_DIR = "/mnt/d/Postgresql/sync_data/data"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def import_table(cur, conn, table_name, files, dry_run=False, count_db=False, keep=False, no_truncate=False):
    logger.info(f"🚀 Import {table_name} ({len(files)} file)")
    if dry_run:
        for f in sorted(files):
            logger.info(f"   ↳ preview file: {f}")
        return

    # Truncate dulu
    if not no_truncate:
        logger.info(f"🧹 Truncate table {table_name} sebelum import")
        cur.execute(f'TRUNCATE TABLE "{PG_SCHEMA}"."{table_name}"')
    else:
        logger.info(f"⏩ Skip truncate table {table_name}")
    #cur.execute(f'TRUNCATE TABLE "{PG_SCHEMA}"."{table_name}"')

    total_rows = 0
    for f in sorted(files):
        file_path = os.path.join(INPUT_DIR, f)

        try:
            # Import CSV ke PostgreSQL
            with open(file_path, "r", encoding="utf-8") as csvfile:
                cur.copy_expert(
                    f"""
                    COPY "{PG_SCHEMA}"."{table_name}"
                    FROM STDIN WITH (FORMAT CSV, DELIMITER '^', QUOTE '"', NULL '')
                    """,
                    csvfile,
                )

            # Hitung jumlah baris di file
            with open(file_path, "r", encoding="utf-8") as fcount:
                row_count = sum(1 for _ in fcount)
            total_rows += row_count

            # Commit per file
            conn.commit()
            logger.info(f"✅ {table_name}: import {f} ({row_count} rows)")

            # Hapus file setelah berhasil (kecuali keep)
            if not keep:
                os.remove(file_path)
                logger.info(f"🗑️ File {f} dihapus setelah berhasil import")
            else:
                logger.info(f"📦 File {f} disimpan (opsi --keep aktif)")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Gagal import {f}: {e}")
            logger.warning(f"⚠️ File {f} tidak dihapus (silakan periksa manual)")

    if count_db:
        cur.execute(f'SELECT COUNT(*) FROM "{PG_SCHEMA}"."{table_name}"')
        db_count = cur.fetchone()[0]
        logger.info(f"📊 {table_name}: jumlah row di database = {db_count}")

    logger.info(f"🎉 {table_name}: selesai import {len(files)} file, total {total_rows} rows\n")


def main():
    dry_run = "--dry-run" in sys.argv
    count_db = "--count-db" in sys.argv
    keep = "--keep" in sys.argv
    no_truncate = "--no-truncate" in sys.argv
    args = [a for a in sys.argv[1:] if a not in ("--dry-run", "--count-db", "--keep", "--no-truncate")]

    if args:
        # Kalau ada argumen → import tabel tertentu
        # tables = [t.lower() for t in args]
        tables = [os.path.splitext(t.lower())[0] for t in args]
    else:
        # Default: scan semua file CSV di folder
        all_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]
        table_map = defaultdict(list)
        for f in all_files:
            # base = f.split("_part")[0]
            base = os.path.splitext(f)[0].split("_part")[0]
            table_map[base].append(f)

        if not table_map:
            logger.warning("⚠️ Tidak ada file CSV ditemukan di folder input.")
            return

        logger.info("📂 Ditemukan tabel untuk import:")
        for t, files in table_map.items():
            logger.info(f"  - {t} ({len(files)} file)")
        tables = list(table_map.keys())

    # --- PostgreSQL Connect ---
    conn = None
    cur = None
    if not dry_run:
        conn = psycopg2.connect(**PG_CONN)
        cur = conn.cursor()

    # Import per table
    for tbl in tables:
        files = [f for f in os.listdir(INPUT_DIR) if f.startswith(tbl)]
        if not files:
            logger.warning(f"⚠️ File untuk {tbl} tidak ditemukan, skip...")
            continue
        import_table(cur, conn, tbl, files, dry_run=dry_run, count_db=count_db, keep=keep, no_truncate=no_truncate)

    if not dry_run:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()

##Contoh cara pakai:
#import-csv → import & hapus file sukses.
#import-csv --keep → import tapi file tetap disimpan.
#import-csv --dry-run → cuma preview.
#import-csv --count-db → setelah selesai tampilkan jumlah row di DB.
#import-csv --no-truncate → tanpa truncate table terlebih dahulu.