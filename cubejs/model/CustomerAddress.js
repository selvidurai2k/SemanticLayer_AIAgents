cube(`CustomerAddress`, {
  sql: `SELECT * FROM customer_address`,
  measures: {
    count: { type: `count` }
  },
  dimensions: {
    addressSk: { sql: `ca_address_sk`, type: `number`, primaryKey: true },
    addressId: { sql: `ca_address_id`, type: `string` },
    city: { sql: `ca_city`, type: `string` },
    county: { sql: `ca_county`, type: `string` },
    state: { sql: `ca_state`, type: `string` },
    zip: { sql: `ca_zip`, type: `string` },
    country: { sql: `ca_country`, type: `string` },
    gmtOffset: { sql: `ca_gmt_offset`, type: `number` },
    locationType: { sql: `ca_location_type`, type: `string` }
  }
});