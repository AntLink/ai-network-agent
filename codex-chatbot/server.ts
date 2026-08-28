/**
 * Express server for Codex Chatbot with 9Router backend.
 */

import "dotenv/config";
import express from "express";
import path from "path";
import { fileURLToPath } from "url";

import {
  chat,
  chatStream,
  createThread,
  deleteThread,
  getDefaultModel,
} from "./codex-client.js";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const PORT = parseInt(process.env.CHATBOT_PORT || "8100", 10);
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------------------
// Express app
// ---------------------------------------------------------------------------

const app = express();
app.use(express.json());
app.use("/static", express.static(path.join(__dirname, "static")));

// Track active threads (session -> threadId)
const sessions = new Map<string, string>();

function getSessionId(req: express.Request): string {
  return (req.headers["x-session-id"] as string) || "default";
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

// Serve chat UI
app.get("/", (_req, res) => {
  res.sendFile(path.join(__dirname, "static", "index.html"));
});

// Non-streaming chat
app.post("/api/chat", async (req, res) => {
  const { message } = req.body;
  if (!message?.trim()) {
    res.status(400).json({ error: "message is required" });
    return;
  }

  const sessionId = getSessionId(req);
  let threadId = sessions.get(sessionId);
  if (!threadId) {
    threadId = createThread();
    sessions.set(sessionId, threadId);
  }

  try {
    const result = await chat(threadId, message);
    res.json({
      reply: result.reply,
      threadId: result.threadId,
      model: getDefaultModel(),
    });
  } catch (err: any) {
    console.error("Chat error:", err);
    res.status(500).json({ error: err.message || "Chat failed" });
  }
});

// Streaming chat (SSE)
app.post("/api/chat/stream", async (req, res) => {
  const { message } = req.body;
  if (!message?.trim()) {
    res.status(400).json({ error: "message is required" });
    return;
  }

  const sessionId = getSessionId(req);
  let threadId = sessions.get(sessionId);
  if (!threadId) {
    threadId = createThread();
    sessions.set(sessionId, threadId);
  }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders();

  try {
    for await (const event of chatStream(threadId, message)) {
      res.write(`data: ${JSON.stringify(event)}\n\n`);
    }
    res.write(`data: ${JSON.stringify({ type: "done", done: true })}\n\n`);
  } catch (err: any) {
    console.error("Stream error:", err);
    res.write(`data: ${JSON.stringify({ type: "error", error: err.message })}\n\n`);
  }

  res.end();
});

// Clear chat session
app.post("/api/chat/clear", (req, res) => {
  const sessionId = getSessionId(req);
  const threadId = sessions.get(sessionId);
  if (threadId) {
    deleteThread(threadId);
    sessions.delete(sessionId);
  }
  res.json({ status: "ok" });
});

// List models
app.get("/api/models", (_req, res) => {
  res.json({
    current: getDefaultModel(),
    models: [
      { id: "oc/big-pickle", name: "Big Pickle", provider: "opencode" },
      { id: "oc/laguna-s-2.1-free", name: "Laguna S 2.1 Free", provider: "opencode" },
      { id: "oc/nemotron-3-ultra-free", name: "Nemotron 3 Ultra Free", provider: "opencode" },
      { id: "oc/nemotron-3.5-lightning-free", name: "Nemotron 3.5 Lightning Free", provider: "opencode" },
    ],
  });
});

// Health check
app.get("/api/health", (_req, res) => {
  res.json({
    status: "ok",
    model: getDefaultModel(),
    ninerouter: process.env.NINEROUTER_URL || "http://127.0.0.1:20128",
    sessions: sessions.size,
  });
});

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------

app.listen(PORT, () => {
  console.log(`\n  Codex Chatbot running at http://localhost:${PORT}`);
  console.log(`  Model: ${getDefaultModel()}`);
  console.log(`  9Router: ${process.env.NINEROUTER_URL || "http://127.0.0.1:20128"}\n`);
});
