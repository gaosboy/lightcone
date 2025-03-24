from gramai.utils import generate_random_str, is_dict
from peewee import CharField, DateTimeField

from lightcone.database import BaseModel


class Account(BaseModel):
    id = CharField(max_length=32, primary_key=True)
    nick = CharField(max_length=255)
    created = DateTimeField()
    modified = DateTimeField()

    @classmethod
    def insert(cls, __data=None, **insert):
        """
        重写insert方法
        插入数据，默认添加或覆盖新的随机ID
        """
        if is_dict(__data) and "id" in __data:
            del __data["id"]
        insert["id"] = generate_random_str()  # 新增数据，则生成一个
        return super().insert(__data, **insert)
