const { consumeChunk, safeJsonParse } = require("../src/parser");

describe("consumeChunk", () => {
  test("extracts one message from single JSON line with newline", () => {
    const result = consumeChunk("", '{"type":"HELLO"}\n');

    expect(result.lines).toEqual(['{"type":"HELLO"}']);
    expect(result.buffer).toBe("");
  });

  test("extracts two messages from msg1\\nmsg2\\n", () => {
    const input = '{"type":"HELLO"}\n{"type":"HELLO","vehicle_id":"V1"}\n';
    const result = consumeChunk("", input);

    expect(result.lines).toEqual([
      '{"type":"HELLO"}',
      '{"type":"HELLO","vehicle_id":"V1"}',
    ]);
    expect(result.buffer).toBe("");
  });

  test("returns no complete message for partial chunk", () => {
    const result = consumeChunk("", '{"type":"HELLO"');

    expect(result.lines).toEqual([]);
    expect(result.buffer).toBe('{"type":"HELLO"');
  });

  test("completes message when next chunk includes newline", () => {
    const first = consumeChunk("", '{"type":"HELLO"');
    const second = consumeChunk(first.buffer, ',"vehicle_id":"A"}\n');

    expect(first.lines).toEqual([]);
    expect(second.lines).toEqual(['{"type":"HELLO","vehicle_id":"A"}']);
    expect(second.buffer).toBe("");
  });
});

describe("safeJsonParse", () => {
  test("handles malformed JSON safely", () => {
    const malformed = '{"type":';

    expect(() => safeJsonParse(malformed)).not.toThrow();

    const result = safeJsonParse(malformed);
    expect(result.ok).toBe(false);
    expect(result.error).toBeInstanceOf(Error);
  });
});
