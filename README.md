# Patreon Patrons Updater

This repository automatically fetches active Patreon patrons via the Patreon API, categorizes them by pledge tier/duration (Notus/1mo, Zephyrus/6mo, Boreas/1yr), and generates:
- CSV files in `_data/` for Jekyll integration (one_month_mentions.csv, etc.)
- `patrons.json` with tier info for client-side use.

## Setup

1. **Push to GitHub**:
   ```
   cd patrons-sydsable
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/patrons-updater.git
   git push -u origin main
   ```

2. **Add GitHub Secrets** (Settings > Secrets and variables > Actions):
   - `PATREON_ACCESS_TOKEN`: Your Patreon API access token
   - `PATREON_CAMPAIGN_ID`: Your campaign ID (e.g., 14963942)

3. **Test Manually**: Go to Actions tab > Update Patrons Data > Run workflow.

## Schedule
- Runs automatically on **1st of every month** at midnight UTC.
- Outputs committed back to repo.

## Access Data
- JSON: `https://raw.githubusercontent.com/YOUR_USERNAME/patrons-updater/main/_data/patrons.json`
- In Jekyll: `site.data.patrons` (array of {member_id, displayed_name, tier, last_payment_timestamp})

## Local Testing
```
pip install requests python-dotenv
python update_patrons.py
```

**Note**: `.patreon.env` is gitignored; use secrets for production.
