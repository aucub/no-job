import json
import os
import re
import requests
import datetime
import arrow
import peewee
import asyncio
from typing import Callable, Dict, List, Tuple
from jd import JD, Level
from base import Base, VerifyException
from ai import LLM
from urllib.parse import parse_qs, urlparse


class ZhiPinBase(Base):
    URL0 = "https://www.zhipin.com/"
    URL1 = "https://www.zhipin.com/web/geek/job?query="
    URL3 = "&page="
    URL4 = "https://www.zhipin.com/wapi/zpgeek/job/card.json?securityId="
    URL5 = "&lid="
    URL6 = "&sessionId="
    URL7 = "&city="
    URL8 = "https://www.zhipin.com/job_detail/"
    URL9 = ".html"
    URL10 = "?lid="
    URL11 = "&securityId="
    URL12 = "https://www.zhipin.com/wapi/zpgeek/search/joblist.json?scene=1&payType=&partTime=&stage=&jobType=&multiBusinessDistrict=&multiSubway=&pageSize=30&query="
    URL13 = "https://www.zhipin.com/web/user/safe/verify-slider"
    URL14 = "https://www.zhipin.com/"
    URL15 = "https://www.zhipin.com/web/user/?ka=header-login"
    URL16 = "https://www.zhipin.com/wapi/zpgeek/job/detail.json?securityId="

    def __init__(self):
        Base.__init__(self)
        self.URL2 = self.config.query_param + "&salary="
        self.mongo = self.mongo_client["zpgeek_job"]
        self.check_network()
        self.wheels = self.load_state()
        if os.environ.get("CI"):
            self.config.llm_chat = False
        if self.config.llm_chat or self.config.llm_check:
            self.llm = LLM()

    def check_network(self):
        r = requests.get(
            self.URL14,
            proxies={"http://": self.proxy, "https://": self.proxy},
            timeout=5,
        )
        r.raise_for_status()

    def iterate_query_parameters(self):
        for city in self.config.query_city_list:
            if city in self.wheels[0]:
                continue
            for query in self.config.query_list:
                if query in self.wheels[1]:
                    continue
                for salary in self.config.salary_list:
                    if salary in self.wheels[2]:
                        continue
                    self.page_count = None
                    for page in range(self.config.page_min, self.config.page_max):
                        if self.page_count is not None and self.page_count < page:
                            break
                        if page <= self.wheels[3]:
                            continue
                        self.execute_query_jobs(city, query, salary, page)
                        self.wheels[3] = page
                        self.save_state(self.wheels)
                    self.wheels[3] = 0
                    self.wheels[2].append(salary)
                    self.save_state(self.wheels)
                self.wheels[2] = []
                self.wheels[1].append(query)
                self.save_state(self.wheels)
            self.wheels[1] = []
            self.wheels[0].append(city)
            self.save_state(self.wheels)
        self.wheels[0] = []
        self.save_state(self.wheels)

    def parse_joblist(self, json_str) -> list[str]:
        data = json.loads(json_str)
        url_list = []
        if data.get("message") != "Success":
            raise VerifyException(data)
        self.mongo["joblist"].insert_one(data)
        job_list = data["zpData"].get("jobList")
        if not job_list:
            self.page_count = 0
        results = asyncio.run(self.parse_job_tasks(job_list))
        for url in results:
            if url:
                url_list.append(url)
        return url_list

    async def parse_job_tasks(self, job_list) -> list[JD]:
        tasks = []
        for job in job_list:
            task = asyncio.create_task(self.parse_job(job))
            tasks.append(task)
        return await asyncio.gather(*tasks)

    async def parse_job(self, job) -> JD:
        jd = JD()
        jd.id = job.get("encryptJobId")
        jd.communicated = job.get("contact", False)
        if self.config.skip_known and self.check_jd_known(jd.id):
            return None
        row = self.get_jd(jd.id)
        if row and row.id == jd.id:
            if row.communicated or row.level == Level.COMMUNICATE.value:
                return None
            jd = row
        jd.url = f"{self.URL8}{jd.id}{self.URL9}"
        jd.name = job.get("jobName")
        jd.city = job.get("cityName")
        jd.company = job.get("brandName")
        jd.industry = job.get("brandIndustry")
        jd.scale = job.get("brandScaleName", "")
        jd.address = f"{job.get('cityName', '')} {job.get('areaDistrict', '')} {job.get('businessDistrict', '')}"
        jd.experience = job.get("jobExperience")
        jd.degree = job.get("jobDegree")
        jd.salary = job.get("salaryDesc") or job.get("jobSalary")
        jd.boss = job.get("bossName")
        jd.boss_title = job.get("bossTitle")
        jd.boss_id = job.get("encryptBossId")
        jd.skill = set(job.get("skills", []))
        last_modify_time = job.get("lastModifyTime")
        if last_modify_time and isinstance(last_modify_time, (int, float)):
            jd.update_date = arrow.Arrow.fromtimestamp(last_modify_time / 1000).date()
        jd.level = Level.LIST.value
        self.executor.submit(self.save_jd, jd)
        if jd and self.check_jd_stage(jd, Level.LIST.value):
            return f"{jd.url}?securityId={job.get('securityId')}"

    def parse_detail(self, json_str) -> bool:
        data = json.loads(json_str)
        if data.get("message") != "Success":
            raise VerifyException(data)
        zp_data = data.get("zpData", {})
        job_info = zp_data.get("jobInfo", {})
        boss_info = zp_data.get("bossInfo", {})
        brand_com_info = zp_data.get("brandComInfo", {})
        ats_online_apply_info = zp_data.get("atsOnlineApplyInfo", {})
        jd = JD()
        jd.id = job_info.get("encryptId")
        jd.communicated = ats_online_apply_info.get("alreadyApply", False)
        row = self.get_jd(jd.id)
        if row and row.id == jd.id:
            jd = row
        data["_id"] = jd.id
        self.mongo["detail"].update_one(
            {"_id": data["_id"]}, {"$set": data}, upsert=True
        )
        jd.url = f"{self.URL8}{jd.id}{self.URL9}"
        jd.name = job_info["jobName"]
        jd.city = job_info["locationName"]
        jd.address = job_info["address"]
        jd.experience = job_info["experienceName"]
        jd.degree = job_info["degreeName"]
        jd.salary = job_info["salaryDesc"]
        jd.position = job_info["positionName"]
        jd.boss_id = job_info["encryptUserId"]
        jd.skill = set(job_info["showSkills"])
        if "新" in job_info["jobStatusDesc"]:
            jd.update_date = arrow.now().date()
        jd.description = job_info["postDescription"]
        jd.boss = boss_info["name"]
        jd.boss_title = boss_info["title"]
        jd.active = boss_info["activeTimeDesc"]
        jd.scale = brand_com_info["scaleName"]
        jd.company = brand_com_info["brandName"]
        jd.industry = brand_com_info["industryName"]
        jd.level = self.check_jd(jd)
        self.executor.submit(self.save_jd, jd)
        return jd.level == Level.COMMUNICATE.value

    def check_jd(self, jd: JD) -> str:
        """检查 JD 信息，并返回其当前阶段"""
        for stage in [Level.LIST, Level.CARD, Level.DETAIL]:
            if not self.check_jd_stage(jd, stage.value):
                return stage.value
        return Level.COMMUNICATE.value

    def check_jd_stage(self, jd: JD, stage: str) -> bool:
        """检查 JD 信息在特定阶段是否满足条件"""
        checks: Dict[str, List[Tuple[str, Callable]]] = {
            Level.LIST.value: [
                ("communicated", lambda jd: not jd.communicated),
            ],
            Level.CARD.value: [
                ("salary", lambda jd: self.check_salary(jd.salary)),
            ],
            Level.DETAIL.value: [
                ("salary", lambda jd: self.check_salary(jd.salary)),
                ("res", lambda jd: self.check_res(jd.res)),
                ("update_date", lambda jd: self.check_update_date(jd.update_date)),
                ("description", lambda jd: self.check_description(jd.description)),
                ("offline", lambda jd: self.check_offline(jd.description, jd.city)),
                ("fund", lambda jd: self.check_fund(jd.fund)),
                ("communicated", lambda jd: not jd.communicated),
            ],
        }
        block_list_fields = {
            Level.LIST.value: ["name", "city", "company", "industry"],
            Level.CARD.value: [
                "description",
                "active",
                "address",
                "experience",
                "degree",
                "boss_title",
            ],
            Level.DETAIL.value: [
                "guide",
                "scale",
                "description",
                "experience",
                "degree",
                "boss_title",
                "position",
            ],
        }
        failed_fields = set()
        # 检查 block_list
        failed_field = self.check_block_list(
            {field: getattr(jd, field) for field in block_list_fields.get(stage, [])}
        )
        if failed_field:
            failed_fields.add(failed_field)
        # 检查 checks
        for field, check in checks[stage]:
            if not check(jd):
                failed_fields.add(field)
                break
        if len(failed_fields) > 0:
            jd.failed_fields = failed_fields
            return False
        elif stage == Level.DETAIL.value and jd.level == Level.COMMUNICATE.value:
            jd.failed_fields = set()
        return True

    def save_jd(self, jd: JD):
        if jd.id:
            jd.checked_time = arrow.Arrow.now().datetime
            try:
                n = jd.save(force_insert=False)
                if n == 0:
                    jd.save(force_insert=True)
            except (
                peewee.OperationalError,
                peewee.IntegrityError,
                peewee.InterfaceError,
            ) as e:
                self.handle_exception(e)
                JD.reconnect()
            print(jd.__data__)

    def get_jd(self, id) -> JD:
        try:
            jd = JD.get_or_none(JD.id == id)
            return jd or JD()
        except (peewee.OperationalError, peewee.InterfaceError) as e:
            self.handle_exception(e)
            JD.reconnect()
            return JD()

    def check_jd_known(self, id: str) -> bool:
        try:
            return (
                JD.select()
                .where((JD.id == id) & (peewee.fn.LENGTH(JD._failed_fields) > 0))
                .limit(1)
                .exists()
            )
        except (peewee.OperationalError, peewee.InterfaceError) as e:
            self.handle_exception(e)
            JD.reconnect()
            return False

    def check_boss_id(self, boss_id: str) -> bool:
        if not boss_id:
            return True
        return not (
            JD.select()
            .where((JD.boss_id == boss_id) & (JD.communicated == True))  # noqa: E712
            .limit(1)
            .exists()
        )

    def get_jd_url_list(self, level: str) -> list[str]:
        """获取指定 level 的 JD URL 列表"""
        return [
            row.url
            for row in JD.select(JD.url).where(
                (JD.communicated == False)  # noqa: E712
                & (
                    (JD._failed_fields.is_null())
                    | (peewee.fn.LENGTH(JD._failed_fields) == 0)
                )
                & (JD.level == level)
            )
        ]

    def check_communicate(self, jd: JD) -> bool:
        result = self.check_boss_id(jd.boss_id)
        if result and self.config.llm_check:
            result = result and self.llm.check_jd(self.config.llm_check_prompt, jd)
        if result:
            return True
        else:
            jd.communicated = True
            self.executor.submit(self.save_jd, jd)
            return False

    def get_encryptJobId(self, url: str) -> str:
        """从 URL 中提取 encryptJobId"""
        match = re.search(r"/job_detail/([^/]+)\.html", url)
        return match.group(1) if match else ""

    def get_securityId(self, url: str) -> str:
        """从 URL 中提取 securityId"""
        query_params = parse_qs(urlparse(url).query)
        return query_params.get("securityId", [""])[0]

    def check_fund(self, fund_text: str) -> bool:
        """检查资金是否满足最低要求"""
        if not fund_text:
            return True
        if "-" in fund_text:
            return False
        if "万" in fund_text:
            match = re.search(r"(\d+\.?\d*)", fund_text)
            if match:
                try:
                    fund = float(match.group(1))
                    return fund >= self.config.fund_min
                except ValueError:
                    return False
        return True

    def check_salary(self, salary_text) -> bool:
        """
        检查薪资
        """
        if not salary_text:
            return True
        if "面议" in salary_text:
            return False
        pattern = r"(\d+)-(\d+)K"
        match = re.search(pattern, salary_text)
        if match:
            low_salary = int(match.group(1))
            return low_salary < self.config.salary_max
        return True

    def check_description(self, description_text: str) -> bool:
        """检查职位描述"""
        if len(description_text) < self.config.description_min:
            return False
        description_text = description_text.lower()
        if all(
            item not in description_text
            for item in self.config.description_necessary_list
        ):
            return False
        exp_date_match = re.search(
            r"截止日期[:：]\s*(\d{4}\.?\d{1,2}\.?\d{1,2})", description_text
        )
        if exp_date_match:
            try:
                exp_date_str = exp_date_match.group(1).replace(".", "-")
                exp_date = arrow.get(exp_date_str).date()
                if exp_date < arrow.now().date():
                    return False
            except (ValueError, arrow.parser.ParserError) as e:
                self.handle_exception(e)
            description_text = description_text.replace(exp_date_match.group(), "")
        # 检查经验名单
        return any(
            item in description_text for item in self.config.description_experience_list
        ) or all(
            item not in description_text
            for item in self.config.description_experience_block_list
        )

    def parse_date(self, res_text) -> datetime.date:
        date_format = "%Y-%m-%d"
        return arrow.Arrow.strptime(res_text, date_format).date()

    def check_res(self, res: datetime.date) -> bool:
        """
        检查成立日期
        """
        if res:
            return arrow.Arrow.fromdate(res).timestamp() < (
                arrow.now().timestamp() - self.config.res_latest
            )
        return True

    def check_update_date(self, update_date: datetime.date) -> bool:
        """
        检查更新日期
        """
        if update_date:
            return arrow.Arrow.fromdate(update_date).timestamp() > (
                arrow.now().timestamp() - self.config.update_furthest
            )
        return True

    def contactable(self, startchat_text) -> bool:
        """
        检查能否沟通
        """
        return "立即" in startchat_text

    def check_offline(self, description_text, city_text) -> bool:
        if self.config.offline_interview:
            if any(item in description_text for item in self.config.offline_word_list):
                return any(item in city_text for item in self.config.offline_city_list)
        return True

    def save_state(self, wheels):
        with open(
            "state.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(wheels, f, ensure_ascii=False)

    def load_state(self) -> list[tuple[list[str], list[str], list[str], int]]:
        try:
            with open(
                "state.json",
                "r",
                encoding="utf-8",
            ) as f:
                return json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            self.handle_exception(e)
            return [[], [], [], 0]
