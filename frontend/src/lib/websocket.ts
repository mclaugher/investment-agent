import type { WSMessage } from "../types";

type MessageHandler = (message: WSMessage) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectDelay = 30000;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = false;
  private messageHandler: MessageHandler | null = null;

  constructor(url?: string) {
    const wsBase =
      import.meta.env.VITE_WS_BASE_URL ||
      `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`;
    this.url = url || `${wsBase}/ws`;
  }

  onMessage(handler: MessageHandler): void {
    this.messageHandler = handler;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.shouldReconnect = true;
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.startPing();
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data) as WSMessage;
        this.messageHandler?.(message);
      } catch {
        // Ignore malformed messages
      }
    };

    this.ws.onclose = () => {
      this.stopPing();
      if (this.shouldReconnect) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = () => {
      // onclose will fire after onerror, triggering reconnect
    };
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this.stopPing();

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  get connected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private startPing(): void {
    this.stopPing();
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000);
  }

  private stopPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private scheduleReconnect(): void {
    const delay = Math.min(
      1000 * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    );
    this.reconnectAttempts++;

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }
}

// Singleton instance
export const wsClient = new WebSocketClient();
