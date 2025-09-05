import os
import requests
from dotenv import load_dotenv

# Load keys from .env
load_dotenv()
FACT_CHECK_API_KEY = os.getenv("FACT_CHECK_API_KEY")

def fact_check_claim(claim: str):
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {
        "query": claim,
        "key": FACT_CHECK_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "claims" in data:
            return data["claims"]
        else:
            return "No fact-check results found."
    else:
        return f"Error: {response.status_code}, {response.text}"

# Test with a sample claim
print(fact_check_claim("Elon Musk bought Google"))
