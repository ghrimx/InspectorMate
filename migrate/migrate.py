"""SQLite schema migration runner.

Applies pending *.sql files from a migrations folder to a SQLite database,
tracking what has already run in a schema_migrations table.

Packaged with PyInstaller (one-file build) and invoked by the InnoSetup
installer during install/update. The resulting exe can also be run
directly from the command line for manual testing, e.g.:

    python migrate.py -i path\\to\\database.db -v
"""

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

MIGRATIONS_DIRNAME = "migrations"


def get_base_dir() -> Path:
    """Folder to resolve the default migrations dir against.

    Frozen (PyInstaller one-file build): migrations/ is bundled inside the
    exe and unpacked at runtime to a temp folder exposed as sys._MEIPASS
    (NOT the folder the exe lives in). Running from source: the script's
    own folder.
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


def setup_logger(log_path: Path, verbose: bool) -> logging.Logger:
    logger = logging.getLogger("migrate")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(file_handler)

    if verbose:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        logger.addHandler(console_handler)

    return logger


def ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def get_applied_migrations(conn: sqlite3.Connection) -> set[str]:
    cursor = conn.execute("SELECT filename FROM schema_migrations")
    return {row[0] for row in cursor.fetchall()}


def get_migration_files(migrations_dir: Path) -> list[Path]:
    return sorted(migrations_dir.glob("*.sql"), key=lambda p: p.name)


def apply_migration(conn: sqlite3.Connection, path: Path, logger: logging.Logger) -> bool:
    """Apply a single migration file inside its own transaction.

    Returns True on success, False on failure (and rolls back).
    """
    sql = path.read_text(encoding="utf-8")
    try:
        conn.executescript(sql)
    except sqlite3.Error as e:
        conn.rollback()
        logger.error("Failed: %s - %s", path.name, e)
        return False

    conn.execute("INSERT INTO schema_migrations (filename) VALUES (?)", (path.name,))
    conn.commit()
    logger.info("Applied: %s", path.name)
    return True


def migrate(db_path: Path, migrations_dir: Path, logger: logging.Logger) -> bool:
    """Apply all pending migrations in order. Returns True if all succeeded."""
    logger.info("Start migration (db=%s, migrations=%s)", db_path, migrations_dir)

    if not migrations_dir.is_dir():
        logger.error("Migrations folder not found: %s", migrations_dir)
        return False

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    success = True
    try:
        ensure_migration_table(conn)
        applied = get_applied_migrations(conn)

        for path in get_migration_files(migrations_dir):
            if path.name in applied:
                logger.info("Already applied: %s", path.name)
                continue
            if not apply_migration(conn, path, logger):
                success = False
                break  # stop here: later migrations may depend on this one
    finally:
        conn.close()

    logger.info("End migration (%s)", "success" if success else "failed")
    return success


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply pending SQL migrations to a SQLite database."
    )
    parser.add_argument(
        "-i", "--dbpath", required=True, type=Path,
        help="Path to the SQLite database file",
    )
    parser.add_argument(
        "-m", "--migrations-dir", type=Path, default=None,
        help="Migrations folder (default: 'migrations' next to the executable/script)",
    )
    parser.add_argument(
        "-l", "--log", type=Path, default=None,
        help="Log file path (default: 'install.log' next to the database)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Also print progress to the console (handy for manual testing)",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    db_path: Path = args.dbpath.resolve()
    migrations_dir: Path = (args.migrations_dir or get_base_dir() / MIGRATIONS_DIRNAME).resolve()
    log_path: Path = (args.log or db_path.parent / "install.log").resolve()

    logger = setup_logger(log_path, args.verbose)
    ok = migrate(db_path, migrations_dir, logger)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))