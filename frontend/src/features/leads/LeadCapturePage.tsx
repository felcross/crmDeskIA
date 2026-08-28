import { useState, useRef, useEffect, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Send, Loader2, CheckCircle2 } from "lucide-react";

import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { LeadForm } from "./LeadForm";
import { LeadChatMessage } from "./LeadChatMessage";
import { sendTicketChatMessage } from "@/api/tickets";
import type { CapturedLeadResponse } from "@/types/api";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

interface TicketResult {
  id: string;
  nome: string;
  email: string;
  descricao: string;
  lead_id?: number;
}

function AtendimentoSummaryCard({ result }: { result: TicketResult }) {
  return (
    <Card className="border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-green-800 dark:text-green-200">
          <CheckCircle2 className="h-5 w-5" />
          Atendimento Registrado
        </CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <dt className="font-medium text-muted-foreground">Nome</dt>
          <dd>{result.nome}</dd>
          <dt className="font-medium text-muted-foreground">Email</dt>
          <dd>{result.email}</dd>
          <dt className="font-medium text-muted-foreground">Descrição</dt>
          <dd>{result.descricao}</dd>
        </dl>
      </CardContent>
    </Card>
  );
}

const INITIAL_BOT_MESSAGE =
  "Olá! Vou registrar seu atendimento. Qual o seu nome completo?";

export default function LeadCapturePage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [fase, setFase] = useState("nome");
  const [dadosParciais, setDadosParciais] = useState<Record<string, string>>({});
  const [tentativasFalhas, setTentativasFalhas] = useState(0);
  const [concluido, setConcluido] = useState(false);
  const [resultado, setResultado] = useState<TicketResult | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Show initial bot message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: INITIAL_BOT_MESSAGE,
          timestamp: Date.now(),
        },
      ]);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const chatMutation = useMutation({
    mutationFn: async (mensagem: string) => {
      return sendTicketChatMessage({
        mensagem,
        fase,
        campos_pendentes: [],
        dados_parciais: dadosParciais,
        tentativas_falhas: tentativasFalhas,
      });
    },
    onSuccess: (data, mensagem) => {
      // Add user message
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: mensagem,
        timestamp: Date.now(),
      };

      // Add bot response
      const botMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.mensagem,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMsg, botMsg]);

      // Update state from response
      setFase(data.fase);
      setDadosParciais(data.dados_parciais);
      setTentativasFalhas(data.tentativas_falhas);

      if (data.concluido && !data.encerrado_por_falha) {
        setConcluido(true);
        if (data.resultado) {
          setResultado(data.resultado as TicketResult);
          toast.success("Atendimento registrado com sucesso!");
        }
      } else if (data.encerrado_por_falha) {
        toast.error("Não foi possível completar o atendimento.");
      }
    },
    onError: (error: Error) => {
      toast.error(error.message || "Erro ao enviar mensagem");
    },
  });

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || chatMutation.isPending || concluido) return;
    setInput("");
    chatMutation.mutate(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFormSuccess = (_lead: CapturedLeadResponse) => {
    // Keep for manual form tab compatibility
  };

  const handleReset = () => {
    setMessages([
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content: INITIAL_BOT_MESSAGE,
        timestamp: Date.now(),
      },
    ]);
    setFase("nome");
    setDadosParciais({});
    setTentativasFalhas(0);
    setConcluido(false);
    setResultado(null);
    setInput("");
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Atendimento</h1>
        <p className="mt-1 text-muted-foreground">
          Registre um novo atendimento via conversa com IA ou formulário manual.
        </p>
      </div>

      <Tabs defaultValue="chat" className="w-full">
        <TabsList>
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="form">Formulário</TabsTrigger>
        </TabsList>

        <TabsContent value="chat" className="space-y-4">
          {resultado && <AtendimentoSummaryCard result={resultado} />}

          <Card>
            <CardContent className="p-4">
              <div className="flex h-[400px] flex-col">
                <div className="flex-1 space-y-4 overflow-y-auto pr-2">
                  {messages.map((msg) => (
                    <LeadChatMessage
                      key={msg.id}
                      role={msg.role}
                      content={msg.content}
                    />
                  ))}
                  {chatMutation.isPending && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Pensando...</span>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                <div className="mt-4 flex gap-2">
                  <Input
                    placeholder={
                      concluido
                        ? "Atendimento concluído"
                        : "Digite sua resposta..."
                    }
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={chatMutation.isPending || concluido}
                  />
                  <Button
                    size="icon"
                    onClick={handleSend}
                    disabled={!input.trim() || chatMutation.isPending || concluido}
                  >
                    {chatMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {messages.length > 1 && (
            <div className="flex justify-center">
              <Button variant="outline" size="sm" onClick={handleReset}>
                Nova conversa
              </Button>
            </div>
          )}
        </TabsContent>

        <TabsContent value="form" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Cadastrar Lead Manualmente</CardTitle>
            </CardHeader>
            <CardContent>
              <LeadForm onSuccess={handleFormSuccess} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
