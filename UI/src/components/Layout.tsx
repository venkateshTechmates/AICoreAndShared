import { useState } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import {
  Database, Brain, Layers, Blocks, Play, Building,
  GitBranch, ChevronRight, Menu, Workflow, FlaskConical,
} from 'lucide-react';

import HomePage from '../pages/HomePage';
import CoreLibraryPage from '../pages/CoreLibraryPage';
import SharedLibraryPage from '../pages/SharedLibraryPage';
import ArchitecturePage from '../pages/ArchitecturePage';
import TrendsPage from '../pages/TrendsPage';
import EnterprisePage from '../pages/EnterprisePage';
import PlaygroundPage from '../pages/PlaygroundPage';
import PipelinesPage from '../pages/PipelinesPage';
import WorkflowsPage from '../pages/WorkflowsPage';
import DomainExamplesPage from '../pages/DomainExamplesPage';

const navSections = [
  {
    title: 'Documentation',
    items: [
      { to: '/', icon: Database, label: 'Overview' },
      { to: '/core', icon: Database, label: 'Core Library' },
      { to: '/shared', icon: Blocks, label: 'Shared Library' },
    ],
  },
  {
    title: 'Architecture',
    items: [
      { to: '/architecture', icon: Layers, label: 'Architecture & Workflows' },
      { to: '/trends', icon: Brain, label: 'Trends & Patterns' },
      { to: '/enterprise', icon: Building, label: 'Enterprise Ops' },
    ],
  },
  {
    title: 'Visualizations',
    items: [
      { to: '/pipelines', icon: Workflow, label: 'Pipelines & Flows' },
      { to: '/workflows', icon: GitBranch, label: 'Workflows & Patterns' },
    ],
  },
  {
    title: 'Interactive',
    items: [
      { to: '/playground', icon: Play, label: 'Playground' },
      { to: '/domain-examples', icon: FlaskConical, label: 'Domain Examples' },
    ],
  },
];

// Use first icon per section for Overview to avoid a duplicate Database icon
navSections[0].items[0] = { to: '/', icon: Layers, label: 'Overview' };

const Layout = () => {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const currentPage = navSections.flatMap(s => s.items).find(i => i.to === location.pathname);

  return (
    <div className="flex h-screen bg-white">
      {/* mobile overlay */}
      {sidebarOpen && <div className="fixed inset-0 z-30 bg-black/20 md:hidden" onClick={() => setSidebarOpen(false)} />}

      {/* sidebar */}
      <aside className={'fixed z-40 inset-y-0 left-0 w-64 bg-zinc-50 border-r border-zinc-200 flex flex-col transition-transform md:translate-x-0 md:static ' + (sidebarOpen ? 'translate-x-0' : '-translate-x-full')}>
        <div className="p-5 border-b border-zinc-200 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-zinc-900 flex items-center justify-center">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-zinc-900 tracking-tight">AI Core & Shared</h1>
            <span className="text-[10px] text-zinc-400 font-mono">v1.0.0 Enterprise</span>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto p-3 space-y-5">
          {navSections.map(section => (
            <div key={section.title}>
              <span className="text-[10px] uppercase tracking-widest text-zinc-400 font-medium px-3">{section.title}</span>
              <div className="mt-2 space-y-0.5">
                {section.items.map(item => {
                  const active = location.pathname === item.to;
                  return (
                    <Link key={item.to} to={item.to} onClick={() => setSidebarOpen(false)} className={'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ' + (active ? 'bg-zinc-900 text-white font-medium' : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900')}>
                      <item.icon className="w-4 h-4" />
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
        <div className="p-4 border-t border-zinc-200 text-[10px] text-zinc-400 space-y-1">
          <div className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Core Library — Ready</div>
          <div className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Shared Library — Ready</div>
        </div>
      </aside>

      {/* main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 border-b border-zinc-200 flex items-center px-4 gap-4 shrink-0 bg-white">
          <button className="md:hidden p-1.5 rounded-lg hover:bg-zinc-100" onClick={() => setSidebarOpen(true)}>
            <Menu className="w-5 h-5 text-zinc-600" />
          </button>
          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <Link to="/" className="hover:text-zinc-900">Docs</Link>
            {currentPage && currentPage.to !== '/' && (
              <>
                <ChevronRight className="w-3 h-3" />
                <span className="text-zinc-900 font-medium">{currentPage.label}</span>
              </>
            )}
          </div>
          <div className="ml-auto flex items-center gap-3 text-xs text-zinc-400">
            <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="hover:text-zinc-600 flex items-center gap-1"><GitBranch className="w-3.5 h-3.5" /> GitHub</a>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-5xl mx-auto p-6 md:p-10">
            <AnimatePresence mode="wait">
              <motion.div key={location.pathname} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.2 }}>
                <Routes location={location}>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/core" element={<CoreLibraryPage />} />
                  <Route path="/shared" element={<SharedLibraryPage />} />
                  <Route path="/architecture" element={<ArchitecturePage />} />
                  <Route path="/trends" element={<TrendsPage />} />
                  <Route path="/enterprise" element={<EnterprisePage />} />
                  <Route path="/playground" element={<PlaygroundPage />} />
                  <Route path="/pipelines" element={<PipelinesPage />} />
                  <Route path="/workflows" element={<WorkflowsPage />} />
                  <Route path="/domain-examples" element={<DomainExamplesPage />} />
                </Routes>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Layout;
