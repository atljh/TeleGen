import requests

API_KEY = 'c_DqnKqLqIrMU5Ba'
API_SECRET = 's_uBbl0op2n6CeWaEEHc0Jkc'
TARGET_URL = 'https://minfin.com.ua/'

headers = {
    "Authorization": f"Bearer {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json"
}

payload = {
    "url": TARGET_URL
}

url = "https://api.rss.app/v1/feeds"

response = requests.post(url, headers=headers, json=payload)

if response.status_code == 200:
    data = response.json()
    items = data.get("items", [])
    
    if items:
        latest = items[0]
        print(latest)
    else:
        print("ℹ️ Лента получена, но новости отсутствуют.")
else:
    print(f"❌ Ошибка {response.status_code}: {response.text}")
