import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send, Clock, Trash2, Plus, Cpu, Bot } from "lucide-react";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useQueryRAG } from "@/api/query";
import { useChatSessions, useChatSession, useDeleteChatSession } from "@/api/chats";
import { useChatStore } from "@/stores/chat-store";
import type { QueryMode, QueryData } from "@/types/query";
import type { ChatMessage } from "@/types/chat";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  data?: QueryData;
  mode?: QueryMode;
}

const modes: { value: QueryMode; label: string }[] = [
  { value: "auto", label: "Auto" },
  { value: "agent", label: "Agent" },
  { value: "vector", label: "Vector" },
  { value: "graph", label: "Graph" },
  { value: "graphrag", label: "GraphRAG" },
  { value: "hybrid", label: "Hybrid" },
];

const agentIcons: Record<string, string> = {
  scheduling: "\u{1F5D3}\uFE0F",
  competency: "\u{1F3AF}",
  analyzer: "\u{1F4CA}",
  recommender: "\u{1F4A1}",
};

export default function QueryPage() {
  const [mode, setMode] = useState<QueryMode>("auto");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const queryRagMutation = useQueryRAG();
  const { activeSessionId, setActiveSession, clearActiveSession } = useChatStore();

  const deleteSession = useDeleteChatSession();
  const { data: sessionsData } = useChatSessions();
  const { data: sessionDetail } = useChatSession(activeSessionId);

  const isPending = queryRagMutation.isPending;
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (sessionDetail?.messages) {
      const loaded: Message[] = sessionDetail.messages.map((m: ChatMessage) => ({
        id: m.id,
        role: m.role as "user" | "assistant",
        content: m.content,
        data: m.metadata_ ? (m.metadata_ as unknown as QueryData) : undefined,
        mode: (m.metadata_ as Record<string, unknown>)?.mode_used as QueryMode | undefined,
      }));
      setMessages(loaded);
    }
  }, [sessionDetail]);

  const handleNewChat = useCallback(() => {
    setMessages([]);
    clearActiveSession();
    setQuestion("");
  }, [clearActiveSession]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isPending) return;

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: question, mode };
    setMessages((prev) => [...prev, userMsg]);

    const onSuccess = (data: QueryData) => {
      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.answer,
        data,
        mode,
      };
      setMessages((prev) => [...prev, assistantMsg]);

      if (data.session_id) {
        if (!activeSessionId) {
          setActiveSession(data.session_id);
        }
      }
      setQuestion("");
    };

    const onError = (err: Error) => {
      const errMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `Error: ${err.message}`,
      };
      setMessages((prev) => [...prev, errMsg]);
    };

    queryRagMutation.mutate(
      { question, mode, session_id: activeSessionId ?? undefined },
      { onSuccess, onError },
    );
  };

  const confirmDeleteSession = (id: string) => {
    if (id === activeSessionId) {
      handleNewChat();
    }
    deleteSession.mutate(id);
    setDeleteTarget(null);
  };

  return (
    <>
      <ConfirmDialog
        open={deleteTarget !== null}
        title="Delete Chat Session"
        description="Are you sure you want to delete this chat session? This action cannot be undone and all messages will be permanently removed."
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={() => deleteTarget && confirmDeleteSession(deleteTarget)}
        onCancel={() => setDeleteTarget(null)}
      />

      <div className="flex h-[calc(100vh-4rem)] -m-6">
        {/* Chat Sessions Sidebar */}
        <div className="hidden lg:flex w-64 shrink-0 flex-col border-r border-border bg-card">
          <div className="flex items-center justify-between border-b border-border p-3">
            <h3 className="flex items-center gap-2 text-sm font-semibold">
              <Clock className="h-4 w-4" /> Sessions
            </h3>
            <button
              onClick={handleNewChat}
              className="flex items-center gap-1 rounded-md bg-primary px-2 py-1 text-xs text-primary-foreground hover:bg-primary/90"
            >
              <Plus className="h-3 w-3" /> New
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {(!sessionsData?.sessions || sessionsData.sessions.length === 0) && (
              <p className="px-2 py-4 text-center text-xs text-muted-foreground">No sessions yet</p>
            )}
            {sessionsData?.sessions?.map((session) => (
              <div
                key={session.id}
                className={`group flex items-start justify-between rounded-md p-2 text-left text-xs hover:bg-accent cursor-pointer transition-colors ${
                  session.id === activeSessionId ? "bg-accent border border-primary/30" : ""
                }`}
                onClick={() => setActiveSession(session.id)}
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">
                    {session.title || "Untitled"}
                  </p>
                  <p className="mt-0.5 text-muted-foreground">
                    {session.mode} &middot; {session.message_count} msgs
                  </p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); setDeleteTarget(session.id); }}
                  className="ml-1 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Chat Area - Full height */}
        <div className="flex flex-1 flex-col min-w-0">
          {/* Mode Selector Bar */}
          <div className="flex items-center gap-2 border-b border-border px-4 py-2">
            <span className="text-xs font-medium text-muted-foreground">Mode:</span>
            {modes.map((m) => (
              <button
                key={m.value}
                onClick={() => setMode(m.value)}
                className={`rounded-md px-3 py-1 text-xs transition-colors ${
                  mode === m.value ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"
                }`}
              >
                {m.label}
              </button>
            ))}
            {activeSessionId && (
              <span className="ml-auto text-xs text-muted-foreground">
                Session active
              </span>
            )}
          </div>

          {/* Messages - Fill available space */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
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
                      <div className="flex flex-wrap gap-2">
                        {msg.data.mode_used && (
                          <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                            {msg.data.mode_used}
                          </span>
                        )}
                        {msg.data.agent_used && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-blue-500/10 px-2 py-0.5 text-xs font-medium text-blue-600 dark:text-blue-400">
                            <Bot className="h-3 w-3" />
                            {agentIcons[msg.data.agent_used] ?? ""} {msg.data.agent_used} agent
                          </span>
                        )}
                      </div>
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
                      {msg.data.graph_entities && msg.data.graph_entities.length > 0 && (
                        <details className="text-xs">
                          <summary className="cursor-pointer text-primary">Graph Entities ({msg.data.graph_entities.length})</summary>
                          <div className="mt-1 space-y-1">
                            {msg.data.graph_entities.map((ent, i) => (
                              <div key={i} className="rounded bg-background p-2">
                                <span className="font-medium">{ent.name}</span>
                                <span className="ml-1 text-muted-foreground">({ent.entity_type})</span>
                                {ent.description && (
                                  <p className="mt-0.5 text-muted-foreground line-clamp-2">{ent.description}</p>
                                )}
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                      {msg.data.cmms_references && msg.data.cmms_references.length > 0 && (
                        <details className="text-xs">
                          <summary className="cursor-pointer text-primary">CMMS References ({msg.data.cmms_references.length})</summary>
                          <div className="mt-1 space-y-1">
                            {msg.data.cmms_references.map((ref, i) => (
                              <div key={i} className="rounded bg-background p-2">
                                <span className="font-medium">{ref.entity_name}</span>
                                {" \u2192 "}
                                <span>{ref.cmms_label}: {ref.cmms_name}</span>
                                {ref.cmms_pg_id && <span className="text-muted-foreground"> (ID: {ref.cmms_pg_id})</span>}
                              </div>
                            ))}
                          </div>
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
            {isPending && (
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

          {/* Input - Fixed at bottom */}
          <form onSubmit={handleSubmit} className="flex gap-2 border-t border-border p-3">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question..."
              className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
            />
            <button
              type="submit"
              disabled={!question.trim() || isPending}
              className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </>
  );
}