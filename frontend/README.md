# Content Clipper Frontend

React + Vite frontend for the Content Clipper application.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API URL
```

3. Start development server:
```bash
npm run dev
```

## Docker

Run with Docker:
```bash
docker-compose up -d frontend
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Lint code
- `npm run format` - Format code with Prettier

## Project Structure
```
src/
├── components/      # Reusable components
├── pages/          # Page components
├── services/       # API service layer
├── hooks/          # Custom React hooks
├── store/          # State management (Zustand)
└── utils/          # Utility functions
```

## Features

- 📤 Media upload and management
- ✂️ Clip creation and editing
- 🤖 AI-powered content generation
- 📅 Social media scheduling
- 🎨 Modern UI with Tailwind CSS