cube(`Reason`, {
  sql: `SELECT * FROM reason`,
  measures: {
    count: { type: `count` }
  },
  dimensions: {
    reasonSk: { sql: `r_reason_sk`, type: `number`, primaryKey: true },
    reasonId: { sql: `r_reason_id`, type: `string` },
    reasonDescription: { sql: `r_reason_desc`, type: `string` }
  }
});