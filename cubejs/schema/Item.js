module.exports = {
  cube: {
    name: 'Item',
    sql: 'SELECT * FROM item',

    measures: {
      count: {
        type: 'count'
      },
      avgCurrentPrice: {
        sql: 'i_current_price',
        type: 'avg'
      },
      avgWholesaleCost: {
        sql: 'i_wholesale_cost',
        type: 'avg'
      }
    },

    dimensions: {
      itemSk: {
        sql: 'i_item_sk',
        type: 'number',
        primaryKey: true
      },
      itemId: {
        sql: 'i_item_id',
        type: 'string'
      },
      recStartDate: {
        sql: 'i_rec_start_date',
        type: 'time'
      },
      recEndDate: {
        sql: 'i_rec_end_date',
        type: 'time'
      },
      itemDesc: {
        sql: 'i_item_desc',
        type: 'string'
      },
      currentPrice: {
        sql: 'i_current_price',
        type: 'number'
      },
      wholesaleCost: {
        sql: 'i_wholesale_cost',
        type: 'number'
      },
      brandId: {
        sql: 'i_brand_id',
        type: 'number'
      },
      brand: {
        sql: 'i_brand',
        type: 'string'
      },
      classId: {
        sql: 'i_class_id',
        type: 'number'
      },
      class: {
        sql: 'i_class',
        type: 'string'
      },
      categoryId: {
        sql: 'i_category_id',
        type: 'number'
      },
      category: {
        sql: 'i_category',
        type: 'string'
      },
      manufactId: {
        sql: 'i_manufact_id',
        type: 'number'
      },
      manufact: {
        sql: 'i_manufact',
        type: 'string'
      },
      size: {
        sql: 'i_size',
        type: 'string'
      },
      color: {
        sql: 'i_color',
        type: 'string'
      },
      units: {
        sql: 'i_units',
        type: 'string'
      }
    }
  }
};
