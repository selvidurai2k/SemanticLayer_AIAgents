# SemanticLayer_AIAgents

This repository contains a starter scaffold to run a local Postgres database seeded with a full TPC-DS-like schema and a Cube.js service acting as the semantic layer. It's intended as a foundation for the master's thesis: "Automating Semantic Layer Management with AI Agents" (metrics, generation, governance).

## Overview

**Database**: PostgreSQL with 15 TPC-DS tables
**Semantic Layer**: Cube.js with pre-built schemas for all major fact and dimension tables
**Data Source**: Sample TPC-DS data loaded from [violetautumn/TPCDS_repo_for_BQ](https://github.com/violetautumn/TPCDS_repo_for_BQ)

## TPC-DS Tables Loaded

### Fact Tables:
- **store_sales**: Point-of-sale transactions (5 rows)
- **catalog_sales**: Mail/catalog order transactions (2 rows)
- **web_sales**: Online transaction sales (2 rows)
- **catalog_returns**: Catalog order returns (1 row)

### Dimension Tables:
- **customer**: Customer master data (5 rows)
- **item**: Product/item master data (5 rows)
- **store**: Store location and attributes (2 rows)
- **date_dim**: Date dimension for temporal analysis (4 rows)
- **customer_address**: Customer address information
- **customer_demographics**: Customer demographic attributes
- **call_center**: Call center information
- **catalog_page**: Catalog page metadata
- **household_demographics**: Household demographic information
- **income_band**: Income band definitions
- **inventory**: Inventory levels by item, warehouse, and date

## Quick Start

### 1. Start Services

```bash
docker compose up -d
```

This starts:
- PostgreSQL container with TPC-DS schema (port 5432)
- Cube.js playground (port 4000)

### 2. Verify Setup

Check if tables are created:
```bash
docker exec semanticlayer_aiagents-postgres-1 psql -U cube -d tpcds -c "\dt"
```

### 3. Access Cube.js

- If you run the repo on your local machine with Docker, open Cube.js playground at [http://localhost:4000](http://localhost:4000).
- If you run this in GitHub.dev / a remote Codespace, use the forwarded URL shown by the editor (for example, `https://...-4000.app.github.dev`).

Explore the cubes:
- `StoreSales`
- `CatalogSales`
- `WebSales`
- `CatalogReturns`
- `Customer`
- `Item`
- `DateDim`
- `Store`

## Cube.js Schema Files

Schema files are located in `cubejs/schema/` and include:

| Cube | File | Purpose |
|------|------|---------|
| StoreSales | StoreSales.js | Point-of-sale transactions analysis |
| CatalogSales | CatalogSales.js | Catalog order analysis |
| WebSales | WebSales.js | Online sales analysis |
| CatalogReturns | CatalogReturns.js | Return analysis |
| Customer | Customer.js | Customer master data |
| Item | Item.js | Product catalog |
| DateDim | DateDim.js | Time dimension |
| Store | Store.js | Store locations |

## Data Structure Reference

### StoreSales Cube Example

```javascript
Measures:
  - count: Total transactions
  - totalNetPaid: Total net paid amount
  - totalNetProfit: Total profit
  - avgSalesPrice: Average sales price

Dimensions:
  - itemSk: Item surrogate key
  - customerSk: Customer surrogate key
  - storeSk: Store surrogate key
  - soldDate: Date of sale
  - quantity: Order quantity
```

Similar structure for CatalogSales, WebSales, and WebReturns cubes.

## Loading Full TPC-DS Data

### Option 1: Use dsdgen Tool (Recommended for realistic testing)

```bash
git clone https://github.com/databricks/tpcds-kit.git
cd tpcds-kit/tools
make

# Generate data at desired scale (1=1GB, 100=100GB, 1000=1TB)
./dsdgen -SCALE 1 -FORCE -DIR /tmp/tpcds_data

# Load into PostgreSQL
psql "postgresql://cube:cube_pass@localhost:5432/tpcds" \
  -c "\COPY store_sales FROM '/tmp/tpcds_data/store_sales.dat' WITH (FORMAT csv, DELIMITER '|')"
```

### Option 2: Generate Synthetic Data at Scale

You can write a Python script to generate larger datasets:

```python
import psycopg2
from faker import Faker
import random
from datetime import datetime, timedelta

conn = psycopg2.connect(
    "dbname=tpcds user=cube password=cube_pass host=localhost port=5432"
)
cur = conn.cursor()

fake = Faker()

# Generate 100,000 customers
for i in range(100000):
    cur.execute("""
        INSERT INTO customer 
        (c_customer_sk, c_customer_id, c_first_name, c_last_name, c_email_address)
        VALUES (%s, %s, %s, %s, %s)
    """, (i, f'CUST{i:06d}', fake.first_name(), fake.last_name(), fake.email()))

conn.commit()
cur.close()
conn.close()
```

## Database Connection Details

```
Host: postgres (localhost within container)
Port: 5432
Database: tpcds
User: cube
Password: cube_pass
```

## Files

- [docker-compose.yml](docker-compose.yml): Docker services configuration
- [docker/initdb/create_tpcds_tables.sql](docker/initdb/create_tpcds_tables.sql): Initial schema (replaced by full TPC-DS)
- [docker/initdb/README.md](docker/initdb/README.md): Data loading instructions
- [cubejs/schema/](cubejs/schema/): All Cube.js schema definitions

## Cube.js Example Queries

### Example 1: Total Sales by Store
```sql
SELECT 
  store.s_store_name,
  storeSales.totalNetPaid
FROM StoreSales
JOIN Store ON StoreSales.storeSk = Store.storeSk
```

### Example 2: Daily Sales Trend
```sql
SELECT
  dateDim.date,
  SUM(storeSales.totalNetPaid) as daily_revenue
FROM StoreSales
JOIN DateDim ON StoreSales.soldDate = DateDim.dateSk
GROUP BY dateDim.date
```

### Example 3: Customer Segmentation
```sql
SELECT
  customer.c_first_name,
  customer.c_last_name,
  SUM(storeSales.totalNetPaid) as total_spent
FROM StoreSales
JOIN Customer ON StoreSales.customerSk = Customer.customerSk
GROUP BY customer.customerSk
ORDER BY total_spent DESC
```

## Resources

- **TPC-DS Reference**: https://www.tpc.org/tpcds/
- **Apache Doris Benchmark**: https://doris.apache.org/docs/3.x/benchmark/tpcds
- **Cube.js Documentation**: https://cube.dev/docs
- **Original Dataset**: https://github.com/violetautumn/TPCDS_repo_for_BQ

## Next Steps

1. **Scale Data**: Follow Option 1 or 2 above to load more realistic data volumes
2. **Create Metrics**: Define business metrics in Cube.js schemas
3. **Build Dashboards**: Use Cube.js UI or connect BI tools
4. **Add Joins**: Create relationships between cubes in the schema files
5. **Implement Governance**: Set up access control and audit logging

## Troubleshooting

### PostgreSQL connection issues
```bash
# Check if postgres is running
docker-compose ps

# View postgres logs
docker-compose logs postgres
```

### Cube.js not connecting
```bash
# Check Cube.js logs
docker-compose logs cube

# Verify credentials
docker exec postgres psql -U cube -d tpcds -c "SELECT 1"
```

### Schema changes not reflected
```bash
# Restart Cube.js
docker-compose restart cube
```

---

For questions or contributions related to AI agents and semantic layer automation, please refer to the thesis documentation.

Automating Semantic Layer Management with AI Agents
