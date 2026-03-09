const net = require("net");
const axios = require("axios");
const { consumeChunk, safeJsonParse } = require("./src/parser");
const { getForwardPath } = require("./src/handler");

const tcpPort = parseInt(process.env.TCP_PORT || "9000", 10);
const backendUrl = process.env.BACKEND_URL || "http://backend:8080";

function log(...args) {
  console.log(new Date().toISOString(), ...args);
}

const server = net.createServer((socket) => {
  const remote = `${socket.remoteAddress}:${socket.remotePort}`;
  log("Client connected", remote);

  socket.setEncoding("utf8");

  let buffer = "";

  socket.on("data", async (chunk) => {
    const parsedChunk = consumeChunk(buffer, chunk);
    buffer = parsedChunk.buffer;

    for (const line of parsedChunk.lines) {
      const parsedLine = safeJsonParse(line);
      if (!parsedLine.ok) {
        log("Invalid JSON from", remote, line);
        continue;
      }

      const msg = parsedLine.value;
      const forwardPath = getForwardPath(msg);

      if (!forwardPath) {
        log("Ignoring non-HELLO type", msg.type);
        socket.write("IGNORED\n");
        continue;
      }

      try {
        await axios.post(`${backendUrl}${forwardPath}`, msg, { timeout: 3000 });
        log("Forwarded HELLO", msg.vehicle_id);
        socket.write("OK\n");
      } catch (e) {
        log("Failed to forward HELLO", e.message);
        socket.write("ERR\n");
      }
    }
  });

  socket.on("close", () => log("Client disconnected", remote));
  socket.on("error", (err) => log("Socket error", remote, err.message));
});

server.listen(tcpPort, "0.0.0.0", () => {
  log(`Gateway TCP listening 0.0.0.0:${tcpPort}`);
});
