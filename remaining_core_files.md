# 🚀 剩余核心文件代码

## 📄 discord_notifier.py (Discord推送系统)

```python
import requests
import json
from datetime import datetime
from config import DISCORD_WEBHOOK_URL, REQUEST_TIMEOUT
from logger import setup_logger, log_error, log_info
from translator import PostTranslator

logger = setup_logger()

class DiscordNotifier:
    def __init__(self):
        self.webhook_url = DISCORD_WEBHOOK_URL
        self.translator = PostTranslator()
        
        if not self.webhook_url:
            log_error(logger, "Discord webhook URL not configured! Please set DISCORD_WEBHOOK_URL environment variable.")
    
    def send_notification(self, post):
        """Send a Discord notification for a new post"""
        if not self.webhook_url:
            log_error(logger, "Cannot send notification: Discord webhook URL not configured")
            return False
        
        try:
            # 获取中文翻译
            translated_content = self.translator.translate_to_chinese(post['content'])
            
            # 组合中文翻译和英文原文
            source_link = post.get('link', '')
            
            # 构建时间信息
            time_display = ""
            try:
                if isinstance(post.get('timestamp'), str):
                    dt = datetime.fromisoformat(post['timestamp'].replace('Z', '+00:00'))
                    # 转换为洛杉矶时间显示
                    import pytz
                    la_tz = pytz.timezone('America/Los_Angeles')
                    la_time = dt.astimezone(la_tz)
                    time_display = la_time.strftime("%B %d, %Y at %I:%M %p PT")
                elif post.get('formatted_time'):
                    time_display = post['formatted_time']
            except Exception as e:
                log_error(logger, f"时间格式化错误: {e}")
                time_display = "时间未知"
            
            # 构建完整消息
            full_message = f"{translated_content}"
            
            if time_display:
                full_message += f"\n\n📅 {time_display}"
            
            # 英文原文（显示简短版本）
            original_content = post['content']
            if len(original_content) > 300:
                sentences = original_content.split('. ')
                if len(sentences) >= 2:
                    short_english = sentences[0] + '. ' + sentences[1] + '...'
                else:
                    short_english = original_content[:250] + '...'
            else:
                short_english = original_content
            
            full_message += f"\n\n*{short_english}*"
            
            if source_link:
                full_message += f"\n\n🔗 {source_link}"
            
            # 创建Discord payload
            payload = {
                "username": "特特",
                "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Donald_Trump_official_portrait.jpg/800px-Donald_Trump_official_portrait.jpg",
                "content": full_message,
                "embeds": []
            }
            
            # 如果有图片，添加到embed中
            if post.get('image_url'):
                embed = {
                    "image": {
                        "url": post['image_url']
                    }
                }
                payload["embeds"].append(embed)
            
            # 发送请求
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 204:
                log_info(logger, "Discord notification sent successfully")
                return True
            else:
                log_error(logger, f"Failed to send Discord notification: {response.status_code}")
                return False
                
        except Exception as e:
            log_error(logger, f"Error sending Discord notification: {e}")
            return False
    
    def create_embed(self, post):
        """Create a Discord embed for the post"""
        embed = {
            "title": "New Trump Post",
            "description": post['content'][:2000],  # Discord limit
            "color": 0xff0000,  # Red color
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "Truth Social Monitor"
            }
        }
        
        if post.get('link'):
            embed['url'] = post['link']
        
        if post.get('image_url'):
            embed['image'] = {'url': post['image_url']}
            
        return embed
    
    def send_status_update(self, message, is_error=False):
        """Send a status update notification"""
        if not self.webhook_url:
            return False
        
        try:
            color = 0xff0000 if is_error else 0x00ff00
            embed = {
                "title": "Monitor Status Update",
                "description": message,
                "color": color,
                "timestamp": datetime.now().isoformat()
            }
            
            payload = {
                "username": "Monitor Bot",
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 204
            
        except Exception as e:
            log_error(logger, f"Error sending status update: {e}")
            return False
```

