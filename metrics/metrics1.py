# 定义综合性能指标计算函数
def calculate_performance(precision, recall, f1_score, hit_rate, ndcg):
    # 定义各个参数的系数（可以根据需要进行调整）
    PRECISION_WEIGHT = 0.2  # 精确率的权重
    RECALL_WEIGHT = 0.2     # 召回率的权重
    F1_SCORE_WEIGHT = 0.2   # F1 分数的权重
    HIT_RATE_WEIGHT = 0.2   # 命中率的权重
    NDCG_WEIGHT = 0.2       # NDCG 的权重
    
    # 综合性能指标（可以根据需要调整权重系数）
    performance_score = (PRECISION_WEIGHT * precision) + (RECALL_WEIGHT * recall) + (F1_SCORE_WEIGHT * f1_score) + (HIT_RATE_WEIGHT * hit_rate) + (NDCG_WEIGHT * ndcg)
    
    return performance_score

# # 示例输入参数（可以替换为实际数据）
# precision = 0.8
# recall = 0.75
# f1_score = 0.77
# hit_rate = 0.9
# ndcg = 1.5

# # 计算并输出结果
# performance_score = calculate_performance(precision, recall, f1_score, hit_rate, ndcg)

# # 输出综合性能得分
# print(f"综合性能指标 (Performance Score): {performance_score:.4f}")
