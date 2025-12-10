import { Message } from '@/types/chat';

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-5 py-4 ${
          isUser
            ? 'bg-gradient-to-r from-violet-600 to-purple-600 text-white shadow-lg'
            : 'bg-white text-gray-800 shadow-md border border-gray-100'
        }`}
      >
        <p className="text-[15px] leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>
        
        {message.sources && message.sources.length > 0 && (
          <div className={`mt-4 pt-4 space-y-2 ${isUser ? 'border-t border-white/20' : 'border-t border-gray-200'}`}>
            <div className="flex items-center gap-2 text-sm font-semibold mb-2">
              <span>📚</span>
              <span>Sumber:</span>
            </div>
            {message.sources.map((source, index) => (
              <div 
                key={index} 
                className={`flex items-start gap-2 text-sm pl-2 ${
                  isUser ? 'opacity-90' : 'opacity-75'
                }`}
              >
                <span className="mt-0.5">📄</span>
                <span>{source}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
