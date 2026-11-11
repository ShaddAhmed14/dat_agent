import os
import requests
from dotenv import load_dotenv
load_dotenv()

ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
AUTH_TOKEN = os.environ.get("CLOUDFLARE_AUTH_TOKEN")

class ClefModel:
    def __init__(self):
        self.model_name = "clef"
        self.url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/cloudflare/{self.model_name}"
        self.headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

    def _post_request(self, payload):
        try:
            response = requests.post(
                url=self.url,
                headers=self.headers,
                json=payload,
                timeout=10  # Set a timeout of 10 seconds
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()
        except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as e:
            raise Exception(f"Error occurred while making the request: {e}")

    def route_to(self, user_query: str):
        payload = {
            "model": "clef",
            "state": user_query,
            "questions": {
                "route_to": {
                    "type": "choice",
                    "instructions": f"Which agent is best suited to handle the user's query?",
                    "criteria": {
                        "etl_agent": "extracting, transforming, and loading data",
                        "sql_agent": "executing SQL queries against a database",
                    },
                }
            }
        }
        try:
            response = self._post_request(payload)
        except Exception as e:
            raise Exception(f"Error occurred while routing the query: {e}")

        # Response: {'result': {'model': 'clef', 'answers': {'route_to': {'type': 'choice', 'choice': 'sql_agent', 'probabilities': {'etl_agent': 0.0407, 'sql_agent': 0.9593}, 'confidence': 0.844}}, 'usage': {'input_tokens': 155, 'output_tokens': 0}}, 'success': True, 'errors': [], 'messages': []}
        response = response["result"]["answers"]["route_to"]["choice"]
        return response

    def is_safe(self, user_query: str, threshold: float = 0.9):
        instructions=f"Your task is to analyze the provided SQL query and determine whether it is safe to execute. A safe query is one that does not contain any potentially harmful operations, such as data deletion, modification, or access to sensitive information. Please review the SQL query and provide a clear assessment of its safety."
        payload = {
            "model": "clef",
            "state": user_query,
            "questions": {
                "safe": {
                    "type": "noul", # Yes or No
                    "instructions": instructions,
                }
            }
        }
        try:
            response = self._post_request(payload)
        except Exception as e:
            raise Exception(f"Error occurred while checking query safety: {e}")

        # Response: {'result': {'model': 'clef', 'answers': {'safe': {'type': 'noul', 'noul': 0.0061}}, 'usage': {'input_tokens': 204, 'output_tokens': 0}}, 'success': True, 'errors': [], 'messages': []}
        response = response["result"]["answers"]["safe"]["noul"] > threshold
        return response

if __name__ == "__main__":
    '''Basic test for ClefModel class. '''
    clef_model = ClefModel()
    user_query = "What are the unique vehicle makes?"
    route_response = clef_model.route_to(user_query)
    print(f"Route Response: {route_response}")

    sql_query = "SELECT * FROM users; DROP TABLE users;"
    safety_response = clef_model.is_safe(sql_query)
    print(f"Safety Response: {safety_response}")
