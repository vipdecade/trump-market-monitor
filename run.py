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
