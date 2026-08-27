export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ResponseEnvelope<T> {
  data: T;
  error: null;
  meta?: PaginationMeta;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMeta;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ErrorResponse {
  data: null;
  error: ErrorDetail;
}

export interface KPIResponse {
  title: string;
  value: number;
}

export interface ChartDataPoint {
  label: string;
  value: number;
  category?: string;
}

export interface ChartResponse {
  chart_type: string;
  title: string;
  data: ChartDataPoint[];
}

export interface DealResponse {
  id: string;
  nome: string;
  valor: number;
  estagio: string;
  pipeline: string;
  data_close: string | null;
  criado_em: string;
}

export interface LeadResponse {
  id: string;
  nome: string;
  email: string | null;
  telefone: string | null;
  status_lead: string | null;
  criado_em: string;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  stage?: string;
  status?: string;
}

export interface DashboardChartsResponse {
  kpis: KPIResponse[];
  charts: ChartResponse[];
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatChunkEvent {
  type: "chunk" | "done" | "error";
  content?: string;
  conversation_id?: string;
  error?: string;
}

export interface LeadCaptureRequest {
  nome: string;
  email: string;
  telefone?: string;
  interesse?: string;
}

export interface ConvertLeadRequest {
  valor: number;
  pipeline?: string;
  estagio?: string;
}

export interface CapturedLeadResponse {
  id: string;
  nome: string;
  email: string;
  telefone: string;
  interesse: string;
  criado_em: string;
}

export interface ReportRequest {
  report_type: string;
  date_from?: string;
  date_to?: string;
  filters?: Record<string, unknown>;
}

export interface ReportResponse {
  report_type: string;
  title: string;
  generated_at: string;
  data: Record<string, unknown>;
  charts?: ChartResponse[];
}

// Market / Currency Quotes
export interface CurrencyQuote {
  code: string;
  codein: string;
  name: string;
  bid: number;
  ask: number;
  varBid: number;
  pctChange: number;
  high: number;
  low: number;
  timestamp: number;
}

export interface CurrencyQuoteResponse {
  quotes: CurrencyQuote[];
}

export interface HistoryPoint {
  timestamp: number;
  bid: number;
  ask: number;
}

export interface CurrencyHistoryResponse {
  moeda: string;
  dias: number;
  data: HistoryPoint[];
}

export interface TicketCaptureRequest {
  nome: string;
  email: string;
  descricao: string;
  prioridade?: string;
}

export interface TicketResponse {
  id: string;
  nome: string;
  email: string;
  descricao: string;
  prioridade: string;
  status: string;
  criado_em: string;
}

export interface SequentialChatRequest {
  mensagem: string;
  fase: string;
  campos_pendentes: string[];
  dados_parciais: Record<string, string>;
  tentativas_falhas: number;
}

export interface SequentialChatResponse {
  mensagem: string;
  fase: string;
  campos_pendentes: string[];
  campos_extraidos: string[];
  dados_parciais: Record<string, string>;
  tentativas_falhas: number;
  concluido: boolean;
  encerrado_por_falha: boolean;
  resultado: unknown;
}
