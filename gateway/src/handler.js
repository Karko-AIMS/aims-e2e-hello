const HELLO_PATH = "/ingest/hello";

function getForwardPath(message) {
  if (message && message.type === "HELLO") {
    return HELLO_PATH;
  }
  return null;
}

module.exports = {
  HELLO_PATH,
  getForwardPath,
};
