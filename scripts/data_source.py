from dataclasses import dataclass


@dataclass
class json_index:
    keywords: str
    index: int


recent_json_index = [
    json_index('battles_count', 0),
    json_index('wins', 1),
    json_index('losses', 2),
    json_index('damage_dealt', 3),
    json_index('ships_spotted', 4),
    json_index('frags', 5),
    json_index('survived', 6),
    json_index('scouting_damage', 7),
    json_index('original_exp', 8),
    json_index('exp', 9),
    json_index('art_agro', 10),
    json_index('tpd_agro', 11),
    json_index('win_and_survived', 12),
    json_index('control_dropped_points', 13),
    json_index('control_captured_points', 14),
    json_index('team_control_captured_points', 15),
    json_index('team_control_dropped_points', 16),
    json_index('planes_killed', 17),
    json_index('frags_by_ram', 18),
    json_index('frags_by_tpd', 19),
    json_index('frags_by_planes', 20),
    json_index('frags_by_dbomb', 21),
    json_index('frags_by_atba', 22),
    json_index('frags_by_main', 23),
    json_index('hits_by_main', 24),
    json_index('shots_by_main', 25),
    json_index('hits_by_skip', 26),
    json_index('shots_by_skip', 27),
    json_index('hits_by_atba', 28),
    json_index('shots_by_atba', 29),
    json_index('hits_by_rocket', 30),
    json_index('shots_by_rocket', 31),
    json_index('hits_by_bomb', 32),
    json_index('shots_by_bomb', 33),
    json_index('hits_by_tpd', 34),
    json_index('shots_by_tpd', 35),
    json_index('hits_by_tbomb', 36),
    json_index('shots_by_tbomb', 37),
]

server_list = {
    'asia': 'http://vortex.worldofwarships.asia',
    'eu': 'http://vortex.worldofwarships.eu',
    'na': 'http://vortex.worldofwarships.com',
    'ru': 'http://vortex.korabli.su',
    'cn': 'http://vortex.wowsgame.cn'
}
useless_index_list = [
    'damage_dealt_to_buildings',
    'max_damage_dealt_to_buildings',
    'max_premium_exp',
    'premium_exp',
    'dropped_capture_points',
    'capture_points',
    'max_suppressions_count',
    'suppressions_count',
    'battles_count_0910',
    'battles_count_078',
    'battles_count_0711',
    'battles_count_512',
    'battles_count_510',
]
useful_index_list = [
    # 基本数据
    'battles_count',                 # 战斗总数
    'wins',                          # 胜利场数
    'losses',                        # 失败场数
    'damage_dealt',                  # 总伤害
    'ships_spotted',                 # 船只侦查数
    'frags',                         # 总击杀数
    'survived',                      # 存活的场数
    'scouting_damage',               # 总侦查伤害
    'original_exp',                  # 总经验（无高账加成）
    'exp',                           # 经验（大概是包括所有模式的总经验，虽然没啥用，但留着吧）
    'art_agro',                      # 总潜在伤害
    'tpd_agro',                      # 总鱼雷潜在伤害
    'win_and_survived',              # 胜利并存活场数
    'control_dropped_points',        # 总防御点数
    'control_captured_points',       # 总占领点数
    'team_control_captured_points',  # 团队总占领点数
    'team_control_dropped_points',   # 团队总防御点数
    'planes_killed',                 # 总飞机击落数

    # 最大记录
    'max_frags_by_planes',           # 最多通过飞机击杀数
    'max_total_agro',                # 最多潜在伤害
    'max_ships_spotted',             # 最多船只侦查数
    'max_frags_by_ram',              # 最多冲撞击杀
    'max_scouting_damage',           # 最大侦查伤害
    'max_frags_by_dbomb',            # 最多深水炸弹击杀
    'max_frags_by_main',             # 最多主炮击杀
    'max_planes_killed',             # 最多飞机击落
    'max_damage_dealt',              # 最大伤害
    'max_frags_by_tpd',              # 最多鱼雷击杀
    'max_exp',                       # 最多经验（无高账加成）
    'max_frags_by_atba',             # 最多副炮击杀数
    'max_frags',                     # 最多击杀数

    # 武器击杀数据
    'frags_by_ram',                  # 冲撞击杀数
    'frags_by_tpd',                  # 鱼雷击杀数
    'frags_by_planes',               # 通过飞机击杀数
    'frags_by_dbomb',                # 深水炸弹的击杀数
    'frags_by_atba',                 # 副炮击杀数
    'frags_by_main',                 # 主炮击杀数
    # 通过起火或进水击杀 = 总击杀 - 上面的累加

    # 武器命中数据
    'hits_by_main',                  # 命中的主炮数
    'shots_by_main',                 # 发射的主炮数
    'hits_by_skip',                  # 命中的跳弹数
    'shots_by_skip',                 # 发射的跳弹数
    'hits_by_atba',                  # 命中的副炮数
    'shots_by_atba',                 # 发射的副炮数
    'hits_by_rocket',                # 命中的火箭弹数
    'shots_by_rocket',               # 发射的火箭弹数
    'hits_by_bomb',                  # 命中的炸弹数
    'shots_by_bomb',                 # 投掷的炸弹数
    'hits_by_tpd',                   # 命中的鱼雷数
    'shots_by_tpd',                  # 发射的鱼雷数
    'hits_by_tbomb',                 # 命中的空袭炸弹数
    'shots_by_tbomb',                # 投掷的空袭炸弹数
]
