import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { createRequire } from "node:module";

const root = path.resolve(import.meta.dirname, "..", "..");
const appDir = path.join(root, "openhands", "source", "openhands-app");
const requireFromApp = createRequire(path.join(appDir, "package.json"));
const { chromium } = requireFromApp("playwright");

const provider = process.env.BROWSER_PROVIDER || "deepseek";
const providers = {
  deepseek: {
    prefix: "DEEPSEEK_BROWSER",
    port: 19000,
    chatUrl: "https://chat.deepseek.com/",
    textareaSelector: "textarea",
    responseSelector: ".ds-markdown",
    model: "deepseek-browser",
    imageWaitMs: 0,
  },
  chatgpt: {
    prefix: "CHATGPT_BROWSER",
    port: 19001,
    chatUrl: "https://chatgpt.com/",
    textareaSelector: "#prompt-textarea",
    responseSelector: "[data-message-author-role='assistant']",
    model: "chatgpt-browser",
    imageWaitMs: 25000,
  },
  claude: {
    prefix: "CLAUDE_BROWSER",
    port: 19002,
    chatUrl: "https://claude.ai/",
    textareaSelector: "div.ProseMirror[contenteditable='true'], div[contenteditable='true']",
    responseSelector: "[data-testid='assistant-answer'], [data-testid*='assistant'], [data-is-streaming]",
    model: "claude-browser",
    imageWaitMs: 0,
  },
};
const selected = providers[provider] || providers.deepseek;
const prefix = selected.prefix;
const env = (name, fallback = "") => process.env[`${prefix}_${name}`] || fallback;
const port = Number(env("PORT", selected.port));
const apiKey = env("API_KEY");
const profileDir = path.resolve(
  env("PROFILE_DIR", path.join(root, "runtime", `${provider}-browser-profile`)),
);
const chatUrl = env("CHAT_URL", selected.chatUrl);
const chatOrigin = new URL(chatUrl).origin;
const requestTimeout = Number(env("TIMEOUT_MS", 300000));
const textareaSelector = env("TEXTAREA_SELECTOR", selected.textareaSelector);
const fileInputSelector = env("FILE_INPUT_SELECTOR", "input[type='file']");
const attachmentUploadWaitMs = Number(env("ATTACHMENT_UPLOAD_WAIT_MS", 25000));
const responseSelector = env("RESPONSE_SELECTOR", selected.responseSelector);
const closeAfterResponse = env("CLOSE_AFTER_RESPONSE", "false") === "true";
const imageWaitMs = Number(env("IMAGE_WAIT_MS", selected.imageWaitMs));
const assetDir = path.join(root, "runtime", `${provider}-browser-generated`);
const workspaceRoot = path.join(process.env.USERPROFILE || process.env.HOME || root, "workspace", "project");
const allowedAttachmentRoots = [root, workspaceRoot];
const seenImageSources = new Set();

function findChrome() {
  const candidates = process.platform === "win32"
    ? [
        path.join(process.env.PROGRAMFILES || "", "Google", "Chrome", "Application", "chrome.exe"),
        path.join(process.env["ProgramFiles(x86)"] || "", "Google", "Chrome", "Application", "chrome.exe"),
        path.join(process.env.LOCALAPPDATA || "", "Google", "Chrome", "Application", "chrome.exe"),
      ]
    : ["/usr/bin/google-chrome", "/usr/bin/chromium", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"];
  return process.env[`${prefix}_EXECUTABLE`] || process.env.DEEPSEEK_BROWSER_EXECUTABLE || candidates.find((candidate) => fs.existsSync(candidate));
}

let context;
let page;
let queue = Promise.resolve();

function json(res, status, body) {
  res.writeHead(status, { "content-type": "application/json" });
  res.end(JSON.stringify(body));
}

function authorized(req) {
  if (!apiKey) return false;
  const value = req.headers.authorization || "";
  return value === `Bearer ${apiKey}`;
}

async function readBody(req) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > 20 * 1024 * 1024) throw new Error("Request body terlalu besar");
    chunks.push(chunk);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}");
}

function lastUserMessage(messages) {
  return [...messages].reverse().find((item) => item.role === "user");
}

