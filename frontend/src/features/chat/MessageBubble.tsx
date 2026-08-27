import { memo, useMemo } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { cn } from "@/lib/utils";
import type { Message } from "@/api/chat";

function renderMarkdown(text: string): string {
  let html = text
    // code blocks
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="bg-muted rounded-md p-3 my-2 overflow-x-auto text-sm"><code>$2</code></pre>')
    // inline code
    .replace(/`([^`]+)`/g, '<code class="bg-muted px-1.5 py-0.5 rounded text-sm">$1</code>')
    // bold
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    // italic
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    // unordered list items
    .replace(/^[-*]\s+(.+)$/gm, '<li class="ml-4">$1</li>')
    // newlines
    .replace(/\n/g, "<br/>");

  // Wrap consecutive <li> in <ul>
  html = html.replace(
    /(<li[^>]*>.*?<\/li>(?:<br\/>)?)+/g,
    (match) =>
      `<ul class="list-disc pl-2 space-y-1 my-1">${match.replace(/<br\/>/g, "")}</ul>`,
  );

  return html;
}

function InlineChart({ chart }: { chart: NonNullable<Message["chart"]> }) {
  const data = useMemo(
    () => chart.data.map((d) => ({ name: d.label, value: d.value })),
    [chart.data],
  );

  const tooltipStyle = {
    backgroundColor: "hsl(222.2 84% 4.9%)",
    border: "1px solid hsl(217.2 32.6% 17.5%)",
    borderRadius: "8px",
    color: "hsl(210 40% 98%)",
  };

  if (chart.chart_type === "line") {
    return (
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(217.2 32.6% 17.5%)" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip contentStyle={tooltipStyle} />
          <Line type="monotone" dataKey="value" stroke="hsl(221 83% 53%)" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  // Default: bar chart (also handles funnel as horizontal bar)
  const isFunnel = chart.chart_type === "funnel";
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} layout={isFunnel ? "vertical" : undefined}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(217.2 32.6% 17.5%)" />
        {isFunnel ? (
          <>
            <XAxis type="number" tick={{ fontSize: 11 }} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={120} />
          </>
        ) : (
          <>
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
          </>
        )}
        <Tooltip contentStyle={tooltipStyle} />
        <Bar dataKey="value" fill="hsl(221 83% 53%)" radius={isFunnel ? [0, 4, 4, 0] : [4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

export const MessageBubble = memo(function MessageBubble({
  message,
  isStreaming,
}: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}
      aria-live="polite"
    >
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm",
          isUser
            ? "bg-primary text-primary-foreground rounded-br-md"
            : "bg-card border shadow-sm rounded-bl-md",
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <>
            <div
              className="prose prose-sm dark:prose-invert max-w-none [&_pre]:my-2 [&_ul]:my-1"
              dangerouslySetInnerHTML={{
                __html:
                  message.content || isStreaming
                    ? renderMarkdown(message.content)
                    : "",
              }}
            />
            {isStreaming && !message.content && (
              <span className="inline-flex gap-1 py-1">
                <span className="h-2 w-2 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:0ms]" />
                <span className="h-2 w-2 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:150ms]" />
                <span className="h-2 w-2 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:300ms]" />
              </span>
            )}
            {isStreaming && message.content && (
              <span className="inline-block w-1.5 h-4 bg-foreground/70 animate-pulse ml-0.5 align-text-bottom" />
            )}
            {message.chart && <InlineChart chart={message.chart} />}
          </>
        )}
      </div>
    </div>
  );
});
