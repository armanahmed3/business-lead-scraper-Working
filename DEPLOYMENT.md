# 🚀 How to Deploy to Streamlit Cloud

Follow these steps to deploy your **Lead Scraper Pro** to the web using Streamlit Community Cloud.

## 1. Prepare Your Project
I have already created the necessary configuration files for you:
*   **requirements.txt**: Lists all Python libraries (Selenium, Streamlit, etc.).
*   **packages.txt**: Lists system dependencies (Chromium Browser) required for the scraper to run on the cloud.

## 2. Push to GitHub
You need to upload your code to a GitHub repository.
1.  **Create a new Repository** on [GitHub](https://github.com/new).
2.  **Upload ALL these files** (this is critical, missing files cause errors):
    *   `streamlit_ui.py`
    *   `selenium_scraper.py`
    *   `dedupe.py`
    *   `exporter.py`
    *   `config.py`
    *   `config.yaml`
    *   `utils.py`
    *   `robots_checker.py`
    *   `yelp_scraper.py`
    *   `yellow_pages_scraper.py`
    *   `requirements.txt`
    *   `packages.txt`
    *   `users.db` (If you want to keep your current admin login)

## 3. Deploy on Streamlit
1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Log in with your **GitHub** account.
3.  Click **"New app"**.
4.  Select your **Repository**, **Branch** (usually `main`), and **Main file path** (select `streamlit_ui.py`).
5.  Click **"Deploy!"**.

## ⚠️ Important Notes for Cloud

### 1. Browser Headless Mode
The scraper is configured to run in **Headless Mode** (hidden browser) by default.
*   **Do NOT** check the "Debug Mode (Show Browser)" box when running on the cloud. The cloud server has no screen, so it will crash if you try to show the browser.

### 2. Memory Limits
The free tier of Streamlit Cloud has resource limits.
*   Don't try to scrape 1000 leads in one go. Keep batches smaller (e.g., 50-100) to prevent the app from crashing due to memory usage.

### 3. File Downloads
*   When you download the Excel/CSV file, it works normally. However, the files generated in the "data" folder on the server will be deleted when the app reboots. Always download your results immediately.
