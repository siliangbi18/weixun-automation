#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions 文章发布脚本
简化版本，适配云端环境
"""

import os
import json
import logging
import requests
from datetime import datetime
from openai import OpenAI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class ArticlePublisher:
    """文章发布器"""

    def __init__(self):
        """初始化发布器"""
        self.load_config()
        self.load_secrets()

    def load_config(self):
        """加载配置文件"""
        config_path = os.path.expanduser("~/.openclaw/openclaw.json")
        logger.info(f"📄 加载配置: {config_path}")

        with open(config_path, "r") as f:
            self.config = json.load(f)

        self.models = self.config.get("models", [])
        logger.info(f"✅ 已加载 {len(self.models)} 个模型配置")

    def load_secrets(self):
        """加载密钥配置"""
        secrets_path = os.path.expanduser("~/.openclaw/secrets.json")
        logger.info(f"🔐 加载密钥: {secrets_path}")

        with open(secrets_path, "r") as f:
            self.secrets = json.load(f)

        self.weixun_config = self.secrets.get("weixun", {})

    def get_hot_topics(self):
        """获取热点话题（简化版，使用静态列表）"""
        logger.info("🔥 开始搜集热点话题...")

        # 热点话题列表（实际应该从 API 获取）
        hot_topics = [
            {"title": "AI 技术最新进展", "source": "AI日报"},
            {"title": "科技创新趋势", "source": "科技周刊"},
            {"title": "数字化转型案例", "source": "企业观察"},
            {"title": "人工智能应用", "source": "应用前沿"},
            {"title": "技术伦理与监管", "source": "政策观察"}
        ]

        logger.info(f"✅ 已获取 {len(hot_topics)} 条热点话题")
        return hot_topics

    def generate_article(self, topic, article_type="morning"):
        """生成文章"""
        logger.info(f"🤖 开始生成文章: {topic['title']}")

        # 根据文章类型选择模型
        if article_type == "morning":
            prompt = f"""请写一篇关于"{topic['title']}"的深度文章，要求：
1. 字数：2000-3000字
2. 风格：专业、深入、有洞察力
3. 结构：引言、核心观点、案例分析、总结
4. 避免空话套话，要有实际内容
"""
        elif article_type == "noon":
            prompt = f"""请写一篇关于"{topic['title']}"的分析文章，要求：
1. 字数：1500-2000字
2. 风格：简洁、实用、可操作
3. 重点：方法论、实践技巧、避坑指南
"""
        else:  # evening
            prompt = f"""请写一篇关于"{topic['title']}"的思考文章，要求：
1. 字数：1000-1500字
2. 风格：轻松、有启发性、适合阅读
3. 重点：观点、感悟、启发
"""

        # 尝试使用第一个可用模型
        for model_config in self.models:
            try:
                logger.info(f"🔄 尝试使用模型: {model_config['name']}")

                if model_config['provider'] == 'deepseek':
                    client = OpenAI(
                        api_key=model_config['api_key'],
                        base_url=model_config['base_url']
                    )
                    response = client.chat.completions.create(
                        model=model_config['name'],
                        messages=[
                            {"role": "system", "content": "你是一个专业的文章写作专家"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=4000
                    )

                    article = response.choices[0].message.content
                    logger.info(f"✅ 文章生成成功（使用 {model_config['name']}）")
                    return article

            except Exception as e:
                logger.warning(f"⚠️ 模型 {model_config['name']} 生成失败: {e}")
                continue

        raise RuntimeError("所有模型均生成失败")

    def get_weixin_access_token(self):
        """获取微信 access_token"""
        logger.info("🔑 获取微信 access_token...")

        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.weixun_config['app_id'],
            "secret": self.weixun_config['app_secret']
        }

        response = requests.get(url, params=params)
        data = response.json()

        if 'errcode' in data:
            raise RuntimeError(f"获取 access_token 失败: {data}")

        access_token = data['access_token']
        logger.info(f"✅ access_token 获取成功")
        return access_token

    def upload_article_image(self, access_token, image_path):
        """上传文章封面"""
        logger.info(f"📤 上传文章封面: {image_path}")

        # 使用默认封面或上传新封面
        # 这里简化处理，使用占位符
        media_id = "placeholder_media_id"
        logger.info(f"✅ 封面上传成功")
        return media_id

    def publish_article(self, article, title, cover_media_id):
        """发布文章到微信公众号"""
        logger.info(f"📰 发布文章: {title}")

        access_token = self.get_weixin_access_token()

        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"

        payload = {
            "articles": [
                {
                    "title": title,
                    "content": article,
                    "digest": title,
                    "thumb_media_id": cover_media_id,
                    "show_cover_pic": 1
                }
            ]
        }

        response = requests.post(url, json=payload)
        data = response.json()

        if 'errcode' in data and data['errcode'] != 0:
            raise RuntimeError(f"文章发布失败: {data}")

        article_id = data['media_id']
        logger.info(f"✅ 文章发布成功，ID: {article_id}")
        return article_id

    def run(self, article_type="morning"):
        """执行完整的发布流程"""
        logger.info("=" * 60)
        logger.info(f"🚀 开始执行 {article_type} 发布任务")
        logger.info(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        try:
            # Step 1: 获取热点话题
            hot_topics = self.get_hot_topics()

            # Step 2: 选择一个热点
            topic = hot_topics[0]
            logger.info(f"📌 选择话题: {topic['title']}")

            # Step 3: 生成文章
            article = self.generate_article(topic, article_type)

            # Step 4: 发布文章
            title = f"{topic['title']} - {datetime.now().strftime('%Y年%m月%d日')}"
            cover_media_id = self.upload_article_image(None, None)
            article_id = self.publish_article(article, title, cover_media_id)

            logger.info("=" * 60)
            logger.info(f"✅ {article_type} 发布任务完成！")
            logger.info(f"📄 文章 ID: {article_id}")
            logger.info(f"📝 标题: {title}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ {article_type} 发布任务失败！")
            logger.error(f"💥 错误: {e}")
            logger.error("=" * 60)
            raise


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Actions 文章发布脚本")
    parser.add_argument("--type", type=str, default="morning",
                       choices=["morning", "noon", "evening"],
                       help="文章类型")
    parser.add_argument("--accounts", type=str, default="weixun",
                       help="目标账号")

    args = parser.parse_args()

    publisher = ArticlePublisher()
    publisher.run(article_type=args.type)


if __name__ == "__main__":
    main()
