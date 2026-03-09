function isNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function validateHelloPayload(payload) {
  const body = payload || {};

  if (body.type !== "HELLO") {
    return { ok: false, error: "type must be HELLO" };
  }

  if (!isNonEmptyString(body.vehicle_id)) {
    return { ok: false, error: "vehicle_id is required" };
  }

  if (!isNonEmptyString(body.firmware_version)) {
    return { ok: false, error: "firmware_version is required" };
  }

  if (!isNonEmptyString(body.timestamp)) {
    return { ok: false, error: "timestamp is required" };
  }

  return { ok: true };
}

module.exports = {
  validateHelloPayload,
};
