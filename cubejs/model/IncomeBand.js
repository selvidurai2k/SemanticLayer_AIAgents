cube(`IncomeBand`, {
  sql: `SELECT * FROM income_band`,
  measures: {
    count: { type: `count` }
  },
  dimensions: {
    incomeBandSk: { sql: `ib_income_band_sk`, type: `number`, primaryKey: true },
    lowerBound: { sql: `ib_lower_bound`, type: `number` },
    upperBound: { sql: `ib_upper_bound`, type: `number` }
  }
});