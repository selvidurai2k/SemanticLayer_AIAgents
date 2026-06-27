cube(`DateDim`, {
    sql: 'SELECT * FROM date_dim',

    measures: {
      count: {
        type: 'count'
      }
    },

    dimensions: {
      dateSk: {
        sql: 'd_date_sk',
        type: 'number',
        primaryKey: true
      },
      dateId: {
        sql: 'd_date_id',
        type: 'string'
      },
      date: {
        sql: 'd_date',
        type: 'time'
      },
      monthSeq: {
        sql: 'd_month_seq',
        type: 'number'
      },
      weekSeq: {
        sql: 'd_week_seq',
        type: 'number'
      },
      quarterSeq: {
        sql: 'd_quarter_seq',
        type: 'number'
      },
      year: {
        sql: 'd_year',
        type: 'number'
      },
      dayOfWeek: {
        sql: 'd_dow',
        type: 'number'
      },
      monthOfYear: {
        sql: 'd_moy',
        type: 'number'
      },
      dayOfMonth: {
        sql: 'd_dom',
        type: 'number'
      },
      quarterOfYear: {
        sql: 'd_qoy',
        type: 'number'
      },
      fiscalYear: {
        sql: 'd_fy_year',
        type: 'number'
      },
      dayName: {
        sql: 'd_day_name',
        type: 'string'
      },
      quarterName: {
        sql: 'd_quarter_name',
        type: 'string'
      },
      holiday: {
        sql: 'd_holiday',
        type: 'string'
      },
      weekend: {
        sql: 'd_weekend',
        type: 'string'
      }
    }
});