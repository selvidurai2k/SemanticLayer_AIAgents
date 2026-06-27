cube(`Promotion`, {
  sql: `SELECT * FROM promotion`,
  measures: {
    count: { type: `count` },
    totalCost: { sql: `p_cost`, type: `sum` }
  },
  dimensions: {
    promoSk: { sql: `p_promo_sk`, type: `number`, primaryKey: true },
    promoId: { sql: `p_promo_id`, type: `string` },
    promoName: { sql: `p_promo_name`, type: `string` },
    startDateSk: { sql: `p_start_date_sk`, type: `number` },
    endDateSk: { sql: `p_end_date_sk`, type: `number` },
    itemSk: { sql: `p_item_sk`, type: `number` },
    cost: { sql: `p_cost`, type: `number` },
    responseTarget: { sql: `p_response_target`, type: `number` }
  }
});