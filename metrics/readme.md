# SQL 查询推荐系统性能评估 README

## 简介
本项目的核心目的是评估 SQL 查询推荐系统的性能，通过一系列指标对推荐结果的准确性和覆盖率进行量化。以下内容概述了系统的评估流程，涉及文件的功能，以及如何利用综合性能得分来衡量系统的整体表现。

---

## 项目功能模块概述

### 1. **`indexes.py`**
该文件的核心任务是处理 SQL 查询执行和推荐评估相关操作，包括：
- **执行 SQL 查询**：通过连接 SQLite 数据库运行推荐和历史查询。
- **结果集相似度计算**：将查询结果转为文档格式，并通过 **TF-IDF** 与 **余弦相似度** 计算结果集的匹配分数。
- **核心函数**：
  - `execute_sql_query(database_folder, db_id, query)`：执行 SQL 查询，返回结果集。
  - `calculate_result_set_similarity(result_set1, result_set2)`：计算两个结果集的相似度。

---

### 2. **`similarity.py`**
该文件负责 SQL 查询相似度的计算逻辑，包括两大核心功能：
1. **组件匹配**：
   - 将查询拆分为多个组件（如 `SELECT`、`WHERE` 等），计算每个组件的相似性。
   - 核心函数：
     - `parse_sql_components(sql)`：解析 SQL 查询为组件。
     - `calculate_component_similarity(comp1, comp2)`：计算两个组件的匹配度。
     - `calculate_total_component_similarity(sql1, sql2)`：综合计算所有组件的匹配分数。
   
2. **结果集验证与匹配**：
   - 对查询执行后的结果集进行对比，通过列对齐和相似性计算验证推荐查询的语义正确性。
   - 核心函数：
     - `align_columns(result_set1, result_set2)`：对齐结果集列的顺序。
     - `calculate_result_set_similarity(result_set1, result_set2)`：综合结果集的行匹配和列匹配分数。
     - `calculate_final_similarity(sql1, sql2, result_set1, result_set2)`：结合组件匹配和结果集相似度，计算最终评分。

---

### 3. **`metrics1.py`**
该文件定义了综合性能得分的计算逻辑，用于将多个评估指标组合成一个最终评分：
- **核心评价指标**：
  - **Precision** (精确率)：前 k 个推荐查询的准确性。
  - **Recall** (召回率)：前 k 个推荐查询的覆盖率。
  - **F1 Score**：精确率和召回率的调和平均值。
  - **Hit Rate** (命中率)：前 k 个推荐查询中是否包含相关查询。
  - **NDCG**：推荐查询的排序质量。
- **核心函数**：
  - `calculate_performance(precision, recall, f1_score, hit_rate, ndcg)`：根据权重组合各指标，输出综合性能得分。

---

## 系统评估流程

### 1. 输入
- **推荐查询 (`recommended_sql_queries`)**：由推荐系统生成的 SQL 查询列表。
- **历史查询 (`actual_reference_sql_queries`)**：系统使用的标准 SQL 查询列表。

### 2. 查询执行与相似度计算
- 执行每个推荐查询和历史查询，获取对应的查询结果集。
- 计算推荐查询与所有历史查询的组件匹配得分和结果集相似度，选择相似度最高值。

### 3. 指标计算
- 根据推荐查询与历史查询的相似度得分，构建 `y_true`（是否为相关查询）与 `y_score`（相似度分数）。
- 通过以下函数计算核心评价指标：
  - **精确率和召回率**：`precision_recall_at_k(y_true, y_score, k)`
  - **F1 分数**：`f1_score(precision, recall)`
  - **命中率**：`hit_rate(y_true, y_score, k)`
  - **NDCG**：`ndcg_at_k(y_true, y_score, k)`

### 4. 综合性能得分
- 将所有指标按权重组合，计算系统的最终得分：
  ```python
  performance_score = calculate_performance(precision, recall, f1, hit, ndcg_val)
  ```

---

## 综合性能评价示例
以下为评价系统性能的完整代码示例：
```python
# 执行历史查询并获取结果集
actual_result_sets = [execute_sql_query(database_folder, db_id, query) for query in actual_reference_sql_queries]

# 计算推荐查询与历史查询的相似度
similarity_scores = []
for query in recommended_sql_queries:
    recommended_result_set = execute_sql_query(database_folder, db_id, query)
    max_similarity = max(
        calculate_result_set_similarity(recommended_result_set, ref_result_set)
        for ref_result_set in actual_result_sets
    )
    similarity_scores.append(max_similarity)

# 生成 y_true 和 y_score
y_true = [1 if query in actual_reference_sql_queries else 0 for query in recommended_sql_queries]
y_score = similarity_scores

# 计算指标
k = len(recommended_sql_queries)  # 或指定 k 值
precision, recall = precision_recall_at_k(y_true, y_score, k)
f1 = f1_score(precision, recall)
hit = hit_rate(y_true, y_score, k)
ndcg_val = ndcg_at_k(y_true, y_score, k)

# 计算综合性能得分
performance_score = calculate_performance(precision, recall, f1, hit, ndcg_val)

# 输出结果
print(f"Precision@{k}: {precision:.4f}")
print(f"Recall@{k}: {recall:.4f}")
print(f"F1 Score: {f1:.4f}")
print(f"Hit Rate@{k}: {hit:.4f}")
print(f"NDCG@{k}: {ndcg_val:.4f}")
print(f"综合性能指标 (Performance Score): {performance_score:.4f}")
```

---

## 结论
本项目通过组件匹配、结果集验证和多指标综合评分的方式，对推荐系统进行了全面评价：
- **组件匹配**：用于分析推荐查询的结构质量。
- **结果集验证**：确保推荐查询的语义准确性。
- **综合性能得分**：量化系统的整体表现。

通过该评估流程，可以科学且直观地了解 SQL 查询推荐系统的性能水平。如果有需要更深入的优化，代码框架支持灵活扩展以适应更多场景需求。 😊