import { useRef, useEffect, useState } from 'react';
import { AgentSelector, API_CONFIG } from './AgentSelector';
import { ChatMessage, IChatMessage } from './ChatMessage';

export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<IChatMessage[]>([]);
  const [input, setInput] = useState('');
  // const [selectedAgent, setSelectedAgent] = useState('base_agent');
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connectWebSocket = (agentName: string) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket(
      `${API_CONFIG.SERVER_URL.replace('http', 'ws')}/ws/${agentName}`
    );

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages((prev) => [
        ...prev,
        { content: message.content, isUser: false },
      ]);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  };

  const handleAgentSelect = (agentName: string) => {
    setSelectedAgent(agentName);
    connectWebSocket(agentName);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !wsRef.current) return;

    const message = { content: input, isUser: true };
    setMessages((prev) => [...prev, message]);
    wsRef.current.send(JSON.stringify({ message: input }));
    setInput('');
  };

  return (
    <div className="h-full flex flex-col">
      <AgentSelector onAgentSelect={handleAgentSelect} />

      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 p-2 border rounded-md resize-none"
            rows={3}
            placeholder="Type your message..."
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-300"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
};
function setSelectedAgent(_agentName: string) {
  throw new Error('Function not implemented.');
}
