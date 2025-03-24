from playhouse.pool import PooledMySQLDatabase

from gramai.utils.cache import singleton
from gramai.utils.config import Config


@singleton
class MySQL:
    def __init__(self, ):
        # 读取配置
        db_config = Config("mysql.ini")
        # 配置连接池
        self._conn = PooledMySQLDatabase(
            database=db_config.get("mysql.database"),
            user=db_config.get("mysql.user"),
            password=db_config.get("mysql.password"),
            host=db_config.get("mysql.host"),
            port=db_config.get("mysql.port"),
            max_connections=db_config.get("mysql.max_connections", 10),
            stale_timeout=db_config.get("mysql.stale_timeout", 300),
            charset='utf8mb4'
        )

    @property
    def conn(self):
        return self._conn
