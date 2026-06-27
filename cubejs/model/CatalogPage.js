cube(`CatalogPage`, {
  sql: `SELECT * FROM catalog_page`,
  measures: {
    count: { type: `count` }
  },
  dimensions: {
    catalogPageSk: { sql: `cp_catalog_page_sk`, type: `number`, primaryKey: true },
    catalogPageId: { sql: `cp_catalog_page_id`, type: `string` },
    startDateSk: { sql: `cp_start_date_sk`, type: `number` },
    endDateSk: { sql: `cp_end_date_sk`, type: `number` },
    department: { sql: `cp_department`, type: `string` },
    catalogNumber: { sql: `cp_catalog_number`, type: `number` },
    catalogPageNumber: { sql: `cp_catalog_page_number`, type: `number` },
    description: { sql: `cp_description`, type: `string` }
  }
});