'use client';

import { useState, useRef, useEffect } from 'react';
import { Message } from '@/types/chat';
import { sendMessage } from '@/lib/api';
import ChatMessage from './ChatMessage';
import LoadingDots from './LoadingDots';

const EXAMPLE_QUERIES = [
  'Sebutkan pasal 13 peraturan akademik ITB',
  'Kapan jadwal ujian semester Januari 2025?',
  'Apa saja syarat kelulusan program sarjana?',
];

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSend = async (question?: string) => {
    const messageText = question || input.trim();
    
    if (!messageText || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await sendMessage(messageText);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Maaf, terjadi kesalahan. Pastikan server backend sedang berjalan.',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat Messages */}
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-6 bg-gray-50 min-h-0"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
            <div className="space-y-3">
              <div className="w-20 h-20 mx-auto bg-gradient-to-br from-violet-600 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
                <span className="text-4xl">👋</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-800">
                Selamat datang!
              </h2>
              <p className="text-gray-600 max-w-md">
                Saya siap membantu menjawab pertanyaan tentang peraturan dan kalender akademik ITB
              </p>
            </div>
            
            <div className="w-full max-w-2xl space-y-3">
              <p className="text-sm font-medium text-gray-500">Coba pertanyaan ini:</p>
              {EXAMPLE_QUERIES.map((query, index) => (
                <button
                  key={index}
                  onClick={() => handleSend(query)}
                  className="w-full text-left px-5 py-4 bg-white hover:bg-violet-50 border-2 border-gray-200 hover:border-violet-400 rounded-xl transition-all duration-200 group"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl opacity-50 group-hover:opacity-100 transition-opacity">💬</span>
                    <span className="text-gray-700 group-hover:text-violet-700 font-medium">
                      {query}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4 max-w-4xl mx-auto">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isLoading && <LoadingDots />}
          </div>
        )}
      </div>

      {/* Input Area - Fixed at bottom */}
      <div className="flex-shrink-0 border-t bg-white p-6">
        <div className="flex gap-3 max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ketik pertanyaan Anda..."
            disabled={isLoading}
            className="flex-1 px-5 py-3 border-2 border-gray-300 rounded-xl focus:outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          />
          <button
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim()}
            className="px-8 py-3 bg-gradient-to-r from-violet-600 to-purple-600 text-white font-semibold rounded-xl hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 transition-all duration-200"
          >
            Kirim
          </button>
        </div>
      </div>
    </div>
  );
}
