import pandas as pd
import sqlite3
import shutil
import logging
from pathlib import Path
from configparser import ConfigParser
from datetime import datetime

# --------------------------------------------------
# Logging
# --------------------------------------------------

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

log_file = Path("logs") / f"loader_{timestamp}.log"

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# --------------------------------------------------
# Config
# --------------------------------------------------

config = ConfigParser()
config.read("config/config.ini")

incoming_folder = Path(config["PATHS"]["incoming_folder"])
archive_folder = Path(config["PATHS"]["archive_folder"])
rejected_folder = Path(config["PATHS"]["rejected_folder"])

db_path = config["DATABASE"]["db_path"]

# --------------------------------------------------
# Database
# --------------------------------------------------

conn = sqlite3.connect(db_path)

required_columns = [
    "po_number",
    "region",
    "supplier_id",
    "material_code",
    "ordered_qty",
    "unit_price_usd",
    "order_date"
]

# --------------------------------------------------
# Counters
# --------------------------------------------------

success_files = 0
failed_files = 0
rows_loaded_total = 0

# --------------------------------------------------
# Process Files
# --------------------------------------------------

for file in incoming_folder.glob("*.csv"):

    file_name = file.name

    try:

        # Empty file check
        if file.stat().st_size == 0:

            conn.execute(
                """
                INSERT INTO etl_file_audit_log
                VALUES(?,?,?,?,?)
                """,
                (
                    file_name,
                    0,
                    "FAILED",
                    "EMPTY_FILE",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )

            conn.commit()

            shutil.move(
                str(file),
                str(rejected_folder / file_name)
            )

            failed_files += 1
            continue

        df = pd.read_csv(file)

        # Schema validation

        missing_cols = [
            col for col in required_columns
            if col not in df.columns
        ]

        if missing_cols:

            conn.execute(
                """
                INSERT INTO etl_file_audit_log
                VALUES(?,?,?,?,?)
                """,
                (
                    file_name,
                    0,
                    "FAILED",
                    "MISSING_REQUIRED_COLUMNS",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )

            conn.commit()

            shutil.move(
                str(file),
                str(rejected_folder / file_name)
            )

            failed_files += 1
            continue

        # Derived Column

        df["total_po_value"] = (
            df["ordered_qty"] *
            df["unit_price_usd"]
        )

        df["source_file_name"] = file_name

        df["loaded_at"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        row_count = len(df)

        # Load staging table

        df.to_sql(
            "stg_regional_po",
            conn,
            if_exists="append",
            index=False
        )

        # Audit

        conn.execute(
            """
            INSERT INTO etl_file_audit_log
            VALUES(?,?,?,?,?)
            """,
            (
                file_name,
                row_count,
                "SUCCESS",
                "",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        conn.commit()

        shutil.move(
            str(file),
            str(archive_folder / file_name)
        )

        success_files += 1
        rows_loaded_total += row_count

    except Exception as e:

        conn.execute(
            """
            INSERT INTO etl_file_audit_log
            VALUES(?,?,?,?,?)
            """,
            (
                file_name,
                0,
                "FAILED",
                str(e),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        conn.commit()

        failed_files += 1

# --------------------------------------------------
# Summary
# --------------------------------------------------

print()
print(f"Successful Files = {success_files}")
print(f"Failed Files = {failed_files}")
print(f"Rows Loaded = {rows_loaded_total}")

conn.close()