function dataUrlFile(value, index, fallbackName = "attachment") {
  const match = /^data:([^;,]+)?;base64,(.+)$/s.exec(value || "");
  if (!match) throw new Error(`Attachment ${index + 1}: data URL tidak valid`);
  const buffer = Buffer.from(match[2], "base64");
  if (!buffer.length || buffer.length > 20 * 1024 * 1024) {
    throw new Error(`Attachment ${index + 1}: ukuran harus 1 byte sampai 20 MB`);
  }
  const extension = (match[1] || "application/octet-stream").split("/")[1] || "bin";
  return {
    name: `${fallbackName}.${extension.replace(/[^a-z0-9.+-]/gi, "")}`,
    mimeType: match[1] || "application/octet-stream",
    buffer,
  };
}

function localFile(value, index, fallbackName = "attachment") {
  let rawPath = String(value || "");
  if (rawPath.startsWith("/workspace/project/")) {
    rawPath = path.join(workspaceRoot, rawPath.slice("/workspace/project/".length));
  }
  const filePath = path.resolve(root, rawPath);
  const isAllowed = allowedAttachmentRoots.some((allowedRoot) => {
    const relative = path.relative(allowedRoot, filePath);
    return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
  });
  if (!isAllowed) throw new Error(`Attachment ${index + 1}: path harus berada di dalam project atau workspace OpenHands`);
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    throw new Error(`Attachment ${index + 1}: file tidak ditemukan`);
  }
  const stat = fs.statSync(filePath);
  if (stat.size > 20 * 1024 * 1024) throw new Error(`Attachment ${index + 1}: ukuran maksimum 20 MB`);
  return filePath;
}

function attachmentInputs(message, index) {
  const inputs = [];
  for (const item of Array.isArray(message?.content) ? message.content : []) {
    if (item?.type === "image_url") {
      const url = typeof item.image_url === "string" ? item.image_url : item.image_url?.url;
      if (url?.startsWith("data:")) inputs.push(dataUrlFile(url, index + inputs.length, "image"));
      else if (url) throw new Error("Attachment image_url harus berupa data URL atau gunakan path lokal");
    }
    if (item?.type === "file") {
      const file = item.file || item;
      const value = file.file_data || file.data;
      if (value?.startsWith("data:")) inputs.push(dataUrlFile(value, index + inputs.length, file.filename || "file"));
      else if (file.file_path || file.path) inputs.push(localFile(file.file_path || file.path, index + inputs.length, file.filename || "file"));
    }
  }
  for (const item of Array.isArray(message?.attachments) ? message.attachments : []) {
    const value = item?.data || item?.file_data;
    if (value?.startsWith("data:")) inputs.push(dataUrlFile(value, index + inputs.length, item.filename || "file"));
    else if (item?.path || item?.file_path) inputs.push(localFile(item.path || item.file_path, index + inputs.length, item.filename || "file"));
    else throw new Error(`Attachment ${index + inputs.length + 1}: gunakan path atau data URL`);
  }
  return inputs;
}

