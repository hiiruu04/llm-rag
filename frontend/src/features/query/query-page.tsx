import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send, Clock, Trash2, Cpu } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { useQueryRAG } from "@/api/query";
import { useQueryHistoryStore } from "@/stores/query-history-store";
import type { QueryMode, QueryData } from "@/types/query";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  data?: QueryData;
  mode?: QueryMode;
}

const modes: { value: QueryMode; label: string }[] = [
  { value: "auto", label: "Auto" },
  { value: "vector", label: "Vector" },
  { value: "graph", label: "Graph" },
  { value: "hybrid", label: "Hybrid" },
];

export default function QueryPage() {
  const [mode, setMode] = useState<QueryMode>("auto");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const queryMutation = useQueryRAG();
  const history = useQueryHistoryStore();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || queryMutation.isPending) return;

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: question, mode };
    setMessages((prev) => [...prev, userMsg]);

    queryMutation.mutate(
      { question, mode },
      {
        onSuccess: (data) => {
          const assistantMsg: Message = { id: crypto.randomUUID(), role: "assistant", content: data.answer, data, mode };
          setMessages((prev) => [...prev, assistantMsg]);
          history.add({ question, mode, answer: data.answer, modeUsed: data.mode_used });
          setQuestion("");
        },
        onError: (err) => {
          const errMsg: Message = { id: crypto.randomUUID(), role: "assistant", content: `Error: ${err.message}` };
          setMessages((prev) => [...prev, errMsg]);
        },
      },
    );
  };

  return (
    <>
      <PageHeader title="AI Query" description="Ask questions about your CMMS data" />

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        {/* Chat Area */}
        <div className="flex flex-col rounded-lg border border-border">
          {/* Mode Selector */}
          <div className="flex items-center gap-2 border-b border-border p-3">
            <span className="text-xs font-medium text-muted-foreground">Mode:</span>
            {modes.map((m) => (
              <button
                key={m.value}
                onClick={() => setMode(m.value)}
                className={`rounded-md px-3 py-1 text-xs ${
                  mode === m.value ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 max-h-[60vh] min-h-[300px]">
            {messages.length === 0 && (
              <div className="flex h-full items-center justify-center text-muted-foreground">
                <p className="text-sm">Ask a question to get started...</p>
              </div>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] min-w-0 overflow-hidden rounded-lg px-4 py-3 text-sm ${
                  msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                }`}>
                  {msg.role === "assistant" ? (
                    <div className="prose prose-sm dark:prose-invert max-w-none overflow-hidden [&_pre]:overflow-x-auto [&_pre]:whitespace-pre-wrap [&_pre]:break-all [&_pre]:rounded [&_pre]:bg-background [&_pre]:p-2 [&_pre]:text-xs [&_pre]:font-mono [&_code]:text-xs [&_code]:rounded [&_code]:bg-background [&_code]:px-1 [&_code]:py-0.5 [&_table]:text-xs [&_a]:text-primary [&_a]:underline">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                  )}
                  {msg.data && (
                    <div className="mt-3 space-y-2 border-t border-border/50 pt-2">
                      {msg.data.mode_used && (
                        <p className="text-xs text-muted-foreground">Mode used: {msg.data.mode_used}</p>
                      )}
                      {msg.data.model_used && (
                        <p className="text-xs text-muted-foreground">Model: {msg.data.model_used}</p>
                      )}
                      {msg.data.tokens_used && (
                        <p className="text-xs text-muted-foreground">
                          Tokens: {msg.data.tokens_used.total} (prompt: {msg.data.tokens_used.prompt}, completion: {msg.data.tokens_used.completion})
                        </p>
                      )}
                      {msg.data.cypher_used && (
                        <details className="overflow-hidden text-xs">
                          <summary className="cursor-pointer text-primary">Cypher Query</summary>
                          <pre className="mt-1 overflow-x-auto whitespace-pre-wrap break-all rounded bg-background p-2 font-mono">{msg.data.cypher_used}</pre>
                        </details>
                      )}
                      {msg.data.sources && msg.data.sources.length > 0 && (
                        <details className="text-xs">
                          <summary className="cursor-pointer text-primary">Sources ({msg.data.sources.length})</summary>
                          <div className="mt-1 space-y-1">
                            {msg.data.sources.map((s, i) => (
                              <div key={i} className="rounded bg-background p-2">
                                <p className="font-medium">{s.filename} (chunk {s.chunk_index})</p>
                                <p className="text-muted-foreground">Score: {(s.similarity_score * 100).toFixed(1)}%</p>
                                <p className="mt-1 line-clamp-2">{s.preview_text}</p>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {queryMutation.isPending && (
              <div className="flex justify-start">
                <div className="rounded-lg bg-muted px-4 py-3 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Cpu className="h-4 w-4 animate-pulse" /> Thinking...
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="flex gap-2 border-t border-border p-3">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question..."
              className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
            />
            <button
              type="submit"
              disabled={!question.trim() || queryMutation.isPending}
              className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>

        {/* Query History Sidebar */}
        <div className="rounded-lg border border-border p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-sm font-semibold">
              <Clock className="h-4 w-4" /> History
            </h3>
            {history.entries.length > 0 && (
              <button onClick={() => history.clear()} className="text-xs text-muted-foreground hover:text-destructive">
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
          <div className="space-y-2 max-h-[60vh] overflow-y-auto">
            {history.entries.length === 0 ? (
              <p className="text-xs text-muted-foreground">No queries yet</p>
            ) : (
              history.entries.map((entry) => (
                <button
                  key={entry.id}
                  onClick={() => { setQuestion(entry.question); setMode(entry.mode); }}
                  className="w-full rounded-md p-2 text-left text-xs hover:bg-accent"
                >
                  <p className="truncate font-medium">{entry.question}</p>
                  <p className="mt-0.5 text-muted-foreground">
                    {entry.mode} — {entry.modeUsed && `used ${entry.modeUsed}`}
                  </p>
                </button>
              ))
            )}
          </div>
        </div>
      </div>
    </>
  );
}
