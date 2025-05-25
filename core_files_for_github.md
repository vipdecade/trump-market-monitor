# 🚀 GitHub上传核心文件代码

## 📋 文件1: run.py

```python
#!/usr/bin/env python3
"""
Trump Truth Social Monitor
Monitors Trump's Truth Social posts and sends Discord notifications

Usage:
    python run.py

Environment Variables:
    DISCORD_WEBHOOK_URL - Discord webhook URL for notifications (required)

Author: Truth Social Monitor
"""

import sys
import os
from main import TruthSocialMonitor
from logger import setup_logger, log_info, log_error

def check_environment():
    """Check if required environment variables are set"""
    logger = setup_logger()
    
    required_vars = ['DISCORD_WEBHOOK_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        log_error(logger, f"Missing required environment variables: {', '.join(missing_vars)}")
        log_error(logger, "Please set the following environment variables:")
        log_error(logger, "  DISCORD_WEBHOOK_URL - Your Discord webhook URL")
        return False
    
    log_info(logger, "Environment check passed")
    return True

def main():
    """Main entry point"""
    logger = setup_logger()
    
    print("=" * 60)
    print("🚨 TRUMP TRUTH SOCIAL MONITOR 🚨")
    print("=" * 60)
    print("Monitoring Trump's Truth Social posts every 5 minutes")
    print("Sending notifications to Discord")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed!")
        print("Please set the required environment variables and try again.")
        sys.exit(1)
    
    try:
        # Start the monitor
        monitor = TruthSocialMonitor()
        monitor.start()
        
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped by user")
        log_info(logger, "Monitor stopped gracefully")
        
    except Exception as e:
        print(f"\n\n💥 Monitor crashed: {str(e)}")
        log_error(logger, "Monitor crashed", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## 📋 文件2: config.py

```python
import os

# Discord configuration
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Request timeout
REQUEST_TIMEOUT = 30

# Check interval (minutes)
CHECK_INTERVAL = 3

# RSS Feed URL
RSS_FEED_URL = "https://trumpstruth.org/feed"
```

---

## 📋 文件3: logger.py

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

## 📋 文件4: storage.py

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

**💡 上传步骤：**
1. 访问：https://github.com/vipdecade/trump-market-monitor
2. 对每个文件：点击 "Add file" → "Create new file"
3. 输入文件名（如 `run.py`）
4. 复制对应的代码
5. 点击 "Commit new file"

这4个文件是系统的基础框架！您想要我继续显示其他文件吗？