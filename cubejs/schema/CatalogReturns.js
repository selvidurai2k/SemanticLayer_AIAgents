module.exports = {
  cube: {
    name: 'CatalogReturns',
    sql: 'SELECT * FROM catalog_returns',

    measures: {
      count: {
        type: 'count'
      },
      totalReturnAmount: {
        sql: 'cr_return_amount',
        type: 'sum'
      },
      totalReturnQuantity: {
        sql: 'cr_return_quantity',
        type: 'sum'
      },
      avgReturnAmount: {
        sql: 'cr_return_amount',
        type: 'avg'
      },
      totalNetLoss: {
        sql: 'cr_net_loss',
        type: 'sum'
      }
    },

    dimensions: {
      itemSk: {
        sql: 'cr_item_sk',
        type: 'number',
        primaryKey: true
      },
      orderNumber: {
        sql: 'cr_order_number',
        type: 'number',
        primaryKey: true
      },
      returnedDateSk: {
        sql: 'cr_returned_date_sk',
        type: 'time'
      },
      returnedTimeSk: {
        sql: 'cr_returned_time_sk',
        type: 'number'
      },
      refundedCustomerSk: {
        sql: 'cr_refunded_customer_sk',
        type: 'number'
      },
      returningCustomerSk: {
        sql: 'cr_returning_customer_sk',
        type: 'number'
      },
      callCenterSk: {
        sql: 'cr_call_center_sk',
        type: 'number'
      },
      catalogPageSk: {
        sql: 'cr_catalog_page_sk',
        type: 'number'
      },
      warehouseSk: {
        sql: 'cr_warehouse_sk',
        type: 'number'
      },
      reasonSk: {
        sql: 'cr_reason_sk',
        type: 'number'
      },
      returnQuantity: {
        sql: 'cr_return_quantity',
        type: 'number'
      },
      returnAmount: {
        sql: 'cr_return_amount',
        type: 'number'
      },
      returnAmtIncTax: {
        sql: 'cr_return_amt_inc_tax',
        type: 'number'
      },
      netLoss: {
        sql: 'cr_net_loss',
        type: 'number'
      }
    }
  }
};
