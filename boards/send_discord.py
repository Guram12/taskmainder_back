import requests

def send_discord_notification(webhook_url, message):
    data = {"content": message}
    response = requests.post(webhook_url, json=data)
    return response.status_code == 204  