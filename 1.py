import itertools
import numpy as np
from collections import defaultdict

# --- 历史数据 (与之前代码相同) ---
history_data = {
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

PLAYERS = ['A1', 'A2', 'A3', 'A4', 'A5']
OPPONENTS = ['B1', 'B2', 'B3', 'B4', 'B5']
NET_SCORE_MATRIX = {}

def calculate_expected_net_score(data):
    """根据历史比分计算期望净得分 E。若无数据，返回 0 (五五开)。"""
    if not data:
        return 0.0 # 假设五五开

    total_A_score = sum(s_a for s_a, s_b in data)
    total_B_score = sum(s_b for s_a, s_b in data)
    
    if total_A_score + total_B_score == 0:
        return 0.0

    W_A = total_A_score / (total_A_score + total_B_score)
    E_net = 2 * (10 * W_A) - 10
    return E_net

# 构建净得分矩阵 NET_SCORE_MATRIX
all_A_pairs = list(itertools.combinations(PLAYERS, 2))
all_B_pairs = list(itertools.combinations(OPPONENTS, 2))

# 预先将所有对阵情况的 E 设为 0
for A_pair in all_A_pairs:
    for B_pair in all_B_pairs:
        NET_SCORE_MATRIX[(tuple(sorted(A_pair)), tuple(sorted(B_pair)))] = 0.0

# 用历史数据覆盖已知 E
for (Ap1, Ap2), opp_data in history_data.items():
    A_pair_sorted = tuple(sorted((Ap1, Ap2)))
    for (Bp1, Bp2), score_list in opp_data.items():
        B_pair_sorted = tuple(sorted((Bp1, Bp2)))
        E_net = calculate_expected_net_score(score_list)
        NET_SCORE_MATRIX[(A_pair_sorted, B_pair_sorted)] = E_net

# --- 2. 核心求解函数 (穷举搜索) ---

def solve_optimal_arrangement(P_B, players=PLAYERS, net_score_matrix=NET_SCORE_MATRIX):
    best_P_A = None
    max_total_net_score = -np.inf

    for P_A in itertools.permutations(players):
        current_total_net_score = 0
        P_A_list = list(P_A)
        P_B_list = list(P_B)

        for i in range(len(players)):
            # 轮比组合
            A_pair = tuple(sorted((P_A_list[i], P_A_list[(i + 1) % 5])))
            B_pair = tuple(sorted((P_B_list[i], P_B_list[(i + 1) % 5])))
            
            # 查找净得分 (未给出的对阵已在 NET_SCORE_MATRIX 中设为 0)
            net_score = net_score_matrix.get((A_pair, B_pair), 0.0)
            current_total_net_score += net_score

        if current_total_net_score > max_total_net_score:
            max_total_net_score = current_total_net_score
            best_P_A = P_A
            
    return best_P_A, max_total_net_score

def get_net_score_for_A_B(P_A, P_B, net_score_matrix=NET_SCORE_MATRIX):
    """计算特定 P_A 和 P_B 下的总净得分"""
    score = 0
    P_A_list = list(P_A)
    P_B_list = list(P_B)
    
    for i in range(len(P_A)):
        A_pair = tuple(sorted((P_A_list[i], P_A_list[(i + 1) % 5])))
        B_pair = tuple(sorted((P_B_list[i], P_B_list[(i + 1) % 5])))
        score += net_score_matrix.get((A_pair, B_pair), 0.0)
    return score

# -------------------------------------------------------------------

## 结果计算与输出

### 1. 问题一：固定对手出场顺序下的最优解



P_B_Q1 = ('B1', 'B2', 'B3', 'B4', 'B5')
P_A_Q1, score_Q1 = solve_optimal_arrangement(P_B_Q1)

print("## 🏸 问题一结果：固定对手 P_B = (B1, B2, B3, B4, B5) ##")
print(f"对手顺序 P_B: {P_B_Q1}")
print(f"我方最优出场顺序 P_A*: {P_A_Q1}")
print(f"最大期望总净得分: {score_Q1:.3f} 分")
print("-" * 50)

# 阶段得分分析 (验证最优解 P_A*)
if P_A_Q1:
    print("最优顺序下的阶段得分 (仅展示已知对阵):")
    P_A_list = list(P_A_Q1)
    P_B_list = list(P_B_Q1)
    for i in range(5):
        A_pair = tuple(sorted((P_A_list[i], P_A_list[(i + 1) % 5])))
        B_pair = tuple(sorted((P_B_list[i], P_B_list[(i + 1) % 5])))
        net_score = NET_SCORE_MATRIX.get((A_pair, B_pair), 0.0)
        print(f"阶段 {i+1}: A组合{A_pair} vs B组合{B_pair}，净得分: {net_score:.3f}")

print("-" * 50)
print(NET_SCORE_MATRIX)

### 2. 问题二：对手最优反制下的 Minimax 应对



P_A_fixed = ('A1', 'A2', 'A3', 'A4', 'A5')

# 步骤 1: 找到对手针对 P_A_fixed 的最优反制 P_B (最小化我方得分)
worst_P_Bs = []
min_score = np.inf

for P_B_candidate in itertools.permutations(OPPONENTS):
    score = get_net_score_for_A_B(P_A_fixed, P_B_candidate)
    
    if score < min_score:
        min_score = score
        worst_P_Bs = [P_B_candidate]
    elif np.isclose(score, min_score, atol=1e-6):
        worst_P_Bs.append(P_B_candidate)

P_B_worst_3 = worst_P_Bs[:3] # 取分数最低的前三种

# 步骤 2: 调整我方出场顺序 (Minimax 策略)
max_min_score = -np.inf
best_P_A_Q2 = None

for P_A_candidate in itertools.permutations(PLAYERS):
    scores_against_worst = []
    for P_B in P_B_worst_3:
        scores_against_worst.append(get_net_score_for_A_B(P_A_candidate, P_B))
        
    current_min_score = min(scores_against_worst) # 最小得分
    
    if current_min_score > max_min_score:
        max_min_score = current_min_score # 最大化最小得分
        best_P_A_Q2 = P_A_candidate

print("## 🛡️ 问题二结果：对手最优反制下的 Minimax 应对 ##")
print(f"我方原计划 P_A: {P_A_fixed} (此顺序下的最低期望得分: {min_score:.3f})")
print(f"对手针对 P_A 的三种最优反制 P_B: {P_B_worst_3}")
print("-" * 50)
print(f"我方 Minimax 最优出场顺序 P_A*: {best_P_A_Q2}")
print(f"通过调整 P_A* 确保的最低期望总净得分: {max_min_score:.3f} 分")
print("-" * 50)