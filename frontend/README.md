# Asisten Akademik ITB - Chat Frontend

Frontend chat interface untuk sistem RAG (Retrieval-Augmented Generation) akademik ITB yang dibangun dengan Next.js, TypeScript, dan Tailwind CSS.

## 🚀 Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Hooks

## 📁 Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout dengan metadata
│   ├── page.tsx            # Home page
│   └── globals.css         # Global styles & animations
├── components/
│   ├── ChatInterface.tsx   # Main chat component
│   ├── ChatMessage.tsx     # Individual message component
│   └── LoadingDots.tsx     # Loading indicator
├── lib/
│   └── api.ts              # API service untuk backend
├── types/
│   └── chat.ts             # TypeScript type definitions
└── .env.local              # Environment variables (gitignored)
```

## 🎯 Features

- ✅ **Modern UI**: Gradient design dengan Tailwind CSS
- ✅ **Real-time Chat**: Komunikasi dengan FastAPI backend
- ✅ **TypeScript**: Type-safe development
- ✅ **Responsive**: Mobile-friendly design
- ✅ **Source Citations**: Tampilkan sumber dokumen
- ✅ **Example Queries**: Quick start dengan contoh pertanyaan
- ✅ **Loading States**: Animated loading indicators
- ✅ **Error Handling**: Graceful error messages

## 🛠️ Setup & Installation

### Prerequisites
- Node.js 18+ 
- NPM atau Yarn
- Backend server running di http://localhost:8000

### Installation

```bash
# Install dependencies (sudah dilakukan)
npm install

# Start development server
npm run dev
```

Server akan berjalan di http://localhost:3000

### Environment Variables

File `.env.local` (sudah dibuat):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📝 Usage

1. **Start Backend Server** (di terminal terpisah):
   ```bash
   cd ../backend
   ..\venv\Scripts\python.exe main.py
   ```

2. **Start Frontend**:
   ```bash
   npm run dev
   ```

3. **Open Browser**:
   - Navigate to http://localhost:3000
   - Start chatting dengan asisten akademik!

## 🎨 Component Breakdown

### `ChatInterface.tsx`
- Main component untuk chat functionality
- Manages messages state
- Handles user input dan API calls
- Auto-scroll ke bottom saat ada message baru

### `ChatMessage.tsx`
- Renders individual messages (user & assistant)
- Different styling untuk user vs assistant
- Displays source citations jika ada

### `LoadingDots.tsx`
- Animated loading indicator
- Bouncing dots animation

## 🔌 API Integration

Komunikasi dengan backend via REST API:

```typescript
// POST /chat
{
  question: string
}

// Response
{
  answer: string,
  sources: string[]
}
```

## 🚢 Build for Production

```bash
# Build production bundle
npm run build

# Start production server
npm start
```

## 📦 Available Scripts

- `npm run dev` - Start development server (Turbopack)
- `npm run build` - Build production bundle
- `npm start` - Start production server  
- `npm run lint` - Run ESLint (if enabled)

## 🎯 Key Decisions

1. **Next.js App Router**: Modern routing dengan server components
2. **TypeScript**: Type safety untuk better DX
3. **Tailwind CSS**: Utility-first CSS untuk rapid development
4. **Client Components**: Chat needs client-side state
5. **No History**: Sesuai requirement, tidak ada persistence

## 🔜 Future Enhancements

- [ ] Chat history dengan localStorage
- [ ] Export conversation
- [ ] Dark mode toggle
- [ ] Voice input
- [ ] File upload untuk query based on document
- [ ] Multi-language support

## 📄 License

Part of ITB Academic Assistant Project
