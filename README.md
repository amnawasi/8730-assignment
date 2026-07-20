# SmartCentres REIT Investment Analysis
BSMM-8730 Data Acquisition & Management — Group Assignment
University of Windsor | Due: July 19, 2026

## Team
- Amna Wasi
- Ahmad
- Eric Tran
- Usman Iqbal

## Project Overview
An investment analysis of SmartCentres Real Estate Investment Trust (TSX: SRU.UN),
evaluating whether a potential investor should buy, hold, or avoid the REIT, based
on financial performance, peer comparison, macroeconomic sensitivity, and
qualitative evidence from regulatory filings.

Structured data (stock prices, Bank of Canada interest rates and inflation, peer
REIT comparisons) is stored in **MySQL**. Semi-structured and unstructured data
(company fundamentals, news headlines, SEDAR+ filings, investor relations
documents) is stored in **MongoDB Atlas**, linked to the MySQL data by a shared
`company_id` field.

## Repository Structure
**`acquisition/`** — all data acquisition, cleaning, and loading scripts
- `yfinance_pull.py` — price history, fundamentals, news (SmartCentres)
- `wowa_scraping.py` — REIT type categorization + current peer metrics
- `interest_rate_pull.py` — Bank of Canada overnight rate
- `inflation_cpi_pull.py` — Bank of Canada CPI
- `smartcentres_documents_pull.py` — company site PDF scraper
- `smartcentres_pdf_to_json.py` — company site PDF to JSON
- `sedar_pdf_to_json.py` — SEDAR+ PDF to JSON
- `save_raw_data.py` — saves yfinance + wowa raw pulls to `data/raw/`
- `process_market_data.py` — cleans fundamentals/news to `data/processed/`
- `load_mysql.py` — loads all structured CSVs into MySQL
- `import_investor_documents.py` — loads investor documents into MongoDB
- `import_sedar_documents.py` — loads SEDAR+ documents into MongoDB
- `import_market_data.py` — loads fundamentals/news into MongoDB

**`data/raw/`** — untouched acquisition output (`smartcentres/`, `peers/`, `bank_of_canada/`)

**`data/processed/`** — cleaned/validated output, ready for database loading (`smartcentres/`, `sedar/`)

**`analysis/`** - contains the output for the analysis with the charts (`outputs/`)

**`.env`** — local credentials (never committed — see Environment Setup below)

## Environment Setup
**Requirements:**
- Python 3.x
- MySQL Server (local) + MySQL Workbench
- A MongoDB Atlas cluster with connection access

**1. Clone and set up a virtual environment:**
```bash
git clone https://github.com/amnawasi/8730-assignment.git
cd 8730-assignment
python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
```

**2. Install dependencies:**
```bash
pip install yfinance pandas requests beautifulsoup4 pymongo mysql-connector-python python-dotenv certifi PyMuPDF
```

**3. Create a `.env` file in the project root** (never commit this file — it's excluded via `.gitignore`):
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=smartcentres

MONGO_URI=mongodb+srv://usman:MongoFix2026@cluster0.ectjwst.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0

**4. Start your local MySQL server** (via MySQL Workbench or System Settings, depending on OS).

## How to Run
Run scripts from the project root, in this order:

**Structured data (MySQL):**
```bash
python acquisition/save_raw_data.py       # Pull yfinance + wowa.ca raw data
python acquisition/interest_rate_pull.py  # Pull Bank of Canada overnight rate
python acquisition/inflation_cpi_pull.py  # Pull Bank of Canada CPI
python acquisition/load_mysql.py          # Load all structured data into MySQL
```

**Semi-structured / unstructured data (MongoDB):**
```bash
python acquisition/process_market_data.py     # Clean fundamentals/news
python acquisition/import_market_data.py      # Load into MongoDB
python acquisition/smartcentres_documents_pull.py
python acquisition/smartcentres_pdf_to_json.py
python acquisition/import_investor_documents.py
python acquisition/sedar_pdf_to_json.py
python acquisition/import_sedar_documents.py
```

All loading scripts are idempotent — safe to re-run at any time; each clears existing
data before reloading rather than creating duplicates.

## Data Sources
- **yfinance** — SmartCentres price history, fundamentals, and news
- **wowa.ca** — Canadian REIT type/sector categorization
- **Bank of Canada Valet API** — overnight rate (series V39079) and CPI (series V41690973)
- **SEDAR+** — SmartCentres MD&A filings (manually retrieved; no public API available)
- **smartcentres.com** — investor relations documents (press releases, AIF, annual report)

Date range: **January 1, 2020 – July 7, 2026** (fixed, not rolling), to ensure
reproducible results across team members and runs.

## Data Validation
Several data quality issues were identified and resolved during development:
- An inconsistent `company_id` value across sources, standardized to `"smartcentres"`
- A `yfinance` library structure change that caused all news headlines to return empty
- A regex filename-parsing bug affecting SEDAR+ document year extraction

See the technical report (Section C: Dataset Description & Validation) for full detail.

## Instructor Access
- Instructor GitHub: @elsharif-UWindsor
- Added as collaborator with read access to this private repository

## Repository
- Repository name: 8730-assignment
- Visibility: Private

## LLM Acknowledgment
This project made use of Claude (Anthropic) for code assistance and for debugging support.
