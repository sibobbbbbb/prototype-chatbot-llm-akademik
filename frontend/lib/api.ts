import { ChatRequest, ChatResponse } from '@/types/chat';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function sendMessage(question: string): Promise<ChatResponse> {
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question } as ChatRequest),
  });

  if (!response.ok) {
    throw new Error('Failed to send message');
  }

  return response.json();
}
