#!/usr/bin/env python3
"""
特朗普Truth Social RSS订阅源爬取器
使用高质量的RSS数据源获取特朗普的官方帖子
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import re
from bs4 import BeautifulSoup
from logger import setup_logger, log_error, log_info, log_warning

logger = setup_logger()

class TrumpRSSScaper:
    def __init__(self):
        self.rss_url = "https://trumpstruth.org/feed"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml',
        })
    
    def get_latest_posts(self):
        """从RSS源获取最新帖子"""
        try:
            log_info(logger, f"正在从RSS源获取特朗普帖子: {self.rss_url}")
            
            response = self.session.get(self.rss_url, timeout=30)
            response.raise_for_status()
            
            # 解析RSS XML
            root = ET.fromstring(response.content)
            
            posts = []
            items = root.findall('.//item')
            
            log_info(logger, f"RSS源中找到 {len(items)} 个条目")
            
            for item in items:
                try:
                    post = self.parse_rss_item(item)
                    if post:
                        posts.append(post)
                except Exception as e:
                    log_warning(logger, f"解析RSS条目时出错: {e}")
                    continue
            
            log_info(logger, f"成功解析 {len(posts)} 个帖子")
            return posts
            
        except Exception as e:
            log_error(logger, f"获取RSS订阅失败: {e}")
            return []
    
    def parse_rss_item(self, item):
        """解析单个RSS条目"""
        try:
            # 获取基本信息
            title_elem = item.find('title')
            description_elem = item.find('description')
            link_elem = item.find('link')
            pub_date_elem = item.find('pubDate') or item.find('pubdate')
            guid_elem = item.find('guid')
            
            # 查找图片信息
            enclosure_elem = item.find('enclosure')
            media_content_elem = item.find('media:content')
            image_url = None
            
            if enclosure_elem is not None and enclosure_elem.get('type', '').startswith('image'):
                image_url = enclosure_elem.get('url')
            elif media_content_elem is not None:
                image_url = media_content_elem.get('url')
            
            if description_elem is None:
                return None
            
            # 提取内容
            title = title_elem.text if title_elem is not None else ""
            description = description_elem.text if description_elem is not None else ""
            
            # 如果RSS中没有图片，尝试从描述中提取图片链接
            if not image_url and description:
                import re
                # 查找img标签
                img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
                img_matches = re.findall(img_pattern, description)
                if img_matches:
                    image_url = img_matches[0]
                
                # 也尝试查找其他可能的图片URL模式
                url_patterns = [
                    r'https://[^\s<>"]+\.(?:jpg|jpeg|png|gif|webp)',
                    r'http://[^\s<>"]+\.(?:jpg|jpeg|png|gif|webp)'
                ]
                for pattern in url_patterns:
                    matches = re.findall(pattern, description, re.IGNORECASE)
                    if matches and not image_url:
                        image_url = matches[0]
            link = link_elem.text if link_elem is not None else ""
            pub_date = pub_date_elem.text if pub_date_elem is not None else ""
            guid = guid_elem.text if guid_elem is not None else ""
            
            # 清理HTML标签
            content = self.clean_html_content(description)
            
            # 如果标题不是默认的，添加到内容中
            if title and not title.startswith('[No Title]') and not title.startswith('REFORMING'):
                if len(title) > 20:  # 只有实际的标题才添加
                    content = f"{title}\n\n{content}"
            
            # 过滤空内容或纯链接的帖子
            if not content or len(content.strip()) < 10:
                return None
            
            # 解析发布时间
            timestamp = self.parse_publish_date(pub_date)
            
            # 如果RSS中的pub_date为空，尝试从网页抓取真实时间
            if not pub_date and guid:
                log_warning(logger, f"RSS条目缺少pub_date数据，GUID: {guid}")
                # 尝试从Truth Social页面获取真实时间
                real_time = self.extract_real_post_time(link)
                if real_time:
                    timestamp = real_time
                    log_info(logger, f"从页面获取到真实时间: {real_time}")
                else:
                    from datetime import datetime
                    timestamp = datetime.now().isoformat()
            
            # 格式化显示时间（洛杉矶时区）
            formatted_time = ""
            if timestamp:
                try:
                    import pytz
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    la_tz = pytz.timezone('America/Los_Angeles')
                    la_time = dt.astimezone(la_tz)
                    formatted_time = la_time.strftime("%Y年%m月%d日 %H:%M (洛杉矶时间)")
                except:
                    formatted_time = ""
            
            # 生成帖子ID
            post_id = self.generate_post_id(guid, content)
            
            post = {
                'id': post_id,
                'content': content.strip(),
                'timestamp': timestamp,
                'publish_date': timestamp,
                'formatted_time': formatted_time,
                'source': 'truth_social_rss',
                'link': link,
                'post_url': link,
                'guid': guid
            }
            
            # 暂时禁用图片提取功能
            # if not image_url and link:
            #     image_url = self.extract_image_from_post_page(link)
            
            # 添加图片信息（如果有的话）
            if image_url:
                post['image'] = image_url
            
            return post
            
        except Exception as e:
            log_error(logger, f"解析RSS条目失败: {e}")
            return None
    
    def clean_html_content(self, html_content):
        """清理HTML内容，保持链接格式"""
        try:
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 处理链接，文字和链接在同一行，但每个条目分行
            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    # 获取ellipsis部分的文本用于显示
                    ellipsis_span = link.find('span', class_='ellipsis')
                    if ellipsis_span:
                        display_text = ellipsis_span.get_text() + "......"
                        # 创建格式：文字和链接在同一行
                        link.replace_with(f" [{display_text}]({href})")
                    else:
                        # 如果没有ellipsis，显示完整链接
                        link.replace_with(f" [{href}]({href})")
            
            # 处理段落换行 - 替换为内容而不是添加标签文本
            for p in soup.find_all('p'):
                p.unwrap()
            
            # 获取文本并保持原始格式
            text = soup.get_text()
            
            # 清理多余空格但保持换行
            lines = []
            for line in text.split('\n'):
                cleaned_line = re.sub(r'\s+', ' ', line).strip()
                if cleaned_line:
                    lines.append(cleaned_line)
            
            text = '\n\n'.join(lines)
            
            # 移除一些常见的RSS标记
            patterns_to_remove = [
                r'\[CDATA\[',
                r'\]\]',
                r'RT:\s*https://\S+',  # 转发链接
            ]
            
            for pattern in patterns_to_remove:
                text = re.sub(pattern, '', text)
            
            return text.strip()
            
        except Exception as e:
            log_warning(logger, f"清理HTML内容时出错: {e}")
            return html_content
    
    def parse_publish_date(self, pub_date_str):
        """解析RSS发布时间"""
        try:
            if not pub_date_str:
                return datetime.now().isoformat()
            
            # 清理可能的CDATA标签
            pub_date_str = pub_date_str.replace('<![CDATA[', '').replace(']]>', '').strip()
            
            # RSS日期格式: Sun, 25 May 2025 04:15:44 +0000
            try:
                dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                return dt.isoformat()
            except ValueError:
                # 尝试其他可能的格式
                formats = [
                    "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%d %H:%M:%S %z",
                    "%a, %d %b %Y %H:%M:%S %Z"
                ]
                for fmt in formats:
                    try:
                        dt = datetime.strptime(pub_date_str, fmt)
                        return dt.isoformat()
                    except ValueError:
                        continue
                
                # 如果所有格式都失败，记录详细信息
                log_warning(logger, f"无法解析时间格式: {pub_date_str}")
                return datetime.now().isoformat()
            
        except Exception as e:
            log_warning(logger, f"解析发布时间失败: {pub_date_str}, 错误: {e}")
            return datetime.now().isoformat()
    
    def generate_post_id(self, guid, content):
        """生成帖子ID"""
        if guid:
            # 从GUID中提取数字ID
            guid_match = re.search(r'/statuses/(\d+)', guid)
            if guid_match:
                return f"rss_post_{guid_match.group(1)}"
        
        # 备用方案：使用内容哈希
        content_hash = abs(hash(content[:100]))
        return f"rss_post_{content_hash}"
    
    def extract_real_post_time(self, post_url):
        """从Truth Social帖子页面提取真实发布时间"""
        try:
            response = requests.get(post_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 查找时间相关的元素
                time_patterns = [
                    'time[datetime]',
                    '[data-testid*="time"]',
                    '.timestamp',
                    '.post-time',
                    '.created-at',
                    'time'
                ]
                
                for pattern in time_patterns:
                    time_elem = soup.select_one(pattern)
                    if time_elem:
                        datetime_attr = time_elem.get('datetime')
                        if datetime_attr:
                            log_info(logger, f"找到页面时间戳: {datetime_attr}")
                            return datetime_attr
                        
                        time_text = time_elem.get_text().strip()
                        if time_text and ('AM' in time_text or 'PM' in time_text):
                            log_info(logger, f"找到页面时间文本: {time_text}")
                            return self._parse_page_time(time_text)
                
                # 在页面HTML中搜索时间模式
                page_html = str(soup)
                
                # 搜索ISO时间格式
                iso_pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[Z\+\-]\d{0,4})'
                iso_matches = re.findall(iso_pattern, page_html)
                if iso_matches:
                    log_info(logger, f"在HTML中找到ISO时间: {iso_matches[0]}")
                    return iso_matches[0]
                
                # 搜索美式时间格式
                us_time_pattern = r'([A-Za-z]{3}\s+\d{1,2},\s+\d{4}\s+·\s+\d{1,2}:\d{2}\s+[AP]M)'
                us_matches = re.findall(us_time_pattern, page_html)
                if us_matches:
                    log_info(logger, f"在HTML中找到美式时间: {us_matches[0]}")
                    return self._parse_page_time(us_matches[0])
                        
        except Exception as e:
            log_warning(logger, f"提取页面时间失败 {post_url}: {e}")
        
        return None
    
    def _parse_page_time(self, time_text):
        """解析页面时间文本"""
        try:
            # 常见格式
            formats = [
                '%b %d, %Y · %I:%M %p',  # May 24, 2025 · 8:30 AM
                '%B %d, %Y · %I:%M %p',  # May 24, 2025 · 8:30 AM
                '%m/%d/%Y %I:%M %p',     # 5/24/2025 8:30 AM
                '%Y-%m-%dT%H:%M:%S%z',   # ISO format
                '%Y-%m-%dT%H:%M:%SZ'     # ISO format with Z
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(time_text, fmt)
                    # 转换为UTC时区
                    if dt.tzinfo is None:
                        # 假设是洛杉矶时间
                        from datetime import timezone, timedelta
                        la_tz = timezone(timedelta(hours=-8))
                        dt = dt.replace(tzinfo=la_tz)
                    return dt.isoformat()
                except ValueError:
                    continue
                    
        except Exception as e:
            log_warning(logger, f"解析页面时间失败: {e}")
        
        return None

def test_trump_rss():
    """测试特朗普RSS爬取器"""
    scraper = TrumpRSSScaper()
    
    log_info(logger, "开始测试特朗普Truth Social RSS爬取...")
    
    posts = scraper.get_latest_posts()
    
    if posts:
        log_info(logger, f"✅ 成功获取到 {len(posts)} 个帖子")
        
        for i, post in enumerate(posts[:3]):  # 显示前3个
            log_info(logger, f"帖子 {i+1}:")
            log_info(logger, f"  ID: {post['id']}")
            log_info(logger, f"  时间: {post['timestamp']}")
            log_info(logger, f"  内容: {post['content'][:100]}...")
            log_info(logger, f"  链接: {post['link']}")
            print()
    else:
        log_warning(logger, "❌ 没有获取到任何帖子")

def test_trump_rss():
    """测试特朗普RSS爬取器"""
    scraper = TrumpRSSScaper()
    posts = scraper.get_latest_posts()
    
    if posts:
        log_info(logger, f"✅ 成功获取到 {len(posts)} 个帖子")
        for i, post in enumerate(posts[:3]):
            log_info(logger, f"帖子 {i+1}:")
            log_info(logger, f"  ID: {post['id']}")
            log_info(logger, f"  时间: {post['timestamp']}")
            log_info(logger, f"  内容: {post['content'][:100]}...")
            log_info(logger, f"  链接: {post['link']}")
            print()
    else:
        log_warning(logger, "❌ 没有获取到任何帖子")

    def extract_image_from_post_page(self, post_url):
        """从Truth Social帖子页面提取图片URL"""
        try:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(post_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找各种可能的图片元素
            image_selectors = [
                'meta[property="og:image"]',  # OpenGraph图片 - 优先
                'img[src*="media"]',
                'img[src*="image"]', 
                'img[src*="photo"]',
                '.post-content img',
                '.media-wrapper img',
                'img[alt*="Image"]',
                'img'  # 最后尝试所有img标签
            ]
            
            for selector in image_selectors:
                if selector.startswith('meta'):
                    # 处理meta标签
                    meta = soup.select_one(selector)
                    if meta:
                        content = meta.get('content')
                        if content and self._is_valid_image_url(content):
                            log_info(logger, f"从meta标签找到图片: {content}")
                            return self._normalize_image_url(content)
                else:
                    # 处理img标签
                    imgs = soup.select(selector)
                    for img in imgs:
                        src = img.get('src') or img.get('data-src')
                        if src and self._is_valid_image_url(src):
                            normalized_url = self._normalize_image_url(src)
                            log_info(logger, f"找到图片: {normalized_url}")
                            return normalized_url
                            
        except Exception as e:
            log_error(logger, f"提取图片失败 {post_url}: {str(e)}")
            
        return None
    
    def _is_valid_image_url(self, url):
        """检查URL是否是有效的图片链接"""
        if not url:
            return False
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        url_lower = url.lower()
        
        # 检查文件扩展名或包含图片相关关键词
        return (any(ext in url_lower for ext in image_extensions) or
                'media' in url_lower or 
                'image' in url_lower or
                'photo' in url_lower)
    
    def _normalize_image_url(self, url):
        """标准化图片URL"""
        if url.startswith('http'):
            return url
        elif url.startswith('//'):
            return 'https:' + url
        elif url.startswith('/'):
            return 'https://trumpstruth.org' + url
        else:
            return 'https://trumpstruth.org/' + url

if __name__ == "__main__":
    test_trump_rss()