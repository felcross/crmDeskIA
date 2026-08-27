import { apiClient } from "./client";
import type {
  LeadCaptureRequest,
  CapturedLeadResponse,
  ConvertLeadRequest,
  DealResponse,
} from "@/types/api";
import type { Message } from "@/api/chat";

interface LeadChatResponse {
  response: string;
  lead_data: CapturedLeadResponse | null;
}

export async function captureLead(
  data: LeadCaptureRequest,
): Promise<CapturedLeadResponse> {
  const { data: lead } = await apiClient.post<CapturedLeadResponse>("/leads", data);
  return lead;
}

export async function sendLeadChatMessage(
  pergunta: string,
  historico: Message[],
): Promise<LeadChatResponse> {
  const body = {
    message: pergunta,
    history: historico.map((m) => ({ role: m.role, content: m.content })),
  };
  const { data: result } = await apiClient.post<LeadChatResponse>(
    "/leads/chat",
    body,
  );
  return result;
}

export async function convertLead(
  leadId: number,
  data: ConvertLeadRequest,
): Promise<DealResponse> {
  const { data: deal } = await apiClient.post<DealResponse>(
    `/leads/${leadId}/convert`,
    data,
  );
  return deal;
}
