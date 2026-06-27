cube(`ShipMode`, {
  sql: `SELECT * FROM ship_mode`,
  measures: {
    count: { type: `count` }
  },
  dimensions: {
    shipModeSk: { sql: `sm_ship_mode_sk`, type: `number`, primaryKey: true },
    shipModeId: { sql: `sm_ship_mode_id`, type: `string` },
    shipModeCode: { sql: `sm_code`, type: `string` },
    carrier: { sql: `sm_carrier`, type: `string` },
    contract: { sql: `sm_contract`, type: `string` }
  }
});