r"""One-time helper to migrate data from a v2 sqlite database into a
fresh v1.0 database.

Usage from repository root::

    python tools/migrate_v2_to_v5.py \
        --source path/to/vehicle_management_v2.db \
        [--dest path/to/vehicle_management_v1.0.db]

If ``--dest`` is omitted the file configured by ``config.DB_FILE`` is used
(which is the same name that the application normally works with).

The script creates the destination database (invoking ``BaseManager`` so the
current schema is applied) and then copies every table found in the source.
Columns that have been renamed are translated, new columns receive sensible
defaults and the legacy ``id`` primary key on ``vehicles`` is ignored
because the v5 schema uses ``vin`` as the key.

This is not a perfect, bullet‑proof migration; you should inspect the data
afterwards and run the unit test suite.  It exists purely to get you started
and to automate the common cases described in the roadmap.
"""
import argparse
import sqlite3
import logging
import sys
import os

# ensure project root is on path so imports work when invoked from tools/
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)

from database.base_manager import BaseManager
from config import DB_FILE as DEFAULT_DEST

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def copy_table(src, dst, table, column_map=None, ignore_cols=None):
    """Copy all rows from ``table`` in ``src`` to ``dst``.

    ``column_map`` is an optional dict mapping old column names to new ones;
    ``ignore_cols`` is a set of column names to skip entirely.
    """
    column_map = column_map or {}
    ignore_cols = ignore_cols or set()

    cur = src.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall() if r[1] not in ignore_cols]
    dst_cols = [column_map.get(c, c) for c in cols]
    placeholder = ",".join("?" for _ in cols)
    # use OR IGNORE so running the migration multiple times doesn't crash on
    # unique constraints (e.g. vehicles.vin); rows that conflict will simply be
    # skipped.
    insert_sql = (
        f"INSERT OR IGNORE INTO {table} ({','.join(dst_cols)}) VALUES ({placeholder})"
    )

    rows = src.execute(f"SELECT {','.join(cols)} FROM {table}").fetchall()
    if not rows:
        msg = f"{table}: no rows to copy"
        print(msg)
        logger.info(msg)
        return

    msg = f"Inserting {len(rows)} rows into {table}"
    print(msg)
    logger.info(msg)
    with dst:
        dst.executemany(insert_sql, rows)


def migrate(src_path, dest_path):
    # open source, keep row factory so we can slice by name if needed
    src = sqlite3.connect(src_path)
    src.row_factory = sqlite3.Row

    # instantiate BaseManager to ensure destination schema is created
    bm = BaseManager(db_path=dest_path)
    dst = bm.conn

    # gather tables present in source
    tbls = [r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    logger.info("Found tables in source: %s", tbls)

    for tbl in tbls:
        if tbl.startswith("sqlite_"):
            continue
        if tbl == "vehicles":
            # map legacy columns, ignore the old autoincrement id and
            # the deprecated gate_out_time column that no longer exists
            # in the v5 schema.
            copy_table(src, dst, tbl,
                       column_map={"loai_xe": "vehicle_type"},
                       ignore_cols={"id", "gate_out_time"})
        else:
            # default copy; if column names changed the user must edit
            copy_table(src, dst, tbl)

    logger.info("migration complete")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate v2 SQLite -> v1.0 (defaults to project root files)"
    )

    # sensible defaults when the old/new database files live alongside the repo
    default_source = os.path.join(root, "vehicle_management_v2.db")
    # config.DB_FILE uses the location of the running script as its base path,
    # which in our case means ``tools/``. ensure we point at the root instead.
    default_dest = os.path.join(root, "vehicle_management_v1.0.db")

    parser.add_argument(
        "--source",
        default=default_source,
        help=(
            "path to v2 database (defaults to '%s' in project root)" % default_source
        ),
    )
    parser.add_argument(
        "--dest",
        default=default_dest,
        help=(
            "destination v1.0 database (defaults to '%s')" % default_dest
        ),
    )

    args = parser.parse_args()

    # some people run the script from tools/ and never see logs, so also
    # print to stdout where it can't be filtered out.
    msg = f"starting migration from {args.source} to {args.dest}"
    print(msg)
    logger.info(msg)
    if not os.path.exists(args.source):
        err = f"source file {args.source} does not exist"
        print(err)
        logger.error(err)
        sys.exit(1)

    migrate(args.source, args.dest)


if __name__ == "__main__":
    main()
