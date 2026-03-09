const request = require("supertest");
const { Pool } = require("pg");
const { createApp } = require("../src/createApp");
const { ensureHelloTable } = require("../src/helloRepository");

const dbUrl = process.env.DATABASE_URL || "postgres://aims:aims@127.0.0.1:5432/aims";

jest.setTimeout(20000);

describe("POST /ingest/hello integration", () => {
  let pool;
  let app;

  beforeAll(async () => {
    pool = new Pool({ connectionString: dbUrl });
    await ensureHelloTable(pool);
    app = createApp({ pool, logger: { error: () => {} } });
  });

  beforeEach(async () => {
    await pool.query("TRUNCATE TABLE hello_messages RESTART IDENTITY");
  });

  afterAll(async () => {
    await pool.end();
  });

  test("stores a row for valid payload", async () => {
    const payload = {
      type: "HELLO",
      vehicle_id: "IT-001",
      firmware_version: "int-test",
      timestamp: "2026-03-09T12:00:00+09:00",
    };

    const response = await request(app).post("/ingest/hello").send(payload);

    expect(response.status).toBe(200);
    expect(response.body).toEqual({ ok: true });

    const rows = await pool.query(
      "SELECT vehicle_id, firmware_version, ts FROM hello_messages WHERE vehicle_id = $1",
      [payload.vehicle_id]
    );

    expect(rows.rowCount).toBe(1);
    expect(rows.rows[0]).toEqual({
      vehicle_id: payload.vehicle_id,
      firmware_version: payload.firmware_version,
      ts: payload.timestamp,
    });
  });

  test("does not insert row for invalid payload", async () => {
    const invalidPayload = {
      type: "HELLO",
      vehicle_id: "IT-002",
      firmware_version: "int-test",
    };

    const response = await request(app).post("/ingest/hello").send(invalidPayload);

    expect(response.status).toBeGreaterThanOrEqual(400);
    expect(response.status).toBeLessThan(500);

    const count = await pool.query(
      "SELECT count(*)::int AS cnt FROM hello_messages WHERE vehicle_id = $1",
      [invalidPayload.vehicle_id]
    );

    expect(count.rows[0].cnt).toBe(0);
  });
});
