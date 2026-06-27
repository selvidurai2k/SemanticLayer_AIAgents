cube(`WebPage`, {
  sql: `SELECT * FROM web_page`,
  measures: {
    count: { type: `count` }
  },
  dimensions: {
    webPageSk: { sql: `wp_web_page_sk`, type: `number`, primaryKey: true },
    webPageId: { sql: `wp_web_page_id`, type: `string` },
    recStartDate: { sql: `wp_rec_start_date`, type: `string` },
    recEndDate: { sql: `wp_rec_end_date`, type: `string` },
    creationDateSk: { sql: `wp_creation_date_sk`, type: `number` },
    accessDateSk: { sql: `wp_access_date_sk`, type: `number` },
    autogenFlag: { sql: `wp_autogen_flag`, type: `string` },
    url: { sql: `wp_url`, type: `string` },
    type: { sql: `wp_type`, type: `string` }
  }
});