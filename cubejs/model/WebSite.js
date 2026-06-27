cube(`WebSite`, {
  sql: `SELECT * FROM web_site`,
  measures: {
    count: { type: `count` }
  },
  dimensions: {
    webSiteSk: { sql: `web_site_sk`, type: `number`, primaryKey: true },
    webSiteId: { sql: `web_site_id`, type: `string` },
    name: { sql: `web_name`, type: `string` },
    openDateSk: { sql: `web_open_date_sk`, type: `number` },
    city: { sql: `web_city`, type: `string` },
    state: { sql: `web_state`, type: `string` },
    country: { sql: `web_country`, type: `string` },
    manager: { sql: `web_manager`, type: `string` }
  }
});