import uiautomator2 as u2
from uiautomator2.exceptions import UiObjectNotFoundError
import json
import re
import time
import datetime
import arrow
from jd import JD
from config import Direction
from zhipin_base import ZhiPinBase


class ZhiPinU2(ZhiPinBase):
    def to_up(self):
        self.d.swipe(0.47, 0.86, 0.45, 0.26)

    def to_down(self):
        self.d.swipe(0.48, 0.25, 0.43, 0.89)

    def to_left(self):
        self.d.swipe(0.91, 0.45, 0.05, 0.43)

    def __init__(self):
        ZhiPinBase.__init__(self)
        self.d = u2.connect()
        self.d.implicitly_wait(self.config.timeout)
        self.d.set_input_ime()

    def start_app(self):
        self.d.app_start("com.hpbr.bosszhipin")
        self.d(resourceId="com.hpbr.bosszhipin:id/cl_card_container").wait()

    def stop_app(self):
        self.d.app_stop("com.hpbr.bosszhipin")
        time.sleep(self.config.small_sleep)

    def iterate_query_parameters(self):
        for city in self.config.query_city_list_ui:
            if city in self.wheels[0]:
                continue
            for query in self.config.query_list:
                if query in self.wheels[1] or "&" in query:
                    continue
                for salary in self.config.salary_list_ui:
                    if salary in self.wheels[2]:
                        continue
                    self.stop_app()
                    self.start_app()
                    self.execute_query_jobs(city, query, salary)
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

    def get_encryptJobId(self, url) -> str:
        field_pattern = r"weijd-job/([^?]*)"
        match = re.search(field_pattern, url)
        if match:
            return match.group(1)
        else:
            return ""

    def parse_date(self, update_text) -> datetime.date:
        try:
            days_pattern = r"(\d+)日内"
            match = re.search(days_pattern, update_text)
            if match:
                days_str = match.group(1)
                days = int(days_str)
                return arrow.now().shift(days=days).date()
        except Exception as e:
            self.handle_exception(e)
        return None

    def save_state(self, wheels):
        with open(
            "state_ui.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(wheels, f, ensure_ascii=False)

    def load_state(self) -> list[tuple[list[str], list[str], list[str]]]:
        try:
            with open(
                "state_ui.json",
                "r",
                encoding="utf-8",
            ) as f:
                return json.load(f)
        except Exception as e:
            self.handle_exception(e)
            return [[], [], []]

    def detail(self):
        jd = JD()
        jd.name = self.d(resourceId="com.hpbr.bosszhipin:id/tv_job_name").get_text()
        jd.boss = self.d(resourceId="com.hpbr.bosszhipin:id/tv_boss_name").get_text()
        self.d(resourceId="com.hpbr.bosszhipin:id/iv_share").click()
        time.sleep(self.config.small_sleep)
        self.d(resourceId="com.hpbr.bosszhipin:id/tv_share_link").click()
        time.sleep(self.config.small_sleep)
        url = self.d.clipboard
        jd.id = self.get_encryptJobId(url)
        jd.url = self.URL8 + jd.id + self.URL9
        row = self.get_jd(jd.id)
        if row and row.id == jd.id:
            jd = row
            if self.config.skip_known or row.communicated:
                time.sleep(self.config.small_sleep)
                return jd.boss
        jd.salary = self.d(resourceId="com.hpbr.bosszhipin:id/tv_job_salary").get_text()
        jd.address = self.d(
            resourceId="com.hpbr.bosszhipin:id/tv_required_location"
        ).get_text()
        jd.experience = self.d(
            resourceId="com.hpbr.bosszhipin:id/tv_required_work_exp"
        ).get_text()
        jd.degree = self.d(
            resourceId="com.hpbr.bosszhipin:id/tv_required_degree"
        ).get_text()
        tv_public_time = self.d(resourceId="com.hpbr.bosszhipin:id/tv_public_time")
        if tv_public_time.exists():
            public_time = tv_public_time.get_text()
            jd.update_date = self.parse_date(public_time)
        jd.boss_title = (
            self.d(resourceId="com.hpbr.bosszhipin:id/tv_boss_title")
            .get_text()
            .split("·")[-1]
            .strip()
        )
        jd.active = (
            self.d(resourceId="com.hpbr.bosszhipin:id/boss_label_tv")
            .get_text()
            .split("|")[0]
            .strip()
        )
        words = ""
        fl_content_above = self.d(resourceId="com.hpbr.bosszhipin:id/fl_content_above")
        btn_words = fl_content_above.child(resourceId="com.hpbr.bosszhipin:id/btn_word")
        for btn_word in btn_words:
            words = words + btn_word.get_text()
        if self.d(resourceId="com.hpbr.bosszhipin:id/tv_com_name").exists():
            self.d.swipe(0.47, 0.86, 0.45, 0.56)
        else:
            self.to_up()
        see_more = self.d(text="查看更多")
        if see_more.exists():
            self.d.click(*see_more.center())
        jd.description = (
            words
            + self.d(resourceId="com.hpbr.bosszhipin:id/tv_description").get_text()
        )
        jd.address = self.d(resourceId="com.hpbr.bosszhipin:id/tv_location").get_text()
        jd.company = self.d(resourceId="com.hpbr.bosszhipin:id/tv_com_name").get_text()
        tv_com_info = (
            self.d(resourceId="com.hpbr.bosszhipin:id/tv_com_info")
            .get_text()
            .split("•")
        )
        jd.scale = tv_com_info[-2].strip()
        jd.industry = tv_com_info[-1].strip()
        jd.checked_time = datetime.datetime.now()
        jd.level = self.check_jd(jd)
        self.save_jd(jd)
        self.to_down()
        time.sleep(self.config.small_sleep)
        return jd.boss

    def execute_query_jobs(self, city, query, salary):
        time.sleep(self.config.large_sleep)
        self.d.click(0.92, 0.07)
        self.d(resourceId="com.hpbr.bosszhipin:id/et_search").set_text(query)
        time.sleep(self.config.small_sleep)
        self.d(resourceId="com.hpbr.bosszhipin:id/tv_search").click()
        self.d(resourceId="com.hpbr.bosszhipin:id/view_job_card")
        tab_labels = self.d(resourceId="com.hpbr.bosszhipin:id/tv_tab_label")
        tab_labels[3].click()
        time.sleep(self.config.small_sleep)
        self.d(resourceId="com.hpbr.bosszhipin:id/tv_btn_action").click()
        time.sleep(self.config.large_sleep)
        try:
            self.d(text=city).click()
        except UiObjectNotFoundError as e:
            self.d(resourceId="com.hpbr.bosszhipin:id/iv_back").click()
            time.sleep(self.config.small_sleep)
            self.d(resourceId="com.hpbr.bosszhipin:id/iv_back").click()
            self.handle_exception(e)
        time.sleep(self.config.small_sleep)
        self.d(resourceId="com.hpbr.bosszhipin:id/view_job_card")
        tab_labels[5].click()
        self.d(resourceId="com.hpbr.bosszhipin:id/btn_confirm")
        try:
            for label in self.config.query_label_list_ui:
                if Direction.UP.value in label:
                    self.to_up()
                    time.sleep(self.config.small_sleep)
                    continue
                self.d(text=label).click()
            self.to_down()
            time.sleep(self.config.small_sleep)
            self.d(text=salary).click()
            time.sleep(self.config.small_sleep)
            self.d(resourceId="com.hpbr.bosszhipin:id/btn_confirm").click()
        except UiObjectNotFoundError as e:
            self.d(resourceId="com.hpbr.bosszhipin:id/iv_back").click()
            self.handle_exception(e)
        time.sleep(self.config.small_sleep)
        tab_labels[4].click()
        time.sleep(self.config.small_sleep)
        try:
            self.d(text="最新优先").click()
        except UiObjectNotFoundError as e:
            self.d.click(0.47, 0.56)
            self.handle_exception(e)
        time.sleep(self.config.large_sleep)
        job_cards = self.d(resourceId="com.hpbr.bosszhipin:id/view_job_card")
        if len(job_cards) == 0:
            return
        self.d.click(*job_cards[0].center())
        for page in range(0, 40):
            text = None
            try:
                text = self.detail()
            except (UiObjectNotFoundError, TypeError) as e:
                self.handle_exception(e)
            self.to_left()
            time.sleep(self.config.small_sleep)
            if text:
                try:
                    if self.d(text=text).exists:
                        break
                except UiObjectNotFoundError as e:
                    self.handle_exception(e)

    def test_query(self):
        self.iterate_query_parameters()


if __name__ == "__main__":
    zpp = ZhiPinU2()
    zpp.test_query()