import Levenshtein
import numpy as np
import sqlparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 编辑距离计算语句相似性
def calculate_sql_similarity(sql1, sql2):
    """使用 Levenshtein 编辑距离计算 SQL 语句的相似度"""
    distance = Levenshtein.distance(sql1, sql2)
    max_len = max(len(sql1), len(sql2))
    return 1 - (distance / max_len) if max_len > 0 else 0

# 解析 SQL 为组件
def parse_sql_components(sql):
    """拆分 SQL 查询成多个组件"""
    parsed = sqlparse.parse(sql)[0]
    components = {"SELECT": "", "FROM": "", "WHERE": "", "GROUP BY": "", "ORDER BY": ""}
    for token in parsed.tokens:
        if token.ttype is None and token.get_type() in components:
            components[token.get_type()] = str(token)
    return components

# 计算组件相似性
def calculate_component_similarity(comp1, comp2):
    """计算组件的相似度"""
    return calculate_sql_similarity(comp1, comp2)

def calculate_total_component_similarity(sql1, sql2):
    """计算整个 SQL 的组件匹配得分"""
    components1 = parse_sql_components(sql1)
    components2 = parse_sql_components(sql2)

    scores = []
    for comp_type in components1.keys():
        scores.append(calculate_component_similarity(components1[comp_type], components2[comp_type]))

    return np.mean(scores) if scores else 0.0

# 计算 Jaccard 相似性
def jaccard_similarity(set1, set2):
    """计算 Jaccard 相似性"""
    if not set1 or not set2:
        return 0.0
    intersection = len(set(set1) & set(set2))
    union = len(set(set1) | set(set2))
    return intersection / union if union > 0 else 0

# 数值列相似性
def numeric_column_similarity(col1, col2):
    """计算数值列的相似性（允许一定误差范围）"""
    if not col1 or not col2:
        return 0.0
    col1, col2 = np.array(col1), np.array(col2)
    min_len = min(len(col1), len(col2))

    if min_len == 0:
        return 0.0

    abs_diff = np.abs(col1[:min_len] - col2[:min_len])
    return np.mean(abs_diff < 1e-3)  # 允许微小误差

# 列对齐
def align_columns(result_set1, result_set2):
    """根据列名对齐两个结果集的列顺序"""
    headers1, headers2 = result_set1[0], result_set2[0]
    
    aligned_cols = []
    for col1 in headers1:
        if col1 in headers2:
            col2_idx = headers2.index(col1)
            aligned_cols.append((headers1.index(col1), col2_idx))
        else:
            aligned_cols.append(None)
            
    return aligned_cols

# 计算结果集相似性
def calculate_result_set_similarity(result_set1, result_set2):
    """综合计算 SQL 查询结果集的相似度"""
    if not result_set1 or not result_set2:
        return 0.0

    aligned_cols = align_columns(result_set1, result_set2)

    col_similarities = []
    for col in aligned_cols:
        if col is None:
            continue
        
        col_idx1, col_idx2 = col
        col1 = [row[col_idx1] for row in result_set1[1:]]
        col2 = [row[col_idx2] for row in result_set2[1:]]
        
        if all(isinstance(x, (int, float)) for x in col1 + col2):
            col_similarities.append(numeric_column_similarity(col1, col2))
        else:
            col_similarities.append(jaccard_similarity(col1, col2))

    col_similarity = np.mean(col_similarities) if col_similarities else 0.0

    row_similarity = jaccard_similarity(result_set1[1:], result_set2[1:])

    return (0.5 * row_similarity) + (0.5 * col_similarity)

# 综合相似性计算
def calculate_final_similarity(sql1, sql2, result_set1, result_set2):
    """结合组件匹配和结果集相似性计算最终得分"""
    component_similarity = calculate_total_component_similarity(sql1, sql2)
    result_set_similarity = calculate_result_set_similarity(result_set1, result_set2)
    final_similarity = (0.4 * component_similarity) + (0.6 * result_set_similarity)
    return final_similarity
