import requests
import webbrowser
import json
import os
from urllib.parse import urlparse, parse_qs

# === CONFIGURATION ===
CLIENT_ID = 'YOUR_CLIENT_ID'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
REDIRECT_URI = 'http://localhost'
TOKEN_FILE = 'tokens.json'

# === STEP 1: Authorize if no token ===
def authorize():
    auth_url = (
        f"https://www.inoreader.com/oauth2/auth"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=read"
    )
    print("Откройте ссылку и авторизуйтесь:")
    print(auth_url)
    webbrowser.open(auth_url)

    code = input("Вставьте значение `code` из URL после авторизации: ").strip()
    token_data = exchange_code_for_token(code)
    save_tokens(token_data)
    return token_data['access_token']


def exchange_code_for_token(code):
    url = "https://www.inoreader.com/oauth2/token"
    data = {
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()


def refresh_token(refresh_token):
    url = "https://www.inoreader.com/oauth2/token"
    data = {
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token',
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()


# === Helpers ===

def save_tokens(data):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(data, f)


def load_tokens():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        return json.load(f)


def get_access_token():
    tokens = load_tokens()
    if not tokens:
        return authorize()

    # try to refresh
    try:
        new_tokens = refresh_token(tokens['refresh_token'])
        save_tokens(new_tokens)
        return new_tokens['access_token']
    except Exception as e:
        print("Ошибка при обновлении токена:", e)
        print("Придется авторизоваться заново")
        return authorize()

# === USAGE ===

def list_subscriptions(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    r = requests.get("https://www.inoreader.com/reader/api/0/subscription/list", headers=headers)
    r.raise_for_status()
    for sub in r.json().get("subscriptions", []):
        print(f"- {sub['title']}\n  Feed ID: {sub['id']}\n")


def get_feed_items(feed_id, access_token, count=5):
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f"https://www.inoreader.com/reader/api/0/stream/contents/{feed_id}"
    r = requests.get(url, headers=headers, params={'n': count})
    r.raise_for_status()
    for item in r.json().get('items', []):
        print(f"📌 {item['title']}")
        print(f"🔗 {item['canonical'][0]['href']}\n")


if __name__ == "__main__":
    token = get_access_token()

    print("\n🔍 Ваши подписки:")
    list_subscriptions(token)

    feed_id = input("\n👉 Введите `Feed ID`, чтобы получить элементы: ").strip()
    print("\n📥 Последние элементы:")
    get_feed_items(feed_id, token)
