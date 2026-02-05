# Price Finder (Windows 11)

A small Windows 11 desktop app that estimates a realistic market price range for a product by searching Google via Selenium.

## Project structure

```
price_finder/
  app.py
  google_search.py
  fetcher.py
  matcher.py
  price_extract.py
  fx.py
  models.py
  utils.py
  requirements.txt
  README.md
```

## Setup (Windows 11)

1. Install Python 3.11+.
2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run the app

```powershell
python app.py
```

## Build a single-file EXE (PyInstaller)

1. Install PyInstaller:

```powershell
pip install pyinstaller
```

2. Build the executable:

```powershell
pyinstaller --onefile --windowed --name PriceFinder app.py
```

3. The EXE will be created in the `dist/` folder.

## Create a desktop shortcut

- Right-click the `PriceFinder.exe` in `dist/`.
- Select **Send to** → **Desktop (create shortcut)**.

## Notes

- Google search uses Selenium Manager to auto-manage ChromeDriver.
- The app writes logs to `app.log` in the same folder.
- Results are saved to `last_results.json` for debugging.
