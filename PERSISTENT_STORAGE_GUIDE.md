# ☁️ How to Setup Free Persistent Storage (Google Sheets)

Since Streamlit Cloud resets your database when it reboots, the best **Lifetime Free** solution is to use a private **Google Sheet** as your database. It never sleeps, is free, and you can easily view your users.

## Step 1: Set up Google Cloud
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a **New Project** (name it "ScraperAuth").
3.  Search for **"Google Sheets API"** → Click **Enable**.
4.  Search for **"Google Drive API"** → Click **Enable** (needed to find the sheet).

## Step 2: Create Service Account
1.  Go to **Credentials** (in the sidebar).
2.  Click **Create Credentials** → **Service Account**.
3.  Name it "streamlit-bot". Click **Create**.
4.  Click on the email address of the account you just created (e.g., `streamlit-bot@...`).
5.  Go to the **Keys** tab → **Add Key** → **Create new key** → **JSON**.
6.  A file will download to your computer. **Keep this safe!**

## Step 3: Create the Database Sheet
1.  Go to Google Sheets and create a new blank sheet.
2.  Name it `user_db`.
3.  In the first row, add these headers exactly:
    *   **A1**: `username`
    *   **B1**: `password`
    *   **C1**: `role`
    *   **D1**: `active`
    *   **E1**: `created_at`
    *   **F1**: `openrouter_key`
    *   **G1**: `smtp_user`
    *   **H1**: `smtp_pass`
    *   **I1**: `gsheets_creds`
4.  Click the **Share** button (top right).
5.  **Copy the "client_email"** from your JSON key file (from Step 2).
6.  Paste it into the Share box and give it **Editor** access. This allows your app to write new users to the sheet.

## Step 4: Configure Streamlit
1.  Go to your app dashboard on [share.streamlit.io](https://share.streamlit.io).
2.  Click the **three dots** next to your app → **Settings** → **Secrets**.
3.  Paste the contents of your JSON key file. Format it like this:

```toml
[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE"
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
auth_uri = "..."
token_uri = "..."
auth_provider_x509_cert_url = "..."
client_x509_cert_url = "..."
```

*(You can copy most of these values directly from your JSON file).*

## Step 5: Update Code
Once you have the sheet ready, I can update your `streamlit_ui.py` to connect to it.

**Would you like me to update the code now to support this Google Sheets connection?**
 (It will include a fallback so it still works offline with SQLite).
