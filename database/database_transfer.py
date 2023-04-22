import json
import os
import gzip
from datetime import date
import time
import sqlite3
from data_source import (
    server_list,
    recent_json_index,
    ach_index_dict,
    ach_json_index
)

old_db_path = r'E:\Kokomi db\database\asia\2023619512'
new_db_path = r'E:\kokomi_database_api\database\user_db\2023619512.db'


def insert_sql(
    temp_json: json
) -> str:
    sql = '''INSERT INTO recent_data(
    date,
    hidden,
    update_time,
    last_battle_time,
    leveling_points,
    karma,
    achievements,
    data
    ) VALUES(?, ?, ?,?, ?, ?, ?, ?)'''
    data = (
        date.today().strftime("%Y-%m-%d"),
        temp_json['hidden'],
        temp_json['update_time'],
        temp_json['data']['user']['last_battle_time'],
        temp_json['data']['user']['leveling_points'],
        temp_json['data']['user']['karma'],
        gzip.compress(
            bytes(str(temp_json['data']['achievements']), encoding='utf-8')),
        gzip.compress(bytes(str(temp_json['data']['ships']), encoding='utf-8')))
    return (sql, data)


def creat_db():
    con = sqlite3.connect('2023619512.db')
    cursorObj = con.cursor()
    cursorObj.execute("""
    CREATE TABLE recent_data(
        date str PRIMARY KEY,
        hidden bool,
        update_time int,
        last_battle_time int,
        leveling_points int,
        karma int,
        achievements bytes,
        ships bytes
    )""")
    con.commit()
    con.close()
    print('创表成功')


def ach_reformat(temp_data):
    res = {}
    for index in ach_json_index:
        if index.keywords in temp_data:
            res[index.index] = temp_data[index.keywords]
    return res


def ships_reformat(temp_data):
    res = {}
    for ship_id, ship_data in temp_data.items():
        res[ship_id] = {'pvp': {}, 'pvp_solo': {},
                        'pvp_div2': {}, 'pvp_div3': {}, 'rank_solo': {}}
        type_list = ['pvp', 'pvp_solo', 'pvp_div2', 'pvp_div3', 'rank_solo']
        for type_index in type_list:
            if ship_data == {} or ship_data[type_index] == {}:
                continue
            else:
                for index in recent_json_index:
                    res[ship_id][type_index][index.index] = ship_data[type_index][index.keywords]
    return res


file_name_list = os.listdir(old_db_path)
#file_name_list = ['2023-04-21.txt', ]
for file_date in file_name_list:
    print(file_date)
    date_json = eval(str(gzip.decompress(
        open(os.path.join(old_db_path, file_date), 'rb').read()), encoding="utf-8"))
    data = (
        file_date.replace('.txt', ''),
        date_json['user']['hidden'],
        int(time.mktime(time.strptime(file_date.replace(
            '.txt', ''), "%Y-%m-%d"))) + 24*60*60-60,
        date_json['info']['last_battle_time'],
        date_json['info']['leveling_points'],
        date_json['info']['karma'],
        gzip.compress(
            bytes(str(ach_reformat(date_json['achievements'])), encoding='utf-8')),
        gzip.compress(bytes(str(ships_reformat(
            date_json['ship'])), encoding='utf-8'))
    )
    sql = '''INSERT INTO recent_data(
    date,
    hidden,
    update_time,
    last_battle_time,
    leveling_points,
    karma,
    achievements,
    ships
    ) VALUES(?, ?, ?,?, ?, ?, ?, ?)'''
    con = sqlite3.connect(new_db_path)
    cursorObj = con.cursor()
    try:
        cursorObj.execute(sql, data)
    except:
        today = file_date.replace('.txt', '')
        cursorObj.execute(f"DELETE from recent_data where date = '{today}'")
        cursorObj.execute(sql, data)
    con.commit()
    con.close()
