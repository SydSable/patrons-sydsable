#!/usr/bin/env python3
"""
Patreon CSV Updater Script
Fetches patron data from Patreon API and updates CSV files
"""

import os
import csv
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from dotenv import dotenv_values # <<< NEW: Recommended for environment files

# --- Configuration ---
CONFIG_FILE = '.patreon.env' # <--- NEW: The file you will GitIgnore

PATREON_ACCESS_TOKEN = ''
CAMPAIGN_ID = ''

# API endpoints
BASE_URL = 'https://www.patreon.com/api/oauth2/v2'

# --- NEW FUNCTION: Load Configuration from Local File ---
def load_config(config_file: str) -> Tuple[str, str]:
    """
    Loads PATREON_ACCESS_TOKEN and CAMPAIGN_ID, prioritizing environment variables (e.g., GitHub Secrets),
    falling back to local file.
    """
    token = os.environ.get('PATREON_ACCESS_TOKEN', '')
    campaign_id = os.environ.get('PATREON_CAMPAIGN_ID', '')

    # Fallback to local file if not in env
    if not token or not campaign_id:
        if os.path.exists(config_file):
            try:
                config = dotenv_values(config_file)
                if not token:
                    token = config.get('PATREON_ACCESS_TOKEN', '')
                if not campaign_id:
                    campaign_id = config.get('PATREON_CAMPAIGN_ID', '')
            except Exception as e:
                print(f"Warning: Could not parse configuration from {config_file}: {e}")

    return token, campaign_id
# -------------------------------------------------------------------

def get_patrons() -> List[Dict]:
    """Fetch all patrons from Patreon API"""
    
    # Use the global variables which are set in main()
    global PATREON_ACCESS_TOKEN, CAMPAIGN_ID

    if not PATREON_ACCESS_TOKEN:
        print("ERROR: PATREON_ACCESS_TOKEN not set.")
        return []
    
    if not CAMPAIGN_ID:
        print("ERROR: PATREON_CAMPAIGN_ID not set.")
        return []
    
    headers = {
        'Authorization': f'Bearer {PATREON_ACCESS_TOKEN}',
    }
    
    # The rest of the function remains the same...
    # Fetch campaign members (patrons)
    url = f'{BASE_URL}/campaigns/{CAMPAIGN_ID}/members'
    params = {
        'include': 'user',
        'fields[member]': 'full_name,patron_status,last_charge_date,last_charge_status,currently_entitled_amount_cents',
        'fields[user]': 'full_name',
    }

    
    all_patrons = []
    
    try:
        while url:
            # Replaced response = requests.get(url, headers=headers, params=params)
            # with the following to include a timeout
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Process members
            included_users = {user['id']: user for user in data.get('included', []) if user['type'] == 'user'}
            
            for member in data.get('data', []):
                if member['attributes']['patron_status'] == 'active_patron':
                    user_id = member['relationships']['user']['data']['id']
                    user = included_users.get(user_id, {})
                    
                    patron_info = {
                        'member_id': member['id'],
                        'displayed_name': user.get('attributes', {}).get('full_name', 'Anonymous'),
                        'last_payment_timestamp': member['attributes'].get('last_charge_date', ''),
                        'pledge_amount_cents': member['attributes'].get('currently_entitled_amount_cents', 0)
                    }

                    all_patrons.append(patron_info)
            
            # Check for next page
            url = data.get('links', {}).get('next')
            params = None  # params only needed for first request
        
        print(f"✓ Successfully fetched {len(all_patrons)} active patrons")
        return all_patrons
    
    except requests.exceptions.RequestException as e:
        print(f"ERROR fetching patrons: {e}")
        return []

