import requests
import time
import json
import pandas as pd
import numpy as np 


class GraphAPI():
    def __init__(self):
        # Carregar configurações e credenciais da Graph API dos arquivos JSON
        
        self.configs = self.load_configs()
        self.creds = self.load_credentials()
        self.results_dict = self.load_results_dict()
        self.check_and_refresh_token()
        
        self.token = "access_token=" + self.creds['graph_api']['current_token']
        
        # Configurar os campos e URLs base a partir do arquivo de configuração
        self.base_url = self.configs["base"]["url"]
        self.api_version = self.configs["base"]["api_version"]
        self.insight_fields = self.configs["base"]["insight_fields"]
        self.insight_breakdowns =  self.configs["base"]["breakdowns"]
        self.insight_action_breakdowns =  self.configs["base"]["action_breakdowns"]
        self.campaign_fields = self.configs["campaign"]["unique_fields"]
        self.adset_fields = self.configs["adset"]["unique_fields"]
        self.ad_fields = self.configs["ad"]["unique_fields"]
        self.creative_fields = self.configs["creative"]["unique_fields"]

        # Checar e atualizar o token de acesso, se necessário
        
    def load_configs(self):
        """Carrega as configurações do arquivo JSON."""
        with open('graph_api_configs.json', 'r') as configs_file:
            return json.load(configs_file)


    def load_credentials(self):
        """Carrega as credenciais do arquivo JSON."""
        with open('graph_api_credentials.json', 'r') as credentials_file:
            return json.load(credentials_file)
        
        
    def load_results_dict(self):
        """Carrega o dicionário que faz as correspondências entre os objetivos de campanha, os optmization_goals e as métricas de resultado"""
        with open('graph_api_results_dict.json', 'r') as results_dict:
            return json.load(results_dict)


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
    
    
    def get_result_metric(self, item):
        objective = item['objective']

        optimization_goal = item['optimization_goal']
 
        result_metric = self.results_dict[objective].get(optimization_goal)
        try:
            item['results'] = next((action['value'] for action in item.get('actions') if action['action_type'] == result_metric), None)
            item['cost_per_result'] = next((action['value'] for action in item.get('cost_per_action_type') if action['action_type'] == result_metric), None)
            item['result_values'] = next((action['value'] for action in item.get('action_values') if action['action_type'] == result_metric), None)
            
        except TypeError:
            item['results'] = 0
        return item

    def get_ads_insights(self, ad_acc, level, date_preset):
        url = self.base_url + self.api_version + "act_" + str(ad_acc)
        url += "/insights?level=" + level
        url += "&fields=" + ",".join(self.insight_fields)
        #url += "&breakdowns=" + ",".join(self.insight_breakdowns)
        url += "&action_breakdowns=" + ",".join(self.insight_action_breakdowns)
        url += "&date_preset=" + date_preset
        response = requests.get(url + "&" + self.token)
        raw_data = json.loads(response.content.decode("utf-8"))
        data = raw_data['data']
        return data
        
    def get_products_from_catalog(self, catalog_id, url=None, all_products=[]):
        if url is None:
            url = self.base_url + self.api_version + str(catalog_id)
            url += "/products?fields=id,name,category,description,price,brandcategory,image_url,custom_data,additional_variant_attributes,availability ,color,inventory,material,product_type,sale_price,sale_price_end_date	,sale_price_start_date,short_description,size,start_date,url&"
            url += self.token
        response = requests.get(url)
        raw_data = json.loads(response.content.decode("utf-8"))
        data = raw_data.get('data', [])
        
        all_products.extend(data)

        next_page = raw_data.get('paging', {}).get('next')
        if next_page:
            print("Encontrada próxima página.")  # Log de depuração
        # Se houver uma próxima página, faz uma chamada recursiva com a nova URL e a lista atualizada de produtos
            self.get_products_from_catalog(catalog_id, next_page, all_products)
        else:

            # Quando não há mais páginas, salva a lista completa de produtos em um arquivo JSON
            with open('productsEB.json', 'w', encoding='utf-8') as f:
                json.dump(all_products, f, ensure_ascii=False, indent=4)
            print(f"Total de {len(all_products)} produtos salvos em 'productsEB.json'.")



if __name__ == "__main__":
    ad_acc = "1543775213042225"
    catalog_id = "577223234522771"
    level = "ad"
    metaAds = GraphAPI()
    date_preset ="maximum"
    # d = metaAds.get_ads_insights(ad_acc, level, date_preset)
    # print(d)
    prods = metaAds.get_products_from_catalog(catalog_id=catalog_id)
  