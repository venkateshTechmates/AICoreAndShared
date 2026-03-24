<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# AI Enterprise Toolkit — Documentation UI

Interactive documentation app for the **AI Enterprise Toolkit** (`ai_core` + `ai_shared`).

> **Live site:** https://venkateshTechmates.github.io/AICoreAndShared/

## Tech Stack

- **React 19** + **TypeScript**
- **Vite 6** (build & dev server)
- **Tailwind CSS 4**
- **React Router** (HashRouter for GitHub Pages SPA)
- **Lucide React** icons
- **Motion** (Framer Motion) animations

## Run Locally

**Prerequisites:** Node.js 18+

```bash
npm install
npm run dev        # → http://localhost:3000
```

## Build & Deploy

```bash
npm run build      # production build → dist/
npm run deploy     # build + publish to GitHub Pages (gh-pages branch)
```

## Project Structure

```
UI/
├── public/            # Static assets + 404.html (SPA redirect)
├── docs/              # Markdown documentation
│   ├── 01-core-library.md
│   ├── 02-shared-library.md
│   ├── 03-architecture-workflows.md
│   ├── 04-trends-design-patterns.md
│   └── 05-enterprise-operations.md
├── src/
│   ├── main.tsx       # Entry point
│   ├── App.tsx        # HashRouter root
│   ├── components/    # Layout, AnimatedPipeline, WorkflowRenderer, UI
│   └── pages/         # Route pages (Home, Core, Shared, Architecture, etc.)
└── package.json
```

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (optional, for AI playground) |

Copy `.env.example` → `.env.local` and fill in your keys.
