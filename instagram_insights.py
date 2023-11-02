import requests
import json
from datetime import date, timedelta
from google_sheets import get_filtered_instagram_ids, get_google_sheets_config_data, authenticate_google_sheets, open_spreadsheet
from facebook_graph_api import check_and_refresh_token

def get_instagram_posts(instagram_id, access_token):                                                           
       sixty_days_ago = (date.today() - timedelta(days=60)).strftime('%Y-%m-%d')                                  
       url = f"https://graph.facebook.com/v18.0/{instagram_id}/media"                                             
       params = {                                                                                                 
           'access_token': access_token,                                                                          
           'since': sixty_days_ago                                                                                
       }                                                                                                          
       response = requests.get(url, params=params)                                                                
       response_json = response.json()                                                                            
       if 'error' in response_json:                                                                               
           print(f"Error getting posts for Instagram ID {instagram_id}: {response_json['error']}")                
           return []                                                                                              
       else:                                                                                                      
           return response_json.get('data', []) 
       
def get_post_insights(post, access_token):                                                                                                                                                               
    post_id = post['id']  # Extract the id from the post dictionary                                                                                                                                      
    url = f"https://graph.facebook.com/v18.0/{post_id}/insights?metric=reach"                                                                                                                
    params = {                                                                                                                                                                                           
        'access_token': access_token                                                                                                                                                                     
    }                                                                                                                                                                                                    
    response = requests.get(url, params=params)                                                                                                                                                          
    response_json = response.json()                                                                                                                                                                      
    if 'error' in response_json:                                                                                                                                                                         
        print(f"Error getting insights for post ID {post_id}: {response_json['error']}: url:{url}")                                                                                                      
        return None                                                                                                                                                                                      
    else:                                                                                                                                                                                                
        return response_json 
        
with open('config.json') as config_file:                                                                       
   config_data = json.load(config_file)                                                                                                                                                                                      
   facebook_app_id = config_data['facebookAPI']['app_id']                                                         
   facebook_app_secret = config_data['facebookAPI']['app_secret']                                                 
   access_token = config_data['facebookAPI']['access_token']                                                      
                                                                                                                  
   # Ensure access token is refreshed if needed                                                                   
   access_token = check_and_refresh_token(facebook_app_id, facebook_app_secret, access_token)                     
                                                                                                                  
   config_data['facebookAPI']['access_token'] = access_token                                                      
   with open('config.json', 'w') as config_file:                                                                  
       json.dump(config_data, config_file)                                                                        
                                                                                                                  
   google_config = get_google_sheets_config_data()                                                                
                                                                                                                  
   auth_client = authenticate_google_sheets(google_config=google_config)                                          
   spreadsheet = open_spreadsheet(auth_client=auth_client, google_config=google_config)                           
   filtered_instagram_ids = get_filtered_instagram_ids(spreadsheet=spreadsheet)                                   
                                                                                                                  
   # Get posts for each Instagram ID                                                                              
   all_posts = []                                                                                                 
   for id in filtered_instagram_ids:                                                                              
       posts = get_instagram_posts(instagram_id=id, access_token=access_token)                                    
       all_posts.extend(posts)
                                                                                          
                                                                                                                  
   # Get insights for each post                                                                                   
   all_insights = []                                                                                                                                                                                        
   for post in all_posts:                                                                                                                                                                                   
       insights = get_post_insights(post, access_token)  # Pass the entire post dictionary                                                                                                                  
       all_insights.append(insights)
       print(all_insights)                                                                                            
                         