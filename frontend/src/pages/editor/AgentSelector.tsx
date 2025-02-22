// components/ChatInterface/AgentSelector.tsx
import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';

// types.ts
export interface Agent {
  name: string;
}

// config.ts
export const API_CONFIG = {
  SERVER_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000',
};

interface AgentSelectorProps {
  onAgentSelect: (agent: string) => void;
}

export const AgentSelector: React.FC<AgentSelectorProps> = ({
  onAgentSelect,
}) => {
  const [agents, setAgents] = useState<Agent[]>([{ name: 'base_agent' }]);
  const [loading, setLoading] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState('base_agent');

  const fetchAgents = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_CONFIG.SERVER_URL}/agents`);
      if (response.ok) {
        const data = await response.json();
        setAgents(data.length ? data : [{ name: 'base_agent' }]);
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const handleAgentChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newAgent = event.target.value;
    setSelectedAgent(newAgent);
    onAgentSelect(newAgent);
  };

  return (
    <div className="flex items-center gap-2 p-4 border-b">
      <select
        value={selectedAgent}
        onChange={handleAgentChange}
        className="flex-1 p-2 border rounded-md bg-white"
      >
        {agents.map((agent) => (
          <option key={agent.name} value={agent.name}>
            {agent.name}
          </option>
        ))}
      </select>
      <button
        onClick={fetchAgents}
        disabled={loading}
        className="p-2 rounded-md hover:bg-gray-100"
      >
        <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
      </button>
    </div>
  );
};
