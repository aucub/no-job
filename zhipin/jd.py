import os
import time
from enum import Enum
from urllib.parse import parse_qs, urlparse
from peewee import (
    Model,
    CharField,
    BooleanField,
    DateField,
    DateTimeField,
    TextField,
    MySQLDatabase,
)
from dotenv import load_dotenv

load_dotenv()
db_url = urlparse(os.getenv("MYSQL_URL"))
db_string = parse_qs(db_url.query)
db = MySQLDatabase(
    host=db_url.hostname,
    port=db_url.port if db_url.port else 3306,
    user=db_string["user"][0],
    password=db_string["password"][0],
    database=db_url.path[1:],
    ssl_verify_identity=True,
    thread_safe=True,
    autocommit=True,
    autoconnect=True,
    connect_timeout=10,
    read_timeout=20,
)
db.connect()


class JD(Model):
    id = CharField(primary_key=True, max_length=255)
    url = CharField(max_length=255, null=True)
    name = CharField(max_length=255, null=True)
    position = CharField(max_length=255, null=True)
    type = CharField(max_length=255, null=True)
    proxy = BooleanField(null=True)
    pay_type = CharField(max_length=255, null=True)
    city = CharField(max_length=100, null=True)
    address = CharField(max_length=255, null=True)
    guide = CharField(max_length=255, null=True)
    scale = CharField(max_length=50, null=True)
    update_date = DateField(null=True)
    salary = CharField(max_length=100, null=True)
    experience = CharField(max_length=100, null=True)
    degree = CharField(max_length=50, null=True)
    company = CharField(max_length=255, null=True)
    company_introduce = TextField(null=True)
    industry = CharField(max_length=255, null=True)
    fund = CharField(max_length=255, null=True)
    res = DateField(null=True)
    boss = CharField(max_length=100, null=True)
    boss_title = CharField(max_length=100, null=True)
    boss_id = CharField(max_length=255, null=True)
    active = CharField(max_length=50, null=True)
    description = TextField(null=True)
    communicated = BooleanField(null=True)
    checked_time = DateTimeField(null=True)
    level = CharField(max_length=50, null=True)
    _skill = CharField(max_length=255, null=True, column_name="skill")

    @property
    def skill(self):
        return set(self._skill.split(",")) if self._skill else set()

    @skill.setter
    def skill(self, value):
        self._skill = ",".join(value)

    _failed_fields = CharField(max_length=255, null=True, column_name="failed_fields")

    @property
    def failed_fields(self):
        return set(self._failed_fields.split(",")) if self._failed_fields else set()

    @failed_fields.setter
    def failed_fields(self, value):
        self._failed_fields = ",".join(value)

    class Meta:
        database = db

    def reconnect():
        JD._meta.database.close()
        time.sleep(2)
        JD._meta.database.connect(reuse_if_open=True)


class Level(Enum):
    LIST = "list"
    CARD = "card"
    DETAIL = "detail"
    COMMUNICATE = "communicate"


jobType = {
    4: "实习",
    6: "兼职",
}
