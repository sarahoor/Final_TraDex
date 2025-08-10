'use client';

import { useState } from 'react';

export default function AssistantPage() {
  const [msgs, setMsgs] = useState<{role:'user'|'ai',text:string}[]>([]);
  const [input, setInput] = useState('');

  async function send() {
    const text = input.trim();
    if (!text) return;
    setMsgs(m => [...m, {role:'user', text}, {role:'ai', text:'…thinking'}]);
    setInput('');

    try {
      const res = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ message: text, risk_profile: 'SIGMA' }),
      });
      const data = await res.json();
      setMsgs(m => [...m.slice(0, -1), {role:'ai', text: data.response ?? 'No response'}]);
    } catch (e:any) {
      setMsgs(m => [...m.slice(0, -1), {role:'ai', text: `Error: ${e?.message || e}`}]);
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-4">
      <h1 className="text-2xl font-semibold">AI Assistant</h1>
      <div className="border rounded-lg p-4 space-y-3 h-[60vh] overflow-y-auto bg-white">
        {msgs.map((m,i)=>(
          <div key={i} className={m.role==='user'?'text-right':''}>
            <div className={`inline-block px-3 py-2 rounded-lg ${m.role==='user'?'bg-indigo-600 text-white':'bg-gray-100'}`}>{m.text}</div>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          className="flex-1 border rounded-md px-3 py-2"
          value={input}
          onChange={e=>setInput(e.target.value)}
          onKeyDown={e=>{ if(e.key==='Enter') send(); }}
          placeholder="Ask about BTC, ETH, on-chain signals…"
        />
        <button onClick={send} className="px-4 py-2 rounded-md bg-indigo-600 text-white">Send</button>
      </div>
    </div>
  );
}
