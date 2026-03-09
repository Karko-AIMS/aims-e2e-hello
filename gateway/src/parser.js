function consumeChunk(buffer, chunk) {
  const merged = `${buffer}${chunk}`;
  const lines = [];
  let start = 0;

  while (true) {
    const newlineIndex = merged.indexOf("\n", start);
    if (newlineIndex === -1) {
      break;
    }

    const rawLine = merged.slice(start, newlineIndex).trim();
    if (rawLine) {
      lines.push(rawLine);
    }
    start = newlineIndex + 1;
  }

  return {
    lines,
    buffer: merged.slice(start),
  };
}

function safeJsonParse(line) {
  try {
    return { ok: true, value: JSON.parse(line) };
  } catch (error) {
    return { ok: false, error };
  }
}

module.exports = {
  consumeChunk,
  safeJsonParse,
};
