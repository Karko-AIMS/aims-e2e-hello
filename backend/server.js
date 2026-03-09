const { Pool } = require("pg");
const { createApp } = require("./src/createApp");
const { ensureHelloTable } = require("./src/helloRepository");

const port = process.env.PORT || 8080;
const dbUrl = process.env.DATABASE_URL;

const pool = new Pool({ connectionString: dbUrl });
const app = createApp({ pool });

async function init() {
  await ensureHelloTable(pool);
  console.log("DB init OK");
}

init()
  .then(() => app.listen(port, () => console.log(`Backend listening :${port}`)))
  .catch((e) => {
    console.error("Failed to init DB", e);
    process.exit(1);
  });
