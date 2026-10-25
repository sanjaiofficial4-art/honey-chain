# Honey Chain — Honey Traceability & Smart Beekeeping

A local academic prototype built with **Python, Flask, SQLite, and SHA-256**. It supports beekeeper registration, hive records, honey-batch registration, batch lookup, and a persistent hash-linked chain.

> This is a single-node educational prototype, not a distributed public blockchain. Hash verification detects changes covered by the chain; it does not prove honey purity, truthful data entry, or independently verified flower origin. Hive temperature/humidity fields are manually entered, not live IoT readings.

## Requirements
- Windows 10/11
- Python 3.10+ (3.11/3.12 recommended)
- Visual Studio Code

## Run in VS Code (Windows)
1. Extract the ZIP to a folder such as `C:\Projects\Honey_Chain_Project`.
2. Open VS Code → **File → Open Folder** → select `Honey_Chain_Project`.
3. Install Python from https://www.python.org/downloads/ if needed. During installation, select **Add Python to PATH**.
4. Open **Terminal → New Terminal**.
5. Run:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   python app.py
   ```
   If PowerShell blocks activation, skip activation and use:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe app.py
   ```
6. Open the URL printed in the terminal, normally **http://127.0.0.1:5000**.
7. Stop the server with **Ctrl+C** in the terminal.

**Shortcut:** double-click `run.bat` to create the virtual environment, install Flask, and start the app.

## Recommended demo sequence
1. Register a beekeeper.
2. Add a hive connected to that beekeeper.
3. Add a honey batch using the hive ID shown in the Hives page.
4. Open **Trace Batch**, enter the Batch ID, and inspect the production record and chain result.
5. Open **Blockchain** to view block indexes, previous hashes, current hashes, and chain verification.

Sample demo values (clearly illustrative):
- Beekeeper: Demo Beekeeper
- Hive location: North Apiary
- Batch ID: HC001
- Quantity: 25 kg
- Flower source: Mango Flower

## Data and persistence
The SQLite file `honey_chain.db` is created in this project folder and persists across restarts. Back up this file before experimenting. Do not edit it while the app is running.

## Troubleshooting
- `py is not recognized`: install Python and enable PATH, then reopen VS Code.
- Port 5000 busy: close the other app or change `app.run(debug=True, port=5001)` in `app.py`.
- Hive/batch form is empty: register a beekeeper before adding a hive, and a hive before adding a batch.
- Duplicate Batch ID: choose a new unique identifier.
- PowerShell activation policy error: use the no-activation commands above.
- Database reset for a clean demo: stop the app, delete `honey_chain.db`, then restart. This deletes local demo records.

## Project structure
```text
Honey_Chain_Project/
├── app.py
├── database.py
├── blockchain.py
├── requirements.txt
├── run.bat
├── README.md
├── .gitignore
├── honey_chain.db        # created on first run
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── beekeepers.html
│   ├── hives.html
│   ├── batches.html
│   ├── trace.html
│   └── blockchain.html
└── static/
    └── style.css
```

## Deployment notes
This version is designed for local demonstration. Before internet deployment, disable Flask debug mode, set a strong secret key using an environment variable, add authentication/authorization, CSRF protection, secure backups, input and access logging, HTTPS, and production hosting (for example, a WSGI server). Never expose the development server directly to the public internet.


## QR code and customer purchase note
The trace page generates a QR code for each registered batch. The QR code opens that batch's trace page. To let a customer scan it on a separate phone, host the app on a publicly reachable HTTPS address, or configure a suitable local-network address while both devices are on the same Wi-Fi. A QR code containing `127.0.0.1` or `localhost` will not open the developer computer's website from a phone.

This prototype does **not** sell honey, maintain sale inventory, collect orders, or process payments. The QR code is for traceability only. Before adding real purchases, implement seller details, price, available quantity, order confirmation, privacy/security controls, and a secure payment flow. A valid hash chain does not prove honey purity; quality claims require appropriate independent evidence.
