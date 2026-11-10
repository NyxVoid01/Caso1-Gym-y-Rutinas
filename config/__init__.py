
import pymysql

pymysql.version_info = (2, 2, 1, "final", 0)   # Django 6 exige mysqlclient 2.2.1 o más
pymysql.install_as_MySQLdb()