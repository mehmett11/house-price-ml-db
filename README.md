### 1) Prepare the environment

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows PowerShell
pip install -r requirements.txt
```

### 2) .env create

```env
DB_NAME=""
DB_USER=""
DB_PASSWORD=""
DB_HOST=localhost
DB_PORT=5432
```

### 3) Start the application

```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```
psql -->
CREATE DATABASE house_price;
CREATE TABLE IF NOT EXISTS "public"."tbl_house" (
  "id" BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "Square_Footage" INTEGER NOT NULL,
  "Num_Bedrooms" INTEGER NOT NULL,
  "Num_Bathrooms" INTEGER NOT NULL,
  "Year_Built" INTEGER NOT NULL,
  "Lot_Size" NUMERIC(12,2) NOT NULL,
  "Garage_Size" INTEGER NOT NULL,
  "Neighborhood_Quality" INTEGER NOT NULL,
  "House_Price" NUMERIC(14,2) NOT NULL
);

