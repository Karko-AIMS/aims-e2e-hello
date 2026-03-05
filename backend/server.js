const express = require("express");
const { Pool } = require("pg");

const app = express();
app.use(express.json({ limit: "1mb" }));

const port = process.env.PORT || 8080;
const dbUrl = process.env.DATABASE_URL;

const pool = new Pool({ connectionString: dbUrl });

async function init() {
  // 테이블 없으면 생성
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
  console.log("DB init OK");
}

app.get("/health", (req, res) => res.json({ ok: true }));

// Gateway가 여기에 전달
app.post("/ingest/hello", async (req, res) => {
  const body = req.body || {};
  if (body.type !== "HELLO" || !body.vehicle_id) {
    return res.status(400).json({ ok: false, error: "Invalid HELLO payload" });
  }

  await pool.query(
    `INSERT INTO hello_messages (vehicle_id, firmware_version, ts, raw_json)
     VALUES ($1, $2, $3, $4)`,
    [body.vehicle_id, body.firmware_version || null, body.timestamp || null, body]
  );

  res.json({ ok: true });
});

init()
  .then(() => app.listen(port, () => console.log(`Backend listening :${port}`)))
  .catch((e) => {
    console.error("Failed to init DB", e);
    process.exit(1);
  });