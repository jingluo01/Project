import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def init_school_db():
    # 1. 解析数据库连接信息 (从 SCHOOL_DATABASE_URL 解析)
    # 格式: mysql+pymysql://root:123456@localhost:3306/school_official
    db_url = os.getenv('SCHOOL_DATABASE_URL')
    if not db_url:
        print("未在 .env 中找到 SCHOOL_DATABASE_URL")
        return

    # 简单解析 URL
    try:
        url_part = db_url.split('://')[1]
        auth_part, rest = url_part.split('@')
        host_port_db = rest.split('/')
        user, password = auth_part.split(':')
        host_port = host_port_db[0].split(':')
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 3306
        db_name = host_port_db[1]
    except Exception as e:
        print(f"解析数据库URL失败: {e}")
        return

    # 2. 连接 MySQL 并创建数据库
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password)
        cursor = conn.cursor()
        
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"数据库 {db_name} 已准备就绪")
        
        # 切换到该数据库
        conn.select_db(db_name)
        
        # 3. 创建表结构 (与 SchoolMember 模型同步)
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS school_members (
            user_no VARCHAR(20) PRIMARY KEY COMMENT '学号/工号',
            real_name VARCHAR(50) NOT NULL COMMENT '真实姓名',
            member_type INT NOT NULL COMMENT '类型: 1-学生, 2-教职工',
            department VARCHAR(100) COMMENT '所属院系/部门',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        cursor.execute(create_table_sql)
        print("表 school_members 已准备就绪")
        
        # 4. 插入模拟数据
        mock_data = [
            # 计算机学院
            ('20230001', '张三', 1, '计算机科学与技术学院'),
            ('20230002', '李四', 1, '人工智能学院'),
            ('20230101', '王维', 1, '软件工程系'),
            ('T1001', '赵老师', 2, '自动化学院'),
            
            # 机械/工程学院
            ('20230003', '王小五', 1, '机械工程学院'),
            ('20230205', '刘星', 1, '材料科学与工程'),
            ('T1102', '高博', 2, '土木工程学院'),
            
            # 管理与文科学院
            ('20230321', '陈默默', 1, '公共管理学院'),
            ('20230415', '林黛', 1, '外国语学院'),
            ('T1002', '钱教授', 2, '管理学院'),
            ('T1205', '周博', 2, '经济学院'),
            
            # 行政与后勤
            ('T1003', '孙主任', 2, '后勤保障部'),
            ('T1501', '李科长', 2, '保卫处'),
            ('T1602', '吴老师', 2, '教务处'),
            
            # 外部/临时账号
            ('2021001', '李同学', 1, '测绘学院'), # 对应项目默认测试账号
            ('T2021001', '王老师', 2, '计算机学院') # 对应项目默认测试账号
        ]
        
        # 使用 REPLACE INTO 防止重复执行报错
        insert_sql = "REPLACE INTO school_members (user_no, real_name, member_type, department) VALUES (%s, %s, %s, %s)"
        cursor.executemany(insert_sql, mock_data)
        
        conn.commit()
        print(f"成功导入 {len(mock_data)} 条模拟师生数据")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"初始化失败: {e}")

if __name__ == "__main__":
    init_school_db()
