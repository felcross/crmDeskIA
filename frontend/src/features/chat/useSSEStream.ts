import { useState, useRef, useCallback, useEffect } from "react";
import { sendMessage, type Message } from "@/api/chat";
import type { ChartResponse } from "@/types/api";

const MAX_RETRIES = 3;

export function useSSEStream() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const retryCountRef = useRef(0);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const clearMessages = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setIsStreaming(false);
    setError(null);
    retryCountRef.current = 0;
  }, []);

  const send = useCallback(
    async (content: string) => {
      if (!content.trim() || isStreaming) return;

      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: content.trim(),
        timestamp: Date.now(),
      };

      const aiMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "",
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMsg, aiMsg]);
      setError(null);
      setIsStreaming(true);
      retryCountRef.current = 0;

      const attemptStream = async (): Promise<void> => {
        const controller = new AbortController();
        abortRef.current = controller;

        let accumulated = "";
        let chart: ChartResponse | undefined;

        try {
          const history = [...messages, userMsg];
          for await (const event of sendMessage(
            userMsg.content,
            history,
            controller.signal,
          )) {
            if (event.type === "chunk" && event.content) {
              accumulated += event.content;
              const text = accumulated;
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last && last.role === "assistant") {
                  updated[updated.length - 1] = { ...last, content: text };
                }
                return updated;
              });
            }

            if (event.type === "done") {
              if (event.content) {
                accumulated += event.content;
              }
              if ("chart" in event && event.chart) {
                chart = event.chart as ChartResponse;
              }
              break;
            }

            if (event.type === "error") {
              throw new Error(event.error ?? "Erro desconhecido");
            }
          }

          // Finalize the message
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === "assistant") {
              updated[updated.length - 1] = {
                ...last,
                content: accumulated,
                ...(chart ? { chart } : {}),
              };
            }
            return updated;
          });

          retryCountRef.current = 0;
        } catch (err) {
          if (controller.signal.aborted) return;

          const msg =
            err instanceof Error ? err.message : "Erro desconhecido";

          if (retryCountRef.current < MAX_RETRIES) {
            retryCountRef.current += 1;
            const delay = Math.pow(2, retryCountRef.current) * 500;
            await new Promise((r) => setTimeout(r, delay));
            return attemptStream();
          }

          setError(msg);
          // Remove the empty assistant message on error
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === "assistant" && !last.content) {
              updated.pop();
            }
            return updated;
          });
        }
      };

      try {
        await attemptStream();
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [messages, isStreaming],
  );

  return { sendMessage: send, messages, isStreaming, error, clearMessages };
}
