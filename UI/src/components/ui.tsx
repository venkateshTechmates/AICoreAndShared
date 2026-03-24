import { useState, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Copy, Check, ChevronDown } from 'lucide-react';

// ── CodeBlock ──────────────────────────────────────────────────
export const CodeBlock = ({ code, language = 'python' }: { code: string; language?: string }) => {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="relative group">
      <div className="absolute right-3 top-3 z-10">
        <button onClick={handleCopy} className="p-1.5 bg-zinc-700 rounded-md text-zinc-400 hover:text-white transition-colors text-xs flex items-center gap-1">
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 overflow-x-auto text-sm leading-relaxed">
        <code className={'text-zinc-300 font-mono language-' + language}>{code}</code>
      </pre>
    </div>
  );
};

// ── FeatureCard ────────────────────────────────────────────────
export const FeatureCard = ({ icon, title, description, tags }: { icon: ReactNode; title: string; description: string; tags?: string[] }) => (
  <motion.div whileHover={{ y: -4, scale: 1.01 }} className="p-6 bg-white border border-zinc-200 rounded-2xl hover:shadow-lg hover:border-zinc-300 transition-all group">
    <div className="p-3 bg-zinc-50 rounded-xl w-fit mb-4 text-zinc-600 group-hover:bg-zinc-900 group-hover:text-white transition-colors">{icon}</div>
    <h3 className="text-lg font-semibold text-zinc-900 mb-2">{title}</h3>
    <p className="text-sm text-zinc-500 leading-relaxed mb-4">{description}</p>
    {tags && (
      <div className="flex flex-wrap gap-1.5">
        {tags.map((tag, i) => (
          <span key={i} className="px-2.5 py-1 bg-zinc-100 text-zinc-600 rounded-full text-[10px] font-medium uppercase tracking-wider">{tag}</span>
        ))}
      </div>
    )}
  </motion.div>
);

// ── StatCard ───────────────────────────────────────────────────
export const StatCard = ({ value, label, icon }: { value: string; label: string; icon: ReactNode }) => (
  <div className="p-6 bg-white border border-zinc-200 rounded-xl text-center">
    <div className="flex justify-center mb-3 text-zinc-400">{icon}</div>
    <div className="text-3xl font-bold text-zinc-900 mb-1">{value}</div>
    <div className="text-sm text-zinc-500">{label}</div>
  </div>
);

// ── SectionHeader ──────────────────────────────────────────────
export const SectionHeader = ({ badge, title, subtitle }: { badge: string; title: string; subtitle: string }) => (
  <div className="mb-12">
    <span className="inline-block px-3 py-1 bg-zinc-100 text-zinc-600 rounded-full text-xs font-medium uppercase tracking-widest mb-4">{badge}</span>
    <h2 className="text-3xl md:text-4xl font-bold text-zinc-900 tracking-tight mb-4">{title}</h2>
    <p className="text-lg text-zinc-500 max-w-2xl">{subtitle}</p>
  </div>
);

// ── DataTable ──────────────────────────────────────────────────
export const DataTable = ({ headers, rows }: { headers: string[]; rows: string[][] }) => (
  <div className="bg-white border border-zinc-200 rounded-2xl overflow-hidden">
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="bg-zinc-50 text-zinc-500 font-mono text-[10px] uppercase tracking-widest">
          <tr>{headers.map((h, i) => <th key={i} className="px-6 py-3 font-medium">{h}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-zinc-100">
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-zinc-50 transition-colors">
              {row.map((cell, j) => (
                <td key={j} className={'px-6 py-3.5 ' + (j === 0 ? 'font-medium text-zinc-900' : 'text-zinc-500')}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

// ── Accordion ──────────────────────────────────────────────────
export const Accordion = ({ title, children, defaultOpen = false }: { title: string; children: ReactNode; defaultOpen?: boolean }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-zinc-200 rounded-xl overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full p-5 flex items-center justify-between bg-white hover:bg-zinc-50 transition-colors">
        <span className="font-semibold text-zinc-900">{title}</span>
        <ChevronDown size={18} className={'text-zinc-400 transition-transform ' + (open ? 'rotate-180' : '')} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <div className="p-5 pt-0 bg-white">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// ── Badge ──────────────────────────────────────────────────────
export const Badge = ({ children, variant = 'default' }: { children: ReactNode; variant?: 'default' | 'success' | 'warning' | 'error' | 'info' }) => {
  const colors = {
    default: 'bg-zinc-100 text-zinc-600',
    success: 'bg-green-50 text-green-600',
    warning: 'bg-amber-50 text-amber-600',
    error: 'bg-red-50 text-red-600',
    info: 'bg-blue-50 text-blue-600',
  };
  return <span className={'px-2.5 py-1 rounded-full text-[10px] font-medium uppercase tracking-wider ' + colors[variant]}>{children}</span>;
};
