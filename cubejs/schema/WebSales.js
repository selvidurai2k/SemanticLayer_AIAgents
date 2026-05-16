module.exports = {
  cube: {
    name: 'WebSales',
    sql: 'SELECT * FROM web_sales',

    measures: {
      count: {
        type: 'count'
      },
      totalNetPaid: {
        sql: 'ws_net_paid',
        type: 'sum'
      },
      totalNetProfit: {
        sql: 'ws_net_profit',
        type: 'sum'
      },
      totalQuantity: {
        sql: 'ws_quantity',
        type: 'sum'
      },
      avgSalesPrice: {
        sql: 'ws_sales_price',
        type: 'avg'
      },
      totalExtSalesPrice: {
        sql: 'ws_ext_sales_price',
        type: 'sum'
      }
    },

    dimensions: {
      itemSk: {
        sql: 'ws_item_sk',
        type: 'number',
        primaryKey: true
      },
      orderNumber: {
        sql: 'ws_order_number',
        type: 'number',
        primaryKey: true
      },
      billCustomerSk: {
        sql: 'ws_bill_customer_sk',
        type: 'number'
      },
      shipCustomerSk: {
        sql: 'ws_ship_customer_sk',
        type: 'number'
      },
      webPageSk: {
        sql: 'ws_web_page_sk',
        type: 'number'
      },
      webSiteSk: {
        sql: 'ws_web_site_sk',
        type: 'number'
      },
      warehouseSk: {
        sql: 'ws_warehouse_sk',
        type: 'number'
      },
      promoSk: {
        sql: 'ws_promo_sk',
        type: 'number'
      },
      soldDate: {
        sql: 'ws_sold_date_sk',
        type: 'time'
      },
      shipDate: {
        sql: 'ws_ship_date_sk',
        type: 'time'
      },
      quantity: {
        sql: 'ws_quantity',
        type: 'number'
      },
      salesPrice: {
        sql: 'ws_sales_price',
        type: 'number'
      },
      netPaid: {
        sql: 'ws_net_paid',
        type: 'number'
      }
    }
  }
};
