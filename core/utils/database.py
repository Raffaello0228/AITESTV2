import pymysql
from config import DB_CONFIG
from dbutils.pooled_db import PooledDB
from threading import Lock
from core.utils.logger import logger


class DBPool:
    _pool = None
    _lock = Lock()

    @classmethod
    def get_pool(cls):
        """获取或创建连接池"""
        with cls._lock:
            if cls._pool is None:
                cls._pool = PooledDB(
                    creator=pymysql,
                    maxconnections=10,  # 最大连接数
                    mincached=2,  # 初始化时创建的空闲连接数
                    maxcached=5,  # 连接池最大空闲连接数
                    maxshared=3,  # 共享连接数
                    blocking=True,  # 连接池满时是否阻塞等待
                    maxusage=None,  # 一个连接最多被重复使用的次数
                    setsession=[],  # 开始会话前执行的命令
                    ping=0,  # ping MySQL服务端确保连接可用
                    host=DB_CONFIG["host"],
                    port=DB_CONFIG["port"],
                    user=DB_CONFIG["user"],
                    password=DB_CONFIG["password"],
                    database=DB_CONFIG["database"],
                    charset=DB_CONFIG["charset"],
                    cursorclass=pymysql.cursors.DictCursor,
                )
                logger.info("数据库连接池初始化成功")
        return cls._pool

    @classmethod
    def query(cls, sql):
        """执行查询，每次从连接池获取新连接"""
        conn = None
        cursor = None
        try:
            conn = cls.get_pool().connection()
            cursor = conn.cursor()
            logger.info(f"执行查询: {sql}")
            cursor.execute(sql)
            result = cursor.fetchall()
            logger.info(f"查询返回 {len(result)} 条记录")
            return result
        except Exception as e:
            logger.error(f"查询执行失败: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()  # 归还连接到连接池

    @classmethod
    def execute(cls, sql, params=None):
        """执行更新，每次从连接池获取新连接"""
        conn = None
        cursor = None
        try:
            conn = cls.get_pool().connection()
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            conn.commit()
            affected = cursor.rowcount
            logger.info(f"执行更新影响 {affected} 行")
            return affected
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"执行更新失败: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()  # 归还连接到连接池
