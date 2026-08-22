"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, Terminal, RefreshCw, Cpu, ShieldCheck } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function DonkChatApp() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Yo. Donk's in the terminal. The Unykorn Rust core passed 100% test coverage. What are we building, breaking, or shipping right now?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [systemStatus, setSystemStatus] = useState({
    lifeline: "AutonomousActive",
    height: 12,
    cuda: "RTX 5090 (Online)",
  });

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

      if (!response.body) throw new Error("No readable stream received.");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        accumulatedText += decoder.decode(value, { stream: true });

        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: accumulatedText,
          };
          return updated;
        });
      }
    } catch (err) {
      console.error("Donk Stream Error:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Damn it, socket dropped or the FastAPI engine on port 8790 is down. Check vault_api_server.py.",
        },
      ]);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#090b0e] text-zinc-100 font-sans selection:bg-emerald-500 selection:text-black">
      {/* Left Telemetry Sidebar */}
      <aside className="w-72 border-r border-zinc-800/80 bg-[#0d1015] p-5 flex flex-col justify-between hidden md:flex">
        <div className="space-y-6">
          <div className="flex items-center gap-3 px-1">
            <div className="h-9 w-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-lg shadow-[0_0_15px_rgba(16,185,129,0.15)]">
              ⚡
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-wider text-zinc-100">DONK RUNTIME</h1>
              <p className="text-[10px] text-zinc-500 font-mono uppercase tracking-widest">Unykorn LLC Core</p>
            </div>
          </div>

          <nav className="space-y-1">
            <button className="w-full text-left px-3.5 py-2.5 text-xs font-semibold text-zinc-300 bg-zinc-800/40 hover:bg-zinc-800/80 rounded-lg transition border border-zinc-700/40 flex items-center gap-2.5">
              <Terminal className="h-4 w-4 text-emerald-400" />
              Interactive Console
            </button>
            <button className="w-full text-left px-3.5 py-2.5 text-xs font-medium text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/30 rounded-lg transition flex items-center gap-2.5">
              <Sparkles className="h-4 w-4 text-cyan-400" />
              Obsidian Brain RAG
            </button>
            <button className="w-full text-left px-3.5 py-2.5 text-xs font-medium text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/30 rounded-lg transition flex items-center gap-2.5">
              <ShieldCheck className="h-4 w-4 text-amber-400" />
              ERC-3643 Gateway
            </button>
          </nav>
        </div>

        {/* Live Systems Telemetry */}
        <div className="p-3.5 bg-[#13171f] rounded-xl border border-zinc-800/90 text-xs space-y-2.5 font-mono">
          <div className="flex items-center justify-between text-[11px] text-zinc-400 border-b border-zinc-800 pb-2">
            <span className="flex items-center gap-1.5">
              <Cpu className="h-3.5 w-3.5 text-emerald-400" /> Hardware Engine
            </span>
            <span className="text-emerald-400 font-semibold">RTX 5090</span>
          </div>
          <div className="flex justify-between text-[10px] text-zinc-400">
            <span>Lifeline State:</span>
            <span className="text-zinc-200 font-semibold">{systemStatus.lifeline}</span>
          </div>
          <div className="flex justify-between text-[10px] text-zinc-400">
            <span>L1 Height:</span>
            <span className="text-emerald-400 font-semibold">#{systemStatus.height}</span>
          </div>
          <div className="pt-1">
            <span className="inline-flex items-center gap-1.5 text-[9px] text-emerald-400/90 font-sans uppercase font-bold tracking-wider">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Zero Guardrails • Candid Core
            </span>
          </div>
        </div>
      </aside>

      {/* Main Conversational Stream */}
      <main className="flex-1 flex flex-col h-full relative overflow-hidden">
        {/* Top Header */}
        <header className="h-14 border-b border-zinc-800/80 px-6 flex items-center justify-between bg-[#090b0e]/90 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <span className="text-sm font-bold text-zinc-100 tracking-wide">Donk</span>
            <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono font-medium">
              v1.0.0-PROD
            </span>
          </div>
          <div className="text-xs text-zinc-500 font-mono">
            Gateway: <span className="text-zinc-300">127.0.0.1:8790</span>
          </div>
        </header>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 max-w-4xl mx-auto w-full">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-4 ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role === "assistant" && (
                <div className="h-8 w-8 rounded-xl bg-[#161a22] border border-zinc-700/60 flex items-center justify-center shrink-0 shadow-sm">
                  <Bot className="h-4 w-4 text-emerald-400" />
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-2xl px-5 py-3.5 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-emerald-600 text-white font-medium shadow-md"
                    : "bg-[#12161f] border border-zinc-800/90 text-zinc-200 shadow-sm"
                }`}
              >
                <div className="whitespace-pre-wrap font-sans">{msg.content}</div>
              </div>

              {msg.role === "user" && (
                <div className="h-8 w-8 rounded-xl bg-zinc-800 border border-zinc-700 flex items-center justify-center shrink-0">
                  <User className="h-4 w-4 text-zinc-300" />
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 md:p-6 bg-[#090b0e] border-t border-zinc-800/80">
          <form
            onSubmit={handleSubmit}
            className="max-w-4xl mx-auto relative flex items-center"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Tell Donk what to build, test, or execute..."
              className="w-full bg-[#12161f] border border-zinc-700/60 rounded-xl px-4 py-3.5 pr-12 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition shadow-inner"
            />
            <button
              type="submit"
              disabled={isStreaming || !input.trim()}
              className="absolute right-2.5 p-2 rounded-lg bg-emerald-500 text-black hover:bg-emerald-400 disabled:opacity-20 disabled:hover:bg-emerald-500 transition cursor-pointer font-bold"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
