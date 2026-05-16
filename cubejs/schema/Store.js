module.exports = {
  cube: {
    name: 'Store',
    sql: 'SELECT * FROM store',

    measures: {
      count: {
        type: 'count'
      },
      avgEmployees: {
        sql: 's_number_employees',
        type: 'avg'
      },
      avgFloorSpace: {
        sql: 's_floor_space',
        type: 'avg'
      }
    },

    dimensions: {
      storeSk: {
        sql: 's_store_sk',
        type: 'number',
        primaryKey: true
      },
      storeId: {
        sql: 's_store_id',
        type: 'string'
      },
      recStartDate: {
        sql: 's_rec_start_date',
        type: 'time'
      },
      recEndDate: {
        sql: 's_rec_end_date',
        type: 'time'
      },
      closedDateSk: {
        sql: 's_closed_date_sk',
        type: 'number'
      },
      storeName: {
        sql: 's_store_name',
        type: 'string'
      },
      numberEmployees: {
        sql: 's_number_employees',
        type: 'number'
      },
      floorSpace: {
        sql: 's_floor_space',
        type: 'number'
      },
      hours: {
        sql: 's_hours',
        type: 'string'
      },
      manager: {
        sql: 's_manager',
        type: 'string'
      },
      marketId: {
        sql: 's_market_id',
        type: 'number'
      },
      geographyClass: {
        sql: 's_geography_class',
        type: 'string'
      },
      marketDesc: {
        sql: 's_market_desc',
        type: 'string'
      },
      divisionId: {
        sql: 's_division_id',
        type: 'number'
      },
      divisionName: {
        sql: 's_division_name',
        type: 'string'
      },
      companyId: {
        sql: 's_company_id',
        type: 'number'
      },
      companyName: {
        sql: 's_company_name',
        type: 'string'
      },
      city: {
        sql: 's_city',
        type: 'string'
      },
      county: {
        sql: 's_county',
        type: 'string'
      },
      state: {
        sql: 's_state',
        type: 'string'
      },
      zip: {
        sql: 's_zip',
        type: 'string'
      },
      country: {
        sql: 's_country',
        type: 'string'
      }
    }
  }
};
