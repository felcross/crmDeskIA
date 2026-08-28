import { apiClient } from "./client";
import type {
  TicketCaptureRequest,
  TicketResponse,
  SequentialChatRequest,
  SequentialChatResponse,
} from "@/types/api";

export async function createTicket(
  data: TicketCaptureRequest,
): Promise<TicketResponse> {
  const { data: ticket } = await apiClient.post<TicketResponse>("/tickets", data);
  return ticket;
}

export async function sendTicketChatMessage(
  data: SequentialChatRequest,
): Promise<SequentialChatResponse> {
  const { data: result } = await apiClient.post<SequentialChatResponse>(
    "/tickets/chat",
    data,
  );
  return result;
}
