"""Project package initialization.

Django's MySQL backend expects the ``MySQLdb`` module. The project ships
PyMySQL (see requirements.txt), so register it as a drop-in replacement.
This keeps MySQL deployments working without needing the mysqlclient C
extension to be compiled on the server.
"""

try:  # pragma: no cover - only relevant when MySQL is used
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:  # pragma: no cover - PyMySQL is optional for SQLite setups
    pass
