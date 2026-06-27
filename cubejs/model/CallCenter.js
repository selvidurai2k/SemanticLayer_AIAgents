cube(`CallCenter`, {
  sql: `SELECT * FROM call_center`,
  measures: {
    count: { type: `count` },
    avgEmployees: { sql: `cc_employees`, type: `avg` },
    totalSqFt: { sql: `cc_sq_ft`, type: `sum` }
  },
  dimensions: {
    callCenterSk: { sql: `cc_call_center_sk`, type: `number`, primaryKey: true },
    callCenterId: { sql: `cc_call_center_id`, type: `string` },
    name: { sql: `cc_name`, type: `string` },
    city: { sql: `cc_city`, type: `string` },
    state: { sql: `cc_state`, type: `string` },
    country: { sql: `cc_country`, type: `string` },
    manager: { sql: `cc_manager`, type: `string` },
    employees: { sql: `cc_employees`, type: `number` }
  }
});