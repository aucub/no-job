import attr
import toml
from enum import Enum
from typing import List


class Direction(Enum):
    UP = "up"


@attr.dataclass
@attr.s(init=False)
class Config:
    query_token: bool = True
    always_token: bool = False
    captcha_image_path: str = "captcha"
    timeout: int = 40
    sleep: float = 0.0
    small_sleep: float = 2.0
    large_sleep: float = 7.0
    max_retries: int = 3
    llm_chat: bool = False
    skip_known: bool = False
    llm_check: bool = False
    llm_check_prompt: str = "我希望你充当求职者的招聘信息检查助手，你将检查职位描述的质量。请仅提供“true”或“false结果，无需解释。"
    resume: str = ""
    salary_max: int = 9
    position_block_list: List = []
    active_block_list: List = [
        "半年",
        "月内",
        "本月",
        "周内",
        "本周",
        "7日",
    ]
    offline_word_list: List = [
        "不支持在线",
        "不支持线上",
        "线下面试",
        "线下笔试",
        "现场面试",
        "现场机考",
        "不接受线上",
        "未开放线上",
        "现场coding",
        "附近优先",
    ]
    scale_block_list: List = ["-20"]  # 规模阻止名单
    degree_block_list: List = ["硕", "博"]  # 学历阻止名单
    experience_block_list: List = []  # 经验阻止名单
    location_block_list: List = []

    @property
    def city_block_list(self) -> List:
        return self.location_block_list

    @property
    def address_block_list(self) -> List:
        return self.location_block_list

    boss_title_block_list: List = []  # boss职位阻止名单
    boss_id_block_list: List = []
    industry_block_list: List = []  # 行业阻止名单
    name_block_list: List = []  # 名称阻止名单
    company_block_list: List = []  # 公司阻止名单
    fund_min: float = 29.0  # 最小注册资金
    res_latest: int = 31536000  # 最晚成立时间
    guide_block_list: List = []  # 导航阻止名单
    update_furthest: int = 7776000  # 最旧更新时间
    offline_interview: bool = True  # 线下检查
    offline_city_list: List = []  # 线下城市
    description_min: int = 30  # 最短描述
    description_necessary_list: List = []  # 描述必备词
    description_block_list: List = []  # 描述阻止名单
    description_experience_block_list: List = []  # 描述经验阻止名单
    description_experience_list: List = []  # 描述经验名单
    query_list: List = []
    query_city_list: List = ["100010000"]
    query_param: str = "&experience=101,102,103,104&scale=302,303,304,305,306&degree=209,208,206,202,203"
    salary_list: List = ["404", "403"]
    page_min: int = 1
    page_max: int = 10
    """
    AndroidUiautomation
    """
    query_city_list_ui: List = [
        "杭州",
        "上海",
        "北京",
        "广州",
        "深圳",
        "苏州",
        "武汉",
        "长沙",
        "成都",
        "天津",
        "西安",
        "厦门",
        "郑州",
        "重庆",
    ]
    query_label_list_ui: List = [
        "高中",
        "1-3年",
        Direction.UP.value,
        "20-99人",
        "100-499人",
        "500-999人",
        "1000-9999人",
        "10000人以上",
    ]
    salary_list_ui: List = ["3-5K", "5-10K"]


def save_config(config: Config) -> None:
    with open("config.toml", "w") as f:
        toml.dump(attr.asdict(config), f)


def load_config() -> Config:
    with open("config.toml", "r") as f:
        config_dict = toml.load(f)
        return Config(**config_dict)


if __name__ == "__main__":
    config = Config()
    save_config(config)
