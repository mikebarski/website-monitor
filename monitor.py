import hashlib
import json
import os
import requests
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime

def get_page_hash(url):
    """Get SHA256 hash of webpage content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return hashlib.sha256(response.text.encode()).hexdigest()
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return None

def load_previous_hashes():
    """Load previous hashes from file"""
    try:
        if os.path.exists('website_hashes.json'):
            with open('website_hashes.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading previous hashes: {str(e)}")
    return {}

def save_hashes(hashes):
    """Save current hashes to file"""
    try:
        with open('website_hashes.json', 'w') as f:
            json.dump(hashes, f, indent=2)
    except Exception as e:
        print(f"Error saving hashes: {str(e)}")

def send_email_notification(changed_sites):
    """Send email notification for changed websites"""
    try:
        # Email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        receiver_email = os.getenv('RECEIVER_EMAIL')
        
        if not all([sender_email, sender_password, receiver_email]):
            print("Email credentials not configured properly")
            return
        
        # Create message
        msg = MimeMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"Website Changes Detected - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        body = "The following websites have changed:\n\n"
        for site in changed_sites:
            body += f"• {site}\n"
        
        body += f"\nCheck performed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        msg.attach(MimeText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        print(f"Email notification sent for {len(changed_sites)} changed sites")
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")

def send_discord_notification(changed_sites):
    """Send Discord notification via webhook"""
    try:
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if not webhook_url:
            return
        
        message = f"🔔 **Website Changes Detected**\n\n"
        for site in changed_sites:
            message += f"• {site}\n"
        
        message += f"\n*Check performed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*"
        
        payload = {
            "content": message
        }
        
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        
        print(f"Discord notification sent for {len(changed_sites)} changed sites")
        
    except Exception as e:
        print(f"Error sending Discord notification: {str(e)}")

def main():
    # List of websites to monitor
    websites = [
        "https://example.com",
        "https://news.ycombinator.com",
        # Add your websites here
    ]
    
    # Load configuration from environment or use defaults
    websites_env = os.getenv('WEBSITES_TO_MONITOR')
    if websites_env:
        websites = [url.strip() for url in websites_env.split(',') if url.strip()]
    
    print(f"Monitoring {len(websites)} websites...")
    
    # Load previous hashes
    previous_hashes = load_previous_hashes()
    current_hashes = {}
    changed_sites = []
    
    # Check each website
    for url in websites:
        print(f"Checking: {url}")
        current_hash = get_page_hash(url)
        
        if current_hash:
            current_hashes[url] = current_hash
            
            # Compare with previous hash
            if url in previous_hashes:
                if previous_hashes[url] != current_hash:
                    print(f"CHANGE DETECTED: {url}")
                    changed_sites.append(url)
                else:
                    print(f"No change: {url}")
            else:
                print(f"First time monitoring: {url}")
        else:
            print(f"Failed to fetch: {url}")
    
    # Save current hashes
    save_hashes(current_hashes)
    
    # Send notifications if changes detected
    if changed_sites:
        print(f"\nSending notifications for {len(changed_sites)} changed sites...")
        send_email_notification(changed_sites)
        send_discord_notification(changed_sites)
    else:
        print("\nNo changes detected.")
    
    print("Monitoring complete.")

if __name__ == "__main__":
    main()
