import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def query_execution_time(database_folder, db_id, query, num_trials=3):
    """
    计算SQL查询的平均执行时间（单位：秒）。
    通过多次执行查询来降低偶然误差，返回平均执行时间。
    
    参数：
        database_folder (str): 数据库根目录，例如 "./spider/database"
        db_id (str): 数据库ID，例如 "customers_and_addresses"
        query (str): 要执行的SQL查询语句
        num_trials (int): 执行次数，默认为3次
        
    返回：
        float: 平均执行时间（秒），如果查询执行出错则返回 None。
    """
    db_path = f"{database_folder}/{db_id}/{db_id}.sqlite"
    times = []
    try:
        for i in range(num_trials):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            start_time = time.time()
            cursor.execute(query)
            # 调用fetchall确保查询执行完毕
            cursor.fetchall()
            end_time = time.time()
            times.append(end_time - start_time)
            cursor.close()
            conn.close()
        avg_time = sum(times) / len(times)
        return avg_time
    except sqlite3.Error as e:
        print(f"执行查询时出错: {e}")
        return None

def execute_queries_parallel(database_folder, db_id, queries, num_trials=3, max_workers=4):
    """
    执行大批量SQL查询，返回每个查询的平均执行时间。
    
    参数：
        database_folder (str): 数据库根目录
        db_id (str): 数据库ID
        queries (list): 要执行的SQL查询语句列表
        num_trials (int): 每个查询执行次数
        max_workers (int): 并行执行的最大线程数
        
    返回：
        dict: 查询语句及其对应的平均执行时间
    """
    results = {}
    
    # 使用ThreadPoolExecutor来并行处理多个查询
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_query = {executor.submit(query_execution_time, database_folder, db_id, query, num_trials): query for query in queries}
        
        for future in as_completed(future_to_query):
            query = future_to_query[future]
            try:
                avg_exec_time = future.result()
                if avg_exec_time is not None:
                    results[query] = avg_exec_time
                else:
                    results[query] = "查询失败"
            except Exception as e:
                print(f"查询 {query} 执行时出错: {e}")
                results[query] = "执行错误"
    
    return results

def calculate_average_execution_time(database_folder, db_id, queries, num_trials=3, max_workers=4):
    """
    计算给定查询列表的平均执行时间。
    
    参数：
        database_folder (str): 数据库根目录
        db_id (str): 数据库ID
        queries (list): 要执行的SQL查询语句列表
        num_trials (int): 每个查询执行次数
        max_workers (int): 并行执行的最大线程数
        
    返回：
        float: 所有查询的平均执行时间（秒）
    """
    query_times = execute_queries_parallel(database_folder, db_id, queries, num_trials, max_workers)
    
    # 计算所有查询的平均执行时间
    valid_times = [time for time in query_times.values() if isinstance(time, float)]
    if valid_times:
        avg_exec_time = sum(valid_times) / len(valid_times)
        return avg_exec_time
    else:
        print("所有查询执行失败，无法计算平均执行时间。")
        return None

# 示例使用
if __name__ == "__main__":
    database_folder = "./spider/database"
    db_id = "customers_and_addresses"
    
    # 假设有多个查询
    queries = [
        "SELECT * FROM Customer_Addresses WHERE Address_id = 11",
        "SELECT * FROM Customer_Addresses WHERE City = 'New York'",
        "SELECT * FROM Customer_Addresses WHERE Address_id = 14",
        "SELECT * FROM Customer_Addresses WHERE Address_id = 5"
    ]
    
    # 计算所有查询的平均执行时间
    avg_exec_time = calculate_average_execution_time(database_folder, db_id, queries)
    
    if avg_exec_time is not None:
        print(f"所有查询的平均执行时间: {avg_exec_time:.4f}秒")
    else:
        print("查询执行失败，无法计算平均执行时间。")
