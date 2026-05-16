module.exports = {
  cube: {
    name: 'Customer',
    sql: 'SELECT * FROM customer',

    measures: {
      count: {
        type: 'count'
      }
    },

    dimensions: {
      customerSk: {
        sql: 'c_customer_sk',
        type: 'number',
        primaryKey: true
      },
      customerId: {
        sql: 'c_customer_id',
        type: 'string'
      },
      cdemSk: {
        sql: 'c_current_cdemo_sk',
        type: 'number'
      },
      hdemSk: {
        sql: 'c_current_hdemo_sk',
        type: 'number'
      },
      addrSk: {
        sql: 'c_current_addr_sk',
        type: 'number'
      },
      firstShiptoDateSk: {
        sql: 'c_first_shipto_date_sk',
        type: 'time'
      },
      firstSalesDateSk: {
        sql: 'c_first_sales_date_sk',
        type: 'time'
      },
      salutation: {
        sql: 'c_salutation',
        type: 'string'
      },
      firstName: {
        sql: 'c_first_name',
        type: 'string'
      },
      lastName: {
        sql: 'c_last_name',
        type: 'string'
      },
      preferredCustFlag: {
        sql: 'c_preferred_cust_flag',
        type: 'string'
      },
      birthDay: {
        sql: 'c_birth_day',
        type: 'number'
      },
      birthMonth: {
        sql: 'c_birth_month',
        type: 'number'
      },
      birthYear: {
        sql: 'c_birth_year',
        type: 'number'
      },
      birthCountry: {
        sql: 'c_birth_country',
        type: 'string'
      },
      emailAddress: {
        sql: 'c_email_address',
        type: 'string'
      }
    }
  }
};