def categorize_patrons(patrons: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize patrons by pledge tier and eligibility duration"""
    now = datetime.now()
    
    categories = {
        'one_month': [],
        'six_months': [],
        'one_year': []
    }
    
    for patron in patrons:
        pledge_cents = patron.get('pledge_amount_cents', 0)
        
        if pledge_cents == 300: # NOTUS: €3.00
            duration_days = 30
            category = 'one_month'
        elif pledge_cents == 500: # ZEPHYRUS: €5.00
            duration_days = 180
            category = 'six_months'
        elif pledge_cents == 1500: # BOREAS: €15.00
            duration_days = 365
            category = 'one_year'
        else:
            print(f"Warning: Unknown pledge amount {pledge_cents} cents for {patron.get('displayed_name')}")
            continue
        
        last_charge = patron.get('last_payment_timestamp', '')
        if not last_charge:
            continue
        
        try:
            # Parse the date (format: YYYY-MM-DD or ISO format)
            if 'T' in last_charge:
                charge_date = datetime.fromisoformat(last_charge.replace('Z', '+00:00'))
            else:
                charge_date = datetime.strptime(last_charge, '%Y-%m-%d')
            
            eligible_until = charge_date + timedelta(days=duration_days)
            if eligible_until > now:
                categories[category].append(patron)
        except (ValueError, TypeError) as e:
            print(f"Warning: Could not parse date for patron {patron.get('displayed_name')}: {last_charge} ({e})")
            continue
    
    # Sort each category alphabetically by displayed_name
    for cat_list in categories.values():
        cat_list.sort(key=lambda p: p['displayed_name'].lower())
    
    return categories


def write_csv(filename: str, patrons: List[Dict]):
    # ... (No changes needed in this function) ...
    """Write patrons to CSV file"""
    fieldnames = ['member_id', 'displayed_name', 'last_payment_timestamp']
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for patron in patrons:
            # Format the date to just YYYY-MM-DD
            timestamp = patron.get('last_payment_timestamp', '')
            if 'T' in timestamp:
                try:
                    # Added safety check for date parsing
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime('%Y-%m-%d')
                except:
                    pass
            
            writer.writerow({
                'member_id': patron['member_id'],
                'displayed_name': patron['displayed_name'],
                'last_payment_timestamp': timestamp
            })

def main():
    """Main function to update patron CSVs"""
    # Set global configuration variables before calling get_patrons
    global PATREON_ACCESS_TOKEN, CAMPAIGN_ID
    
    # --- NEW: Load Config ---
    PATREON_ACCESS_TOKEN, CAMPAIGN_ID = load_config(CONFIG_FILE)
    
    print("🔄 Fetching patron data from Patreon API...")
    
    patrons = get_patrons()
    
    if not patrons:
        print("⚠️  No patrons found or API request failed.")
        print("\nSet PATREON_ACCESS_TOKEN and PATREON_CAMPAIGN_ID as environment variables,")
        print("or create '.patreon.env' (gitignore'd) with:")
        print("   PATREON_ACCESS_TOKEN='your_token_here'")
        print("   PATREON_CAMPAIGN_ID='your_campaign_id'")

        # Ensure an empty patrons.json exists so downstream steps don't fail
        data_dir = '_data'
        os.makedirs(data_dir, exist_ok=True)
        json_path = os.path.join(data_dir, 'patrons.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2, ensure_ascii=False)
        print(f"✓ Generated {json_path} (empty)")
        return
    
    print("📊 Categorizing patrons by subscription length...")
    categories = categorize_patrons(patrons)
    
    # Define file paths
    data_dir = '_data'
    os.makedirs(data_dir, exist_ok=True)
    
    files = {
        'one_month': os.path.join(data_dir, 'one_month_mentions.csv'),
        'six_months': os.path.join(data_dir, 'six_months_mentions.csv'),
        'one_year': os.path.join(data_dir, 'one_year_mentions.csv')
    }
    
    # Write CSV files
    for category, filepath in files.items():
        patron_list = categories[category]
        write_csv(filepath, patron_list)
        print(f"✓ Updated {filepath} with {len(patron_list)} patrons")

    # Generate patrons.json for client-side auth/perks lookup
    tier_names = {
        'one_month': 'NOTUS',
        'six_months': 'ZEPHYRUS',
        'one_year': 'BOREAS'
    }
    all_patrons_data = []
    for category, patron_list in categories.items():
        for patron in patron_list:
            all_patrons_data.append({
                'member_id': patron['member_id'],
                'displayed_name': patron['displayed_name'],
                'tier': tier_names[category],
                'last_payment_timestamp': patron['last_payment_timestamp']
            })
    
    json_path = os.path.join(data_dir, 'patrons.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_patrons_data, f, indent=2, ensure_ascii=False)
    print(f"✓ Generated {json_path} with {len(all_patrons_data)} patrons")

    print(f"\n✅ All patron data updated successfully!")
    print(f"   • One Year+: {len(categories['one_year'])} patrons")
    print(f"   • Six Months: {len(categories['six_months'])} patrons")
    print(f"   • One Month: {len(categories['one_month'])} patrons")


if __name__ == '__main__':
    main()
