import hashlib
import json
import os
import requests
import smtplib
from datetime import datetime

def debug_environment():
    """Debug environment variables and configuration"""
    print("=== DEBUGGING ENVIRONMENT ===")
    
    # Check required environment variables
    required_vars = ['WEBSITES_TO_MONITOR', 'SENDER_EMAIL', 'SENDER_PASSWORD', 'RECEIVER_EMAIL']
    optional_vars = ['SMTP_SERVER', 'SMTP_PORT', 'DISCORD_WEBHOOK_URL']
    
    print("Required variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Don't print sensitive data, just confirm it exists
            if 'PASSWORD' in var or 'WEBHOOK' in var:
                print(f"✓ {var}: [SET - {len(value)} chars]")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: NOT SET")
    
    print("\nOptional variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var or 'WEBHOOK' in var:
                print(f"✓ {var}: [SET - {len(value)} chars]")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"- {var}: Not set (using default)")
    
    print("=" * 30)

def get_page_hash(url):
    """Get SHA256 hash of webpage content with detailed error reporting"""
    try:
        print(f"Fetching: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status code: {response.status_code}")
        response.raise_for_status()
        
        content_length = len(response.text)
        print(f"Content length: {content_length} characters")
        
        page_hash = hashlib.sha256(response.text.encode()).hexdigest()
        print(f"Hash: {page_hash[:16]}...")
        return page_hash
        
    except requests.exceptions.Timeout:
        print(f"✗ Timeout error for {url}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"✗ Connection error for {url}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP error for {url}: {e}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error for {url}: {str(e)}")
        return None

def load_previous_hashes():
    """Load previous hashes from file with error handling"""
    try:
        if os.path.exists('website_hashes.json'):
            with open('website_hashes.json', 'r') as f:
                data = json.load(f)
                print(f"Loaded {len(data)} previous hashes")
                return data
        else:
            print("No previous hashes file found (first run)")
            return {}
    except Exception as e:
        print(f"Error loading previous hashes: {str(e)}")
        return {}

def save_hashes(hashes):
    """Save current hashes to file with error handling"""
    try:
        with open('website_hashes.json', 'w') as f:
            json.dump(hashes, f, indent=2)
        print(f"Saved {len(hashes)} hashes to file")
    except Exception as e:
        print(f"Error saving hashes: {str(e)}")

def test_email_connection():
    """Test email connection without sending"""
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        
        print(f"Testing email connection to {smtp_server}:{smtp_port}")
        print(f"Sender email: {sender_email}")
        
        if not sender_email or not sender_password:
            print("✗ Email credentials missing")
            return False
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.quit()
        
        print("✓ Email connection successful")
        return True
        
    except Exception as e:
        print(f"✗ Email connection failed: {str(e)}")
        return False

def send_email_notification(changed_sites):
    """Send email notification for changed websites using simple SMTP"""
    try:
        # Email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        receiver_email = os.getenv('RECEIVER_EMAIL')
        
        if not all([sender_email, sender_password, receiver_email]):
            print("✗ Email credentials not configured properly")
            return False
        
        # Create simple email message
        subject = f"Website Changes Detected - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        body = "The following websites have changed:\n\n"
        for site in changed_sites:
            body += f"• {site}\n"
        
        body += f"\nCheck performed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        # Create email message string
        message = f"""From: {sender_email}
To: {receiver_email}
Subject: {subject}

{body}"""
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message)
        server.quit()
        
        print(f"✓ Email notification sent for {len(changed_sites)} changed sites")
        return True
        
    except Exception as e:
        print(f"✗ Error sending email: {str(e)}")
        return False

def send_discord_notification(changed_sites):
    """Send Discord notification via webhook"""
    try:
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if not webhook_url:
            print("Discord webhook not configured (optional)")
            return True
        
        message = f"🔔 **Website Changes Detected**\n\n"
        for site in changed_sites:
            message += f"• {site}\n"
        
        message += f"\n*Check performed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*"
        
        payload = {
            "content": message
        }
        
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        
        print(f"✓ Discord notification sent for {len(changed_sites)} changed sites")
        return True
        
    except Exception as e:
        print(f"✗ Error sending Discord notification: {str(e)}")
        return False

def main():
    print("=== WEBSITE MONITOR DEBUG VERSION ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Debug environment
    debug_environment()
    
    # Get websites to monitor
    websites_env = os.getenv('WEBSITES_TO_MONITOR')
    if not websites_env:
        print("✗ WEBSITES_TO_MONITOR not set!")
        return 1
    
    websites = [url.strip() for url in websites_env.split(',') if url.strip()]
    print(f"\nMonitoring {len(websites)} websites:")
    for i, url in enumerate(websites, 1):
        print(f"  {i}. {url}")
    
    # Test email connection first
    print(f"\n=== TESTING EMAIL CONNECTION ===")
    email_works = test_email_connection()
    
    # Load previous hashes
    print(f"\n=== LOADING PREVIOUS HASHES ===")
    previous_hashes = load_previous_hashes()
    current_hashes = {}
    changed_sites = []
    
    # Check each website
    print(f"\n=== CHECKING WEBSITES ===")
    for i, url in enumerate(websites, 1):
        print(f"\n[{i}/{len(websites)}] Checking: {url}")
        current_hash = get_page_hash(url)
        
        if current_hash:
            current_hashes[url] = current_hash
            
            # Compare with previous hash
            if url in previous_hashes:
                if previous_hashes[url] != current_hash:
                    print(f"🔔 CHANGE DETECTED: {url}")
                    changed_sites.append(url)
                else:
                    print(f"✓ No change detected")
            else:
                print(f"ℹ First time monitoring this URL")
        else:
            print(f"✗ Failed to fetch this URL")
    
    # Save current hashes
    print(f"\n=== SAVING HASHES ===")
    save_hashes(current_hashes)
    
    # Send notifications if changes detected
    if changed_sites:
        print(f"\n=== SENDING NOTIFICATIONS ===")
        print(f"Changes detected in {len(changed_sites)} sites:")
        for site in changed_sites:
            print(f"  • {site}")
        
        if email_works:
            send_email_notification(changed_sites)
        else:
            print("Skipping email notification due to connection issues")
        
        send_discord_notification(changed_sites)
    else:
        print(f"\n✓ No changes detected in any monitored websites")
    
    print(f"\n=== MONITORING COMPLETE ===")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
