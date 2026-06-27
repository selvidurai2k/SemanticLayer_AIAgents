cube(`TimeDim`, {
  sql: `SELECT * FROM time_dim`,
  measures: {
    count: { type: `count` }
  },
  dimensions: {
    timeSk: { sql: `t_time_sk`, type: `number`, primaryKey: true },
    timeId: { sql: `t_time_id`, type: `string` },
    hour: { sql: `t_hour`, type: `number` },
    minute: { sql: `t_minute`, type: `number` },
    second: { sql: `t_second`, type: `number` },
    amPm: { sql: `t_am_pm`, type: `string` },
    shift: { sql: `t_shift`, type: `string` },
    subShift: { sql: `t_sub_shift`, type: `string` },
    mealTime: { sql: `t_meal_time`, type: `string` }
  }
});