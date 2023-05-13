from .ship_data import ships_server_data


def get_personal_rating(
    ship_id: str,
    ship_data: list,
    battle_type: str
):
    '''
    计算pr数据
    ship_data [battles,wins,damage,frag]
    '''
    battles_count = ship_data[0]
    avg_damage = ship_data[2]/battles_count
    avg_wins = ship_data[1]/battles_count
    avg_frag = ship_data[3]/battles_count

    for row in ships_server_data:
        if row.ship_id == ship_id:
            if avg_damage > row.avg_damage*0.4:
                n_damage = (avg_damage-row.avg_damage * 0.4) / \
                    (row.avg_damage*0.6)
            else:
                n_damage = 0
            if avg_wins > row.win_rate*0.7:
                n_win_rate = (avg_wins-row.win_rate*0.7) / (row.win_rate*0.3)
            else:
                n_win_rate = 0
            if avg_frag > row.avg_frag*0.1:
                n_kd = (avg_frag-row.avg_frag*0.1)/(row.avg_frag*0.9)
            else:
                n_kd = 0
            if battle_type == 'rank_solo':
                pr = 600*n_damage+350*n_kd+400*n_win_rate
            else:
                pr = 700*n_damage+300*n_kd+150*n_win_rate
            return {
                'value_battles_count': battles_count,
                'personal_rating': round(pr*battles_count, 6),
                'n_damage_dealt': round((avg_damage/row.avg_damage)*battles_count, 6),
                'n_frags': round((avg_frag/row.avg_frag)*battles_count, 6)
            }
        else:
            continue
    return {
        'value_battles_count': 0,
        'personal_rating': -1,
        'n_damage_dealt': -1,
        'n_frags': -1
    }
