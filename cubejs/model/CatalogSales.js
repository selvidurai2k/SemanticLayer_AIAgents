cube(`CatalogSales`, {
  sql: `SELECT * FROM (
          SELECT cs.*, 
            d.d_year AS sold_year,
            d.d_date::timestamp AS sold_date
          FROM catalog_sales cs 
          LEFT JOIN date_dim d ON cs.cs_sold_date_sk = d.d_date_sk
        ) AS catalog_sales_enriched`,

  measures: {
    count: { type: `count` },
    totalNetPaid: { sql: `cs_net_paid`, type: `sum` },
    totalNetProfit: { sql: `cs_net_profit`, type: `sum` },
    totalQuantity: { sql: `cs_quantity`, type: `sum` },
    avgSalesPrice: { sql: `cs_sales_price`, type: `avg` },
    totalExtSalesPrice: { sql: `cs_ext_sales_price`, type: `sum` },
  
    ytdNetProfit: {
      sql: `cs_net_profit`,
      type: `sum`,
      filters: [{
        sql: `${CUBE}.sold_year = 2003`
      }]
    },

    ytdQuantity: {
      sql: `cs_quantity`,
      type: `sum`,
      filters: [{
        sql: `${CUBE}.sold_year = 2003`
      }]
    },

    yoyNetProfit: {
      sql: `cs_net_profit`,
      type: `sum`,
      filters: [{
        sql: `${CUBE}.sold_year = 2002`
      }]
    },

    yoyQuantity: {
      sql: `cs_quantity`,
      type: `sum`,
      filters: [{
        sql: `${CUBE}.sold_year = 2002`
      }]
    },

    last30DaysNetProfit: {
      sql: `cs_net_profit`,
      type: `sum`,
      filters: [{
        sql: `${CUBE}.sold_date >= (SELECT MAX(d_date) FROM date_dim WHERE d_year = 2003)::timestamp - INTERVAL '30 days'`
      }]
    },

    last30DaysQuantity: {
      sql: `cs_quantity`,
      type: `sum`,
      filters: [{
        sql: `${CUBE}.sold_date >= (SELECT MAX(d_date) FROM date_dim WHERE d_year = 2003)::timestamp - INTERVAL '30 days'`
      }]
    }
  },

  dimensions: {
    itemSk: { sql: `cs_item_sk`, type: `number`, primaryKey: true },
    orderNumber: { sql: `cs_order_number`, type: `number` },
    soldYear: { sql: `sold_year`, type: `number` },
    billCustomerSk: { sql: `cs_bill_customer_sk`, type: `number` },
    shipCustomerSk: { sql: `cs_ship_customer_sk`, type: `number` },
    warehouseSk: { sql: `cs_warehouse_sk`, type: `number` },
    quantity: { sql: `cs_quantity`, type: `number` },
    netProfit: { sql: `cs_net_profit`, type: `number` },
    netPaid: { sql: `cs_net_paid`, type: `number` },
    salesPrice: { sql: `cs_sales_price`, type: `number` }
  },
  pre_aggregations: {
    yearlyNetProfitQuantity: {
      type: `rollup`,
      measures: [CatalogSales.count, CatalogSales.totalNetProfit, CatalogSales.totalQuantity],
      dimensions: [CatalogSales.soldYear],
      external: false
    }
  }
});