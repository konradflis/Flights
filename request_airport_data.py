import requests

with open("your_api_key.txt") as f:
    api_key = f.read()
API_key = api_key

iata_codes = []     # TODO: set of iata codes from the database
results = []

try:
    for code in iata_codes:

        url = f"https://api.aviationstack.com/v1/airports"
        params = {
            "access_key": API_key,
            "iata_code": code
        }

        response = requests.get(url, params=params)
        data = response.json()

        if 'data' in data and data['data']:
            latitude = data['data'][0]['latitude']
            longitude = data['data'][0]['longitude']

            results.append([code, latitude, longitude])

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")


print(results)