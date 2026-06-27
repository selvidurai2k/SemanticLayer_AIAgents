cube(`CustomerDemographics`, {
  sql: `SELECT * FROM customer_demographics`,
  measures: {
    count: { type: `count` }
  },
  dimensions: {
    demoSk: { sql: `cd_demo_sk`, type: `number`, primaryKey: true },
    gender: { sql: `cd_gender`, type: `string` },
    maritalStatus: { sql: `cd_marital_status`, type: `string` },
    educationStatus: { sql: `cd_education_status`, type: `string` },
    purchaseEstimate: { sql: `cd_purchase_estimate`, type: `number` },
    creditRating: { sql: `cd_credit_rating`, type: `string` },
    depCount: { sql: `cd_dep_count`, type: `number` },
    depEmployedCount: { sql: `cd_dep_employed_count`, type: `number` },
    depCollegeCount: { sql: `cd_dep_college_count`, type: `number` }
  }
});