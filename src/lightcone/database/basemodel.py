from peewee import DoesNotExist
from peewee import Model

from gramai.utils import is_dict
from lightcone.database.mysql import MySQL
from lightcone.utils.tools import logging


class BaseModel(Model):
    class Meta:
        database = MySQL().conn

    @classmethod
    def insert_exclude_fields(cls) -> list:
        """
        排除默认加入到update或insert语句中的字段
        当通过实例方法执行更新或插入动作时，若被排除字段值为None，则不会被加入语句

        默认排除created和modified，数据库中可以定义插入或更新时的字段默认值
        ->   `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间",
        ->   `modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "修改时间",
        """
        return ["created", "modified"]

    @classmethod
    def update_exclude_fields(cls) -> list:
        """
        排除默认加入到update或insert语句中的字段
        当通过实例方法执行更新或插入动作时，若被排除字段值为None，则不会被加入语句

        默认排除created和modified，数据库中可以定义插入或更新时的字段默认值
        ->   `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间",
        ->   `modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "修改时间",
        """
        return ["modified"]

    @classmethod
    def insert(cls, __data=None, **insert):
        """
        重写insert方法，清理需要排除的字段
        当前Model执行insert操作，将自动清理语句中 insert_exclude_fields() 所返回的字段
        若有个性化需求：
            可重写 insert_exclude_fields 方法，更新排除字段列表
            或 从写 insert 方法，更新排除逻辑
        """
        for exclude_key in cls.insert_exclude_fields():
            if is_dict(__data) and exclude_key in __data:
                del __data[exclude_key]
            if is_dict(insert) and exclude_key in insert:
                del insert[exclude_key]

        # 取出入参中的主键值
        primary_key_field_name = cls._meta.primary_key.name  # noqa
        primary_key_value = None
        if is_dict(insert) and primary_key_field_name in insert:
            primary_key_value = insert[primary_key_field_name]
        if is_dict(__data) and primary_key_field_name in __data:  # __data的优先级更高
            primary_key_value = __data[primary_key_field_name]
        # 把主键值记录在返回的query中，供插入成功后使用
        insert_query = super().insert(__data, **insert)
        insert_query.primary_key_value = primary_key_value

        return insert_query

    @classmethod
    def update(cls, __data=None, **update):
        """
        重写update方法，清理需要排除的字段
        当前Model执行update操作，将自动清理语句中 update_exclude_fields() 所返回的字段
        若有个性化需求：
            可重写 update_exclude_fields 方法，更新排除字段列表
            或 从写 update 方法，更新排除逻辑
        """
        for exclude_key in cls.update_exclude_fields():
            if is_dict(__data) and exclude_key in __data:
                del __data[exclude_key]
            if is_dict(update) and exclude_key in update:
                del update[exclude_key]

        return super().update(__data, **update)

    @classmethod
    def exists(cls, **kwargs):
        try:
            query = cls.select()
            for field, value in kwargs.items():
                query = query.where(getattr(cls, field) == value)
                return query.exists()
        except Exception as e:
            logging.info(f"查询出错：{e}")
            return False

    @classmethod
    def get_or_instantiate(cls, defaults=None, override=False, **kwargs):
        """
        根据参数表构造查询条件，通过get()方法从数据库读取数据
        若有返回，则直接返回get()的结果，或覆盖后返回
        若无返回，则仅根据 defaults 字典定义构造一个实例返回
            注意：如果defaults中含有与当前Model定义字段以外的key，构造时会自动过滤

        :param.defaults:            默认属性列表
        :param.override:            当有返回，是否需要用defaults覆盖数据库的查询结果
                    True:           覆盖
                    False:          不覆盖
        e.g.
        class MyClass(BaseModel):
            id = AutoField()
            field_1 = CharField(max_length=255)
            field_2 = CharField(max_length=255)

        my_instance = MyClass.get_or_instantiate(id=1, defaults={
                                                        "id" : 1000,
                                                        "field_1" : "value_1",
                                                        "field_2" : "value_2"
                                                        }
        若数据库中有 id 为 1 的数据，则返回的
            my_instance.id = 1
            (其他字段均为数据库返回值，defaults参数被忽略)
        若数据库中没有 id 为 1 的数据，则返回的
            my_instance.id = 1000
            my_instance.field_1 = value_1
            my_instance.field_2 = value_2
        """
        if not is_dict(defaults):
            defaults = {}
        cls._filter_dict_by_attrs(defaults)  # 过滤Model定义字段以外的key

        query = cls.select()
        for field, value in kwargs.items():
            query = query.where(getattr(cls, field) == value)
        try:
            result = query.get()
            if result is not None and override:
                for key in result._meta.combined:  # noqa
                    try:
                        if key in defaults:
                            setattr(result, key, defaults.get(key))
                    except KeyError as e:
                        logging.error(f"覆盖更新查询结果异常：{e}")
            return result
        except DoesNotExist:
            logging.info(f"数据库没查到，实例化一个。SQL：{query}")
            return cls(**defaults)

    def update_by_pk(self, defaults=None, **kwargs):
        """
        进行主键更新，把当前实例的数据update进数据库
        若更新成功，通过get_by_id读取新数据，并返回
        若更新失败，返回None
            若有 defaults 参数，先试用 defaults 的值覆盖当前实例的值（若defaults中含有主键属性，则不过滤）
        e.g.
        class MyClass(BaseModel):
            id = AutoField()
            field_1 = CharField(max_length=255)
            field_2 = CharField(max_length=255)

        my_instance = MyClass(id=1000, field_1="value_1", field_2="value_2")
        update_result = my_instance.update_by_pk(field_1="new_value_1",
                                                 field_2="new_value_2",
                                                 defaults={"field_2" : "new_new_value_2"}
        若数据库中有 id 为 1000 的数据，则更新该条数据：
            update_result 为 my_instance 同类型实例
                update_result.id = 1000
                update_result.field_1 = new_value_1
                update_result.field_2 = new_new_value_2
        """
        if not is_dict(defaults):
            defaults = {}

        cls = type(self)
        # 获取主键
        primary_key_field = self._meta.primary_key  # noqa
        primary_key_value = getattr(self, primary_key_field.name)
        if primary_key_value is not None:
            # 在参数里清理主键
            kwargs.pop(primary_key_field.name, None)
            # 从参数列表里构造要更新的数据字典
            normalized_data = self._normalize_data_from_attrs()
            for key in kwargs:  # 用 参数表中的值覆盖通过实例序列化出来的值，供更新用（低优先级）
                if key in self._meta.combined:  # noqa
                    normalized_data[key] = kwargs[key]
            for key in defaults:
                if key in self._meta.combined:  # noqa 用 defaults中的值覆盖通过实例序列化出来的值，供更新用（高优先级）
                    normalized_data[key] = defaults[key]
            try:
                update = cls.update(**normalized_data).where(primary_key_field == primary_key_value)
                logging.info(f"update: {update}")
                update.execute()
                # 更新完成，在读取一次结果
                return cls.get_by_id(primary_key_value)
            except Exception as e:
                logging.error(f"获取更新后的数据({primary_key_value})失败:{e}")
                raise e
        # 兜底返回空
        return None

    def update_or_create(self, defaults=None, **kwargs):
        """
        进行主键更新，把当前实例的数据update进数据库
        若更新成功，通过get_by_id读取新数据，并返回
        若更新失败，则执行插入操作，把当前实例写入数据库（将过滤该实例的主键属性）
            若有 defaults 参数，先试用 defaults 的值覆盖当前实例的值（若defaults中含有主键属性，则不过滤）
        e.g.
        class MyClass(BaseModel):
            id = AutoField()
            field_1 = CharField(max_length=255)
            field_2 = CharField(max_length=255)

        my_instance = MyClass(id=1000, field_1="value_1", field_2="value_2")
        update_result = my_instance.update_or_create(field_1="new_value_1",
                                                        field_2="new_value_2",
                                                        defaults={"field_2" : "new_new_value_2"}

        若数据库中有 id 为 1000 的数据，则更新该条数据：
            update_result 为 my_instance 同类型实例
                update_result.id = 1000
                update_result.field_1 = new_value_1
                update_result.field_2 = new_new_value_2

        若数据库中没有 id 为 1000 的数据，则执行写入操作
            数据库会插入如下数据：
                id: [自增主键]
                field_1: new_value_1
                field_2: new_new_value_2

            update_result 为 my_instance 同类型实例
                update_result.id = [自增主键]
                update_result.field_1 = new_value_1
                update_result.field_2 = new_new_value_2
        """
        if not is_dict(defaults):
            defaults = {}

        cls = type(self)
        # 获取主键
        primary_key_field = self._meta.primary_key  # noqa
        primary_key_value = getattr(self, primary_key_field.name)
        # 在参数里清理主键
        kwargs.pop(primary_key_field.name, None)
        # 从参数列表里构造要更新的数据字典
        normalized_data = self._normalize_data_from_attrs()
        for key in kwargs:  # 用 参数表中的值覆盖通过实例序列化出来的值，供更新用（低优先级）
            if key in self._meta.combined:  # noqa
                normalized_data[key] = kwargs[key]
        for key in defaults:
            if key in self._meta.combined:  # noqa 用 defaults中的值覆盖通过实例序列化出来的值，供更新用（高优先级）
                normalized_data[key] = defaults[key]
        data_exists = cls.exists(**{primary_key_field.name: primary_key_value})
        if data_exists:
            try:
                update = cls.update(**normalized_data).where(primary_key_field == primary_key_value)
                logging.info(f"update: {update}")
                update.execute()
                updated_data = cls.get_by_id(primary_key_value)
            except Exception as e:
                logging.info(f"更新失败:{e}")
                raise e
        else:
            try:
                # 执行插入操作
                insert = cls.insert(**normalized_data)
                logging.info(f"insert: {insert}")
                pk_inserted = insert.execute()
                primary_key_value = insert.primary_key_value or pk_inserted
                logging.info(f"新插入数据主键：{primary_key_value}")
                updated_data = cls.get_by_id(primary_key_value)
            except Exception as e:
                logging.error(f"插入失败:{e}")
                raise e
        return updated_data

    def _normalize_data_from_attrs(self):
        normalized = {}
        for key in self._meta.combined:  # noqa
            try:
                value = getattr(self, key)
                if value is not None:
                    normalized[key] = getattr(self, key)
            except KeyError as e:
                raise e
        return normalized

    def _update_attrs_from_data(self, data):
        if is_dict(data):
            for key in self._meta.combined:  # noqa
                try:
                    if key in data:
                        setattr(self, key, data[key])
                except KeyError as e:
                    raise e

    @classmethod
    def _filter_dict_by_attrs(cls, value):
        keys_to_remove = []
        if is_dict(value):
            for key in value:
                if key not in cls._meta.combined:  # noqa
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                try:
                    del value[key]
                except KeyError as e:
                    raise e

        return value
