#!/usr/bin/env python3
"""
Test a working query to see the correct format.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cost_estimator.query_builders import EC2QueryBuilder

load_dotenv()

def test_working_query():
    """Test a query that we know works."""
    
    api_key = os.getenv("INFRACOST_API_KEY")
    if not api_key:
        print("❌ INFRACOST_API_KEY not set")
        return
    
    # Test EC2 instance query (we know this works)
    query = EC2QueryBuilder.build_instance_query({
        "Region": "us-east-1",
        "InstanceType": "t3.medium"
    })
    
    print("Testing EC2 Instance Query:")
    print(query)
    
    url = "https://pricing.api.infracost.io/graphql"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, data=query, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_working_query() 