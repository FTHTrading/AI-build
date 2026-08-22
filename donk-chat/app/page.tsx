"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, Terminal, Copy, Check } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function DonkChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Yo. Donk in the chair. What are we building, breaking, or shipping today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMessage: Message = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsStreaming(true);

    const assistantMessage: Message = { role: "assistant", content: "" };
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      const response = await fetch("http://127.0.0.1:8790/v1/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, userMessage],
        }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        accumulated += chunk;

        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: accumulated,
          };
          return updated;
        });
      }
    } catch (err) {
      console.error("Stream error:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Damn it, socket dropped or backend is offline. Check port 8790.",
        },
      ]);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#0d0f12] text-zinc-100 font-sans">
      {/* Sidebar */}
      <aside className="w-64 border-r border-zinc-800 bg-[#12151a] p-4 flex flex-col justify-between hidden md:flex">
        <div>
          <div className="flex items-center gap-2 mb-8 px-2">
            <div className="h-8 w-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold">
              ⚡
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-wide">DONK RUNTIME</h1>
              <p className="text-[10px] text-zinc-500 uppercase tracking-wider">Unykorn LLC Core</p>
            </div>
          </div>

          <div className="space-y-1">
            <button className="w-full text-left px-3 py-2 text-xs font-medium text-zinc-400 hover:text-white hover:bg-zinc-800/50 rounded-md transition flex items-center gap-2">
              <Terminal className="h-4 w-4 text-emerald-400" />
              Active Core Session
            </button>
            <button className="w-full text-left px-3 py-2 text-xs font-medium text-zinc-400 hover:text-white hover:bg-zinc-800/50 rounded-md transition flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-cyan-400" />
              Obsidian Brain RAG
            </button>
          </div>
        </div>

        <div className="p-3 bg-zinc-900/60 rounded-lg border border-zinc-800 text-[11px] text-zinc-400">
          <p className="font-semibold text-zinc-300">RTX 5090 Active</p>
          <p className="text-[10px] text-emerald-400">● 100% Unrestricted Local Inference</p>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col h-full relative">
        {/* Top Header */}
        <header className="h-14 border-b border-zinc-800/80 px-6 flex items-center justify-between bg-[#0d0f12]/80 backdrop-blur">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-zinc-200">Donk</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Live Interactive
            </span>
          </div>
        </header>

        {/* Message Feed */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 max-w-4xl mx-auto w-full">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-4 ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role === "assistant" && (
                <div className="h-8 w-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center shrink-0">
                  <Bot className="h-4 w-4 text-emerald-400" />
                </div>
              )}

              <div
                className={`max-w-[80%] rounded-2xl px-5 py-3.5 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-emerald-600 text-white font-medium"
                    : "bg-[#161a22] border border-zinc-800 text-zinc-200 shadow-sm"
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>

              {msg.role === "user" && (
                <div className="h-8 w-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center shrink-0">
                  <User className="h-4 w-4 text-zinc-300" />
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 md:p-6 bg-[#0d0f12] border-t border-zinc-800/80">
          <form
            onSubmit={handleSubmit}
            className="max-w-4xl mx-auto relative flex items-center"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Donk anything, drop code, or issue a build command..."
              className="w-full bg-[#161a22] border border-zinc-700/80 rounded-xl px-4 py-3.5 pr-12 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-emerald-500 transition shadow-inner"
            />
            <button
              type="submit"
              disabled={isStreaming || !input.trim()}
              className="absolute right-2.5 p-2 rounded-lg bg-emerald-500 text-black hover:bg-emerald-400 disabled:opacity-30 disabled:hover:bg-emerald-500 transition cursor-pointer"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
