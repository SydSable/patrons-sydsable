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
   - `PATREON_CAMPAIGN_ID`: Your campaign ID
   - `GH_RELEASE_TOKEN`: The Personal Access token that commits to the patrons.json

3. **Test Manually**: Go to Actions tab > Update Patrons Data > Run workflow.

## Schedule
- Runs automatically on **1st of every month** at midnight UTC.
- Outputs committed back to repo.

## Access Data (Public even for private repo)
- **JSON Raw file (if repo public)**: [https://raw.githubusercontent.com/SydSable/patrons-sydsable/refs/heads/main/_data/patrons.json](https://raw.githubusercontent.com/SydSable/patrons-sydsable/refs/heads/main/_data/patrons.json)
- In Jekyll: `site.data.patrons` (array of {member_id, displayed_name, tier, last_payment_timestamp})

**Private Repo Note**: Release assets are always public. Workflow uploads to Releases tag "data".

## Local Testing
```
pip install requests python-dotenv
python update_patrons.py
```

**Domain Proxy**: If you have a domain, fetch from release URL server-side (e.g., Jekyll Liquid fetch or Node proxy) to cache/brand.

**Note**: `.patreon.env` gitignored; GitHub Secrets prioritized.
