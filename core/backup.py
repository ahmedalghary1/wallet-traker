import json
import sqlite3
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings
from django.db import connection
from django.utils import timezone


class BackupError(Exception):
    pass


def create_backup_archive(backup_directory):
    if not backup_directory:
        raise BackupError("لم يتم تحديد مسار حفظ النسخة الاحتياطية.")

    backup_dir = Path(backup_directory).expanduser()
    if backup_dir.exists() and not backup_dir.is_dir():
        raise BackupError("مسار النسخ الاحتياطي يجب أن يكون مجلدًا وليس ملفًا.")

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
    archive_path = backup_dir / f"wallet-tracker-backup-{timestamp}.zip"

    with tempfile.TemporaryDirectory(dir=backup_dir) as temp_dir:
        db_snapshot = Path(temp_dir) / "db.sqlite3"
        _snapshot_database(db_snapshot)

        with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
            archive.write(db_snapshot, "db.sqlite3")
            _write_media_files(archive)
            _write_manifest(archive)

    return archive_path


def _snapshot_database(destination):
    if connection.vendor == "sqlite":
        db_name = str(settings.DATABASES["default"]["NAME"])
        if db_name.startswith("file:") or db_name == ":memory:":
            connection.ensure_connection()
            destination.write_bytes(connection.connection.serialize())
            return

        db_path = Path(db_name)
        if not db_path.exists():
            raise BackupError("ملف قاعدة البيانات غير موجود.")

        source_uri = db_path.resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(source_uri, uri=True, timeout=10) as source_connection:
            with sqlite3.connect(destination) as target_connection:
                source_connection.backup(target_connection)
        return

    db_path = Path(settings.DATABASES["default"]["NAME"])
    if not db_path.exists():
        raise BackupError("ملف قاعدة البيانات غير موجود.")
    destination.write_bytes(db_path.read_bytes())


def _write_media_files(archive):
    media_root = Path(settings.MEDIA_ROOT)
    if not media_root.exists():
        return

    for path in media_root.rglob("*"):
        if path.is_file():
            archive.write(path, Path("media") / path.relative_to(media_root))


def _write_manifest(archive):
    manifest = {
        "created_at": timezone.localtime().isoformat(),
        "database": "db.sqlite3",
        "media_directory": "media",
    }
    archive.writestr(
        "backup-manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2),
    )
