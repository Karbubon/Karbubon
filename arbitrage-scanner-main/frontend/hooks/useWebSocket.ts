import { useEffect, useState, useCallback, useRef } from 'react';
import { ArbitrageOpportunity } from '@/lib/api';

interface WebSocketMessage {
  type: 'new_opportunity' | 'opportunity_gone' | 'ping' | 'pong';
  data?: ArbitrageOpportunity;
  opportunity_id?: number;
  timestamp: string;
}

export const useWebSocket = (url?: string) => {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [newOpportunities, setNewOpportunities] = useState<ArbitrageOpportunity[]>([]);
  const [goneOpportunityIds, setGoneOpportunityIds] = useState<number[]>([]);
  
  // Правильный URL для WebSocket (без /api)
  const wsUrl = url || 'ws://localhost:8000/ws/opportunities';

  const connectRef = useRef<() => WebSocket | null>(() => null);

  const connect = useCallback(() => {
    console.log('Connecting to WebSocket:', wsUrl);
    
    const websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
      console.log('WebSocket connected successfully');
      setIsConnected(true);
      setWs(websocket);
    };
    
    websocket.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        console.log('WebSocket message received:', message.type);
        setLastMessage(message);
        
        if (message.type === 'new_opportunity' && message.data) {
          setNewOpportunities(prev => [message.data!, ...prev].slice(0, 50));
        } else if (message.type === 'opportunity_gone' && message.opportunity_id) {
          setGoneOpportunityIds(prev => [...prev, message.opportunity_id!]);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };
    
    websocket.onclose = (event) => {
      console.log(`WebSocket disconnected: ${event.code} - ${event.reason}`);
      setIsConnected(false);
      setWs(null);
      
      // Reconnect after 3 seconds
      setTimeout(() => {
        connectRef.current();
      }, 3000);
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return websocket;
  }, [wsUrl]);

  // keep the ref in sync with latest connect
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);
  
  useEffect(() => {
    const websocket = connect();
    return () => {
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.close();
      }
    };
  }, [connect]);
  
  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not open, cannot send message');
    }
  }, [ws]);
  
  const clearNewOpportunities = useCallback(() => {
    setNewOpportunities([]);
  }, []);
  
  const clearGoneOpportunityIds = useCallback(() => {
    setGoneOpportunityIds([]);
  }, []);
  
  return {
    isConnected,
    lastMessage,
    newOpportunities,
    goneOpportunityIds,
    sendMessage,
    clearNewOpportunities,
    clearGoneOpportunityIds,
  };
};