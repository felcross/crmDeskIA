import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/api/v1/dashboard/kpis", () => {
    return HttpResponse.json({
      data: [
        { title: "Total de Ofertas", value: 10 },
        { title: "Valor do Pipeline", value: 50000 },
        { title: "Ticket Médio", value: 5000 },
        { title: "Ofertas Fechadas", value: 3 },
      ],
    });
  }),
  http.get("/api/v1/dashboard/charts", () => {
    return HttpResponse.json({
      data: {
        deals_by_stage: { chart_type: "bar", title: "Ofertas", data: [] },
        sales_funnel: { chart_type: "funnel", title: "Funil", data: [] },
        value_by_month: { chart_type: "line", title: "Valor", data: [] },
        contacts_by_month: { chart_type: "bar", title: "Contatos", data: [] },
      },
    });
  }),
  http.get("/api/v1/dashboard/deals", () => {
    return HttpResponse.json({ data: [], meta: { total: 0, page: 1, page_size: 20, total_pages: 0 } });
  }),
  http.get("/api/v1/dashboard/leads", () => {
    return HttpResponse.json({ data: [], meta: { total: 0, page: 1, page_size: 20, total_pages: 0 } });
  }),
  http.post("/api/v1/leads", () => {
    return HttpResponse.json({
      data: { id: "1", nome: "Teste", email: "test@test.com", telefone: "", interesse: "", criado_em: "2025-01-01" },
    });
  }),
];
