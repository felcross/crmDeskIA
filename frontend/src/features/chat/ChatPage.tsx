import { useEffect, useRef, useCallback } from "react";
import { Trash2, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSSEStream } from "./useSSEStream";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";

const STARTER_QUESTIONS = [
  "Qual o status das minhas ofertas este mês?",
  "Quais leads precisam de acompanhamento?",
  "Gere um resumo do pipeline de vendas.",
  "Quais são os KPIs do dashboard?",
];

export default function ChatPage() {
  const { sendMessage, messages, isStreaming, error, clearMessages } =
    useSSEStream();
  const scrollRef = useRef<HTMLDivElement>(null);
  const isEmpty = messages.length === 0;

  // Auto-scroll on new content
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [messages]);

  const handleSend = useCallback(
    (content: string) => {
      sendMessage(content);
    },
    [sendMessage],
  );

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          <h1 className="text-lg font-semibold">Chat com IA</h1>
        </div>
        {!isEmpty && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearMessages}
            disabled={isStreaming}
          >
            <Trash2 className="mr-1.5 h-4 w-4" />
            Limpar conversa
          </Button>
        )}
      </div>

      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4">
        {isEmpty ? (
          <div className="flex h-full flex-col items-center justify-center gap-6">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
              <MessageSquare className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-center text-muted-foreground">
              Faça uma pergunta sobre seus dados de CRM
            </p>
            <div className="grid w-full max-w-md gap-2">
              {STARTER_QUESTIONS.map((q) => (
                <Button
                  key={q}
                  variant="outline"
                  className="h-auto justify-start whitespace-normal py-3 text-left text-sm"
                  onClick={() => handleSend(q)}
                >
                  {q}
                </Button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-4">
            {messages.map((msg, i) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                isStreaming={
                  isStreaming &&
                  msg.role === "assistant" &&
                  i === messages.length - 1
                }
              />
            ))}
          </div>
        )}
      </div>

      {/* Error banner */}
      {error && (
        <div className="border-t bg-destructive/10 px-4 py-2 text-center text-sm text-destructive">
          {error}
          <Button
            variant="link"
            size="sm"
            className="ml-2 h-auto p-0 text-destructive underline"
            onClick={() => {
              const lastUser = [...messages]
                .reverse()
                .find((m) => m.role === "user");
              if (lastUser) sendMessage(lastUser.content);
            }}
          >
            Tentar novamente
          </Button>
        </div>
      )}

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={isStreaming} />
    </div>
  );
}
