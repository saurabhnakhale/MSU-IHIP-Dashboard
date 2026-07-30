# MSU · IDSP Disease Surveillance Report

A Power BI-styled, live Streamlit dashboard for the MSU IDSP P-Form/L-Form
disease surveillance data (Nagpur).

## What "live" means here

- The app reads `data/MSU_IDSP_Disease_Surveillance.csv` from disk every time
  you hit **Refresh data** in the sidebar (it clears Streamlit's cache and
  re-reads the file) — so it stays in sync with whatever is on disk / in the
  repo, without needing a redeploy.
- You can also drop in any other CSV with the same columns via the sidebar
  uploader, for a one-off look without touching the repo file.
- On every load, the app reconciles `P Form + L Form` against the CSV's own
  `Total` column and shows a **✓ Reconciled** / **⚠ Check totals** badge in
  the header, so bad data never publishes silently.

## Project structure

```
.
├── app.py                  # the Streamlit app
├── requirements.txt
├── data/
│   └── MSU_IDSP_Disease_Surveillance.csv
└── .streamlit/
    └── config.toml         # Power BI-style theme colors
```

## Run it locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

To refresh with new data locally: replace/edit
`data/MSU_IDSP_Disease_Surveillance.csv` directly, then click **Refresh data**
in the running app — no restart needed.

## Deploy for free on Streamlit Community Cloud

1. Create a new GitHub repo and push this folder:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: IDSP surveillance dashboard"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, and click **New app**.
3. Pick your repo, branch `main`, and main file path `app.py`. Click
   **Deploy**.
4. You'll get a URL like `https://<app-name>.streamlit.app` — that's your
   live dashboard.

### Updating the data on the deployed app

Streamlit Cloud serves whatever is in your GitHub repo, so to publish new
data:

```bash
# replace data/MSU_IDSP_Disease_Surveillance.csv with the new export, then:
git add data/MSU_IDSP_Disease_Surveillance.csv
git commit -m "Update surveillance data"
git push
```

The app redeploys automatically within a minute or two. Once it's live,
clicking **Refresh data** in the sidebar re-reads that file — useful if the
app was already open in a browser tab when you pushed the update.

If you'd rather not commit data to GitHub each time, use the sidebar's CSV
uploader instead — it works the same way on the deployed app and never
touches the repo.
