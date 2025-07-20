from send_discord import send_discord_notification

if __name__ == "__main__":
    webhook_url = "https://discord.com/api/webhooks/1396471759263236236/prup1mvWM85rdkkKm0lq4kOCRG6bAsvvkq_jkqKlRd6zki7y5Mzheycr9ePfvIxQN8q2"  # Replace with your actual webhook URL
    message = "🚀 This is a test notification from TaskMeinder backend! rogor xar?"
    success = send_discord_notification(webhook_url, message)
    if success:
        print("Notification sent successfully!")
    else:
        print("Failed to send notification.")