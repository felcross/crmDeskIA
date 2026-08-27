import { apiClient } from "./client";
import type { TicketCaptureRequest, TicketResponse } from "@/types/api";

export async function createTicket(
  data: TicketCaptureRequest,
): Promise<TicketResponse> {
  const { data: ticket } = await apiClient.post<TicketResponse>("/tickets", data);
  return ticket;
}
