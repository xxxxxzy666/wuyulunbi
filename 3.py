import itertools
from collections import defaultdict
import numpy as np

# --- 1. 数据定义与预处理 ---

# 历史数据：(A组合, B组合): [我方得分:对方得分, ...]
# 注意：A/B的索引从1开始 (A1, A2, ...)
history_data_A = {
    ('A1', 'A2'): {('B1', 'B2'): [(23, 21), (21, 18), (21, 19)]},
    ('A1', 'A3'): {('B1', 'B2'): [(20, 22), (21, 19), (22, 20)],
                   ('B3', 'B5'): [(21, 10)]},
    ('A1', 'A4'): {('B2', 'B4'): [(18, 21), (21, 17), (21, 19)]},
    ('A1', 'A5'): {('B1', 'B5'): [(18, 21), (21, 14), (21, 16)]},
    ('A2', 'A3'): {('B2', 'B3'): [(21, 15), (21, 12)]},
    ('A2', 'A4'): {('B2', 'B4'): [(21, 15), (13, 21)]},
    ('A2', 'A5'): {('B3', 'B5'): [(21, 12), (21, 16)]},
    ('A3', 'A4'): {('B3', 'B4'): [(19, 21), (22, 20)],
                   ('B4', 'B5'): [(21, 14)]},
    ('A4', 'A5'): {('B3', 'B5'): [(21, 11), (14, 21)]}
}
history_data_A_new = {
    ('A1', 'A6'): {('B1', 'B3'): [(16, 22), (21, 19)]},
    ('A3', 'A5'): {('B5', 'B6'): [(22, 20), (21, 17), (16, 21)]},
    ('A5', 'A6'): {('B4', 'B5'): [(17, 21), (22, 20)]},
    ('A2', 'A6'): {('B2', 'B6'): [(23, 25), (16, 21)]},
    ('A1', 'A5'): {('B1', 'B6'): [(18, 21), (21, 14),  (21, 19)]}, # A1A5 vs B1B6
    ('A3', 'A4'): {('B4', 'B6'): [(21, 14)]}, # A3A4 vs B4B6
}

# 合并所有数据
history_data = history_data_A
# 合并新数据，注意新数据中包含了一些旧的A组合与新的B组合的对阵
for pair_A, opp_data in history_data_A_new.items():
    if pair_A not in history_data:
        history_data[pair_A] = {}
    history_data[pair_A].update(opp_data)

# 所有可能的我方队员和对手队员
ALL_PLAYERS = [f'A{i}' for i in range(1, 7)]
ALL_OPPONENTS = [f'B{i}' for i in range(1, 7)]

# 所有可能的双打组合 (i < j)
ALL_PAIRS_A = tuple(itertools.combinations(ALL_PLAYERS, 2))
ALL_PAIRS_B = tuple(itertools.combinations(ALL_OPPONENTS, 2))

def calculate_expected_net_score(data):
    """根据历史比分计算期望净得分 E"""
    if not data:
        # 数据缺失，返回0，表示平均水平（无优势）
        return 0.0

    total_A_score = sum(s_a for s_a, s_b in data)
    total_B_score = sum(s_b for s_a, s_b in data)
    
    if total_A_score + total_B_score == 0:
        return 0.0

    # A队得分权重 W_A
    W_A = total_A_score / (total_A_score + total_B_score)
    
    # 10分制期望得分 E_A = 10 * W_A
    # 期望净得分 E = 2 * E_A - 10
    E_net = 2 * (10 * W_A) - 10
    return E_net

# --- 2. 鲁棒性评估：计算组合内在强度 $\bar{E}_{ij}$ ---

# 存储所有我方组合的平均内在强度
A_pair_strength = defaultdict(lambda: 0.0)

# 计算 E_ij,kl
for A_pair in ALL_PAIRS_A:
    total_E = 0
    count = 0
    
    # 找到所有对手组合的对抗数据
    opp_data = history_data.get(A_pair, {})
    
    # 遍历所有可能的对手 B 组合，进行平均
    for B_pair in ALL_PAIRS_B:
        data = opp_data.get(B_pair, None)
        
        # 实际数据计算 E
        E_net = calculate_expected_net_score(data)
        
        # 记录数据，用于计算平均值
        total_E += E_net
        count += 1
    
    # 计算平均内在强度 $\bar{E}_{ij}$
    if count > 0:
        A_pair_strength[A_pair] = total_E / count
    
# 将字典键改为元组 (A1, A2) 而非 ('A1', 'A2')，方便后续处理
A_pair_strength_final = {}
for pair, strength in A_pair_strength.items():
    # 统一将较小索引的队员放前面，如 (A1, A3)
    sorted_pair = tuple(sorted(pair))
    A_pair_strength_final[sorted_pair] = strength

# --- 3. 队员选择 (6选5) ---

ALL_SIX = ALL_PLAYERS
best_S_A = None
max_total_strength = -np.inf

# 穷举所有 6 选 5 的队员组合
for S_A_tuple in itertools.combinations(ALL_SIX, 5):
    S_A = set(S_A_tuple)
    current_total_strength = 0
    
    # 统计这 5 人组成的所有 10 个双打组合的总强度
    for pair in itertools.combinations(S_A, 2):
        sorted_pair = tuple(sorted(pair))
        current_total_strength += A_pair_strength_final[sorted_pair]
    
    if current_total_strength > max_total_strength:
        max_total_strength = current_total_strength
        best_S_A = tuple(S_A_tuple)

print(f"## 队员选择结果 (Step 3) ##")
print(f"最优五人组 S_A* (具备最高平均内在强度): {best_S_A}")
print(f"该五人组的总平均内在强度: {max_total_strength:.3f}")
print("-" * 40)

# --- 4. 顺序优化：最大化总平均强度 ---

best_P_A = None
max_sequence_strength = -np.inf

# 穷举最优五人组的所有 5! = 120 种出场顺序
for P_A in itertools.permutations(best_S_A):
    P_A_list = list(P_A)
    current_sequence_strength = 0
    
    # 1. 计算 P_A 形成的 5 个轮比组合的强度
    # 组合 C_i = (A_pi, A_p(i+1)) for i=1..4
    # 组合 C_5 = (A_p5, A_p1)
    
    for i in range(5):
        player1 = P_A_list[i]
        player2 = P_A_list[(i + 1) % 5] # 循环取下一个队员
        
        # 确保字典查询的键是排序后的
        pair = tuple(sorted((player1, player2)))
        
        # 加上该轮比组合的平均内在强度
        current_sequence_strength += A_pair_strength_final.get(pair, 0)
        
    if current_sequence_strength > max_sequence_strength:
        max_sequence_strength = current_sequence_strength
        best_P_A = P_A

print(f"## 顺序优化结果 (Step 4) ##")
print(f"最优稳定出场顺序 P_A*: {best_P_A}")
print(f"该顺序下的总平均内在强度 : {max_sequence_strength:.3f}")

# 最终结论
if max_sequence_strength > 0:
    print("\n结论：存在一个稳定的最优出场顺序。")
else:
    print("\n结论：不存在具有绝对稳定优势的出场顺序（总平均强度为负或零）。")