require("dotenv").config();

function maskSecret(value) {
  if (!value) return "(empty)";
  if (value.length <= 2) return "*".repeat(value.length);
  return value[0] + "*".repeat(value.length - 2) + value[value.length - 1];
}

const envs = {
  NODE_ENV: process.env.NODE_ENV,
  DB_HOST: process.env.DB_HOST,
  DB_PORT: process.env.DB_PORT,
  DB_NAME: process.env.DB_NAME,
  DB_USER: process.env.DB_USER,
  DB_PASSWORD: maskSecret(process.env.DB_PASSWORD),
  BACKEND_URL: process.env.BACKEND_URL,
  BACKEND_PORT: process.env.BACKEND_PORT,
  TCP_PORT: process.env.TCP_PORT,
  IMAGE_TAG: process.env.IMAGE_TAG
};

console.log("Loaded environment variables:");
console.table(envs);

const requiredKeys = [
  "NODE_ENV",
  "DB_HOST",
  "DB_PORT",
  "DB_NAME",
  "DB_USER",
  "DB_PASSWORD",
  "BACKEND_URL",
  "BACKEND_PORT",
  "TCP_PORT"
];

const missingKeys = requiredKeys.filter((key) => !process.env[key]);

if (missingKeys.length > 0) {
  console.error("Missing required env keys:", missingKeys.join(", "));
  process.exit(1);
}

console.log("All required env keys are present.");