import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BrainCircuit,
  Sparkles,
  AlertTriangle,
  Send,
  CheckCircle2,
  HelpCircle,
  TrendingDown,
  ShieldAlert,
  Loader2,
  Bot,
  User,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { aiService } from '../../services/aiService';
import { AIInsight, AIAssistantMessage } from '../../types';
import { formatDate } from '../../utils';

export const AIInsightsDashboard: React.FC = () => {
  const queryClient = useQueryClient();
  const [messages, setMessages] = useState<AIAssistantMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Hello, I am the VERISUB Intelligent Copilot. I analyze subscription telemetry, invoice anomalies, contract SLAs, and payment reconciliations. How can I assist you today?',
      timestamp: new Date().toISOString(),
      sources: ['VERISUB Active Ledger'],
    },
  ]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [isAsking, setIsAsking] = useState(false);

  // Queries
  const { data: insights = [], isLoading } = useQuery({
    queryKey: ['aiInsights'],
    queryFn: () => aiService.getInsights(),
  });

  // Acknowledge Mutation
  const ackMutation = useMutation({
    mutationFn: (id: string) => aiService.acknowledgeInsight(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['aiInsights'] }),
  });

  // Send Chat message
  const handleSendMessage = async (promptToSend?: string) => {
    const text = (promptToSend || inputPrompt).trim();
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
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: 'err-' + Date.now(),
          role: 'assistant',
          content: `Backend Assistant Error: ${err.message || 'Failed to communicate with AI endpoint.'}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsAsking(false);
    }
  };

  const QUICK_QUESTIONS = [
    'Which invoices are overdue?',
    'Which subscriptions have unusual billing?',
    'What is our outstanding amount?',
    'Which customers have payment issues?',
  ];

  return (
    <div className="space-y-6 text-left">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              AI Insights & Intelligent Assistant
            </h1>
            <span className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-semibold text-brand-700 dark:bg-brand-950/60 dark:text-brand-300">
              <Sparkles className="h-3.5 w-3.5" />
              Real Telemetry
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Proactive anomaly detection across invoice cycles, unexpected discount spikes, and natural language analytics
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Anomalies & Detected Insights */}
        <div className="lg:col-span-7 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Detected Anomalies & Risk Signals ({insights.length})
          </h3>

          {isLoading ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-32 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse" />
              ))}
            </div>
          ) : (
            insights.map((insight) => {
              const isHigh = insight.severity === 'high';
              const isMedium = insight.severity === 'medium';

              return (
                <Card
                  key={insight.id}
                  className={`border transition-all ${
                    isHigh
                      ? 'border-rose-200 dark:border-rose-900 bg-rose-50/20'
                      : isMedium
                      ? 'border-amber-200 dark:border-amber-900 bg-amber-50/20'
                      : 'border-slate-200 dark:border-slate-800'
                  }`}
                >
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-center gap-2">
                        {isHigh ? (
                          <ShieldAlert className="h-5 w-5 text-rose-600 shrink-0" />
                        ) : isMedium ? (
                          <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />
                        ) : (
                          <BrainCircuit className="h-5 w-5 text-brand-600 shrink-0" />
                        )}
                        <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                          {insight.title}
                        </h4>
                      </div>
                      <Badge
                        variant={isHigh ? 'danger' : isMedium ? 'warning' : 'info'}
                        size="sm"
                      >
                        {insight.severity.toUpperCase()}
                      </Badge>
                    </div>

                    <p className="mt-2 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                      {insight.explanation}
                    </p>

                    <div className="mt-3 rounded-lg bg-white/70 p-2.5 text-xs text-slate-700 dark:bg-slate-800/80 dark:text-slate-200 border border-slate-100 dark:border-slate-800">
                      <span className="font-semibold text-brand-600 dark:text-brand-400">
                        Recommended Action:{' '}
                      </span>
                      {insight.recommended_action}
                    </div>

                    <div className="mt-4 flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800/60 text-xs">
                      <span className="font-mono text-slate-400 text-[11px]">
                        Ref: {insight.entity_reference}
                      </span>
                      {insight.is_reviewed ? (
                        <span className="inline-flex items-center gap-1 font-semibold text-emerald-600">
                          <CheckCircle2 className="h-3.5 w-3.5" /> Reviewed
                        </span>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => ackMutation.mutate(insight.id)}
                          isLoading={ackMutation.isPending}
                        >
                          Acknowledge
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>

        {/* Right Column: AI Assistant Chat Interface */}
        <div className="lg:col-span-5 flex flex-col h-[650px] rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 overflow-hidden">
          {/* Header */}
          <div className="flex items-center gap-3 border-b border-slate-100 bg-slate-50/70 p-4 dark:border-slate-800 dark:bg-slate-800/50">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white shadow-xs">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-900 dark:text-white">
                Member 3 Assistant Endpoint
              </h3>
              <p className="text-[10px] text-slate-500">FastAPI Natural Language Agent</p>
            </div>
          </div>

          {/* Messages Area */}
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
                      isUser
                        ? 'bg-slate-800 text-white dark:bg-slate-700'
                        : 'bg-brand-600 text-white'
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
                    {m.sources && m.sources.length > 0 && (
                      <div className="mt-2 pt-1 border-t border-slate-200/40 text-[10px] text-slate-500 dark:text-slate-400">
                        Sources: {m.sources.join(', ')}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            {isAsking && (
              <div className="flex items-center gap-2 text-xs text-slate-400 italic">
                <Loader2 className="h-4 w-4 animate-spin text-brand-600" />
                Querying platform telemetry and calculating authoritative response...
              </div>
            )}
          </div>

          {/* Quick Prompts */}
          <div className="border-t border-slate-100 bg-slate-50/50 p-2.5 dark:border-slate-800 dark:bg-slate-900/50">
            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5 px-1">
              Suggested Questions:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {QUICK_QUESTIONS.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(q)}
                  disabled={isAsking}
                  className="rounded-md border border-slate-200 bg-white px-2 py-1 text-[11px] font-medium text-slate-700 hover:border-brand-500 hover:text-brand-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-brand-500"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Input Box */}
          <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={inputPrompt}
                onChange={(e) => setInputPrompt(e.target.value)}
                placeholder="Ask about overdue bills, churn risk, SLA breaches..."
                className="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
              <Button
                type="submit"
                size="sm"
                disabled={!inputPrompt.trim() || isAsking}
                isLoading={isAsking}
              >
                <Send className="h-3.5 w-3.5" />
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
