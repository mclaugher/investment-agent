import type {
  PortfolioSummary,
  Holding,
  PaginatedTransactions,
  PaginatedReports,
  ReportDetail,
  AgentSummary,
  AgentDetail,
  ChatMessage,
  ChatResponse,
  RiskProfile,
  ScheduleEntry,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
const TOKEN_KEY = "superhuman_alpha_token";

// --- Token management ---

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// --- Generic fetch wrapper ---

async function request<T>(
  method: string,
  path: string,
  body?: unknown
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    method,
    headers,
  };

  if (body !== undefined) {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(`${BASE_URL}${path}`, config);

  if (response.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(
      `API error ${response.status}: ${errorBody || response.statusText}`
    );
  }

  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
  delete: <T>(path: string) => request<T>("DELETE", path),
};

// --- Typed API functions ---

export function login(credentials: {
  username: string;
  password: string;
}): Promise<{ access_token: string }> {
  return api.post("/api/auth/login", credentials);
}

// Portfolio
export function fetchPortfolio(): Promise<PortfolioSummary> {
  return api.get("/api/portfolio/summary");
}

export function fetchHoldings(): Promise<Holding[]> {
  return api.get("/api/portfolio/holdings");
}

export function fetchTransactions(
  page = 1,
  limit = 20
): Promise<PaginatedTransactions> {
  return api.get(`/api/portfolio/transactions?page=${page}&limit=${limit}`);
}

// Reports
export function fetchReports(params?: {
  page?: number;
  limit?: number;
  agent_name?: string;
  report_type?: string;
  symbol?: string;
}): Promise<PaginatedReports> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.agent_name) searchParams.set("agent_name", params.agent_name);
  if (params?.report_type) searchParams.set("report_type", params.report_type);
  if (params?.symbol) searchParams.set("symbol", params.symbol);
  const qs = searchParams.toString();
  return api.get(`/api/reports${qs ? `?${qs}` : ""}`);
}

export function fetchReportDetail(id: string): Promise<ReportDetail> {
  return api.get(`/api/reports/${id}`);
}

// Agents
export function fetchAgents(): Promise<AgentSummary[]> {
  return api.get("/api/agents");
}

export function fetchAgentDetail(name: string): Promise<AgentDetail> {
  return api.get(`/api/agents/${name}`);
}

export function triggerAgent(name: string): Promise<{ task_id: string }> {
  return api.post(`/api/agents/${name}/trigger`);
}

// Chat
export function sendChatMessage(message: string): Promise<ChatResponse> {
  return api.post("/api/chat", { message });
}

export function fetchChatHistory(): Promise<ChatMessage[]> {
  return api.get("/api/chat/history");
}

// Settings
export function fetchRiskProfile(): Promise<RiskProfile> {
  return api.get("/api/settings/risk-profile");
}

export function updateRiskProfile(
  updates: Partial<RiskProfile>
): Promise<RiskProfile> {
  return api.put("/api/settings/risk-profile", updates);
}

export function fetchWatchlist(): Promise<string[]> {
  return api.get("/api/settings/watchlist");
}

export function addToWatchlist(symbol: string): Promise<{ symbol: string }> {
  return api.post("/api/settings/watchlist", { symbol });
}

export function removeFromWatchlist(symbol: string): Promise<void> {
  return api.delete(`/api/settings/watchlist/${symbol}`);
}

// Schedule
export function fetchSchedule(): Promise<ScheduleEntry[]> {
  return api.get("/api/schedule");
}
