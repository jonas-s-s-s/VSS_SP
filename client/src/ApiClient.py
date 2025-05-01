import requests

class ApiClient:
    def __init__(self, base_url):
        """
        Initialize the API client with the base URL of the server
        """
        self.base_url = base_url.rstrip('/')

    def list_services(self):
        """
        Get the list of available benchmark services from the server
        """
        url = f"{self.base_url}/services"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error listing services: {e}")
            return None

    def get_current_service(self):
        """
        Get the current active benchmark service from the server
        """
        url = f"{self.base_url}/service"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting current service: {e}")
            return None

    def change_service(self, service_name):
        """
        Change the current benchmark service on the server
        """
        url = f"{self.base_url}/service"
        data = {'serviceName': service_name}
        try:
            response = requests.put(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 400:
                error_detail = response.json().get('error', 'Unknown error')
                print(f"Error changing service: {error_detail}")
            else:
                print(f"Error changing service: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error changing service: {e}")
            return None