function saysAttachmentUnavailable(answer) {
  return /(?:not|cannot|can't|unable to|could not)\s+(?:see|access|find|view|detect)|(?:not|no|without)\s+(?:attached|available|provided|visible)|(?:belum|tidak|tak)\s+(?:ter)?lihat|(?:belum|tidak|tak)\s+(?:tersedia|terlampir|ada)|silakan\s+unggah|please\s+upload/i.test(answer || "");
}

async function uploadAttachments(browserPage, message) {
  const attachments = attachmentInputs(message, 0);
  if (!attachments.length) return;
  let fileInput = browserPage.locator(fileInputSelector).first();
  if (!await fileInput.count()) {
    const attachButton = browserPage.getByRole("button", {
      name: /attach|add files|upload|tambah file|lampir/i,
    }).first();
    if (!await attachButton.count()) throw new Error(`Tombol attachment ${provider} tidak ditemukan`);
    await attachButton.click();
    await browserPage.waitForTimeout(300);
    fileInput = browserPage.locator(fileInputSelector).first();
  }
  if (!await fileInput.count()) throw new Error(`Input upload file ${provider} tidak ditemukan setelah menu attachment dibuka`);
  await fileInput.setInputFiles(attachments);
  // ChatGPT uploads the selected files asynchronously before the prompt can be submitted.
  await browserPage.waitForTimeout(attachmentUploadWaitMs);
}

async function ensurePage() {
  fs.mkdirSync(profileDir, { recursive: true });
  if (!context) {
    const executablePath = findChrome();
    const headless = env("HEADLESS", "true") !== "false";
    if (provider === "claude") {
      // Claude.ai uses aggressive Cloudflare Turnstile. Best chance is to run
      // REAL installed Chrome (channel) in non-headless with a persistent profile
      // that the operator logs into once manually. No --enable-automation flag.
      fs.mkdirSync(profileDir, { recursive: true });
      context = await chromium.launchPersistentContext(profileDir, {
        channel: "chrome",
        headless: false,
        viewport: { width: 1440, height: 1000 },
        args: [
          "--disable-blink-features=AutomationControlled",
          "--no-first-run",
          "--no-default-browser-check",
          "--disable-infobars",
          "--disable-dev-shm-usage",
          "--start-maximized",
        ],
        ignoreDefaultArgs: ["--enable-automation"],
        ...(executablePath ? { executablePath } : {}),
      });
    } else {
      // Base stealth args for non-Claude providers
      const stealthArgs = [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--no-first-run",
        "--no-default-browser-check",
      ];
      context = await chromium.launchPersistentContext(profileDir, {
        headless,
        viewport: { width: 1440, height: 1000 },
        colorScheme: "dark",
        args: ["--force-dark-mode", ...stealthArgs],
        ignoreDefaultArgs: ["--enable-automation"],
        ...(executablePath ? { executablePath } : {}),
      });
    }
    page = context.pages()[0] || (await context.newPage());
    // Stealth injection to reduce bot fingerprinting
    await page.addInitScript(() => {
      Object.defineProperty(navigator, "webdriver", { get: () => undefined });
      window.chrome = window.chrome || { runtime: {} };
      Object.defineProperty(navigator, "languages", { get: () => ["en-US", "en"] });
      Object.defineProperty(navigator, "plugins", {
        get: () => [1, 2, 3, 4, 5].map((i) => ({
          0: { type: "application/x-google-chrome-pdf" },
          length: 1,
          item: () => null,
          namedItem: () => null,
          name: `Plugin ${i}`,
        })),
      });
      const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
      if (originalQuery) {
        window.navigator.permissions.query = (parameters) =>
          parameters && parameters.name === "notifications"
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters);
      }
    });
  }
  if (!page.url().startsWith(chatOrigin)) {
    await page.goto(chatUrl, { waitUntil: "domcontentloaded", timeout: requestTimeout });
  }
  return page;
}

async function closeBrowserAfterResponse() {
  if (!closeAfterResponse || !context) return;
  await context.close();
  context = undefined;
  page = undefined;
}

function buildImageHeaders(cookieHeader = "") {
  const headers = {
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    ...(chatOrigin && chatOrigin.startsWith("https") ? { referer: chatOrigin } : {}),
  };
  if (cookieHeader) headers.cookie = cookieHeader;
  return headers;
}