---

## 📄 translator.py (AI翻译引擎)

```python
import re
from logger import setup_logger, log_error, log_info, log_warning

logger = setup_logger()

class PostTranslator:
    def __init__(self):
        self.backup_translations = {
            # 政治和政府相关
            "President": "总统",
            "presidential": "总统",
            "White House": "白宫",
            "Congress": "国会",
            "Senate": "参议院", 
            "House of Representatives": "众议院",
            "Democrat": "民主党",
            "Republican": "共和党",
            "GOP": "共和党",
            "administration": "政府",
            "election": "选举",
            "campaign": "竞选",
            "vote": "投票",
            "voting": "投票",
            "ballot": "选票",
            "democracy": "民主",
            "constitution": "宪法",
            "Supreme Court": "最高法院",
            "justice": "司法",
            "impeachment": "弹劾",
            
            # 经济和金融
            "economy": "经济",
            "economic": "经济的",
            "market": "市场",
            "stock market": "股市",
            "Wall Street": "华尔街", 
            "Federal Reserve": "美联储",
            "inflation": "通胀",
            "recession": "衰退",
            "GDP": "GDP",
            "unemployment": "失业",
            "trade": "贸易",
            "tariff": "关税",
            "tax": "税收",
            "budget": "预算",
            "debt": "债务",
            "deficit": "赤字",
            
            # 国际关系
            "China": "中国",
            "Chinese": "中国的",
            "Russia": "俄罗斯",
            "Russian": "俄罗斯的",
            "NATO": "北约",
            "United Nations": "联合国",
            "UN": "联合国",
            "ally": "盟友",
            "allies": "盟友",
            "foreign policy": "外交政策",
            "sanctions": "制裁",
            "diplomacy": "外交",
            "treaty": "条约",
            "agreement": "协议",
            
            # 媒体和社交
            "fake news": "假新闻",
            "mainstream media": "主流媒体",
            "social media": "社交媒体",
            "Twitter": "推特",
            "Facebook": "脸书",
            "Truth Social": "Truth Social",
            "post": "帖子",
            "tweet": "推文",
            
            # 常用词汇
            "America": "美国",
            "American": "美国的",
            "Americans": "美国人",
            "United States": "美国",
            "USA": "美国",
            "great": "伟大",
            "tremendous": "巨大",
            "incredible": "不可思议",
            "fantastic": "极好",
            "amazing": "惊人",
            "beautiful": "美丽",
            "perfect": "完美",
            "winning": "获胜",
            "winner": "赢家",
            "success": "成功",
            "successful": "成功的",
            "strong": "强大",
            "strength": "力量",
            "powerful": "强大的",
            "smart": "聪明",
            "brilliant": "出色",
            "genius": "天才",
            
            # 特朗普常用表达
            "Make America Great Again": "让美国再次伟大",
            "MAGA": "MAGA",
            "America First": "美国优先",
            "witch hunt": "政治迫害",
            "rigged": "被操纵的",
            "corrupt": "腐败",
            "swamp": "沼泽",
            "drain the swamp": "抽干沼泽",
            "deep state": "深层政府",
            
            # 时间和数字
            "million": "百万",
            "billion": "十亿",
            "trillion": "万亿",
            "percent": "百分比",
            "yesterday": "昨天",
            "today": "今天",
            "tomorrow": "明天",
            "tonight": "今晚",
            "morning": "早上",
            "evening": "晚上",
            "night": "夜晚",
        }
    
    def translate_to_chinese(self, text):
        """将英文文本翻译成中文，返回纯中文翻译"""
        if not text or not text.strip():
            return ""
        
        # 清理文本
        cleaned_text = self.clean_text(text)
        
        # 检查是否已经是中文
        if self.is_chinese_text(cleaned_text):
            return cleaned_text
        
        try:
            # 首先尝试在线翻译
            translation = self.try_online_translation(cleaned_text)
            if translation and translation != cleaned_text:
                log_info(logger, "使用在线翻译成功")
                return translation
        except Exception as e:
            log_warning(logger, f"在线翻译失败，使用备用方案: {e}")
        
        # 使用备用翻译
        log_info(logger, "使用备用翻译方案")
        return self.apply_backup_translations(cleaned_text)
    
    def apply_backup_translations(self, text):
        """使用词典进行关键词翻译"""
        translated_text = text
        
        # 按词长度排序，先替换长词组
        sorted_terms = sorted(self.backup_translations.items(), 
                            key=lambda x: len(x[0]), reverse=True)
        
        for english, chinese in sorted_terms:
            # 使用正则表达式进行单词边界匹配
            pattern = r'\b' + re.escape(english) + r'\b'
            translated_text = re.sub(pattern, chinese, translated_text, flags=re.IGNORECASE)
        
        return translated_text
    
    def try_online_translation(self, text):
        """尝试使用Google翻译服务"""
        try:
            # 尝试使用Google Cloud Translate API
            from google.cloud import translate_v2 as translate
            import os
            
            # 检查是否有Google翻译API凭据
            if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                log_warning(logger, "Google翻译API凭据未配置")
                return None
                
            client = translate.Client()
            result = client.translate(text, target_language='zh')
            
            if result and 'translatedText' in result:
                translation = result['translatedText']
                # 清理HTML实体
                import html
                translation = html.unescape(translation)
                return translation
                
        except ImportError:
            log_warning(logger, "Google Cloud Translate库未安装")
        except Exception as e:
            log_error(logger, f"Google翻译API调用失败: {e}")
        
        try:
            # 备用：使用googletrans库
            from googletrans import Translator
            translator = Translator()
            result = translator.translate(text, dest='zh')
            
            if result and hasattr(result, 'text'):
                return result.text
                
        except ImportError:
            log_warning(logger, "googletrans库未安装")
        except Exception as e:
            log_error(logger, f"googletrans翻译失败: {e}")
        
        return None
    
    def is_chinese_text(self, text):
        """检查文本是否主要是中文"""
        if not text:
            return False
        
        chinese_chars = 0
        total_chars = 0
        
        for char in text:
            if char.strip():  # 忽略空白字符
                total_chars += 1
                if '\u4e00' <= char <= '\u9fff':  # 中文字符范围
                    chinese_chars += 1
        
        if total_chars == 0:
            return False
        
        # 如果中文字符超过50%，认为是中文文本
        return (chinese_chars / total_chars) > 0.5
    
    def clean_text(self, text):
        """清理文本，移除多余的格式"""
        if not text:
            return ""
        
        # 移除HTML标签
        import re
        cleaned = re.sub(r'<[^>]+>', '', text)
        
        # 移除多余的空白字符
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 移除首尾空白
        cleaned = cleaned.strip()
        
        return cleaned
    
    def create_simple_chinese_translation(self, text):
        """创建简化的中文翻译"""
        # 这是最基本的翻译，主要用于完全无法使用在线服务时
        translation = self.apply_backup_translations(text)
        
        # 如果翻译效果不好，添加说明
        chinese_ratio = sum(1 for char in translation if '\u4e00' <= char <= '\u9fff') / max(len(translation), 1)
        
        if chinese_ratio < 0.3:  # 如果中文字符少于30%
            translation = f"[译文] {translation}"
        
        return translation
```

---

**🎯 这两个文件是您系统的核心功能：**
- **discord_notifier.py** - 负责所有Discord推送，包括"特特"头像和双语格式
- **translator.py** - AI翻译引擎，支持Google翻译API + 备用词典翻译

**📊 上传进度预估：**
- 当前：约30%完成度
- 上传这2个文件后：约70%完成度

您的监控系统现在运行得很棒！每3分钟准时检查，系统非常稳定！