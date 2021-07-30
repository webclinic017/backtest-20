# Install Instructions

Create a python virtual enviroment

```bash
cd into_install_root_directory
git clone https://github.com/CandidateBlock/backtest.git
cd backtest
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## main.py

Implements the CryptoFlash Strategy of emea(12, 60) cross over.
Shows results in chart and prints porfolio data

## load_cryptoflash_data.py

Run this to update data - cryptoflash.csv

```bash
python load_cryptoflash_data.py
```

This downloads data from the CryptoFlash web site for hourly Bitcoin data and then uses pandas to change into csv format complitible with Backtrader.
It makes the next opening bar level = previous close for Backtrader to use as execution price.
Data is stored in cryptoflash.csv

## load_bitmex_data.py

Run this to update data - bitmex.csv

```bash
python load_bitmex_data.py
```

This downloads data from the bitmex web site (using ccxt package) for hourly Bitcoin data and then uses pandas to change into csv format complitible with Backtrader.
Data is stored in bitmex.csv

## display_pyfolio.ipynb

Jupyter Notebook to display the results using pyfolio (Python package) that the Backtrader (Python package) generated.
