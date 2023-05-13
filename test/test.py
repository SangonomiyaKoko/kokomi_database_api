import re
import sqlite3
import json
import gzip
import time
# qqid = "[CQ:at,qq=2694522387]"
# match = re.compile(r"[CQ:at,qq=(.*?)]", qqid, re.S)
# if match:
#     print(match.group().split())
# a = ['a', 'b', 'a']
# print(a.index('a'))

# con = sqlite3.connect('2023619512.db')
# cursorObj = con.cursor()
# cursorObj.execute("""
# CREATE TABLE recent_data(
#     date str PRIMARY KEY,
#     hidden bool,
#     update_time int,
#     last_battle_time int,
#     leveling_points int,
#     karma int,
#     achievements bytes,
#     ships bytes
# )""")
# con.commit()
# con.close()
# print('创表成功')

# a = b'00000001'
# con = sqlite3.connect('test.db')
# cursorObj = con.cursor()
# cursorObj.execute(
#     'INSERT INTO recent_data(date, data) VALUES(?, ?)', ('2023-04-21', a))
# con.commit()
# con.close()
# print('插入数据成功')

# con = sqlite3.connect('test.db')
# cursorObj = con.cursor()
# cursorObj.execute("DELETE from recent_data where date = '2023-04-21'")
# con.commit()
# con.close()
# print('数据删除成功')


# def test_db_ship(db_data):
#     # 4074157872
#     shipdata = eval(str(gzip.decompress(db_data), encoding="utf-8"))
#     if '4074157872' in shipdata:
#         return shipdata['4074157872']['pvp'][0]
#     return 0


# st = time.time()
# con = sqlite3.connect(r'E:\kokomi_database_api\database\user_db\2023619512.db')
# cursorObj = con.cursor()
# cursorObj.execute("SELECT * FROM recent_data")
# rows = cursorObj.fetchall()
# i = 0
# for row in rows:
#     a = {
#         'date': row[0],
#         'hidden': row[1],
#         'update_time': row[2],
#         'last_battle_time': row[3],
#         'leveling_points': row[4],
#         'karma': row[5],
#         'achievements': 0,
#         'ships': test_db_ship(row[7])
#     }
#     i += 1
#     print(a)
# print()
# print(f'从数据库读取{i}个日期数据，耗时{round(time.time()-st,4)}s')
# print()


# with open(f'dbtest.json', 'w', encoding='utf-8') as f:
#     f.write(json.dumps(b))
# f.close()
# print('遍历数据库完成')
