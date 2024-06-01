import requests
import time
import json

class GraphAPI():
    def __init__(self):
        # Carregar configurações e credenciais da Graph API dos arquivos JSON
        self.configs = self.load_configs()
        self.creds = self.load_credentials()
        
        self.check_and_refresh_token()
        
        
        self.token = "&access_token=" + self.creds['graph_api']['current_token']

        # Configurar os campos e URLs base a partir do arquivo de configuração
        self.base_url = self.configs["base"]["url"]
        self.api_version = self.configs["base"]["api_version"]
        self.insight_fields = self.configs["base"]["insight_fields"]
        self.campaign_fields = self.configs["campaign"]["unique_fields"]
        self.adset_fields = self.configs["adset"]["unique_fields"]
        self.ad_fields = self.configs["ad"]["unique_fields"]
        self.creative_fields = self.configs["creative"]["unique_fields"]

        # Checar e atualizar o token de acesso, se necessário
        
        self.token = "&access_token=" + self.creds['graph_api']['current_token']

    def load_configs(self):
        """Carrega as configurações do arquivo JSON."""
        with open('graph_api_configs.json', 'r') as configs_file:
            return json.load(configs_file)

    def load_credentials(self):
        """Carrega as credenciais do arquivo JSON."""
        with open('graph_api_credentials.json', 'r') as credentials_file:
            return json.load(credentials_file)

    def check_and_refresh_token(self):
        """
        Verifica se o token de acesso atual está prestes a expirar e, se estiver,
        atualiza-o.
        """
        app_id = self.creds["graph_api"]["app_id"]
        app_secret = self.creds["graph_api"]["app_secret"]
        current_token = self.creds["graph_api"]["current_token"]

        url = f"https://graph.facebook.com/debug_token?input_token={current_token}&access_token={current_token}"
        response = requests.get(url).json()
        print(response)
        expire_time = response["data"]["expires_at"]

        # Se o token expirar em menos de 3 dias, atualize-o
        if (expire_time - time.time()) < (3 * 24 * 60 * 60):
            self.refresh_access_token(app_id, app_secret, current_token)

    def refresh_access_token(self, app_id, app_secret, current_token):
        """Atualiza o token de acesso usando as credenciais fornecidas."""
        url = f"https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id={app_id}&client_secret={app_secret}&fb_exchange_token={current_token}"
        response = requests.get(url).json()
        new_token = response.get("access_token")

        # Atualizar o arquivo de credenciais com o novo token
        self.creds['graph_api']['current_token'] = new_token
        with open('graph_api_credentials.json', 'w') as credentials_file:
            json.dump(self.creds, credentials_file, indent=4)
            
    def get_ads_insights(self, ad_acc, level):
        url = self.base_url +  self.api_version + "act_" + str(ad_acc)
        url += "/insights?level=" + level
        url += "&fields=" + ",".join(self.insight_fields)
        data = requests.get(url + self.token)
        data = json.loads(data._content.decode("utf-8"))
        print(data)

if __name__ == "__main__":
    ad_acc = "197321610993362"
    level = "ad"
    self = GraphAPI()
    self.get_ads_insights(ad_acc, level)