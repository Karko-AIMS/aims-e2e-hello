const net = require("net");
const axios = require("axios");

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
    buffer += chunk;

    // newline-delimited 처리
    while (true) {
      const idx = buffer.indexOf("\n");
      if (idx === -1) break;

      const line = buffer.slice(0, idx).trim();
      buffer = buffer.slice(idx + 1);

      if (!line) continue;

      let msg;
      try {
        msg = JSON.parse(line);
      } catch (e) {
        log("Invalid JSON from", remote, line);
        continue;
      }

      if (msg.type === "HELLO") {
        try {
          await axios.post(`${backendUrl}/ingest/hello`, msg, { timeout: 3000 });
          log("Forwarded HELLO", msg.vehicle_id);
          socket.write(`OK\n`);
        } catch (e) {
          log("Failed to forward HELLO", e.message);
          socket.write(`ERR\n`);
        }
      } else {
        log("Ignoring non-HELLO type", msg.type);
        socket.write(`IGNORED\n`);
      }
    }
  });

  socket.on("close", () => log("Client disconnected", remote));
  socket.on("error", (err) => log("Socket error", remote, err.message));
});

server.listen(tcpPort, "0.0.0.0", () => {
  log(`Gateway TCP listening 0.0.0.0:${tcpPort}`);
});