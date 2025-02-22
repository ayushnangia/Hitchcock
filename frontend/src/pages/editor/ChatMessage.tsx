export interface IChatMessage {
  content: string;
  isUser: boolean;
}

interface ChatMessageProps {
  message: IChatMessage;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  return (
    <div
      className={`p-3 ${
        message.isUser ? 'bg-blue-50' : 'bg-gray-50'
      } rounded-lg mb-2`}
    >
      <p className="text-sm">{message.content}</p>
    </div>
  );
};
