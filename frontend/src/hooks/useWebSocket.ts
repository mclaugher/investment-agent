import { useEffect, useState } from "react";
import { wsClient } from "../lib/websocket";
import { usePortfolioStore } from "../store/portfolioStore";
import { useAgentStore } from "../store/agentStore";
import type { WSMessage } from "../types";

/**
 * Hook that manages the WebSocket connection lifecycle.
 * Connects on mount, disconnects on unmount, and dispatches
 * incoming messages to the appropriate Zustand stores.
 */
export function useWebSocket(): { connected: boolean } {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const updatePrice = usePortfolioStore.getState().updatePrice;
    const updateAgentStatus = useAgentStore.getState().updateAgentStatus;
    const fetchAgents = useAgentStore.getState().fetchAgents;
    const fetchSummary = usePortfolioStore.getState().fetchSummary;

    wsClient.onMessage((message: WSMessage) => {
      switch (message.type) {
        case "price_update":
          if (message.payload.symbol && message.payload.price) {
            updatePrice(message.payload.symbol, message.payload.price);
          }
          break;

        case "agent_status":
          if (message.payload.name && message.payload.status) {
            updateAgentStatus(message.payload.name, message.payload.status);
          }
          break;

        case "new_report":
          // Refresh agents to pick up new report counts
          fetchAgents();
          break;

        case "new_decision":
          // Refresh portfolio when a new trade decision is made
          fetchSummary();
          break;

        case "analysis_progress":
          // Could be used for progress indicators; dispatch to agent store
          if (message.payload.name && message.payload.status) {
            updateAgentStatus(message.payload.name, message.payload.status);
          }
          break;
      }
    });

    wsClient.connect();

    // Poll connection state since WebSocket doesn't fire React-friendly events
    const interval = setInterval(() => {
      setConnected(wsClient.connected);
    }, 1000);

    return () => {
      clearInterval(interval);
      wsClient.disconnect();
    };
  }, []);

  return { connected };
}
