# 🔥 关键缺失文件代码

## 📄 main.py (监控系统核心逻辑)

```python
import schedule
import time
from datetime import datetime
from trump_rss_scraper import TrumpRSSScaper
from discord_notifier import DiscordNotifier
from storage import PostStorage
from logger import setup_logger, log_info, log_error

logger = setup_logger()

class TruthSocialMonitor:
    def __init__(self):
        self.scraper = TrumpRSSScaper()
        self.notifier = DiscordNotifier()
        self.storage = PostStorage()
        
    def check_for_new_posts(self):
        """Check for new posts and send notifications"""
        try:
            log_info(logger, "Checking for new Trump posts...")
            
            # Get latest posts from RSS
            posts = self.scraper.get_latest_posts()
            
            if not posts:
                log_info(logger, "No posts found from RSS feed")
                return
            
            # Check for new posts
            last_post_id = self.storage.get_last_post_id()
            new_posts = []
            
            for post in posts:
                if last_post_id is None or post['id'] != last_post_id:
                    new_posts.append(post)
                else:
                    break
            
            if new_posts:
                log_info(logger, f"Found {len(new_posts)} new posts")
                
                # Send notifications for new posts (in reverse order - oldest first)
                for post in reversed(new_posts):
                    success = self.notifier.send_notification(post)
                    if success:
                        log_info(logger, f"Sent notification for post: {post['id']}")
                    time.sleep(2)  # Rate limiting
                
                # Update last post ID
                if new_posts:
                    self.storage.set_last_post_id(new_posts[0]['id'])
                    
            else:
                log_info(logger, "No new posts found")
                
        except Exception as e:
            log_error(logger, f"Error checking for new posts: {e}")
    
    def run_monitor(self):
        """Run the monitoring job"""
        self.check_for_new_posts()
        
    def start(self):
        """Start the monitoring service"""
        log_info(logger, "Starting Truth Social Monitor...")
        
        # Schedule the monitoring job every 3 minutes
        schedule.every(3).minutes.do(self.run_monitor)
        
        # Run initial check
        self.run_monitor()
        
        log_info(logger, "Monitor started. Press Ctrl+C to stop.")
        
        # Keep the program running
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
```

---

## 📄 config.py (系统配置)

```python
import os

# Discord configuration
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
FEAR_GREED_WEBHOOK_URL = os.getenv('FEAR_GREED_WEBHOOK_URL')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Request timeout
REQUEST_TIMEOUT = 30

# Check interval (minutes)
CHECK_INTERVAL = 3

# RSS Feed URL
RSS_FEED_URL = "https://trumpstruth.org/feed"

# Google Translation
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
```

---

## 📄 logger.py (日志系统)

```python
import logging
import os

def setup_logger():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )
    return logging.getLogger(__name__)

def log_error(logger, message, exception=None):
    """Log error with optional exception details"""
    if exception:
        logger.error(f"{message}: {str(exception)}")
    else:
        logger.error(message)

def log_info(logger, message):
    """Log info message"""
    logger.info(message)

def log_warning(logger, message):
    """Log warning message"""
    logger.warning(message)
```

---

## 📄 storage.py (数据存储)

```python
import json
import os
from datetime import datetime
from logger import setup_logger, log_error, log_info

logger = setup_logger()

class PostStorage:
    def __init__(self, storage_file="last_post.json"):
        self.storage_file = storage_file
        self.data = self.load_data()
    
    def load_data(self):
        """Load data from storage file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            log_error(logger, f"Error loading storage data: {e}")
        
        return {
            'last_post_id': None,
            'last_updated': None,
            'processed_posts': []
        }
    
    def save_data(self):
        """Save data to storage file"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log_error(logger, f"Error saving storage data: {e}")
    
    def get_last_post_id(self):
        """Get the ID of the last checked post"""
        return self.data.get('last_post_id')
    
    def set_last_post_id(self, post_id):
        """Set the ID of the last checked post"""
        self.data['last_post_id'] = post_id
        self.data['last_updated'] = datetime.now().isoformat()
        self.save_data()
    
    def get_last_updated(self):
        """Get the timestamp of last update"""
        return self.data.get('last_updated')
```

---

**🎯 上传这4个文件后，您就有了完整的监控系统基础架构！**

**📊 您的监控系统现在运行得很稳定 - 每3分钟检查新推文，状态良好！**