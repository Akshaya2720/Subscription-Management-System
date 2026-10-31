import React, { useState } from 'react';
import { Bot, User, Send, Sparkles, Loader2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { aiService } from '../../services/aiService';
import { AIAssistantMessage } from '../../types';

export const CustomerHelp: React.FC = () => {
  const [messages, setMessages] = useState<AIAssistantMessage[]>([
    {
      id: 'welcome-cust',
      role: 'assistant',
      content:
        'Welcome to Acme Customer Support! I can help you check your next billing date, explain invoice line items, calculate SLA credit eligibility, or answer plan upgrade questions.',
      timestamp: new Date().toISOString(),
      sources: ['VERISUB Customer Care Engine'],
    },
  ]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [isAsking, setIsAsking] = useState(false);

  const handleSend = async (query?: string) => {
    const text = (query || inputPrompt).trim();
    if (!text || isAsking) return;

    const userMsg: AIAssistantMessage = {
      id: 'user-' + Date.now(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputPrompt('');
    setIsAsking(true);

    try {
      const response = await aiService.askAssistant(text);
      setMessages((prev) => [...prev, response]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: 'err-' + Date.now(),
          role: 'assistant',
          content: 'I was unable to retrieve that record at this moment. Please try again or open a dispute.',
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div className="space-y-6 text-left max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Customer AI Assistant & Knowledge Base
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Instant answers to billing schedules, invoice calculations, and contract questions
        </p>
      </div>

      <div className="flex flex-col h-[550px] rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((m) => {
            const isUser = m.role === 'user';
            return (
              <div
                key={m.id}
                className={`flex items-start gap-2.5 ${isUser ? 'flex-row-reverse' : ''}`}
              >
                <div
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold ${
                    isUser ? 'bg-slate-800 text-white' : 'bg-brand-600 text-white'
                  }`}
                >
                  {isUser ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
                </div>
                <div
                  className={`max-w-[85%] rounded-xl p-3 text-xs leading-relaxed ${
                    isUser
                      ? 'bg-brand-600 text-white'
                      : 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200'
                  }`}
                >
                  <p className="whitespace-pre-line">{m.content}</p>
                </div>
              </div>
            );
          })}
          {isAsking && (
            <div className="flex items-center gap-2 text-xs text-slate-400 italic">
              <Loader2 className="h-4 w-4 animate-spin text-brand-600" />
              Checking your account records...
            </div>
          )}
        </div>

        {/* Input */}
        <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              placeholder="Ask a question about your invoices or service uptime..."
              className="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
            <Button type="submit" size="sm" disabled={!inputPrompt.trim() || isAsking}>
              <Send className="h-3.5 w-3.5" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};
