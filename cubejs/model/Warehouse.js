cube(`Warehouse`, {
  sql: `SELECT * FROM warehouse`,
  measures: {
    count: { type: `count` },
    totalSqft: { sql: `w_warehouse_sq_ft`, type: `sum` }
  },
  dimensions: {
    warehouseSk: { sql: `w_warehouse_sk`, type: `number`, primaryKey: true },
    warehouseId: { sql: `w_warehouse_id`, type: `string` },
    warehouseName: { sql: `w_warehouse_name`, type: `string` },
    city: { sql: `w_city`, type: `string` },
    county: { sql: `w_county`, type: `string` },
    state: { sql: `w_state`, type: `string` },
    zip: { sql: `w_zip`, type: `string` },
    country: { sql: `w_country`, type: `string` },
    sqft: { sql: `w_warehouse_sq_ft`, type: `number` }
  }
});