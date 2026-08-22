"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Terminal, ShieldCheck, ShieldAlert, BookOpen, GitBranch,
  Cpu, Play, CheckCircle2, AlertTriangle, ChevronRight,
  Send, Mic, Square, CornerDownLeft, FileCode, Check, RefreshCw, Flame
} from "lucide-react";

// --- EVENT TYPES ---
type EnginePhase = "idle" | "listening" | "retrieving" | "analyzing" | "awaiting_approval" | "executing" | "completed";

interface TimelineEvent {
  id: string;
  phase: string;
  label: string;
  status: "pending" | "running" | "success" | "warning" | "failed";
  timestamp: string;
  details?: string;
}

interface Citation {
  source: string;
  title: string;
  authority: string;
  snippet?: string;
}

interface PendingAction {
  actionId: string;
  title: string;
  description: string;
  diff?: string;
  risk: "draft" | "write" | "irreversible";
}

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  action?: PendingAction;
  runId?: string;
}

export default function DonkControlRoom() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Yo Kevan. Donk's live in the core with full Grok-level candid intelligence. I'm zero-filter on technical analysis, hyper-competent on systems engineering, and locked into our 2,461-node Vault, Rust L1 state engine, and RTX 5090 CUDA node. What are we building, roasting, or executing right now?",
    },
  ]);
  const [input, setInput] = useState("");
  const [phase, setPhase] = useState<EnginePhase>("idle");
  const [isStreaming, setIsStreaming] = useState(false);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // --- 3D SPECTRAL CORE / WAVEFORM RENDERING ---
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;
    let t = 0;

    const render = () => {
      t += 0.04;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;

      let baseRadius = 24;
      let amp = 3;
      let colorPrimary = "rgba(225, 29, 72, "; // Crimson default for Donk
      let colorGlow = "rgba(225, 29, 72, 0.25)";

      if (phase === "retrieving" || phase === "analyzing") {
        baseRadius = 26;
        amp = 6;
        colorPrimary = "rgba(56, 189, 248, "; // Cyan
        colorGlow = "rgba(56, 189, 248, 0.35)";
      } else if (phase === "awaiting_approval") {
        baseRadius = 28;
        amp = 5;
        colorPrimary = "rgba(245, 158, 11, "; // Amber
        colorGlow = "rgba(245, 158, 11, 0.45)";
      } else if (phase === "executing") {
        baseRadius = 27;
        amp = 8;
        colorPrimary = "rgba(16, 185, 129, "; // Emerald
        colorGlow = "rgba(16, 185, 129, 0.4)";
      }

      // Render outer containment glow
      const grad = ctx.createRadialGradient(centerX, centerY, baseRadius * 0.4, centerX, centerY, baseRadius * 1.8);
      grad.addColorStop(0, colorGlow);
      grad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(centerX, centerY, baseRadius * 1.8, 0, Math.PI * 2);
      ctx.fill();

      // Render pulsating liquid-metal orb lines
      for (let i = 0; i < 3; i++) {
        ctx.beginPath();
        for (let a = 0; a <= Math.PI * 2; a += 0.1) {
          const distortion = Math.sin(a * 4 + t + i) * amp + Math.cos(a * 2 - t) * (amp * 0.5);
          const r = baseRadius + distortion + i * 2;
          const x = centerX + Math.cos(a) * r;
          const y = centerY + Math.sin(a) * r;
          if (a === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.strokeStyle = `${colorPrimary}${0.8 - i * 0.2})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      animationId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationId);
  }, [phase]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, timeline]);

  // --- DISPATCH COGNITIVE RUNTIME EVENT STREAM ---
  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userPrompt = input.trim();
    setInput("");
    setIsStreaming(true);
    setPhase("retrieving");

    const runId = `run_${Math.random().toString(36).substring(2, 7)}`;
    setActiveRunId(runId);
    setTimeline([]);

    setMessages((prev) => [...prev, { role: "user", content: userPrompt }]);
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", runId, citations: [] }
    ]);

    try {
      const res = await fetch("http://127.0.0.1:8790/v1/chat/threads/master/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userPrompt, workspace: "Unykorn-Core" }),
      });

      if (!res.body) throw new Error("No readable stream");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const block of events) {
          if (!block.startsWith("event:")) continue;
          const [eLine, dLine] = block.split("\n");
          const eventType = eLine.replace("event: ", "").trim();
          const data = JSON.parse(dLine.replace("data: ", "").trim());

          if (eventType === "status") {
            setPhase(data.phase || "analyzing");
            setTimeline((prev) => [
              ...prev,
              {
                id: Math.random().toString(),
                phase: data.phase,
                label: data.label,
                status: "running",
                timestamp: new Date().toLocaleTimeString(),
              },
            ]);
          } else if (eventType === "citation") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              last.citations = [...(last.citations || []), data];
              return updated;
            });
          } else if (eventType === "tool_call") {
            setTimeline((prev) => [
              ...prev,
              {
                id: Math.random().toString(),
                phase: "tool",
                label: `Invoked Tool: ${data.tool}`,
                status: data.status === "completed" ? "success" : "running",
                timestamp: new Date().toLocaleTimeString(),
                details: JSON.stringify(data.parameters || {}),
              },
            ]);
          } else if (eventType === "delta") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              last.content += data.text;
              return updated;
            });
          } else if (eventType === "action_required") {
            setPhase("awaiting_approval");
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              last.action = data;
              return updated;
            });
          } else if (eventType === "completed") {
            setPhase("completed");
            setTimeline((prev) =>
              prev.map((t) => ({ ...t, status: t.status === "running" ? "success" : t.status }))
            );
          }
        }
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "⚠️ Socket dropped or FastAPI on port 8790 is down." }
      ]);
    } finally {
      setIsStreaming(false);
      setTimeout(() => setPhase("idle"), 2500);
    }
  };

  const handleApproveAction = async (action: PendingAction) => {
    setPhase("executing");
    setTimeline((prev) => [
      ...prev,
      {
        id: Math.random().toString(),
        phase: "write",
        label: `Authorizing: ${action.title}`,
        status: "running",
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);

    await fetch("http://127.0.0.1:8790/v1/chat/threads/master/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actionId: action.actionId }),
    });

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: `🔥 **Done. Signed & Dispatched:** ${action.title}\n\nStaging patch committed. Signed execution receipt logged to daily vault ledger.`,
      },
    ]);
    setPhase("idle");
  };

  return (
    <div className="flex h-screen bg-[#07090c] text-zinc-100 font-sans selection:bg-rose-500 selection:text-white overflow-hidden">
      
      {/* --- 1. LEFT NAVIGATION RAIL --- */}
      <aside className="w-72 border-r border-zinc-800/80 bg-[#0b0e14] flex flex-col justify-between hidden md:flex z-10">
        <div className="p-5 space-y-6">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 font-bold shadow-[0_0_15px_rgba(244,63,94,0.2)]">
              ⚡
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-wider text-zinc-100">DONK RUNTIME</h1>
              <p className="text-[10px] text-zinc-500 font-mono uppercase tracking-widest">Candid & Unfiltered Engine</p>
            </div>
          </div>

          <button className="w-full py-2.5 px-3 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-xl text-xs flex items-center justify-between transition shadow-md shadow-rose-950/40">
            <span>+ New Mission</span>
            <span className="text-[10px] font-mono text-rose-200">⌘N</span>
          </button>

          <div className="space-y-4">
            <div>
              <p className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest px-2 mb-2">Active Missions</p>
              <div className="space-y-1 text-xs">
                <button className="w-full text-left px-3 py-2 rounded-lg bg-zinc-800/60 text-rose-400 border border-rose-500/30 flex items-center gap-2 font-medium">
                  <Terminal className="h-3.5 w-3.5 text-rose-400" />
                  <span>ERC-3643 Config Audit</span>
                </button>
                <button className="w-full text-left px-3 py-2 rounded-lg hover:bg-zinc-800/30 text-zinc-400 flex items-center gap-2 transition">
                  <Cpu className="h-3.5 w-3.5 text-cyan-400" />
                  <span>Rust L1 State Verification</span>
                </button>
                <button className="w-full text-left px-3 py-2 rounded-lg hover:bg-zinc-800/30 text-zinc-400 flex items-center gap-2 transition">
                  <ShieldCheck className="h-3.5 w-3.5 text-amber-400" />
                  <span>SPV Collateral Attestation</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-zinc-800/80 bg-[#0e1219]/60 font-mono text-[11px] space-y-2">
          <div className="flex justify-between items-center text-zinc-400">
            <span>Persona Mode:</span>
            <span className="text-rose-400 font-semibold flex items-center gap-1">
              <Flame className="h-3 w-3 text-rose-500" /> Grok Candid
            </span>
          </div>
          <div className="flex justify-between items-center text-zinc-400">
            <span>Action Safety:</span>
            <span className="text-emerald-400 font-semibold">EIP-712 Gated</span>
          </div>
          <div className="flex justify-between items-center text-zinc-400">
            <span>CUDA Node:</span>
            <span className="text-zinc-200">RTX 5090</span>
          </div>
        </div>
      </aside>

      {/* --- 2. CENTER CONVERSATIONAL OPERATOR --- */}
      <main className="flex-1 flex flex-col h-full bg-[#07090c] relative">
        <header className="h-16 border-b border-zinc-800/80 px-6 flex items-center justify-between bg-[#0b0e14]/70 backdrop-blur-md z-10">
          <div className="flex items-center gap-4">
            <div className="relative h-10 w-10 flex items-center justify-center">
              <canvas ref={canvasRef} width={80} height={80} className="w-10 h-10" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-zinc-100">Donk</span>
                <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-mono">
                  UNFILTERED INTEL • {phase.toUpperCase()}
                </span>
              </div>
              <p className="text-[10px] text-zinc-500 font-mono">Autonomous Systems Architect</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              L1 Height: #13
            </span>
          </div>
        </header>

        {/* Message Feed */}
        <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6 max-w-3xl mx-auto w-full">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-4 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "assistant" && (
                <div className="h-8 w-8 rounded-xl bg-[#11141c] border border-rose-500/30 flex items-center justify-center text-rose-400 font-bold text-xs shrink-0 shadow-sm">
                  ⚡
                </div>
              )}

              <div className="space-y-3 max-w-[88%]">
                <div
                  className={`rounded-2xl px-5 py-4 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-rose-600 text-white font-medium shadow-md"
                      : "bg-[#0f131a] border border-zinc-800 text-zinc-200 shadow-sm"
                  }`}
                >
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>

                {msg.citations && msg.citations.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <p className="text-[10px] font-mono uppercase text-zinc-500 tracking-wider">Grounding Evidence</p>
                    <div className="flex flex-wrap gap-2">
                      {msg.citations.map((c, ci) => (
                        <div key={ci} className="px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs flex items-center gap-2 text-zinc-300 font-mono">
                          <BookOpen className="h-3.5 w-3.5 text-cyan-400" />
                          <span>{c.title}</span>
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-zinc-800 text-emerald-400">{c.authority}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {msg.action && (
                  <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/40 space-y-3 font-mono">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-amber-400 flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4" /> Action Approval Required
                      </span>
                      <span className="text-[10px] px-2 py-0.5 bg-amber-500/10 text-amber-300 rounded border border-amber-500/20">
                        {msg.action.risk.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-300">{msg.action.description}</p>
                    {msg.action.diff && (
                      <pre className="p-3 bg-black/60 rounded-lg text-[11px] text-emerald-400 overflow-x-auto border border-zinc-800">
                        {msg.action.diff}
                      </pre>
                    )}
                    <button
                      onClick={() => handleApproveAction(msg.action!)}
                      className="w-full py-2 bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs rounded-lg transition flex items-center justify-center gap-2 cursor-pointer"
                    >
                      <Check className="h-4 w-4" /> Authorize EIP-712 & Commit Staging Patch
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Composer */}
        <div className="p-4 md:p-6 bg-[#07090c] border-t border-zinc-800/80">
          <form onSubmit={handleSend} className="max-w-3xl mx-auto relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Donk anything—unfiltered analysis, L1 audits, or staging patches..."
              className="w-full bg-[#0f131a] border border-zinc-700/60 rounded-xl px-4 py-3.5 pr-20 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-rose-500 transition shadow-inner font-sans"
            />
            <div className="absolute right-2.5 flex items-center gap-1.5">
              <button
                type="submit"
                disabled={isStreaming || !input.trim()}
                className="p-2 rounded-lg bg-rose-600 text-white hover:bg-rose-500 disabled:opacity-20 transition font-bold cursor-pointer"
              >
                <CornerDownLeft className="h-4 w-4" />
              </button>
            </div>
          </form>
        </div>
      </main>

      {/* --- 3. RIGHT RAIL: EXECUTION TRACE --- */}
      <aside className="w-80 border-l border-zinc-800/80 bg-[#0b0e14] p-5 flex flex-col justify-between hidden lg:flex">
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
            <span className="text-xs font-mono font-bold text-zinc-300 uppercase tracking-wider">Live Execution Trace</span>
            {activeRunId && <span className="text-[10px] font-mono text-zinc-500">{activeRunId}</span>}
          </div>

          {timeline.length === 0 ? (
            <div className="py-12 text-center text-xs text-zinc-600 font-mono">
              Awaiting next operational command.
            </div>
          ) : (
            <div className="space-y-3 font-mono">
              {timeline.map((item, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-[#0e1219] border border-zinc-800/80 text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-400 text-[10px] uppercase">{item.phase}</span>
                    <span className="text-zinc-600 text-[9px]">{item.timestamp}</span>
                  </div>
                  <div className="flex items-center gap-2 text-zinc-200 text-[11px]">
                    {item.status === "running" && <RefreshCw className="h-3 w-3 text-cyan-400 animate-spin" />}
                    {item.status === "success" && <CheckCircle2 className="h-3 w-3 text-emerald-400" />}
                    <span>{item.label}</span>
                  </div>
                  {item.details && (
                    <p className="text-[10px] text-zinc-500 truncate">{item.details}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-3 rounded-xl bg-zinc-900/80 border border-zinc-800 text-[10px] font-mono text-zinc-400 space-y-1">
          <p className="text-rose-400 font-semibold">Donk Grok Mode Active</p>
          <p>• Unfiltered natural language</p>
          <p>• Action execution gated via EIP-712</p>
        </div>
      </aside>

    </div>
  );
}
