from send_discord import send_discord_notification

if __name__ == "__main__":
    webhook_url = "https://discord.com/api/webhooks/1398700394892496947/vgQ772w2NhbLCqE7nlZ-c2nxbf--8g8ZwkHPCdjQoiwOC9brFtazkJmM66V8LKI3Jeqf"  # Replace with your actual webhook URL
    message = "🚀 This is a test notification from TaskMeinder backend! rogor xar?"
    success = send_discord_notification(webhook_url, message)
    if success:
        print("Notification sent successfully!")
    else:
        print("Failed to send notification.")