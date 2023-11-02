import requests
import time
import json

def refresh_access_token(app_id, app_secret, current_token):
    url = f"https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id={app_id}&client_secret={app_secret}&fb_exchange_token={current_token}"
    response = requests.get(url).json()
    new_token = response.get("access_token")
    
    # Atualizar o arquivo config.json com o novo token
    with open('config.json', 'r') as config_file:
        config_data = json.load(config_file)
    
    config_data['facebookAPI']['access_token'] = new_token
    
    with open('config.json', 'w') as config_file:
        json.dump(config_data, config_file, indent=4)
    
    return new_token

def check_and_refresh_token(app_id, app_secret, current_token):
    url = f"https://graph.facebook.com/debug_token?input_token={current_token}&access_token={current_token}"
    response = requests.get(url).json()
    expire_time = response["data"]["expires_at"]
    if (expire_time - time.time()) < (3 * 24 * 60 * 60):
        return refresh_access_token(app_id, app_secret, current_token)
    return current_token
