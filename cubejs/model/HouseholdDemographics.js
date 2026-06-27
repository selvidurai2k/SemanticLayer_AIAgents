cube(`HouseholdDemographics`, {
  sql: `SELECT * FROM household_demographics`,
  measures: {
    count: { type: `count` }
  },
  dimensions: {
    demoSk: { sql: `hd_demo_sk`, type: `number`, primaryKey: true },
    incomeBandSk: { sql: `hd_income_band_sk`, type: `number` },
    buyPotential: { sql: `hd_buy_potential`, type: `string` },
    depCount: { sql: `hd_dep_count`, type: `number` },
    vehicleCount: { sql: `hd_vehicle_count`, type: `number` }
  }
});