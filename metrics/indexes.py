import numpy as np
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import roc_auc_score
import Levenshtein  # 可选：计算编辑距离
from metrics1 import calculate_performance
from similarity import calculate_result_set_similarity
from similarity import calculate_sql_similarity

##############################################
# 1. 基于本地数据集计算SQL查询结果集相似度
##############################################
def execute_sql_query(database_folder, db_id, query):
    """ 执行 SQL 查询，返回查询结果集 """
    db_path = f"{database_folder}/{db_id}/{db_id}.sqlite"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return None

# def result_set_to_document(result_set):
#     """ 将查询结果集转换为文本字符串 """
#     if not result_set:
#         return ""
#     return "\n".join(" ".join(map(str, row)) for row in result_set)

# def calculate_result_set_similarity(result_set1, result_set2):
#     """ 计算两个查询结果集的相似度 """
#     doc1 = result_set_to_document(result_set1)
#     doc2 = result_set_to_document(result_set2)
    
#     if not doc1 or not doc2:
#         return 0.0
    
#     vectorizer = TfidfVectorizer()
#     tfidf = vectorizer.fit_transform([doc1, doc2])
#     return cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]

##############################################
# 2. 评价指标计算
##############################################
def precision_recall_at_k(y_true, y_score, k):
    """ 计算 Precision@k 和 Recall@k """
    assert len(y_true) == len(y_score)
    
    # 计算每个推荐查询的最大相似度
    scores = []
    for i in range(len(y_true)):
        # 如果 y_true 为 1，则 score 为 1
        if y_true[i] == 1:
            scores.append(1)
        else:
            scores.append(y_score[i])  # 否则使用最大相似度得分
    
    precision = np.mean(scores)  # 求所有查询的平均值
    recall = recall_at_k(y_true, y_score, k)  # 使用改进后的 recall 函数

    #recall = np.sum(scores) / np.sum(y_true) if np.sum(y_true) > 0 else 0  # 计算召回率
    return precision, recall

def recall_at_k(y_true, y_score, k):
    """ 计算 Recall@k """
    assert len(y_true) == len(y_score)
    
    # 对于每个推荐查询，如果它是相关的（y_true[i] == 1），并且得分较高（大于某个阈值），则认为它是命中
    relevant_queries = np.sum(y_true)  # 相关查询的总数
    relevant_hit = np.sum([1 if y_true[i] == 1 and y_score[i] > 0 else 0 for i in range(len(y_true))])
    
    return relevant_hit / relevant_queries if relevant_queries > 0 else 0


def f1_score(precision, recall):
    """ 计算 F1 分数 """
    return 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

def hit_rate(y_true, y_score, k):
    """ 计算命中率 Hit@k """
    order = np.argsort(y_score)[::-1][:k]
    y_true_k = np.take(y_true, order)
    return 1.0 if np.sum(y_true_k) > 0 else 0.0

def ndcg_at_k(y_true, y_score, k):
    """ 计算 NDCG@k，仅考虑推荐查询的相似度 y_score """
    order = np.argsort(y_score)[::-1][:k]  # 排序推荐查询，选择前 k 个
    y_score_k = np.take(y_score, order)  # 获取前 k 个推荐查询的相似度
    
    # 计算 DCG：考虑排名，计算相似度的折扣
    dcg = np.sum(y_score_k / np.log2(np.arange(2, k + 2)))  # 使用 log2(i+1) 的折扣
    # 计算理想的 DCG（IDCG）：假设所有推荐查询的相似度为 1，计算最理想的 DCG 值
    ideal_dcg = np.sum(1 / np.log2(np.arange(2, k + 2)))  # 理想 DCG，假设每个推荐查询相似度为 1

    return dcg / ideal_dcg if ideal_dcg > 0 else 0.0  # 防止除以0


##############################################
# 3. 整合推荐 SQL 查询的评价流程
##############################################

# 示例数据（请确保数据库路径和表名正确）
database_folder = "./spider/database"
db_id = "customers_and_addresses"

# 历史查询（可以有多条）
actual_reference_sql_queries = [
    "SELECT * FROM Customer_Addresses WHERE address_id = 11",
    "SELECT * FROM Customer_Addresses WHERE customer_id = 5",
    "SELECT * FROM Customer_Addresses WHERE address_type = 'Billing'",
    "SELECT * FROM Customer_Addresses WHERE date_address_from >= '2024-01-01'",
]


# 推荐的 SQL 查询
recommended_sql_queries = [
    "SELECT * FROM Customer_Addresses WHERE address_id = 11",  # 直接匹配
    "SELECT * FROM Customer_Addresses WHERE customer_id = 3",  # 不同的 customer_id
    "SELECT * FROM Customer_Addresses WHERE address_type = 'Shipping'",  # 不同类型
    "SELECT * FROM Customer_Addresses WHERE date_address_from BETWEEN '2023-01-01' AND '2023-12-31'",  # 时间范围不同
    "SELECT * FROM Customer_Addresses WHERE date_address_to IS NOT NULL",  # 查询非空 date_address_to
]


# 执行所有历史查询，获取结果集
actual_result_sets = []
for ref_query in actual_reference_sql_queries:
    result_set = execute_sql_query(database_folder, db_id, ref_query)
    actual_result_sets.append(result_set)

# 计算推荐查询的相似度得分
similarity_scores = []
for query in recommended_sql_queries:
    recommended_result_set = execute_sql_query(database_folder, db_id, query) 
    
    # 计算推荐查询与所有历史查询结果集的最大相似度
    max_similarity = max(
        calculate_result_set_similarity(recommended_result_set, ref_result_set)
        for ref_result_set in actual_result_sets
    )
    
    # 计算 SQL 语句的相似度（可以单独加权）
    sql_similarity = max(
        calculate_sql_similarity(query, ref_query)
        for ref_query in actual_reference_sql_queries
    )
    
    # 综合结果：结合 SQL 语句相似度与查询结果集相似度
    final_similarity = 0.3 * sql_similarity + 0.7 * max_similarity  # 这里的权重可以根据需求调整
    similarity_scores.append(final_similarity)

# 计算 y_true，若推荐查询在历史查询列表中出现则标记为 1，否则为 0
y_true = [1 if query.strip().lower() in [q.strip().lower() for q in actual_reference_sql_queries] else 0 for query in recommended_sql_queries]
y_score = similarity_scores

# 输出相似度得分
print("推荐查询与历史查询的最大结果集相似度得分：")
for i, score in enumerate(y_score):
    print(f"推荐查询{i+1}: {score:.4f}")

# 计算评价指标
k = len(recommended_sql_queries)  # 或设定为特定的 k
precision, recall = precision_recall_at_k(y_true, y_score, k)
f1 = f1_score(precision, recall)
hit = hit_rate(y_true, y_score, k)
ndcg_val = ndcg_at_k(y_true, y_score, k)

print("\n评价指标结果：")
print(f"Precision@{k}: {precision:.4f}")
print(f"Recall@{k}: {recall:.4f}")
print(f"F1 Score: {f1:.4f}")
print(f"Hit Rate@{k}: {hit:.4f}")
print(f"NDCG@{k}: {ndcg_val:.4f}")

# 计算并输出结果
performance_score = calculate_performance(precision, recall, f1, hit, ndcg_val)

# 输出综合性能得分
print(f"综合性能指标 (Performance Score): {performance_score:.4f}")