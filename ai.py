import os
import httpx
from dotenv import load_dotenv
from loguru import logger
from jd import JD
from portkey_ai import Portkey


class LLM:
    def __init__(self) -> None:
        load_dotenv()
        os.environ["all_proxy"] = ""
        os.environ["ALL_PROXY"] = ""
        config = {
            "strategy": {"mode": "fallback"},
            "targets": [
                {"provider": "google", "api_key": os.environ["PORTKEY_API_KEY"]},
            ],
        }
        self.client = Portkey(
            base_url=os.environ["PORTKEY_GATEWAY_URL"],
            config=config,
            provider="google",
            custom_host=os.environ["PORTKEY_CUSTOM_HOST"],
        )

    @logger.catch
    def send(self, text):
        try:
            response = self.client.chat.completions.create(
                model="gemini-1.5-flash-latest",
                temperature=0.9,
                messages=[
                    {
                        "role": "user",
                        "content": text,
                    }
                ],
            )
            return response.choices[0].message.content
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
        return None

    def check_jd(self, base_prompt: str, jd: JD):
        prompt = (
            base_prompt + "\n职位名称：" + jd.name + "\n职位描述：" + jd.description
        )
        if jd.skill:
            prompt += "\n要求技能：" + str(jd.skill)
        result = self.send(prompt)
        if result and isinstance(result, str):
            return "true" in result.lower()
        return True

    def generate_greet(self, resume: str, jd: JD):
        prompt = f"""
        你正在作为求职者申请一个职位，请根据提供的简历和职位描述，撰写一条不超过210字的求职消息。需清晰、专业地描述你的优势。注意事项如下：
        1. 这是一条求职消息，不需要邮件格式。使用纯文本，不使用Markdown等标记语言，避免空行和换行。不得使用“*”等符号表示强调。
        2. 使用简体中文撰写消息。
        3. 避免透露个人信息，如姓名或个人经历。例如不要出现“我是一名”、“我有3年经验”、“我是一位”等词汇。
        4. 使用“你好”称呼对方，不添加其他敬语，也无需结束词。
        5. 注意职位描述中的拼写错误，确保求职消息中无拼写错误。
        6. 不得添加情绪化语言，如“非常高兴”。
        7. 消息需要一次完成，避免使用注释、转义字符、括号或中括号标注的内容，例如避免加入"[工作名]"、"[你的名字]"等需要二次修改的内容。
        8. 避免无关信息，如“我来帮您写一条求职消息”。
        9. 避免使用简历中与职位描述不匹配的信息。例如在软件测试相关职位中减少对简历中软件开发能力的描述的使用（比如“熟悉Spring Boot”）。如果职位描述和简历相关性不高（比如“电话销售职位”和软件开发工程师的简历），不要使用任何简历内容，使用相对泛用的语言。
        职位名称: {jd.name}
        职位描述: {jd.description}
        简历内容: {resume}
        """
        greet = self.send(prompt)
        if greet:
            greet = greet.replace("\n", "").replace("  ", "")
        return greet


if __name__ == "__main__":
    jd = JD()
    llm = LLM()
    jd.id = "test"
    jd.name = "测试"
    jd.description = "测试"
    print(llm.generate_greet(jd))
