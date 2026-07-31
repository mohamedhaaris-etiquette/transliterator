# PyMySQL allows Django's MySQL backend to work on Windows without compiling mysqlclient.
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
