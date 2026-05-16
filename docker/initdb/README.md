This folder contains helper scripts and instructions to initialize a local TPC-DS-like dataset
for the Postgres container.

Quick options to provision data:

1) Minimal / sample data (fast)
   - The file `create_tpcds_tables.sql` creates a small `store_sales` table and inserts a few rows.
   - This will be executed automatically when Postgres first initializes (via Docker entrypoint).

2) Full TPC-DS generation (recommended for realistic testing)
   - Install `tpcds-kit` on the host or in a container, generate CSV data for your desired scale factor (e.g. SF1):

     git clone https://github.com/databricks/tpcds-kit.git
     cd tpcds-kit/tools
     make
     ./dsdgen -SCALE 1 -TABLE store_sales -FORCE -DIR /tmp/tpcds_data

   - Adjust the output delimiter/format if needed and then load CSVs into Postgres using `psql` or `COPY`.

   Example load command (host):

     psql "postgresql://cube:cube_pass@localhost:5432/tpcds" -c "\copy store_sales FROM '/tmp/tpcds_data/store_sales.dat' WITH (FORMAT csv, DELIMITER '|')"

Notes:
- The minimal sample is intended to let Cube.js connect and start exploring cubes quickly.
- Generating full TPC-DS data can take several minutes and needs build tools.
