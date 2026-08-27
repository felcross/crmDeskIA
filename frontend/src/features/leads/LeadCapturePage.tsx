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
import { sendLeadChatMessage } from "@/api/leads";
import type { Message } from "@/api/chat";
import type { CapturedLeadResponse } from "@/types/api";

interface ChatMessage extends Message {
  leadData?: CapturedLeadResponse | null;
}

function LeadSummaryCard({ lead }: { lead: CapturedLeadResponse }) {
  return (
    <Card className="border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-green-800 dark:text-green-200">
          <CheckCircle2 className="h-5 w-5" />
          Lead Capturado
        </CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <dt className="font-medium text-muted-foreground">Nome</dt>
          <dd>{lead.nome}</dd>
          <dt className="font-medium text-muted-foreground">Email</dt>
          <dd>{lead.email}</dd>
          {lead.telefone && (
            <>
              <dt className="font-medium text-muted-foreground">Telefone</dt>
              <dd>{lead.telefone}</dd>
            </>
          )}
          <dt className="font-medium text-muted-foreground">Interesse</dt>
          <dd>{lead.interesse || "—"}</dd>
          <dt className="font-medium text-muted-foreground">Criado em</dt>
          <dd>{new Date(lead.criado_em).toLocaleDateString("pt-BR")}</dd>
        </dl>
      </CardContent>
    </Card>
  );
}

export default function LeadCapturePage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [capturedLead, setCapturedLead] = useState<CapturedLeadResponse | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const chatMutation = useMutation({
    mutationFn: async (pergunta: string) => {
      const history: Message[] = messages.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        timestamp: m.timestamp,
      }));
      return sendLeadChatMessage(pergunta, history);
    },
    onSuccess: (data, pergunta) => {
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: pergunta,
        timestamp: Date.now(),
      };
      const aiMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.response,
        leadData: data.lead_data,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMsg, aiMsg]);

      if (data.lead_data) {
        setCapturedLead(data.lead_data);
        toast.success("Lead capturado com sucesso!");
      }
    },
    onError: (error: Error) => {
      toast.error(error.message || "Erro ao enviar mensagem");
    },
  });

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || chatMutation.isPending) return;
    setInput("");
    chatMutation.mutate(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFormSuccess = (lead: CapturedLeadResponse) => {
    setCapturedLead(lead);
  };

  const handleReset = () => {
    setMessages([]);
    setCapturedLead(null);
    setInput("");
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Captura de Leads</h1>
        <p className="mt-1 text-muted-foreground">
          Capture novos leads via conversa com IA ou formulário manual.
        </p>
      </div>

      <Tabs defaultValue="chat" className="w-full">
        <TabsList>
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="form">Formulário</TabsTrigger>
        </TabsList>

        <TabsContent value="chat" className="space-y-4">
          {capturedLead && <LeadSummaryCard lead={capturedLead} />}

          <Card>
            <CardContent className="p-4">
              <div className="flex h-[400px] flex-col">
                <div className="flex-1 space-y-4 overflow-y-auto pr-2">
                  {messages.length === 0 && (
                    <div className="flex h-full items-center justify-center text-muted-foreground">
                      <p className="text-center text-sm">
                        Olá! Sou o assistente de captura de leads.
                        <br />
                        Me conte sobre o interesse do seu lead e eu ajudarei a
                        registrar as informações.
                      </p>
                    </div>
                  )}
                  {messages.map((msg) => (
                    <LeadChatMessage
                      key={msg.id}
                      role={msg.role}
                      content={msg.content}
                      leadData={msg.leadData}
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
                    placeholder="Descreva o lead..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={chatMutation.isPending}
                  />
                  <Button
                    size="icon"
                    onClick={handleSend}
                    disabled={!input.trim() || chatMutation.isPending}
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

          {messages.length > 0 && (
            <div className="flex justify-center">
              <Button variant="outline" size="sm" onClick={handleReset}>
                Nova conversa
              </Button>
            </div>
          )}
        </TabsContent>

        <TabsContent value="form" className="space-y-4">
          {capturedLead && <LeadSummaryCard lead={capturedLead} />}

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
