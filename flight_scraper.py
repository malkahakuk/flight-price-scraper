# Google Colab Flight Scraper - FOR DEVELOPMENT/TESTING ONLY
# This won't run automatically - you need to execute manually

# Install required packages
!pip install requests

# Import libraries
import requests
import json
from datetime import datetime, timedelta
import time
import pandas as pd
from IPython.display import display, HTML

# Configuration - SET THESE VALUES
API_KEY = "your_amadeus_api_key"
API_SECRET = "your_amadeus_api_secret"
PRICE_THRESHOLD = 800  # CAD
EMAIL_TO = "your_email@gmail.com"

class ColabFlightScraper:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = None
        
    def get_access_token(self):
        """Get OAuth token from Amadeus API"""
        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret
        }
        
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            self.access_token = response.json()['access_token']
            print("✅ Successfully authenticated with Amadeus API")
            return True
        else:
            print(f"❌ Authentication failed: {response.text}")
            return False
    
    def search_flights(self, departure_date):
        """Search for flights using Amadeus API"""
        if not self.access_token:
            if not self.get_access_token():
                return []
        
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'originLocationCode': 'YYZ',
            'destinationLocationCode': 'GRU',
            'departureDate': departure_date,
            'adults': 1,
            'max': 10,
            'currencyCode': 'CAD'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return self.parse_flight_data(response.json())
            else:
                print(f"API Error: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def parse_flight_data(self, data):
        """Parse API response into readable format"""
        flights = []
        
        if 'data' not in data:
            return flights
            
        for offer in data['data']:
            try:
                price = float(offer['price']['grandTotal'])
                currency = offer['price']['currency']
                
                itinerary = offer['itineraries'][0]
                segments = itinerary['segments']
                
                first_segment = segments[0]
                last_segment = segments[-1]
                
                flight = {
                    'airline': first_segment['carrierCode'],
                    'price': price,
                    'currency': currency,
                    'departure_date': first_segment['departure']['at'].split('T')[0],
                    'departure_time': first_segment['departure']['at'].split('T')[1][:5],
                    'arrival_time': last_segment['arrival']['at'].split('T')[1][:5],
                    'duration': itinerary['duration'],
                    'stops': len(segments) - 1,
                    'deal': price <= PRICE_THRESHOLD
                }
                
                flights.append(flight)
                
            except Exception as e:
                print(f"Error parsing flight: {e}")
                continue
                
        return flights

# Initialize scraper
scraper = ColabFlightScraper(API_KEY, API_SECRET)

# Search flights for next 7 days
print("🔍 Searching for flights YYZ → GRU...")
all_flights = []
today = datetime.now()

for i in range(7):
    check_date = (today + timedelta(days=i)).strftime('%Y-%m-%d')
    print(f"Checking {check_date}...")
    
    flights = scraper.search_flights(check_date)
    all_flights.extend(flights)
    
    time.sleep(1)  # Rate limiting

# Convert to DataFrame for better display
df = pd.DataFrame(all_flights)

if not df.empty:
    # Sort by price
    df = df.sort_values('price')
    
    # Display all flights
    print(f"\n📊 Found {len(df)} flights")
    display(df)
    
    # Filter and display deals
    deals = df[df['deal'] == True]
    
    if not deals.empty:
        print(f"\n🎯 Found {len(deals)} deals under ${PRICE_THRESHOLD}!")
        
        # Create HTML table for better visualization
        html_table = deals.to_html(index=False, classes='table table-striped')
        display(HTML(f"""
        <h3>✈️ Great Deals Found!</h3>
        {html_table}
        """))
        
        # Show cheapest deal
        cheapest = deals.iloc[0]
        print(f"\n💰 Cheapest deal: {cheapest['airline']} - ${cheapest['price']:.2f} on {cheapest['departure_date']}")
        
    else:
        print(f"\n📈 No deals found under ${PRICE_THRESHOLD}")
        print(f"💡 Cheapest flight: ${df.iloc[0]['price']:.2f}")
        
else:
    print("❌ No flights found")

# Optional: Save results to Google Drive
# from google.colab import drive
# drive.mount('/content/drive')
# df.to_csv('/content/drive/MyDrive/flight_prices.csv', index=False)
# print("💾 Results saved to Google Drive")
