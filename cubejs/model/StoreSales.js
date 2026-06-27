cube(`StoreSales`, {
    sql: 'SELECT * FROM store_sales',

    measures: {
      count: {
        type: 'count'
      },
      totalNetPaid: {
        sql: 'ss_net_paid',
        type: 'sum'
      },
      totalNetPaidIncTax: {
        sql: 'ss_net_paid_inc_tax',
        type: 'sum'
      },
      totalNetProfit: {
        sql: 'ss_net_profit',
        type: 'sum'
      },
      totalQuantity: {
        sql: 'ss_quantity',
        type: 'sum'
      },
      avgSalesPrice: {
        sql: 'ss_sales_price',
        type: 'avg'
      },
      avgListPrice: {
        sql: 'ss_list_price',
        type: 'avg'
      },
      maxSalesPrice: {
        sql: 'ss_sales_price',
        type: 'max'
      },
      minSalesPrice: {
        sql: 'ss_sales_price',
        type: 'min'
      }
    },

    dimensions: {
      itemSk: {
        sql: 'ss_item_sk',
        type: 'number',
        primaryKey: true
      },
      customerSk: {
        sql: 'ss_customer_sk',
        type: 'number'
      },
      storeSk: {
        sql: 'ss_store_sk',
        type: 'number'
      },
      cdemSk: {
        sql: 'ss_cdemo_sk',
        type: 'number'
      },
      hdemSk: {
        sql: 'ss_hdemo_sk',
        type: 'number'
      },
      addrSk: {
        sql: 'ss_addr_sk',
        type: 'number'
      },
      promoSk: {
        sql: 'ss_promo_sk',
        type: 'number'
      },
      ticketNumber: {
        sql: 'ss_ticket_number',
        type: 'number'
      },
      soldDate: {
        sql: 'ss_sold_date_sk',
        type: 'time'
      },
      soldTime: {
        sql: 'ss_sold_time_sk',
        type: 'number'
      },
      quantity: {
        sql: 'ss_quantity',
        type: 'number'
      },
      wholesaleCost: {
        sql: 'ss_wholesale_cost',
        type: 'number'
      },
      listPrice: {
        sql: 'ss_list_price',
        type: 'number'
      },
      salesPrice: {
        sql: 'ss_sales_price',
        type: 'number'
      },
      netPaid: {
        sql: 'ss_net_paid',
        type: 'number'
      },
      netProfit: {
        sql: 'ss_net_profit',
        type: 'number'
      }
    }
});