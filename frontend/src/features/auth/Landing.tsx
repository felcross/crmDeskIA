import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { MessageSquare } from "lucide-react";
import { InlineChat } from "./InlineChat";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

async function handleGoogleLogin() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
      credentials: "include",
    });
    const data = await res.json();
    if (data.url) {
      window.location.href = data.url;
    } else {
      alert(data.message ?? "Google OAuth is not configured.");
    }
  } catch {
    alert("Failed to initiate login. Please try again.");
  }
}

type FlowState = "idle" | "atendimento";

export default function Landing() {
  const [flowState, setFlowState] = useState<FlowState>("idle");

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      {/* Left side — Login */}
      <div className="flex flex-1 items-center justify-center bg-background p-8">
        <Card className="w-full max-w-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">CRM AI</CardTitle>
            <CardDescription>Acesse o painel de suporte</CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              className="w-full"
              size="lg"
              onClick={handleGoogleLogin}
            >
              <svg
                className="mr-2 h-5 w-5"
                aria-hidden="true"
                viewBox="0 0 24 24"
              >
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
              </svg>
              Entrar com Google
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Divider */}
      <div className="hidden w-px bg-border md:block" />
      <div className="h-px bg-border md:hidden" />

      {/* Right side — Public vitrine */}
      <div className="flex flex-1 items-center justify-center bg-muted/30 p-8">
        <div className="w-full max-w-sm space-y-6">
          {flowState === "idle" && (
            <>
              <div className="text-center">
                <h2 className="text-xl font-semibold">Sou cliente</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Inicie um atendimento sem precisar de login.
                </p>
              </div>
              <div className="space-y-3">
                <Button
                  variant="outline"
                  className="w-full justify-start gap-3"
                  size="lg"
                  onClick={() => setFlowState("atendimento")}
                >
                  <MessageSquare className="h-5 w-5" />
                  Iniciar atendimento
                </Button>
              </div>
            </>
          )}

          {flowState === "atendimento" && (
            <div className="h-[450px]">
              <InlineChat
                endpoint="/tickets/chat"
                greeting="Olá! 👋 Sou o assistente virtual da empresa. Para que um de nossos especialistas possa entrar em contato com você, preciso de algumas informações. Qual o seu nome completo?"
                onComplete={() => {}}
                onReset={() => setFlowState("idle")}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
