import ChatInterface from '@/components/ChatInterface';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-600 to-purple-700 flex items-center justify-center p-4">
      <div className="w-full max-w-5xl h-[95vh] bg-white rounded-3xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-violet-600 to-purple-600 px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center text-2xl shadow-lg">
              🎓
            </div>
            <div>
              <h1 className="text-white text-xl font-bold">Asisten Akademik ITB</h1>
              <p className="text-violet-100 text-sm">Peraturan & Kalender Akademik</p>
            </div>
          </div>
        </div>

        {/* Chat Interface */}
        <ChatInterface />
      </div>
    </div>
  );
}
