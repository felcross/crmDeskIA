import type { ChatChunkEvent, ChartResponse } from "@/types/api";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  chart?: ChartResponse;
  timestamp: number;
}

interface SSEWireEvent {
  chunk?: string;
  done?: boolean;
  type?: string;
  content?: string;
  conversation_id?: string;
  error?: string;
  chart?: ChartResponse;
}

export async function* sendMessage(
  pergunta: string,
  historico: Message[],
  signal?: AbortSignal,
): AsyncGenerator<ChatChunkEvent & { chart?: ChartResponse }> {
  const body = {
    message: pergunta,
    history: historico.map((m) => ({ role: m.role, content: m.content })),
  };

  let response: Response;
  try {
    response = await fetch("/api/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if (signal?.aborted) return;
    throw new Error("Erro de conexão. Verifique sua rede e tente novamente.");
  }

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Sessão expirada. Faça login novamente.");
    }
    throw new Error(`Erro do servidor (${response.status}). Tente novamente.`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("Resposta inválida do servidor.");

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith("data:")) continue;

        const jsonStr = trimmed.slice(5).trim();
        if (jsonStr === "[DONE]") {
          yield { type: "done" };
          return;
        }

        try {
          const parsed: SSEWireEvent = JSON.parse(jsonStr);

          // Wire format: {"chunk": "...", "done": false}
          if ("done" in parsed || "chunk" in parsed) {
            if (parsed.done) {
              yield {
                type: "done",
                content: parsed.chunk,
                ...(parsed.chart ? { chart: parsed.chart } : {}),
                ...(parsed.conversation_id
                  ? { conversation_id: parsed.conversation_id }
                  : {}),
              };
              return;
            }
            yield { type: "chunk", content: parsed.chunk ?? "" };
            continue;
          }

          // Already in ChatChunkEvent shape: {"type": "chunk", "content": "..."}
          if (parsed.type === "chunk" || parsed.type === "done" || parsed.type === "error") {
            yield {
              type: parsed.type,
              content: parsed.content,
              ...(parsed.chart ? { chart: parsed.chart } : {}),
              ...(parsed.conversation_id
                ? { conversation_id: parsed.conversation_id }
                : {}),
              ...(parsed.error ? { error: parsed.error } : {}),
            } as ChatChunkEvent & { chart?: ChartResponse };
            if (parsed.type === "done") return;
            continue;
          }
        } catch {
          // skip malformed JSON
        }
      }
    }

    // Stream ended without explicit [DONE]
    yield { type: "done" };
  } finally {
    reader.releaseLock();
  }
}
