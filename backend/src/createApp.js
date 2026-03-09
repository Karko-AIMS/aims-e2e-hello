const express = require("express");
const { validateHelloPayload } = require("./validateHello");
const { insertHello } = require("./helloRepository");

function createApp({ pool, logger = console }) {
  if (!pool) {
    throw new Error("pool is required");
  }

  const app = express();
  app.use(express.json({ limit: "1mb" }));

  app.get("/health", (req, res) => res.json({ ok: true }));

  app.post("/ingest/hello", async (req, res) => {
    const body = req.body || {};
    const validation = validateHelloPayload(body);

    if (!validation.ok) {
      return res.status(400).json({ ok: false, error: validation.error });
    }

    try {
      await insertHello(pool, body);
      return res.json({ ok: true });
    } catch (error) {
      logger.error("Failed to insert HELLO", error.message);
      return res.status(500).json({ ok: false, error: "DB insert failed" });
    }
  });

  return app;
}

module.exports = {
  createApp,
};
