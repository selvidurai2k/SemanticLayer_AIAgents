module.exports = {
  cube: {
    name: 'CatalogSales',
    sql: 'SELECT * FROM catalog_sales',

    measures: {
      count: {
        type: 'count'
      },
      totalNetPaid: {
        sql: 'cs_net_paid',
        type: 'sum'
      },
      totalNetProfit: {
        sql: 'cs_net_profit',
        type: 'sum'
      },
      totalQuantity: {
        sql: 'cs_quantity',
        type: 'sum'
      },
      avgSalesPrice: {
        sql: 'cs_sales_price',
        type: 'avg'
      },
      totalExtSalesPrice: {
        sql: 'cs_ext_sales_price',
        type: 'sum'
      }
    },

    dimensions: {
      itemSk: {
        sql: 'cs_item_sk',
        type: 'number',
        primaryKey: true
      },
      orderNumber: {
        sql: 'cs_order_number',
        type: 'number',
        primaryKey: true
      },
      billCustomerSk: {
        sql: 'cs_bill_customer_sk',
        type: 'number'
      },
      shipCustomerSk: {
        sql: 'cs_ship_customer_sk',
        type: 'number'
      },
      callCenterSk: {
        sql: 'cs_call_center_sk',
        type: 'number'
      },
      catalogPageSk: {
        sql: 'cs_catalog_page_sk',
        type: 'number'
      },
      warehouseSk: {
        sql: 'cs_warehouse_sk',
        type: 'number'
      },
      promoSk: {
        sql: 'cs_promo_sk',
        type: 'number'
      },
      soldDate: {
        sql: 'cs_sold_date_sk',
        type: 'time'
      },
      shipDate: {
        sql: 'cs_ship_date_sk',
        type: 'time'
      },
      quantity: {
        sql: 'cs_quantity',
        type: 'number'
      },
      salesPrice: {
        sql: 'cs_sales_price',
        type: 'number'
      },
      netPaid: {
        sql: 'cs_net_paid',
        type: 'number'
      }
    }
  }
};
