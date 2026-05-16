# TPC-DS Data Integration with Cube.js - Setup Guide

## Overview

This document explains how the TPC-DS dataset from [violetautumn/TPCDS_repo_for_BQ](https://github.com/violetautumn/TPCDS_repo_for_BQ) has been integrated into the semantic layer using Cube.js and PostgreSQL.

## Architecture

```
TPC-DS Dataset (BigQuery DDL)
         ↓
PostgreSQL DDL (Converted)
         ↓
PostgreSQL Database (15 Tables)
         ↓
Cube.js Schemas (8 Cubes)
         ↓
Analytics/BI Tools
```

## What Has Been Done

### 1. **Schema Creation**
- Converted BigQuery DDL format to PostgreSQL-compatible DDL
- Created 15 TPC-DS tables in PostgreSQL:
  - 4 Fact tables (store_sales, catalog_sales, web_sales, catalog_returns)
  - 11 Dimension tables (customer, item, date_dim, store, etc.)

### 2. **Data Loading**
- Loaded sample TPC-DS data (20+ rows across fact tables)
- Data includes:
  - 5 sample customers with demographics and addresses
  - 5 sample items across multiple categories
  - 2 sample stores with location info
  - 4 date dimension entries
  - 5 store sales transactions
  - 2 catalog sales transactions
  - 2 web sales transactions
  - 1 catalog return record

### 3. **Cube.js Schemas**
Created 8 Cube.js schema files that map PostgreSQL tables to semantic cubes:

| Cube | Primary Keys | Key Measures | Key Dimensions |
|------|--------------|--------------|-----------------|
| StoreSales | item_sk, ticket_number | totalNetPaid, totalNetProfit, avgSalesPrice | customerSk, storeSk, soldDate, quantity |
| CatalogSales | item_sk, order_number | totalNetPaid, totalNetProfit | billCustomerSk, shipCustomerSk, warehouseSk |
| WebSales | item_sk, order_number | totalNetPaid, totalNetProfit | billCustomerSk, webSiteSk, soldDate |
| CatalogReturns | item_sk, order_number | totalReturnAmount, totalNetLoss | refundedCustomerSk, returnedDate |
| Customer | customer_sk | count | firstName, lastName, emailAddress, birthCountry |
| Item | item_sk | count, avgCurrentPrice | category, brand, manufacturer, size, color |
| DateDim | date_sk | count | year, month, dayOfWeek, quarter |
| Store | store_sk | count, avgEmployees | storeName, city, state, divisionName |

### 4. **Container Setup**
- PostgreSQL 15 running on localhost:5432
- Cube.js running on localhost:4000
- All services configured via docker-compose.yml

## How to Reference TPC-DS Data in Cube.js

### Method 1: Using Cube.js UI

1. **Open Cube.js Playground**
   ```
   http://localhost:4000
   ```

2. **Build a Query**
   - Select a cube (e.g., StoreSales)
   - Choose measures (e.g., totalNetPaid, count)
   - Choose dimensions (e.g., soldDate, storeSk)
   - Apply filters and drill-downs
   - Execute query

3. **Example: Total Sales by Date**
   ```
   Cube: StoreSales
   Measures: [totalNetPaid]
   Dimensions: [soldDate]
   ```

### Method 2: Using Cube.js API

```bash
curl -X GET http://localhost:4000/api/v1/cubes \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Method 3: Using SQL API (if enabled)

```javascript
import cubejs from '@cubejs-client/core';

const cubejsApi = cubejs(
  'YOUR_API_TOKEN',
  { apiUrl: 'http://localhost:4000/api/v1' }
);

const resultSet = await cubejsApi.load({
  measures: ['StoreSales.totalNetPaid'],
  timeDimensions: [{
    dimension: 'StoreSales.soldDate',
    granularity: 'day'
  }]
});

console.log(resultSet.tablePivot());
```

### Method 4: Direct PostgreSQL Query

```bash
# From host machine
psql -h localhost -U cube -d tpcds -c "SELECT * FROM store_sales;"

# Via Docker
docker exec semanticlayer_aiagents-postgres-1 psql -U cube -d tpcds -c "SELECT * FROM store_sales;"
```

## Understanding the TPC-DS Dimension Model

### Star Schema Design

The TPC-DS data follows a traditional star schema:

```
                    date_dim
                      ↑
                      |
    item ← store_sales → customer
                      |
                      ↓
                   store
```

### Key Surrogate Keys

All TPC-DS tables use surrogate keys (SK) for efficient joins:

- `customer.c_customer_sk` → `store_sales.ss_customer_sk`
- `item.i_item_sk` → `store_sales.ss_item_sk`
- `store.s_store_sk` → `store_sales.ss_store_sk`
- `date_dim.d_date_sk` → `store_sales.ss_sold_date_sk`

### Example Join in Cube.js Schema

```javascript
// StoreSales can reference Customer via customer_sk
dimensions: {
  customerFirstName: {
    sql: 'c_first_name',
    // Would need explicit join definition
    type: 'string'
  }
}
```

## Extending the Schema

### Adding More Cubes

Create a new file `cubejs/schema/WebReturns.js`:

```javascript
module.exports = {
  cube: {
    name: 'WebReturns',
    sql: 'SELECT * FROM web_returns',
    
    measures: {
      totalReturnAmount: {
        sql: 'wr_return_amt',
        type: 'sum'
      }
    },
    
    dimensions: {
      returnedDate: {
        sql: 'wr_returned_date_sk',
        type: 'time'
      }
    }
  }
};
```

### Adding Relationships

```javascript
// In StoreSales.js
relationships: {
  customer: {
    sql: `${CUBE}.ss_customer_sk = ${CUBE.Customer}.c_customer_sk`
  },
  item: {
    sql: `${CUBE}.ss_item_sk = ${CUBE.Item}.i_item_sk`
  }
}
```

## Scaling the Data

### Option 1: Use dsdgen Tool

```bash
# Generate 1GB TPC-DS dataset
git clone https://github.com/databricks/tpcds-kit.git
cd tpcds-kit/tools
make

./dsdgen -SCALE 1 -TABLE store_sales -FORCE -DIR /tmp/tpcds_data

# Load data (pipe-delimited)
psql "postgresql://cube:cube_pass@localhost:5432/tpcds" -c \
  "\COPY store_sales FROM '/tmp/tpcds_data/store_sales.dat' WITH (FORMAT csv, DELIMITER '|')"
```

### Option 2: Generate Synthetic Data

```python
import psycopg2
import random
from datetime import datetime, timedelta

conn = psycopg2.connect("dbname=tpcds user=cube password=cube_pass host=localhost")
cur = conn.cursor()

# Generate 1 million store sales records
base_date = datetime(2020, 1, 1)
for i in range(1_000_000):
    cur.execute("""
        INSERT INTO store_sales 
        (ss_sold_date_sk, ss_item_sk, ss_customer_sk, ss_store_sk, ss_quantity, 
         ss_sales_price, ss_net_paid, ss_ticket_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        int((base_date + timedelta(days=random.randint(0, 1000))).strftime('%Y%m%d')),
        random.randint(1, 5000),
        random.randint(1, 500),
        random.randint(1, 50),
        random.randint(1, 10),
        round(random.uniform(10, 500), 2),
        round(random.uniform(5, 450), 2),
        i
    ))
    
    if i % 10000 == 0:
        conn.commit()

conn.commit()
cur.close()
conn.close()
```

## Query Examples in Cube.js

### 1. Revenue by Store

```json
{
  "measures": ["StoreSales.totalNetPaid"],
  "dimensions": ["Store.storeName"],
  "order": {
    "StoreSales.totalNetPaid": "desc"
  }
}
```

### 2. Sales Trend (Daily)

```json
{
  "measures": ["StoreSales.totalNetPaid", "StoreSales.count"],
  "dimensions": ["DateDim.date"],
  "timeDimensions": [{
    "dimension": "StoreSales.soldDate",
    "granularity": "day"
  }],
  "order": {
    "DateDim.date": "asc"
  }
}
```

### 3. Top Products

```json
{
  "measures": ["StoreSales.totalNetPaid", "StoreSales.totalQuantity"],
  "dimensions": ["Item.itemDesc", "Item.category"],
  "order": {
    "StoreSales.totalNetPaid": "desc"
  },
  "limit": 10
}
```

### 4. Customer Segmentation

```json
{
  "measures": ["StoreSales.totalNetPaid"],
  "dimensions": ["Customer.firstName", "Customer.lastName", "Customer.birthCountry"],
  "order": {
    "StoreSales.totalNetPaid": "desc"
  },
  "limit": 20
}
```

## Database Connection Info

```
Database Type: PostgreSQL 15
Host: localhost (or 'postgres' from Docker container)
Port: 5432
Database: tpcds
Username: cube
Password: cube_pass
```

## Available Schemas Files

```
cubejs/schema/
├── StoreSales.js          # Point-of-sale transactions
├── CatalogSales.js        # Catalog order transactions  
├── WebSales.js            # Online sales transactions
├── CatalogReturns.js      # Return transactions
├── Customer.js            # Customer master data
├── Item.js                # Product/item master
├── Store.js               # Store locations
├── DateDim.js             # Date dimension
└── [Coming soon]
    ├── WebReturns.js
    ├── CallCenter.js
    ├── Inventory.js
    └── HouseholdDemographics.js
```

## Troubleshooting

### Issue: Cube.js can't connect to PostgreSQL
**Solution**: Verify connection string in docker-compose.yml and ensure PostgreSQL is running
```bash
docker-compose ps
docker-compose logs postgres
```

### Issue: Schema changes not reflected in Cube.js
**Solution**: Restart Cube.js service
```bash
docker-compose restart cube
```

### Issue: Data not loading properly
**Solution**: Check for constraint violations and data type mismatches
```bash
docker exec semanticlayer_aiagents-postgres-1 psql -U cube -d tpcds -c \
  "SELECT COUNT(*) FROM store_sales;"
```

## References

- **TPC-DS Official**: https://www.tpc.org/tpcds/
- **Cube.js Documentation**: https://cube.dev/docs
- **PostgreSQL Documentation**: https://www.postgresql.org/docs
- **Original Repository**: https://github.com/violetautumn/TPCDS_repo_for_BQ
- **Apache Doris Benchmark**: https://doris.apache.org/docs/3.x/benchmark/tpcds

## Next Steps

1. **Load full-scale data** using dsdgen tool (1GB, 10GB, or 100GB scale)
2. **Create pre-aggregations** in Cube.js for performance
3. **Add drill-down relationships** between cubes
4. **Implement row-level security** for multi-tenant scenarios
5. **Connect BI tools** (Tableau, Metabase, Superset) to Cube.js API
6. **Develop metrics** specific to business requirements
