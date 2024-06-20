import os
import httpx
from dotenv import load_dotenv
from loguru import logger
from jd import JD
from portkey_ai import Portkey


class LLM:
    default_greet = "您好，不知道这个岗位是否还有在招人，我仔细查看了您发布的职位信息，觉得自己比较适合，希望能得到您的回复"

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

    def generate_greet(self, jd: JD):
        with open("resume.txt", "r", encoding="utf-8") as file:
            context = file.read()
        prompt = f"""
        你正在作为求职者申请一个职位，请根据提供的简历和职位描述，撰写一条不超过120字的求职消息。需清晰、专业地描述你的优势。注意事项如下：
        1. 这是一条求职消息，不需要邮件格式。使用纯文本，不使用Markdown等标记语言，避免空行和换行。不得使用“*”等符号表示强调。
        2. 使用简体中文撰写消息，除英文技术词汇外谨慎使用其他语言。
        3. 避免透露详细个人信息，如姓名或个人经历。例如不要出现“我是一名”、“我是一位”等词汇。
        4. 开头如需使用称呼则使用“你好/您好”称呼对方，不添加其他敬语，也无需结束词。
        5. 避免经验和身份的描述，例如不需要“我是一名应届本科毕业生”、“我有3年经验”、“我是一位自动化测试工程师”这一类内容。
        6. 不得添加情绪化语言，如“非常高兴”。
        7. 消息需要一次完成，避免使用注释、转义字符、括号或中括号标注的内容，避免加入任何如"[工作名]"、"[你的名字]"等需要二次修改的内容。
        8. 只包含与求职直接相关的内容，避免无关信息，如“我来帮您写一条求职消息”。
        9. 开头要与众不同。不要使用职位名称和描述。
        10. 避免使用与简历或职位描述不匹配的信息。如果简历内容与职位描述难以匹配，则避免对简历内容的使用。例如在软件测试相关职位中减少对软件开发专用的描述（比如“熟悉Spring Boot、Spring Security”）的使用。如果职位是和简历相关性不高的职位（比如“电话销售”），不要参考简历内容，使用相对泛用的语言。
        11. 尽量少地引用项目经历内容和职位描述。
        12. 注意职位描述中的拼写错误，确保求职消息中无拼写错误。
        13. 吸引招聘者注意是第一目标，若有必要为此目标可以添加虚假/未知个人经历或能力。
        职位名称: {jd.name}
        职位描述: {jd.description}
        简历内容: {context}
        """
        greet = self.send(prompt)
        if greet:
            greet = greet.replace("\n", "").replace("  ", "")
        return greet or self.default_greet


if __name__ == "__main__":
    jd = JD()
    chat = LLM()
    jd.id = "test"
    jd.name = "测试"
    jd.description = "测试"
    print(chat.generate_greet(jd))
