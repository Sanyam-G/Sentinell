'use client';

import { useEffect, useMemo, useState } from 'react';

const typingTexts = [
  'with autonomous SREs',
  'that remediate in seconds',
  'with zero downtime',
  'powered by AI playbooks',
];

const featureBlocks = [
  {
    title: 'Unified signal plane',
    description: 'Bring metrics, traces, logs, and Git metadata into one searchable timeline with automatic correlation.',
    icon: '📡',
  },
  {
    title: 'Self-healing workflows',
    description: 'Built-in automations triage incidents, open PRs, and ship fixes without waiting for humans to wake up.',
    icon: '🛠️',
  },
  {
    title: 'Human-grade reporting',
    description: 'Readable summaries, stakeholder-ready updates, and captured reasoning for every incident.',
    icon: '🧠',
  },
];

const metrics = [
  { label: 'Incidents automated', value: '92%', meta: 'per on-call shift' },
  { label: 'Mean time to repair', value: '4m 12s', meta: '-83% vs baseline' },
  { label: 'Signals ingested', value: '12 sources', meta: 'logs, traces, code, Slack' },
];

export default function Home() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [typedText, setTypedText] = useState('');
  const [textIndex, setTextIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const storedTheme = localStorage.getItem('sentinell-landing-theme') as 'light' | 'dark' | null;
    const nextTheme = storedTheme ?? 'light';
    setTheme(nextTheme);
    document.documentElement.classList.toggle('dark', nextTheme === 'dark');
  }, []);

  useEffect(() => {
    const currentText = typingTexts[textIndex];
    const typingSpeed = isDeleting ? 45 : 85;

    const timer = setTimeout(() => {
      if (!isDeleting && typedText.length < currentText.length) {
        setTypedText(currentText.slice(0, typedText.length + 1));
        return;
      }

      if (!isDeleting && typedText.length === currentText.length) {
        setTimeout(() => setIsDeleting(true), 1400);
        return;
      }

      if (isDeleting && typedText.length > 0) {
        setTypedText(currentText.slice(0, typedText.length - 1));
        return;
      }

      setIsDeleting(false);
      setTextIndex((prev) => (prev + 1) % typingTexts.length);
    }, typingSpeed);

    return () => clearTimeout(timer);
  }, [typedText, textIndex, isDeleting]);

  const toggleTheme = () => {
    setTheme((prev) => {
      const nextTheme = prev === 'light' ? 'dark' : 'light';
      document.documentElement.classList.toggle('dark', nextTheme === 'dark');
      localStorage.setItem('sentinell-landing-theme', nextTheme);
      return nextTheme;
    });
  };

  const heroStats = useMemo(
    () => [
      { label: '24/7 coverage', value: 'Autonomous SRE pods' },
      { label: 'PRs shipped', value: '82 this week' },
      { label: 'Signals watched', value: 'logs · traces · Git · Slack' },
    ],
    []
  );

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 text-gray-900 dark:text-slate-100 transition-colors duration-500">
      <div className="relative z-10">
        <header className="container mx-auto px-6 py-6 flex flex-wrap gap-4 items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-11 w-11 rounded-2xl bg-blue-600 shadow-lg shadow-blue-500/30 flex items-center justify-center text-white font-bold">
              S
            </div>
            <div>
              <p className="text-sm uppercase tracking-[0.2em] text-gray-500 dark:text-slate-400">Sentinell</p>
              <p className="font-semibold text-lg">Autonomous Operations</p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-sm">
            <a href="#features" className="text-gray-600 dark:text-slate-300 hover:text-blue-600">Features</a>
            <a href="#playbooks" className="text-gray-600 dark:text-slate-300 hover:text-blue-600">Playbooks</a>
            <a href="#integrations" className="text-gray-600 dark:text-slate-300 hover:text-blue-600">Integrations</a>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={toggleTheme}
              className="p-3 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:border-blue-400 dark:hover:border-blue-500 transition-all"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? (
                <svg className="w-5 h-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zM9 16a1 1 0 012 0v1a1 1 0 11-2 0v-1z" />
                  <path d="M4.222 5.636a1 1 0 011.414 0l.707.707A1 1 0 115.636 7.757l-.707-.707a1 1 0 010-1.414zM3 11a1 1 0 100-2H2a1 1 0 000 2h1zm12.364-4.95a1 1 0 111.414 1.414l-.707.707a1 1 0 01-1.414-1.414l.707-.707zM18 11a1 1 0 100-2h-1a1 1 0 100 2h1z" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-blue-600" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10 2a8 8 0 106.32 12.906A7 7 0 0110 2z" />
                </svg>
              )}
            </button>
            <a
              href="http://localhost:5173"
              className="px-5 py-3 text-sm font-semibold rounded-xl text-white bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/40 transition"
            >
              Launch dashboard
            </a>
          </div>
        </header>

        <main className="container mx-auto px-6 pb-24">
          <section className="grid gap-12 lg:grid-cols-[1.05fr_0.95fr] items-center pt-10">
            <div className="space-y-8">
              <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-gray-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/40 shadow-sm">
                <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                <p className="text-sm text-gray-600 dark:text-slate-300">Autonomous SRE • Real-time response</p>
              </div>

              <div>
                <p className="text-sm uppercase tracking-[0.3em] text-blue-600 dark:text-blue-300 mb-4">Always-on operations</p>
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold leading-tight text-balance">
                  Infrastructure observability
                  <span className="block text-blue-600 dark:text-blue-400">
                    {typedText}
                    <span className="animate-pulse">|</span>
                  </span>
                </h1>
              </div>

              <p className="text-lg text-gray-600 dark:text-slate-300 max-w-2xl">
                Sentinell is your autonomous site reliability engineer. It watches every signal, correlates context, and ships fixes before PagerDuty ever lights up.
              </p>

              <div className="flex flex-wrap gap-4">
                <a
                  href="http://localhost:5173"
                  className="inline-flex items-center justify-center px-7 py-3 rounded-2xl bg-blue-600 text-white font-semibold shadow-lg shadow-blue-500/40 hover:translate-y-[-2px] transition"
                >
                  Continue to dashboard
                  <svg className="w-5 h-5 ml-2" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                  </svg>
                </a>
                <button className="px-7 py-3 rounded-2xl border border-gray-300 dark:border-slate-700 bg-white dark:bg-transparent text-gray-900 dark:text-slate-100 font-semibold hover:border-blue-400">
                  Book a demo
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {heroStats.map((stat) => (
                  <div key={stat.label} className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm">
                    <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-slate-400">{stat.label}</p>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">{stat.value}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl shadow-blue-500/5 p-8 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-slate-400">Current incident</p>
                  <h3 className="text-xl font-semibold">Latency regression on checkout</h3>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-600 dark:bg-orange-500/20 dark:text-orange-300">high</span>
              </div>
              <div className="rounded-2xl bg-gray-50 dark:bg-slate-950/40 border border-gray-200 dark:border-slate-800 p-5 space-y-4">
                <div className="space-y-2 text-sm text-gray-600 dark:text-slate-300">
                  <p>⚙️ Running synthetic traces on checkout endpoints</p>
                  <p>🪵 Pulling correlated stack traces from worker pods</p>
                  <p>📦 Queueing remediation PR with config rollback</p>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-slate-400">
                  <span>Autofix ETA</span>
                  <span className="text-blue-600 dark:text-blue-300 font-semibold">01m 48s</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-center">
                {metrics.map((metric) => (
                  <div key={metric.label} className="rounded-2xl border border-gray-100 dark:border-slate-800 bg-gray-50 dark:bg-slate-950/40 px-4 py-5">
                    <p className="text-sm font-semibold text-blue-600 dark:text-blue-300">{metric.value}</p>
                    <p className="text-xs text-gray-500 dark:text-slate-400">{metric.label}</p>
                    <p className="text-[11px] text-gray-400 dark:text-slate-500">{metric.meta}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section id="features" className="mt-24 space-y-10">
            <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
              <div>
                <p className="text-sm uppercase tracking-[0.3em] text-blue-600 dark:text-blue-400">Playbooks</p>
                <h2 className="text-3xl md:text-4xl font-semibold text-balance">Modern incident response out of the box</h2>
              </div>
              <p className="max-w-xl text-gray-600 dark:text-slate-300 text-sm">
                Each Sentinell playbook is a LangGraph-powered workflow that observes, reasons, and acts. Customize the nodes, swap tools, and layer guardrails without writing glue code.
              </p>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
              {featureBlocks.map((block) => (
                <div key={block.title} className="rounded-3xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm hover:border-blue-400 dark:hover:border-blue-500 transition">
                  <span className="text-3xl block mb-4">{block.icon}</span>
                  <h3 className="text-xl font-semibold mb-2">{block.title}</h3>
                  <p className="text-gray-600 dark:text-slate-400 text-sm leading-relaxed">{block.description}</p>
                </div>
              ))}
            </div>
          </section>

          <section id="integrations" className="mt-24 grid gap-10 lg:grid-cols-[1fr_1fr] items-center">
            <div className="rounded-3xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 space-y-6 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <p className="text-sm text-gray-500 dark:text-slate-400">Connected services</p>
              </div>
              <ul className="space-y-4 text-sm text-gray-600 dark:text-slate-300">
                <li className="flex items-center justify-between">
                  <span>GitHub + GitLab</span>
                  <span className="text-blue-600 dark:text-blue-300 font-semibold">PR automation</span>
                </li>
                <li className="flex items-center justify-between">
                  <span>Datadog, Prometheus, CloudWatch</span>
                  <span className="text-blue-600 dark:text-blue-300 font-semibold">Signal ingest</span>
                </li>
                <li className="flex items-center justify-between">
                  <span>PagerDuty, Slack, Teams</span>
                  <span className="text-blue-600 dark:text-blue-300 font-semibold">Human loop</span>
                </li>
              </ul>
            </div>

            <div className="rounded-3xl border border-blue-100 dark:border-slate-800 bg-blue-50 dark:bg-slate-900 text-blue-900 dark:text-slate-100 p-8 shadow-sm space-y-6">
              <p className="text-sm uppercase tracking-[0.3em] text-blue-400 dark:text-blue-300">Deployment</p>
              <h3 className="text-2xl font-semibold">Four services, one autonomous loop</h3>
              <p className="text-sm leading-relaxed text-blue-900/80 dark:text-slate-300">
                Run the landing page, dashboard, backend API, and background worker together. The Launch Dashboard button connects straight to the Vite frontend while the worker syncs repos and the backend streams agent state.
              </p>
              <div className="space-y-2 text-sm font-mono text-blue-900/70 dark:text-slate-300">
                <p>1. `cd landing && npm run dev`</p>
                <p>2. `cd frontend && npm run dev`</p>
                <p>3. `cd backend && uvicorn app:app --reload`</p>
                <p>4. `cd backend && python worker.py`</p>
              </div>
            </div>
          </section>
        </main>

        <footer className="border-t border-gray-200 dark:border-slate-800 py-8 mt-10">
          <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between gap-4 text-sm text-gray-500 dark:text-slate-400">
            <span>© {new Date().getFullYear()} Sentinell. Autonomous reliability for modern teams.</span>
            <span>Crafted with Next.js + LangGraph + Claude</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
