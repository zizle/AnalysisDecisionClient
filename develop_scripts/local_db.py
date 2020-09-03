# _*_ coding:utf-8 _*_
# @File  : local_db.py
# @Time  : 2020-09-03 21:25
# @Author: zizle

""" 创建本地sqlite数据库 """
import os
import sqlite3
from settings import BASE_DIR

db_path = os.path.join(BASE_DIR, "dawn/local_data.db")

conn = sqlite3.connect(db_path)

c = conn.cursor()

c.execute(
    "CREATE TABLE UPDATE_FOLDER ("
    "ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
    "CLIENT VARCHAR(36) NOT NULL,"
    "VARIETY_EN VARCHAR(2) NOT NULL,"
    "GROUP_ID INT NOT NULL,"
    "FOLDER VARCHAR(1024) NOT NULL"
    ");"
)
conn.commit()
conn.close()
