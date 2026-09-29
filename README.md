# Virtual Office — Web Test

Browser test version of the approved Virtual Office UI. It uses Python rules and Excel data; no OpenAI API, n8n or local LLM is required.

## Local test
1. Install Python 3.11+.
2. `pip install -r requirements.txt`
3. `python app.py`
4. Open `http://127.0.0.1:5000`

## GitHub + Render
1. Create a GitHub repository and upload all files/folders from this package.
2. In Render choose **New > Blueprint** and connect the repository.
3. Render reads `render.yaml` and deploys the web service.
4. Open the Render URL from the office PC browser.

## What works
- Approved Virtual Office home visual
- Clickable Accounting, Sales, Inventory, Finance, Audit and Reporting areas
- Jaseer rule-based chat
- Bundled September 2026 test workbook
- Excel upload for compatible workbooks
- Python sales/GP, negative stock, duplicate and bank-reconciliation checks

## Important
This web test cannot directly access your office PC `D:\` folders or automate CODE7. Those are local Windows/EXE features. Uploaded files on a free web host should be treated as temporary test data; do not upload confidential live company data until authentication and secure storage are added.
