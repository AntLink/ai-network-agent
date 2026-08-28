/**
 * Codex SDK client wrapper for 9Router integration.
 *
 * Uses @openai/codex-sdk which spawns the Codex CLI and communicates
 * via JSONL over stdin/stdout. The baseUrl option points to 9Router.
 */

import { Codex } from "@openai/codex-sdk";
import type { Thread } from "@openai/codex-sdk";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const NINEROUTER_URL = process.env.NINEROUTER_URL || "http://127.0.0.1:20128";
const NINEROUTER_KEY = process.env.NINEROUTER_KEY || "";
const DEFAULT_MODEL = process.env.CHATBOT_MODEL || "oc/big-pickle";

const SYSTEM_PROMPT = [
  "You are a network operations assistant for AI Network Agent.",
  "You help manage network devices (Cisco, MikroTik, Aruba),",
  "GNS3 labs, Containerlab, and provide network troubleshooting guidance.",
  "You can help with SSH configuration, routing protocols (OSPF, BGP, static),",
  "VLAN setup, firewall rules, and network automation.",
  "Be concise, professional, and provide actionable answers.",
].join(" ");

// ---------------------------------------------------------------------------
// Codex client instance
// ---------------------------------------------------------------------------

const codex = new Codex({
  // Point the built-in OpenAI provider at 9Router
  baseUrl: `${NINEROUTER_URL}/v1`,
  // The SDK injects this as CODEX_API_KEY for the CLI
  // 9Router accepts it as Bearer token
  env: {
    ...(NINEROUTER_KEY ? { OPENAI_API_KEY: NINEROUTER_KEY } : {}),
  },
  // Pass model + system prompt overrides via CLI config
  config: {
    model: DEFAULT_MODEL,
    model_reasoning_effort: "low",
  },
  // Skip git repo check for chatbot use case
  skipGitRepoCheck: true,
});

// ---------------------------------------------------------------------------
// Thread management
// ---------------------------------------------------------------------------

const threads = new Map<string, Thread>();
let threadCounter = 0;

/**
 * Create a new chat thread.
 */
export function createThread(): string {
  const id = `chat-${++threadCounter}-${Date.now()}`;
  const thread = codex.startThread({
    skipGitRepoCheck: true,
  });
  threads.set(id, thread);
  return id;
}

/**
 * Get an existing thread, or create a new one.
 */
export function getThread(id: string): Thread {
  let thread = threads.get(id);
  if (!thread) {
    thread = codex.startThread({ skipGitRepoCheck: true });
    threads.set(id, thread);
  }
  return thread;
}

/**
 * Delete a thread from the map.
 */
export function deleteThread(id: string): boolean {
  return threads.delete(id);
}

// ---------------------------------------------------------------------------
// Chat functions
// ---------------------------------------------------------------------------

/**
 * Send a message and get a full response (non-streaming).
 */
export async function chat(
  threadId: string,
  message: string,
): Promise<{ reply: string; threadId: string }> {
  const thread = getThread(threadId);

  const turn = await thread.run(
    `${SYSTEM_PROMPT}\n\nUser: ${message}`,
  );

  return {
    reply: turn.finalResponse,
    threadId,
  };
}

/**
 * Send a message and stream the response as async events.
 */
export async function* chatStream(
  threadId: string,
  message: string,
): AsyncGenerator<{ type: string; content?: string; done?: boolean; error?: string }> {
  const thread = getThread(threadId);

  try {
    const { events } = await thread.runStreamed(
      `${SYSTEM_PROMPT}\n\nUser: ${message}`,
    );

    for await (const event of events) {
      if (event.type === "item.completed" && "item" in event) {
        const item = (event as any).item;
        if (item?.type === "message" && item?.role === "assistant") {
          const text = item.content
            ?.filter((c: any) => c.type === "output_text")
            .map((c: any) => c.text)
            .join("");
          if (text) {
            yield { type: "content", content: text };
          }
        }
      }
      if (event.type === "turn.completed") {
        yield { type: "done", done: true };
      }
    }
  } catch (err: any) {
    yield { type: "error", error: err.message || "Stream failed" };
  }
}

/**
 * Get the default model name.
 */
export function getDefaultModel(): string {
  return DEFAULT_MODEL;
}
