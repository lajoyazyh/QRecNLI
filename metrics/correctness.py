import sqlite3
from concurrent.futures import ThreadPoolExecutor

def sql_syntax_validity(database_folder, db_id, query):
    """
    检查SQL查询的语法是否正确。
    
    仅检查语法，不关心返回结果。
    
    参数：
        database_folder (str): 数据库根目录，例如 "./spider/database"
        db_id (str): 数据库ID，例如 "customers_and_addresses"
        query (str): 要检测的SQL查询语句
        
    返回：
        int: 1 表示语法正确，0 表示语法错误。
    """
    db_path = f"{database_folder}/{db_id}/{db_id}.sqlite"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        cursor.close()
        conn.close()
        return 1  # 语法正确
    except sqlite3.Error:
        return 0  # 语法错误

def batch_sql_syntax_check(database_folder, db_id, queries, max_workers=4):
    """
    批量检查SQL查询的语法正确率。
    
    参数：
        database_folder (str): 数据库根目录
        db_id (str): 数据库ID
        queries (list): SQL查询语句列表
        max_workers (int): 并行执行的最大线程数
        
    返回：
        float: SQL 语法正确率（正确查询数量 / 总查询数量）。
    """
    total_queries = len(queries)
    if total_queries == 0:
        return 0.0  # 避免除零错误

    correct_count = 0

    # 并行执行查询语法检查
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(lambda q: sql_syntax_validity(database_folder, db_id, q), queries)

    correct_count = sum(results)
    
    return correct_count / total_queries  # 计算正确率

# 示例使用
if __name__ == "__main__":
    database_folder = "./spider/database"
    db_id = "customers_and_addresses"

    # 假设有多个查询（其中一个包含语法错误）
    queries = [
        "SELECT * FROM Customer_Addresses WHERE Address_id = 11",
        "SELECT * FROM Customer_Addresses WHERE City = 'New York'", #
        "SELECT * FORM Customer_Addresses WHERE Address_id = 14",  
        "SELECT * FROM Customer_Addresses WHERE Address_id = 5",
        "SELECT * FROM Customer_Addresses WHERE City = 'San Francisco'", #
        "SELECT * FROM Customer_Addresses WHERE Address_id = 12", #
        "SELECT * FROM Customer_Addresses WHERE City = 'Los Angeles'", #
        "SELECT * FROM Customer_Addresses WHERE Address_id = 13", 
        "SELECT * FROM Customer_Addresses WHERE City = 'Chicago'", #
        "SELECT * FROM Customer_Addresses WHERE Address_id = 10",
        #一共有5/10个对的
    ]

    syntax_accuracy = batch_sql_syntax_check(database_folder, db_id, queries)

    print(f"SQL 语法正确率: {syntax_accuracy:.2%}")
