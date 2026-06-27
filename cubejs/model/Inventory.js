cube(`Inventory`, {
  sql: `SELECT * FROM inventory`,
  measures: {
    count: { type: `count` },
    totalQuantityOnHand: { sql: `inv_quantity_on_hand`, type: `sum` },
    avgQuantityOnHand: { sql: `inv_quantity_on_hand`, type: `avg` }
  },
  dimensions: {
    dateSk: { sql: `inv_date_sk`, type: `number`, primaryKey: true },
    itemSk: { sql: `inv_item_sk`, type: `number` },
    warehouseSk: { sql: `inv_warehouse_sk`, type: `number` },
    quantityOnHand: { sql: `inv_quantity_on_hand`, type: `number` }
  }
});