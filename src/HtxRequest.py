import httpx
import os
import dotenv
import json
from urllib.parse import urlparse

dotenv.load_dotenv()

API_KEY = os.getenv("API_KEY")

class HtxRequest:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.rate_limit = 5 # there's no documentation so i just ball

    def parse_url(self, url: str):
        try:
            parsed = urlparse(url)
            #print(parsed)
            if parsed.scheme == 'https' and parsed.netloc == 'civitai.com' and parsed.path.startswith('/models/'):
                path_parts = parsed.path.split('/')
                if len(path_parts) >= 3:  # ['', 'models', '{model_id}']
                    model_id = path_parts[2]
                    return int(model_id)
                else:
                    raise ValueError(f"Invalid URL path format: {parsed.path}")
            else:
                raise ValueError(f"Invalid URL: must be a civitai.com models URL")
        except ValueError as e:
            raise ValueError(f"Invalid URL: {url} - {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing URL: {url} - {str(e)}")

    def get_model(self, model_id: str):
        url = f"https://civitai.com/api/v1/models/{model_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        response = httpx.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_models_by_list(self, model_list: list[str]) -> list[dict]:
        '''
        Get models by list of urls
        '''
        models = []
        for model_url in model_list:
            models.append(self.get_model(self.parse_url(model_url)))
        return models

    def get_models_by_list_file(self, model_list_file: str) -> list[dict]:
        '''
        Get models by list of urls from file. 
        One url per line
        '''
        with open(model_list_file, "r") as file:
            model_list = file.read().splitlines()
        return self.get_models_by_list(model_list)

    def print_response(self, response: dict):
        '''
        Print the response in a pretty format
        '''
        print(json.dumps(response, indent=4))
        return