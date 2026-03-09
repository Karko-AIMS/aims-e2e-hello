const { getForwardPath, HELLO_PATH } = require("../src/handler");

describe("getForwardPath", () => {
  test('returns HELLO path when type is "HELLO"', () => {
    const path = getForwardPath({ type: "HELLO", vehicle_id: "V1" });

    expect(path).toBe(HELLO_PATH);
  });

  test("returns null when type is missing", () => {
    const path = getForwardPath({ vehicle_id: "V1" });

    expect(path).toBeNull();
  });

  test("returns null when type is not HELLO", () => {
    const path = getForwardPath({ type: "PING" });

    expect(path).toBeNull();
  });
});
