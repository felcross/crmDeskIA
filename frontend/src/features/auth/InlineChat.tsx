import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { Loader2, RotateCcw, Bot, User, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/api/client";
import type { SequentialChatResponse } from "@/types/api";

interface ChatMsg {
  role: "user" | "assistant";
  content: string;
}

interface InlineChatProps {
  endpoint: "/leads/chat" | "/tickets/chat";
  onComplete: (resultado: unknown) => void;
  onReset: () => void;
  greeting: string;
}

export function InlineChat({
  endpoint,
  onComplete,
  onReset,
  greeting,
}: InlineChatProps) {
  const [messages, setMessages] = useState<ChatMsg[]>([
    { role: "assistant", content: greeting },
  ]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [isFailed, setIsFailed] = useState(false);
  const [fase, setFase] = useState("nome");
  const [camposPendentes, setCamposPendentes] = useState<string[]>([]);
  const [dadosParciais, setDadosParciais] = useState<Record<string, string>>({});
  const [tentativasFalhas, setTentativasFalhas] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending, scrollToBottom]);

  useEffect(() => {
    if (!isSending && !isDone) {
      inputRef.current?.focus();
    }
  }, [isSending, isDone]);

  const memoizedMessages = useMemo(() => messages, [messages]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isSending || isDone) return;

    const userMsg: ChatMsg = { role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsSending(true);

    try {
      const { data } = await apiClient.post<SequentialChatResponse>(endpoint, {
        mensagem: trimmed,
        fase: fase,
        campos_pendentes: camposPendentes,
        dados_parciais: dadosParciais,
        tentativas_falhas: tentativasFalhas,
      });

      const botMsg: ChatMsg = { role: "assistant", content: data.mensagem };
      setMessages((prev) => [...prev, botMsg]);

      // Update state from backend response
      setFase(data.fase);
      setCamposPendentes(data.campos_pendentes);
      setDadosParciais(data.dados_parciais);
      setTentativasFalhas(data.tentativas_falhas);

      if (data.concluido) {
        setIsDone(true);
        if (data.encerrado_por_falha) {
          setIsFailed(true);
        } else {
          onComplete(data.resultado);
        }
      }
    } catch (err) {
      const errorMsg: ChatMsg = {
        role: "assistant",
        content: `Erro: ${err instanceof Error ? err.message : "Tente novamente."}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleReset = () => {
    setMessages([{ role: "assistant", content: greeting }]);
    setFase("nome");
    setCamposPendentes([]);
    setDadosParciais({});
    setTentativasFalhas(0);
    setIsDone(false);
    setIsFailed(false);
    onReset();
  };

  return (
    <div className="flex h-full flex-col">
      <div
        className="flex-1 space-y-3 overflow-y-auto pr-2"
        role="log"
        aria-label="Conversa"
        aria-live="polite"
      >
        {memoizedMessages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "assistant" && (
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted">
                <Bot className="h-3.5 w-3.5" />
              </div>
            )}
            <div
              className={`max-w-[80%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              }`}
            >
              {msg.content}
            </div>
            {msg.role === "user" && (
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                <User className="h-3.5 w-3.5" />
              </div>
            )}
          </div>
        ))}

        {isSending && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Digitando...</span>
          </div>
        )}

        {isDone && !isFailed && (
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
            <CheckCircle2 className="h-4 w-4" />
            <span className="text-sm">Concluído!</span>
          </div>
        )}

        {isDone && isFailed && (
          <div className="flex items-center gap-2 text-destructive">
            <XCircle className="h-4 w-4" />
            <span className="text-sm">Atendimento encerrado</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {!isDone ? (
        <div className="mt-3 flex gap-2">
          <Input
            ref={inputRef}
            placeholder="Digite sua mensagem..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSending}
            aria-label="Mensagem"
          />
          <Button
            size="sm"
            onClick={handleSend}
            disabled={!input.trim() || isSending}
            aria-label="Enviar mensagem"
          >
            Enviar
          </Button>
        </div>
      ) : (
        <div className="mt-3 flex justify-center">
          <Button variant="outline" size="sm" onClick={handleReset} aria-label="Recomeçar atendimento">
            <RotateCcw className="mr-2 h-3.5 w-3.5" />
            Recomeçar
          </Button>
        </div>
      )}
    </div>
  );
}
