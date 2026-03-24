# Remaining steps (GitHub UI or one auth refresh)

Your token did not include the `user` scope, so profile fields (bio, location, company, website in the sidebar) were not set via API.

## Option A: Paste in the browser

GitHub.com → Settings → Public profile

- **Bio:** Associate Solutions Engineer at Datasembly. SQL, Snowflake, Python. Building RepTrack and NorthStar Forge.
- **URL:** https://kmsmohamedansar.github.io/
- **Location:** Canada
- **Company:** Datasembly (optional)

## Option B: CLI after expanding scope

```bash
gh auth refresh -h github.com -s user
gh api -X PATCH user \
  -f bio='Associate Solutions Engineer at Datasembly. SQL, Snowflake, Python. Building RepTrack and NorthStar Forge.' \
  -f blog='https://kmsmohamedansar.github.io/' \
  -f location='Canada' \
  -f company='Datasembly'
```

## Pin six repositories (order matters)

Profile → Customize your pins → select in this order:

1. kmsmohamedansar.github.io  
2. reptrack  
3. sql-playground  
4. high-value-customer-predictor  
5. ai_knowledge_assistant  
6. dagster-playground  

GitHub does not expose an API for profile pins; this step is manual.
