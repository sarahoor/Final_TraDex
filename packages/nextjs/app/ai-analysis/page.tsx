/* eslint-disable react/no-unescaped-entities */
'use client';

import { useState, useRef, useEffect } from 'react';
import { Brain, Send, TrendingUp, Shield, Zap } from 'lucide-react';

type Msg = { role: 'user' | 'ai'; text: string };
type Risk = 'DIAMOND' | 'SIGMA' | 'DEGEN';

async function askAI(message: string, risk: Risk) {
  const res = await fetch('/api/ai/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, risk_profile: risk }),
  });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return String(data.response ?? 'No response');
}

// Helper function to format AI responses with proper markdown
function formatAIResponse(text: string) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold text
    .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic text
    .replace(/```([\s\S]*?)```/g, '<code class="block bg-base-200 p-2 rounded">$1</code>') // Code blocks
    .replace(/`(.*?)`/g, '<code class="bg-base-200 px-1 rounded">$1</code>') // Inline code
    .replace(/\n/g, '<br>') // Line breaks
    .replace(/🎯|📊|🎰|💰|⚠️|🚀|💎|📈|📉|💹|🔥|⭐|✅|❌|🔍|💡/g, '<span class="text-lg">$&</span>'); // Make emojis larger
}

export default function AIAnalysisPage() {
  const [risk, setRisk] = useState<Risk>('SIGMA');
  const [msgs, setMsgs] = useState<Msg[]>([
    { role: 'ai', text: "Welcome to your **Professional Financial AI Assistant**. I provide institutional-grade cryptocurrency analysis and investment strategies tailored to your risk profile. You can:\n\n• **Analyze individual tokens**: \"Analyze Bitcoin fundamentals\"\n• **Compare multiple assets**: \"Compare Bitcoin vs Ethereum vs Solana\"\n• **Scan opportunities**: \"Scan current market opportunities\"\n• **Get market insights**: \"Current market sentiment analysis\"\n\nHow can I assist with your investment analysis today?" },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [msgs]);

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setInput('');
    setMsgs(m => [...m, { role: 'user', text }, { role: 'ai', text: '📊 Conducting market analysis and risk assessment...' }]);
    setSending(true);
    try {
      const reply = await askAI(text, risk);
      setMsgs(m => [...m.slice(0, -1), { role: 'ai', text: reply }]);
    } catch (e: any) {
      setMsgs(m => [...m.slice(0, -1), { role: 'ai', text: `❌ **Analysis Error**: ${e?.message || 'Request failed'}. Please try again.` }]);
    } finally {
      setSending(false);
    }
  };

  const getRiskIcon = (riskLevel: Risk) => {
    switch (riskLevel) {
      case 'DIAMOND': return <Shield className="h-4 w-4" />;
      case 'SIGMA': return <TrendingUp className="h-4 w-4" />;
      case 'DEGEN': return <Zap className="h-4 w-4" />;
    }
  };

  const getRiskColor = (riskLevel: Risk) => {
    switch (riskLevel) {
      case 'DIAMOND': return 'select-success';
      case 'SIGMA': return 'select-warning';
      case 'DEGEN': return 'select-error';
    }
  };

  const quickPrompts = [
    'Analyze Bitcoin fundamentals', 
    'Compare Bitcoin vs Ethereum', 
    'Scan current market opportunities', 
    'Risk assessment for portfolio',
    'Market sentiment analysis',
    'DeFi investment strategies'
  ];

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="btn btn-circle btn-primary text-white">
            <Brain className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Financial AI Assistant</h1>
            <p className="text-sm opacity-70">Advanced cryptocurrency analysis & investment strategies</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm font-medium opacity-70">Investment Style:</span>
          <div className="flex items-center gap-2">
            {getRiskIcon(risk)}
            <select
              className={`select select-sm select-bordered ${getRiskColor(risk)}`}
              value={risk}
              onChange={e => setRisk(e.target.value as Risk)}
            >
              <option value="DIAMOND">🛡️ Play it Safe (Low Risk)</option>
              <option value="SIGMA">📊 Smart Investor (Calculated Risk)</option>
              <option value="DEGEN">🚀 High Risk High Reward</option>
            </select>
          </div>
        </div>
      </div>
# Only run this if you haven't installed dependencies yet
pip install -r requirements.txt
      <div className="card bg-base-100 shadow-lg border border-base-300">
        <div className="card-body p-4 md:p-6">
          <div className="space-y-4 h-[60vh] overflow-y-auto pr-2">
            {msgs.map((m, i) => (
              <div key={i} className={`chat ${m.role === 'user' ? 'chat-end' : 'chat-start'}`}>
                <div className={`chat-bubble max-w-[85%] ${
                  m.role === 'user' 
                    ? 'chat-bubble-primary' 
                    : 'chat-bubble-secondary bg-base-200 text-base-content'
                }`}>
                  {m.role === 'ai' ? (
                    <div 
                      className="whitespace-pre-wrap leading-relaxed"
                      dangerouslySetInnerHTML={{ __html: formatAIResponse(m.text) }}
                    />
                  ) : (
                    <div className="whitespace-pre-wrap">{m.text}</div>
                  )}
                </div>
              </div>
            ))}
            <div ref={endRef} />
          </div>

          <div className="mt-4 space-y-3">
            <div className="flex gap-2">
              <input
                className="input input-bordered flex-1 focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Ask for analysis, comparisons, or market insights (e.g., 'Compare Bitcoin vs Ethereum')..."
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
              />
              <button 
                className="btn btn-primary min-w-[100px]" 
                onClick={send} 
                disabled={sending}
              >
                {sending ? (
                  <span className="loading loading-spinner loading-sm"></span>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-1" /> Send
                  </>
                )}
              </button>
            </div>

            <div className="flex flex-wrap gap-2">
              {quickPrompts.map(prompt => (
                <button 
                  key={prompt} 
                  className="btn btn-xs btn-outline hover:btn-primary transition-all duration-200" 
                  onClick={() => setInput(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Risk Profile Indicator */}
      <div className="alert alert-info">
        <div className="flex items-center gap-2">
          {getRiskIcon(risk)}
          <span className="font-medium">
            Current Strategy: {
              risk === 'DIAMOND' ? 'Conservative - Focus on stable, established cryptocurrencies' :
              risk === 'SIGMA' ? 'Balanced - Mix of stability and growth potential' :
              'Aggressive - High-growth potential with higher volatility'
            }
          </span>
        </div>
      </div>
    </div>
  );
}