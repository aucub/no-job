import os
import sys
import cv2
import copy
import time
import arrow
import random
import shutil
import socket
import atexit
import asyncio
from captcha import cracker
from jd import JD, Level
from zhipin_base import ZhiPinBase, VerifyException
from DrissionPage import ChromiumPage, ChromiumOptions, SessionOptions, WebPage
from collections.abc import Iterable
from json.decoder import JSONDecodeError
from DrissionPage.common import Settings, wait_until
from DrissionPage.errors import (
    ElementNotFoundError,
    NoRectError,
    ElementLostError,
    WaitTimeoutError,
    WrongURLError,
)

Settings.raise_when_ele_not_found = True


class ZhiPinDrissionPage(ZhiPinBase):
    def find_free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    def __init__(self):
        ZhiPinBase.__init__(self)
        atexit.register(self.cleanup_drission_page)
        self.cookies_co = (
            ChromiumOptions(read_file=False)
            .set_timeouts(self.config.timeout)
            .set_retry(self.config.max_retries)
            .set_paths(user_data_path=self.parser.parse_args().data_path)
            .set_pref("credentials_enable_service", False)
            .set_pref("enable_do_not_track", True)
            .set_pref("webrtc.ip_handling_policy", "disable_non_proxied_udp")
            .set_pref("webrtc.multiple_routes_enabled", False)
            .set_pref("webrtc.nonproxied_udp_enabled", False)
            .set_argument("--disable-translate")
            .set_argument("--block-third-party-cookies")
            .set_argument("--disable-dev-shm-usage")
            .set_argument("--disable-infobars")
            .set_argument("-disable-browser-side-navigation")
            .set_argument("--disable-save-password-bubble")
            .set_argument("--disable-single-click-autofill")
            .set_argument("--disable-oopr-debug-crash-dump")
            .set_argument("--disable-top-sites")
            .set_argument("--no-crash-upload")
            .set_argument("--deny-permission-prompts")
            .set_argument("--no-first-run")
            .set_argument("--disable-notifications")
            .set_argument("--disable-autofill-keyboard-accessory-view[8]")
            .set_argument("--dom-automation")
            .set_argument("--disable-hang-monitor")
            .set_argument("--disable-sync")
            .set_argument("--hide-crash-restore-bubble")
            .set_argument("--disable-reading-from-canvas")
            .set_argument("--disable-breakpad")
            .set_argument("--disable-crash-reporter")
            .set_argument("--no-default-browser-check")
            .set_argument("--disable-prompt-on-repost")
            .set_argument("--webview-force-disable-3pcs")
            .set_argument(
                "--disable-features",
                "OptimizationHintsFetching,Translate,OptimizationTargetPrediction,PrivacySandboxSettings4,DownloadBubble,DownloadBubbleV2,InsecureDownloadWarnings",
            )
            .set_argument(
                "--host-rules",
                '"MAP apm-fe.zhipin.com 127.0.0.1,MAP apm-fe-qa.weizhipin.com 127.0.0.1,MAP logapi.zhipin.com 127.0.0.1,MAP datastar-dev.weizhipin.com 127.0.0.1,MAP z.zhipin.com 127.0.0.1,MAP img.bosszhipin.com 127.0.0.1,MAP hm.baidu.com 127.0.0.1,MAP t.kanzhun.com 127.0.0.1,MAP res.zhipin.com 127.0.0.1,MAP c-res.zhipin.com 127.0.0.1,MAP t.zhipin.com 127.0.0.1"',
            )
        )
        self.co = (
            copy.deepcopy(self.cookies_co)
            .set_paths(
                local_port=self.find_free_port(),
                user_data_path=os.path.expanduser("~") + "/.cache/chromium-temp",
            )
            .incognito()
        )
        self.so = (
            SessionOptions(read_file=False)
            .set_timeout(self.config.timeout)
            .set_retry(self.config.max_retries)
        )
        if (
            hasattr(self.parser.parse_args(), "communicate")
            and self.parser.parse_args().communicate
        ):
            self.config.query_token = True
            self.config.always_token = True
        if self.config.always_token:
            self.config.query_token = True
        if self.config.query_token:
            self.cookies_page = ChromiumPage(
                self.cookies_co.set_argument("--no-proxy-server"),
                timeout=self.config.timeout,
            )
            self.switch_page(True)
            self.set_blocked_urls()
            if self.config.always_token:
                self.page.clear_cache(cookies=False)
            self.login()
            time.sleep(self.config.small_sleep)
            self.check_dialog()
        if not self.config.always_token:
            if self.proxy:
                self.co.set_proxy(self.proxy)
                self.so.set_proxies(self.proxy, self.proxy)
            self.original_page = WebPage("d", self.config.timeout, self.co, self.so)
            self.switch_page(False)
            self.set_blocked_urls()
            self.check_network_drission_page()
        if self.parser.parse_args().communicate:
            self.test_communicate()
        else:
            self.test_query()

    def login(self):
        self.page.get(self.URL14)
        while not self.check_login():
            self.page.get(self.URL15)
            self.page.ele(".btn-sign-switch ewm-switch").click()
            self.page.wait.url_change(
                text="header-login",
                exclude=True,
                timeout=360,
                raise_err=False,
            )

    def switch_page(self, cookies_page: bool):
        if cookies_page and hasattr(self, "cookies_page"):
            self.page = self.cookies_page
        elif not cookies_page and hasattr(self, "original_page"):
            self.page = self.original_page

    def cleanup_drission_page(self):
        if hasattr(self, "original_page") and self.original_page:
            self.original_page.quit()
        if hasattr(self, "cookies_page") and self.cookies_page:
            self.cookies_page.quit()

    def check_network_drission_page(self):
        """
        检查网络
        """
        self.page.get(self.URL1 + "测试")
        try:
            self.page.wait.eles_loaded(
                locators=[
                    ".job-card-wrapper",
                ],
                any_one=True,
                raise_err=True,
            )
        except (ElementNotFoundError, WaitTimeoutError) as e:
            self.handle_exception(e)
            self.check_verify()

    def test_query(self):
        self.iterate_query_parameters()

    def execute_query_jobs(self, *args):
        for _ in range(self.config.max_retries):
            try:
                self.query_jobs(*args)
                break
            except (ElementNotFoundError, VerifyException) as e:
                self.handle_exception(e)

    def query_jobs(self, *args):
        if self.config.query_token:
            self.switch_page(True)
        url_list = self.job_list(*args)
        if self.config.query_token:
            if not self.check_login():
                sys.exit("登录状态丢失")
            self.switch_page(False)
        self.detail_list(url_list)

    def set_blocked_urls(self):
        self.page.set.blocked_urls(
            [
                "https://static.zhipin.com/*.jpg",
                "https://static.zhipin.com/*.png",
                "https://www.zhipin.com/wapi/zpuser/wap/getSecurityGuideV1",
                "https://www.zhipin.com/wapi/zpgeek/collection/popup/window",
                "https://static.zhipin.com/library/js/sdk/verify-sdk-v2.3.js",
                "https://static.zhipin.com/library/js/analytics/ka.zhipin.min.js",
            ]
        )

    def job_s_list(self, city, query, salary, page) -> list[str]:
        self.page.get(
            self.URL12
            + query
            + self.URL7
            + city
            + "&salary="
            + salary
            + self.URL3
            + str(page)
            + self.config.query_param
        )
        return self.parse_joblist(self.page.ele("tag:pre").text)

    def job_list(self, city, query, salary, page) -> list[str]:
        if (not self.config.query_token) and random.random() > 0.25:
            try:
                return self.job_s_list(city, query, salary, page)
            except (VerifyException, JSONDecodeError) as e:
                self.handle_exception(e)
        self.page.set.load_mode.none()
        self.page.listen.start("wapi/zpgeek/search/joblist")
        if self.URL1 in self.page.url and (self.URL3 + str(page - 1)) in self.page.url:
            arrow_right = self.page.ele(".ui-icon-arrow-right")
            if arrow_right.states.is_clickable:
                arrow_right.click()
        else:
            self.page.get(
                self.URL1
                + query
                + self.URL7
                + city
                + self.URL2
                + salary
                + self.URL3
                + str(page)
            )
        listen_result = self.page.listen.wait(
            timeout=self.config.large_sleep, raise_err=False
        )
        url_list = []
        if listen_result:
            if not isinstance(listen_result, Iterable):
                listen_result = [listen_result]
            try:
                for data in listen_result:
                    if not data.is_failed:
                        if data.response.status == 200:
                            url_list.extend(self.parse_joblist(data.response.raw_body))
            except (VerifyException, JSONDecodeError) as e:
                self.handle_exception(e)
        self.page.listen.stop()
        self.page.stop_loading()
        self.page.set.load_mode.normal()
        if len(url_list) > 0:
            return url_list
        try:
            element_list = self.page.eles(
                "@|class=job-card-wrapper@|class=job-empty-wrapper"
            )
            if len(element_list) == 0:
                raise ElementNotFoundError()
        except ElementNotFoundError as e:
            self.handle_exception(e)
            self.check_dialog()
            self.check_verify(verify_exception=True)
            return []
        if "没有找到相关职位" in element_list[0].text:
            self.page_count = page - 1
            return []
        if page == 1:
            try:
                options_pages = self.page.ele(
                    ".options-pages", timeout=self.config.small_sleep
                )
                options_page_list = options_pages.children(
                    "tag:a", timeout=self.config.small_sleep
                )
                page_count = 0
                for options_page in options_page_list:
                    if (
                        len(options_page.text) > 0
                        and options_page.text.isdecimal()
                        and int(options_page.text) > page_count
                    ):
                        page_count = int(options_page.text)
                if page_count < 10:
                    self.page_count = page_count
            except ElementNotFoundError as e:
                self.handle_exception(e)
        for element in element_list:
            try:
                jd = JD()
                job_info_html = element.ele(".:job-info clearfix").inner_html
                jd.communicated = not self.contactable(job_info_html)
                url = element.ele("css:.job-card-left").property("href")
                jd.id = self.get_encryptJobId(url)
                row = self.get_jd_skip(jd.id)
                if row is None:
                    continue
                elif jd.id == row.id:
                    jd = row
                jd.url = url.split("&securityId")[0]
                jd.name = element.ele("css:.job-name").text
                jd.city = element.ele("css:.job-area").text
                jd.company = element.ele("css:.company-name a").text
                jd.industry = element.ele("css:.company-tag-list    li").text
                jd.checked_time = arrow.now().datetime
                jd.level = Level.LIST.value
                self.executor.submit(self.save_jd, jd)
                if self.check_jd_stage(jd, Level.LIST.value):
                    url_list.append(url)
            except ElementNotFoundError as e:
                self.handle_exception(e)
        return url_list

    def check_dialog(self):
        try:
            dialog_element_list = self.page.eles(
                locator=".dialog-container",
                timeout=self.config.small_sleep,
            )
            for dialog_element in dialog_element_list:
                if (
                    dialog_element.states.is_displayed
                    and dialog_element.states.has_rect
                    and (
                        "安全问题" in dialog_element.text
                        or "沟通" in dialog_element.text
                    )
                ):
                    close_element = dialog_element.ele(
                        locator=".close", timeout=self.config.small_sleep
                    )
                    if (
                        close_element.states.is_displayed
                        and close_element.states.has_rect
                    ):
                        close_element.click()
                        time.sleep(self.config.sleep)
        except (ElementNotFoundError, NoRectError) as e:
            self.handle_exception(e)

    def check_verify(self, verify_exception: bool = False):
        current_url = self.page.url
        captcha_result = False
        while "safe/verify-slider" in current_url and captcha_result is False:
            try:
                captcha_result = self.captcha()
                self.page.get(self.URL1 + "测试")
                self.page.wait.eles_loaded(
                    locators=[
                        ".job-card-wrapper",
                        ".job-empty-wrapper",
                        "css:.btn",
                    ],
                    any_one=True,
                    raise_err=True,
                )
                current_url = self.page.url
                if "safe/verify-slider" not in current_url:
                    break
            except (
                ZeroDivisionError,
                ElementNotFoundError,
                cv2.error,
                NoRectError,
                ElementLostError,
                WaitTimeoutError,
            ) as e:
                self.handle_exception(e)
                self.page.get(self.URL1 + "测试")
        if "403.html" in current_url or "error.html" in current_url:
            self.page.get_screenshot(path="tmp", name="error.jpg", full_page=True)
            sys.exit("403或错误")
        if "job_detail" in current_url:
            try:
                error_text = self.page.ele(
                    ".error-content", timeout=self.config.large_sleep
                ).text
                if "无法继续" in error_text:
                    self.page.get_screenshot(
                        path="tmp", name="error.jpg", full_page=True
                    )
                    sys.exit("403或错误")
            except ElementNotFoundError as e:
                self.handle_exception(e)
        if verify_exception:
            raise VerifyException()

    def captcha(self):
        captcha_image_path = self.config.captcha_image_path
        if os.path.exists(captcha_image_path):
            shutil.rmtree(captcha_image_path)
        os.makedirs(captcha_image_path)
        self.page.ele("css:.btn").click()
        self.page.wait.ele_displayed("text:依次")
        element = self.page.ele(".geetest_item_wrap")
        self.page.ele(".geetest_tip_img").get_screenshot(
            path=captcha_image_path, name="tip_image.png", scroll_to_center=False
        )
        self.page.ele(".geetest_item_wrap").get_screenshot(
            path=captcha_image_path, name="img_image.png", scroll_to_center=False
        )
        (element_width, element_height) = element.rect.size
        image = cv2.imread(captcha_image_path + "/" + "img_image.png")
        height, width, _ = image.shape
        scale_width = width / element_width
        scale_height = height / element_height
        click_list = cracker(
            tip_image=captcha_image_path + "/" + "tip_image.png",
            img_image=captcha_image_path + "/" + "img_image.png",
            path=captcha_image_path,
        )
        for click in click_list:
            x1, y1, x2, y2 = click
            x_offset = (x1 + x2) / 2 / scale_width
            y_offset = (y1 + y2) / 2 / scale_height
            element.click.at(x_offset, y_offset)
            time.sleep(random.uniform(self.config.sleep, self.config.small_sleep))
        time.sleep(random.uniform(self.config.small_sleep, self.config.large_sleep))
        self.page.ele(
            "css:body > div.geetest_panel.geetest_wind > div.geetest_panel_box.geetest_no_logo.geetest_panelshowclick > div.geetest_panel_next > div > div > div.geetest_panel > a"
        ).click()
        time.sleep(random.uniform(self.config.small_sleep, self.config.large_sleep))
        try:
            result = self.page.ele(".geetest_result_tip").text
            return "失败" not in result
        except ElementNotFoundError as e:
            self.handle_exception(e)
        return False

    def check_login(self) -> bool:
        try:
            return (
                "未登录"
                not in self.page.ele(
                    locator=".user-nav",
                    timeout=self.config.large_sleep,
                ).inner_html
            )
        except ElementNotFoundError as e:
            self.handle_exception(e)
        return True

    def change_page_mode(self, mode: str):
        if hasattr(self.page, "mode") and self.page.mode != mode:
            self.page.change_mode(mode, False, False)

    def detail_list(self, url_list):
        self.change_page_mode("s")
        results = asyncio.run(self.detail_s_list(url_list))
        self.change_page_mode("d")
        for url in results:
            if url:
                self.dp_detail(url)

    async def detail_s_list(self, url_list):
        tasks = []
        for url in url_list:
            task = asyncio.create_task(self.detail(url))
            tasks.append(task)
        return await asyncio.gather(*tasks)

    async def detail(self, url):
        try:
            self.page.get(
                self.URL16 + self.get_securityId(url),
                proxies={"http": self.proxy, "https": self.proxy},
            )
            if not self.parse_detail(self.page.raw_data):
                return None
        except (JSONDecodeError, VerifyException, ElementNotFoundError) as e:
            self.handle_exception(e)
        return url

    def dp_detail(self, url):
        self.page.set.load_mode.none()
        jd = self.get_jd(self.get_encryptJobId(url))
        try:
            self.page.get(url)
            self.page.ele("职位描述")
            self.page.stop_loading()
            element = self.page.ele("@|class=btn btn-more@|class=btn btn-startchat")
            jd.communicated = not self.contactable(element.text)
            if jd.communicated:
                return
            jd.guide = self.page.ele(".pos-bread city-job-guide").text
            if len(jd.guide) > 2:
                jd.guide = jd.guide[2:]
            jd.scale = self.page.ele("css:.sider-company > p:nth-child(4)").text
            if "人" not in jd.scale:
                jd.scale = ""
            update_text = self.page.ele("css:p.gray").text
            if ":" in update_text:
                jd.update_date = self.parse_date(update_text.split(":")[1])
            jd.description = self.page.ele("css:.job-detail-section").text
            try:
                jd.fund = self.page.ele("css:.company-fund").text
                if len(jd.fund.splitlines()) > 1:
                    jd.fund = jd.fund.splitlines()[-1]
                res_text = self.page.ele("css:.res-time").text
                if len(res_text.splitlines()) > 1:
                    jd.res = self.parse_date(res_text.splitlines()[-1])
            except ElementNotFoundError as e:
                self.handle_exception(e)
            jd.level = self.check_jd(jd)
            self.executor.submit(self.save_jd, jd)
        except (ElementNotFoundError, WrongURLError) as e:
            self.handle_exception(e)
            self.check_dialog()
            self.check_verify()
        self.page.set.load_mode.normal()

    def start_chat(self, url: str):
        self.page.get(url)
        jd = self.get_jd(self.get_encryptJobId(url))
        if not self.check_communicate(jd):
            return
        element = self.page.ele(
            "@|class=btn btn-more@|class=btn btn-startchat@|class=error-content"
        )
        if (
            "继续" in element.text
            or "更多" in element.text
            or "页面不存在" in element.text
        ):
            jd.communicated = True
            self.executor.submit(self.save_jd, jd)
            return
        elif "异常" in element.text:
            raise ElementNotFoundError()
        description = self.page.ele(".job-sec-text").text
        element = self.page.ele("css:btn btn-startchat")
        redirect_url = element.attr("redirect-url")
        element.click()
        chat_box = False
        try:
            find_element = self.page.ele("@|class=dialog-con@|class=chat-input")
            if "chat" in self.page.url or "发送" in find_element.text:
                chat_box = True
        except ElementNotFoundError as e:
            self.handle_exception(e)
            return
        if "已达上限" in find_element.text:
            sys.exit("已达上限")
        jd.communicated = True
        self.executor.submit(self.save_jd, jd)
        jd.description = description
        time.sleep(self.config.sleep)
        if chat_box:
            try:
                greet = self.config.default_greet
                if "chat" not in self.page.url and redirect_url:
                    self.page.get(f"{self.URL14[:-1]}{redirect_url}")
                if self.config.llm_chat:
                    greet = (
                        self.llm.generate_greet(self.config.resume, jd)
                        or self.config.default_greet
                    )
                self.send_greet_to_chat_box(greet)
            except ElementNotFoundError as e:
                self.handle_exception(e)
                return
        time.sleep(self.config.sleep)
        self.check_dialog()

    def send_greet_to_chat_box(self, greet):
        chat_box = self.page.ele("@|class=input-area@|class=chat-input")
        chat_box.clear()
        chat_box.input(greet)
        time.sleep(self.config.sleep)
        self.page.ele("@|class=btn-v2 btn-sure-v2 btn-send@|class=send-message").click()
        time.sleep(self.config.small_sleep)
        if "chat" in self.page.url:
            wait_until(
                lambda: self.page.ele(".:message-content").ele(
                    ".:status status-delivery"
                ),
                timeout=self.config.timeout,
            )
        else:
            wait_until(
                lambda: self.page.ele(".:message-list").ele(".:status success"),
                timeout=self.config.timeout,
            )

    def test_communicate(self):
        urls = set(url for url in self.get_jd_url_list(Level.COMMUNICATE.value))
        urls.discard(None)
        urls.discard("")
        self.switch_page(True)
        for url in urls:
            try:
                self.start_chat(url)
            except ElementNotFoundError as e:
                self.handle_exception(e)
                self.check_dialog()
                self.check_verify()


if __name__ == "__main__":
    ZhiPinDrissionPage()
