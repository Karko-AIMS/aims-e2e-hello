async function ensureHelloTable(pool) {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS hello_messages (
      id SERIAL PRIMARY KEY,
      vehicle_id TEXT NOT NULL,
      firmware_version TEXT,
      ts TEXT,
      raw_json JSONB NOT NULL,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
  `);
}

async function insertHello(pool, payload) {
  await pool.query(
    `INSERT INTO hello_messages (vehicle_id, firmware_version, ts, raw_json)
     VALUES ($1, $2, $3, $4)`,
    [payload.vehicle_id, payload.firmware_version, payload.timestamp, payload]
  );
}

module.exports = {
  ensureHelloTable,
  insertHello,
};
