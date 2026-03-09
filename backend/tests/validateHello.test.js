const { validateHelloPayload } = require("../src/validateHello");

describe("validateHelloPayload", () => {
  const validPayload = {
    type: "HELLO",
    vehicle_id: "VHC-001",
    firmware_version: "1.0.0",
    timestamp: "2026-03-09T12:00:00+09:00",
  };

  test("passes valid HELLO payload", () => {
    expect(validateHelloPayload(validPayload)).toEqual({ ok: true });
  });

  test("fails when vehicle_id is missing", () => {
    const payload = { ...validPayload };
    delete payload.vehicle_id;

    expect(validateHelloPayload(payload)).toEqual({
      ok: false,
      error: "vehicle_id is required",
    });
  });

  test("fails when firmware_version is missing", () => {
    const payload = { ...validPayload };
    delete payload.firmware_version;

    expect(validateHelloPayload(payload)).toEqual({
      ok: false,
      error: "firmware_version is required",
    });
  });

  test("fails when timestamp is missing", () => {
    const payload = { ...validPayload };
    delete payload.timestamp;

    expect(validateHelloPayload(payload)).toEqual({
      ok: false,
      error: "timestamp is required",
    });
  });

  test("fails when type is not HELLO", () => {
    const payload = { ...validPayload, type: "PING" };

    expect(validateHelloPayload(payload)).toEqual({
      ok: false,
      error: "type must be HELLO",
    });
  });
});
