import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { User, Bot } from "lucide-react";
import type { CapturedLeadResponse } from "@/types/api";

interface LeadChatMessageProps {
  role: "user" | "assistant";
  content: string;
  leadData?: CapturedLeadResponse | null;
}

function LeadDataCard({ lead }: { lead: CapturedLeadResponse }) {
  return (
    <Card className="mt-2 border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-green-800 dark:text-green-200">
          Lead Capturado
        </CardTitle>
      </CardHeader>
      <CardContent className="text-sm">
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1">
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
        </dl>
      </CardContent>
    </Card>
  );
}

export function LeadChatMessage({
  role,
  content,
  leadData,
}: LeadChatMessageProps) {
  const isUser = role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
          <Bot className="h-4 w-4" />
        </div>
      )}
      <div
        className={`max-w-[80%] space-y-2 ${
          isUser
            ? "rounded-lg bg-primary px-4 py-2 text-primary-foreground"
            : "rounded-lg bg-muted px-4 py-2"
        }`}
      >
        <p className="whitespace-pre-wrap text-sm">{content}</p>
        {leadData && <LeadDataCard lead={leadData} />}
      </div>
      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
}
