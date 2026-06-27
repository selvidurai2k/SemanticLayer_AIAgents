cube(`WebReturns`, {
  sql: `SELECT * FROM web_returns`,
  measures: {
    count: { type: `count` },
    totalReturnAmount: { sql: `wr_return_amt`, type: `sum` },
    totalNetLoss: { sql: `wr_net_loss`, type: `sum` },
    totalReturnQuantity: { sql: `wr_return_quantity`, type: `sum` }
  },
  dimensions: {
    itemSk: { sql: `wr_item_sk`, type: `number`, primaryKey: true },
    orderNumber: { sql: `wr_order_number`, type: `number` },
    returnedDateSk: { sql: `wr_returned_date_sk`, type: `number` },
    webPageSk: { sql: `wr_web_page_sk`, type: `number` },
    reasonSk: { sql: `wr_reason_sk`, type: `number` },
    returnQuantity: { sql: `wr_return_quantity`, type: `number` },
    returnAmt: { sql: `wr_return_amt`, type: `number` },
    netLoss: { sql: `wr_net_loss`, type: `number` }
  }
});