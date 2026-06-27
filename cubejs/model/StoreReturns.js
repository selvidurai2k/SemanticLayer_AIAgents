cube(`StoreReturns`, {
  sql: `SELECT * FROM store_returns`,
  measures: {
    count: { type: `count` },
    totalReturnAmount: { sql: `sr_return_amt`, type: `sum` },
    totalNetLoss: { sql: `sr_net_loss`, type: `sum` },
    totalReturnQuantity: { sql: `sr_return_quantity`, type: `sum` }
  },
  dimensions: {
    itemSk: { sql: `sr_item_sk`, type: `number`, primaryKey: true },
    ticketNumber: { sql: `sr_ticket_number`, type: `number` },
    returnedDateSk: { sql: `sr_returned_date_sk`, type: `number` },
    storeSk: { sql: `sr_store_sk`, type: `number` },
    customerSk: { sql: `sr_customer_sk`, type: `number` },
    reasonSk: { sql: `sr_reason_sk`, type: `number` },
    returnQuantity: { sql: `sr_return_quantity`, type: `number` },
    returnAmt: { sql: `sr_return_amt`, type: `number` },
    netLoss: { sql: `sr_net_loss`, type: `number` }
  }
});