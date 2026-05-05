import argparse
import os
import socket
from pathlib import Path


def configure_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wallet_tracker.settings")
    os.environ.setdefault("DESKTOP_LOCAL_MODE", "1")
    os.environ.setdefault("DJANGO_DEBUG", "0")

    import django

    django.setup()


def parse_args():
    parser = argparse.ArgumentParser(description="Start the Wallet Tracker desktop backend.")
    parser.add_argument(
        "--host",
        default=os.getenv("APP_HOST", "127.0.0.1"),
        help="The host interface for the server.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("APP_PORT", "8000")),
        help="The port for the local desktop server.",
    )
    return parser.parse_args()


def get_lan_addresses():
    addresses = set()

    try:
        addresses.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe_socket:
            probe_socket.connect(("8.8.8.8", 80))
            addresses.add(probe_socket.getsockname()[0])
    except OSError:
        pass

    return sorted(address for address in addresses if address and not address.startswith("127."))


def print_server_urls(host, port):
    print(f"Starting server on http://{host}:{port} ...")
    print(f"Local URL: http://127.0.0.1:{port}/")

    if host in {"0.0.0.0", "::"}:
        for address in get_lan_addresses():
            print(f"Network URL: http://{address}:{port}/")


def ensure_database_is_ready():
    from django.conf import settings
    from django.core.management import call_command
    from django.db import connections
    from django.db.migrations.executor import MigrationExecutor

    db_path = Path(settings.DATABASES["default"]["NAME"])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Using database: {db_path}")

    connection = connections["default"]
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    has_pending_migrations = bool(executor.migration_plan(targets))

    if has_pending_migrations:
        print("Pending migrations found. Applying...")
        call_command("migrate", "--noinput", verbosity=0)
        print("Migrations applied successfully.")
    else:
        print("Database is up to date.")


def main():
    args = parse_args()
    configure_django()
    ensure_database_is_ready()

    from wallet_tracker.wsgi import application
    from waitress import serve

    print_server_urls(args.host, args.port)
    print(f"SERVER_READY=http://127.0.0.1:{args.port}/", flush=True)
    serve(application, host=args.host, port=args.port, threads=6)


if __name__ == "__main__":
    main()