async function rawFetchImage(url, cookieHeader = "") {
  const res = await fetch(url, {
    redirect: "follow",
    headers: buildImageHeaders(cookieHeader),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  if (!buf.length) throw new Error("Response kosong");
  return buf;
}

async function fetchImage(url, cookieHeader = "") {
  // Tolak gambar dari origin luar chat (anti SSRF), kecuali origin itu sendiri.
  const imageUrl = new URL(url);
  if (imageUrl.origin !== chatOrigin) throw new Error("Gambar eksternal ditolak");
  try {
    return await rawFetchImage(url);
  } catch (error) {
    if (!/HTTP 40[13]|HTTP 403|HTTP 401/.test(error.message) || !cookieHeader) throw error;
    console.log(`[${provider}-bridge] Download src tanpa cookie gagal (${error.message}), retry dengan cookie.`);
    return await rawFetchImage(url, cookieHeader);
  }
}

function slugifyPrompt(prompt) {
  return prompt
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48) || "image";
}

async function captureImages(prompt) {
  if (!page || !context) return [];
  fs.mkdirSync(assetDir, { recursive: true });
  const cookies = await context.cookies(chatOrigin).catch(() => []);
  const cookieHeader = cookies
    .map((cookie) => `${cookie.name}=${cookie.value}`)
    .join("; ");
  const images = page.locator('[class*="imagegen-image"] img');
  const count = await images.count().catch(() => 0);
  const assets = [];
  const meta = [];
  const slug = slugifyPrompt(prompt);
  for (let index = 0; index < count; index += 1) {
    const image = images.nth(index);
    const src = await image.getAttribute("src").catch(() => "");
    if (!src || src === "about:blank" || seenImageSources.has(src)) continue;
    seenImageSources.add(src);
    const filename = `${provider}-${slug}-${Date.now()}-${index}.png`;
    const filePath = path.join(assetDir, filename);
    let method = "src";
    try {
      if (src.startsWith("data:image/")) {
        const m = /^data:image\/([a-zA-Z0-9.+-]+);base64,(.+)$/.exec(src);
        if (!m) throw new Error("data URI tidak valid");
        fs.writeFileSync(filePath, Buffer.from(m[2], "base64"));
      } else if (src.startsWith("blob:")) {
        throw new Error("blob src tidak didukung untuk download langsung");
      } else {
        const buf = await fetchImage(src, cookieHeader);
        fs.writeFileSync(filePath, buf);
      }
    } catch (e) {
      method = "screenshot";
      console.log(`[${provider}-bridge] Download src gagal (${e.message}), fallback screenshot.`);
      await image.screenshot({ path: filePath }).catch(() => {});
    }
    assets.push(`http://127.0.0.1:${port}/assets/${filename}`);
    meta.push({ prompt, slug, filename, file: `assets/${filename}`, src, method, created_at: new Date().toISOString() });
  }
  if (meta.length) {
    fs.writeFileSync(path.join(assetDir, `${provider}-${slug}-${Date.now()}.json`), JSON.stringify(meta, null, 2), "utf-8");
  }
  return assets;
}

async function isCloudflareChallenge(browserPage) {
  return browserPage.evaluate(() => {
    const lockedUrl = location.href.includes("challenges.cloudflare.com");
    const lockedIframe = Boolean(
      document.querySelector('#px-captcha, iframe[src*="challenges.cloudflare.com"], #turnstile-wrapper, .g-recaptcha, iframe[src*="captcha"], iframe[src*="hcaptcha"]')
    );
    const bodyText = (document.body && document.body.innerText || "").toLowerCase();
    const lockedText =
      /verify you are human|checking your browser please wait|solve this captcha/i.test(bodyText) ||
      /performing security verification|security service to protect against malicious bots/i.test(bodyText);
    return lockedUrl || lockedIframe || lockedText;
  });
}

async function waitForUsableTextarea(browserPage, deadline) {
  const textarea = browserPage.locator(textareaSelector).first();
  const end = deadline ?? (Date.now() + requestTimeout);
  let noted = false;
  while (Date.now() < end) {
    if (await textarea.count() && await textarea.isVisible().catch(() => false)) return textarea;
    if (await isCloudflareChallenge(browserPage)) {
      if (!noted) {
        noted = true;
        console.log(`[${provider}-bridge] Deteksi halaman verifikasi (Cloudflare/captcha). Menunggu verifikasi manual di browser...`);
      }
    }
    await browserPage.waitForTimeout(500);
  }
  throw new Error("Halaman tidak siap: kolom input tidak muncul (mungkin masih di halaman verifikasi/login).");
}

async function countLoadedImages(browserPage) {
  return browserPage.evaluate(() => {
    let count = 0;
    document.querySelectorAll('[class*="imagegen-image"] img').forEach((el) => {
      const w = el.naturalWidth || 0;
      const h = el.naturalHeight || 0;
      if (w >= 200 && h >= 200) count += 1;
    });
    return count;
  });
}

async function generatedImageSources(browserPage) {
  return browserPage.locator('[class*="imagegen-image"] img').evaluateAll((items) =>
    items.map((item) => item.currentSrc || item.getAttribute("src") || "").filter(Boolean),
  );
}

async function markExistingImages(browserPage) {
  for (const source of await generatedImageSources(browserPage).catch(() => [])) {
    seenImageSources.add(source);
  }
}

async function complete(messages, attachmentRetry = false) {
  const browserPage = await ensurePage();
  const lastUser = lastUserMessage(messages);
  if (!lastUser) throw new Error("Request tidak memiliki user message");
  const prompt = typeof lastUser.content === "string"
    ? lastUser.content
    : lastUser.content?.map((part) => part.text || "").join("\n") || "";
  const attachments = attachmentInputs(lastUser, 0);
  if (!prompt.trim() && !attachments.length) throw new Error("User message kosong");

  const response = browserPage.locator(responseSelector);
  const beforeCount = await response.count();
  const beforeText = beforeCount ? (await response.last().innerText().catch(() => "")).trim() : "";
  const beforeImages = await countLoadedImages(browserPage);
  await markExistingImages(browserPage);
  const deadline = Date.now() + requestTimeout;
  let answer = "";
  let gotImage = false;
  const textarea = await waitForUsableTextarea(browserPage, deadline);
  if (attachments.length) await uploadAttachments(browserPage, lastUser);
  await textarea.fill(prompt);
  await textarea.press("Enter");
  let lastText = beforeText;
  let stableSince = Date.now();
  let imageStableSince = 0;
  let responseReadyAt = 0;
  while (Date.now() < deadline && !gotImage) {
    const imageSources = await generatedImageSources(browserPage).catch(() => []);
    const hasNewImageElement = imageSources.some((source) => !seenImageSources.has(source));
    const imgCount = await countLoadedImages(browserPage);
    if (hasNewImageElement || imgCount > beforeImages) {
      if (!imageStableSince) imageStableSince = Date.now();
      if (Date.now() - imageStableSince >= 2200) {
        gotImage = true;
        answer = (await response.last().innerText().catch(() => "") || "").trim();
        break;
      }
    }
    const count = await response.count();
    const current = (count ? await response.last().innerText().catch(() => "") : "").trim();
    const isNewResponse = count > beforeCount || (current && current !== beforeText);
    if (isNewResponse && current !== lastText) {
      lastText = current;
      stableSince = Date.now();
    } else if (isNewResponse && current && Date.now() - stableSince >= 2200) {
      answer = current;
      if (!responseReadyAt) responseReadyAt = Date.now();
      // Give the DOM a short post-response window to expose a generated image.
      if (!hasNewImageElement && Date.now() - responseReadyAt >= 2500) break;
    }
    await browserPage.waitForTimeout(250);
  }
  if (!answer && !gotImage) {
    throw new Error(`Respons tidak ditemukan dalam ${Math.round(requestTimeout / 1000)} detik (mungkin terblokir verifikasi).`);
  }
  if (attachments.length && !attachmentRetry && saysAttachmentUnavailable(answer)) {
    const retryMessages = messages.map((message, index) => {
      if (index !== messages.length - 1 || message.role !== "user") return message;
      const content = typeof message.content === "string" ? message.content : prompt;
      return {
        ...message,
        content: `${content}\n\nAttachment sudah dikirim melalui upload browser. Jangan meminta saya mengunggah ulang; analisis file yang terlampir pada pesan ini.`,
      };
    });
    return complete(retryMessages, true);
  }
  return answer;
}

async function streamComplete(messages, send) {
  const browserPage = await ensurePage();
  const lastUser = lastUserMessage(messages);
  if (!lastUser) throw new Error("Request tidak memiliki user message");
  const prompt = typeof lastUser.content === "string"
    ? lastUser.content
    : lastUser.content?.map((part) => part.text || "").join("\n") || "";
  const attachments = attachmentInputs(lastUser, 0);
  if (!prompt.trim() && !attachments.length) throw new Error("User message kosong");

  const response = browserPage.locator(responseSelector);
  const beforeCount = await response.count();
  const beforeText = beforeCount ? (await response.last().innerText()).trim() : "";
  await markExistingImages(browserPage);
  const textarea = await waitForUsableTextarea(browserPage);
  if (attachments.length) await uploadAttachments(browserPage, lastUser);
  await textarea.fill(prompt);
  await textarea.press("Enter");

  let previous = "";
  const deadline = Date.now() + requestTimeout;
  while (Date.now() < deadline) {
    const count = await response.count();
    const current = count ? (await response.last().innerText()).trim() : "";
    const isNewResponse = count > beforeCount || (current && current !== beforeText);
    if (isNewResponse && current && current.length > previous.length) {
      const delta = current.slice(previous.length);
      previous = current;
      send(delta);
    }
    if (previous && current === previous) {
      await browserPage.waitForTimeout(2200);
      const settled = count ? (await response.last().innerText()).trim() : current;
      if (settled === previous) return previous;
    }
    await browserPage.waitForTimeout(250);
  }
  if (!previous) throw new Error(`Respons ${provider} tidak ditemukan; selector mungkin berubah`);
  return previous;
}

async function handle(req, res) {
  if (req.url === "/health" && req.method === "GET") {
    return json(res, 200, { status: "ok", provider, profile_configured: fs.existsSync(profileDir) });
  }
  if (req.url.startsWith("/assets/") && req.method === "GET") {
    const filename = path.basename(decodeURIComponent(req.url.slice("/assets/".length)));
    const assetPath = path.join(assetDir, filename);
    if (!filename || !fs.existsSync(assetPath)) return json(res, 404, { error: { message: "Asset not found" } });
    res.writeHead(200, { "content-type": "image/png", "cache-control": "public, max-age=3600" });
    return fs.createReadStream(assetPath).pipe(res);
  }
  if (!authorized(req)) return json(res, 401, { error: { message: "Unauthorized" } });
  if (req.url === "/v1/models" && req.method === "GET") {
    const model = selected.model || `${provider}-browser`;
    return json(res, 200, { object: "list", data: [{ id: model, object: "model", owned_by: provider }] });
  }
  if (req.url !== "/v1/chat/completions" || req.method !== "POST") {
    return json(res, 404, { error: { message: "Not found" } });
  }
  try {
    const body = await readBody(req);
    const id = `${provider}-browser-${Date.now()}`;
    const prompt = (body.messages || [])
      .slice()
      .reverse()
      .find((item) => item.role === "user");
    const userPrompt = typeof prompt?.content === "string"
      ? prompt.content
      : prompt?.content?.map((part) => part.text || "").join("\n") || "";
    if (body.stream) {
      res.writeHead(200, { "content-type": "text/event-stream", "cache-control": "no-cache", connection: "keep-alive" });
      const task = queue.then(async () => {
        await streamComplete(body.messages || [], (delta) => {
          res.write(`data: ${JSON.stringify({ id, object: "chat.completion.chunk", choices: [{ index: 0, delta: { content: delta }, finish_reason: null }] })}\n\n`);
        });
        const images = await captureImages(userPrompt);
        await closeBrowserAfterResponse();
        return images;
      });
      queue = task.catch(() => undefined);
      const images = await task;
      if (images.length) {
        res.write(`data: ${JSON.stringify({ id, object: "chat.completion.chunk", choices: [{ index: 0, delta: { content: `\n\n${images.map((asset) => `![Generated image](${asset})`).join("\n")}` }, finish_reason: null }] })}\n\n`);
      }
      res.write(`data: ${JSON.stringify({ id, object: "chat.completion.chunk", choices: [{ index: 0, delta: {}, finish_reason: "stop" }] })}\n\n`);
      res.write("data: [DONE]\n\n");
      return res.end();
    }
    const task = queue.then(async () => {
      const answer = await complete(body.messages || []);
      const images = await captureImages(userPrompt);
      await closeBrowserAfterResponse();
      return { answer, images };
    });
    queue = task.catch(() => undefined);
    const { answer, images } = await task;
    const imageMarkdown = images.length ? `\n\n${images.map((asset) => `![Generated image](${asset})`).join("\n")}` : "";
    return json(res, 200, { id, object: "chat.completion", created: Math.floor(Date.now() / 1000), model: body.model || `${provider}-browser`, choices: [{ index: 0, message: { role: "assistant", content: answer + imageMarkdown }, finish_reason: "stop" }], images, usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 } });
  } catch (error) {
    try {
      if (page) {
        fs.mkdirSync(path.join(root, "openhands", "logs"), { recursive: true });
        await page.screenshot({ path: path.join(root, "openhands", "logs", `${provider}-browser-error.png`), fullPage: true });
      }
    } catch {
      // Diagnostic screenshot is best effort and must not mask the API error.
    }
    // Only close the browser after an error if the operator explicitly wants
    // auto-close. For interactive/manual providers (e.g. claude) leave the
    // browser open so the operator can finish login/verification.
    await closeBrowserAfterResponse();
    if (res.headersSent) {
      res.write(`data: ${JSON.stringify({ error: { message: `${provider} browser bridge gagal: ${error.message}` } })}\n\n`);
      res.write("data: [DONE]\n\n");
      return res.end();
    }
    return json(res, 503, { error: { message: `${provider} browser bridge gagal: ${error.message}` } });
  }
}

const server = http.createServer((req, res) => handle(req, res));
server.on("error", (error) => {
  console.error(`[${provider}-bridge] Server error: ${error.message}`);
  if (error.code === "EADDRINUSE") process.exitCode = 1;
});
server.listen(port, "127.0.0.1", () => console.log(`${provider} browser bridge listening on 127.0.0.1:${port}`));
process.on("SIGINT", async () => { await context?.close(); server.close(); });
process.on("SIGTERM", async () => { await context?.close(); server.close(); });
