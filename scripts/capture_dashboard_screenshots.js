const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawn } = require("node:child_process");

const port = Number(process.env.CDP_PORT || "9224");
const outDir = process.env.OUT_DIR || path.resolve("docs", "screenshots");
const dashboardUrl = process.env.DASHBOARD_URL || "http://127.0.0.1:8502/";
const edgePath = process.env.EDGE_PATH || "";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function json(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return await response.json();
}

async function waitForTarget() {
  for (let index = 0; index < 80; index += 1) {
    try {
      const targets = await json(`http://127.0.0.1:${port}/json`);
      const target =
        targets.find((item) => item.type === "page" && item.url.includes("127.0.0.1:8502")) ||
        targets.find((item) => item.type === "page");
      if (target?.webSocketDebuggerUrl) {
        return target.webSocketDebuggerUrl;
      }
    } catch {
      // Chrome may need a moment to open the debugging endpoint.
    }
    await sleep(250);
  }
  throw new Error("Timed out waiting for CDP target.");
}

async function connect(wsUrl) {
  const ws = new WebSocket(wsUrl);
  const pending = new Map();
  let id = 0;

  ws.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const { resolve, reject } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) {
        reject(new Error(JSON.stringify(message.error)));
      } else {
        resolve(message.result);
      }
    }
  });

  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener("error", reject, { once: true });
  });

  return {
    send(method, params = {}) {
      const callId = ++id;
      ws.send(JSON.stringify({ id: callId, method, params }));
      return new Promise((resolve, reject) => pending.set(callId, { resolve, reject }));
    },
    close() {
      ws.close();
    },
  };
}

async function waitForText(client, text) {
  for (let index = 0; index < 120; index += 1) {
    const result = await client.send("Runtime.evaluate", {
      expression: `document.body && document.body.innerText.includes(${JSON.stringify(text)})`,
      returnByValue: true,
    });
    if (result.result?.value === true) {
      return;
    }
    await sleep(500);
  }
  throw new Error(`Timed out waiting for dashboard text: ${text}`);
}

async function screenshot(client, filename) {
  const result = await client.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
  });
  fs.writeFileSync(path.join(outDir, filename), Buffer.from(result.data, "base64"));
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = edgePath ? launchBrowser() : null;
  const client = await connect(await waitForTarget());
  try {
    await client.send("Page.enable");
    await client.send("Runtime.enable");
    await client.send("Emulation.setDeviceMetricsOverride", {
      width: 1600,
      height: 1000,
      deviceScaleFactor: 1,
      mobile: false,
    });

    await waitForText(client, "$921.89");
    await client.send("Runtime.evaluate", { expression: "window.scrollTo(0, 0)" });
    await sleep(800);
    await screenshot(client, "costops-dashboard-overview.png");

    await client.send("Runtime.evaluate", {
      expression: 'document.getElementById("cost-by-incident-type")?.scrollIntoView({block:"start"})',
    });
    await sleep(800);
    await screenshot(client, "costops-cost-drivers.png");
  } finally {
    client.close();
    if (browser) {
      browser.kill();
    }
  }
}

function launchBrowser() {
  const userDataDir = path.join(os.tmpdir(), `costops-shot-${Date.now()}`);
  return spawn(
    edgePath,
    [
      "--headless=new",
      "--disable-gpu",
      "--hide-scrollbars",
      `--remote-debugging-port=${port}`,
      "--window-size=1600,1000",
      `--user-data-dir=${userDataDir}`,
      "--no-first-run",
      "--no-default-browser-check",
      dashboardUrl,
    ],
    { stdio: "ignore", windowsHide: true },
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
