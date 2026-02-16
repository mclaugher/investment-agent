// Types matching backend API schemas for Superhuman Alpha Fund

export interface Holding {
  symbol: string;
  asset_type: string;
  shares: number;
  avg_cost_basis: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  weight_pct: number;
  sector: string;
}

export interface PortfolioSummary {
  total_value: number;
  daily_pnl: number;
  daily_pnl_pct: number;
  total_return: number;
  total_return_pct: number;
  cash_balance: number;
  allocation: Record<string, number>;
}

export interface Transaction {
  id: string;
  symbol: string;
  action: string;
  shares: number;
  price_per_share: number;
  total_amount: number;
  fees: number;
  agent_decision_id: string;
  executed_at: string;
}

export interface PaginatedTransactions {
  items: Transaction[];
  total: number;
  page: number;
  limit: number;
}

export interface ReportSummary {
  id: string;
  agent_name: string;
  agent_role: string;
  report_type: string;
  symbol: string;
  sector: string;
  title: string;
  recommendation: string;
  confidence: number;
  created_at: string;
}

export interface ReportDetail extends ReportSummary {
  content: string;
  key_metrics: Record<string, any>;
  parent_report_id: string | null;
}

export interface PaginatedReports {
  items: ReportSummary[];
  total: number;
  page: number;
  limit: number;
}

export interface DecisionTrailNode {
  report_id: string;
  agent_name: string;
  agent_role: string;
  report_type: string;
  title: string;
  content: string;
  recommendation: string;
  confidence: number;
  children: DecisionTrailNode[];
}

export interface AgentSummary {
  name: string;
  role: string;
  description: string;
  status: string;
  last_run: string | null;
  next_scheduled: string | null;
  reports_count: number;
}

export interface AgentDetail extends AgentSummary {
  tools: string[];
  recent_reports: ReportSummary[];
}

export interface ChatMessage {
  role: string;
  content: string;
  timestamp: string;
  intent?: string;
}

export interface ChatResponse {
  response: string;
  intent: string;
  data?: Record<string, any>;
  actions_taken: string[];
}

export interface RiskProfile {
  aggressiveness: string;
  max_single_position_pct: number;
  max_sector_pct: number;
  min_cash_pct: number;
  target_equity_pct: number;
  target_fixed_income_pct: number;
  target_cash_pct: number;
  updated_by: string;
  notes: string;
}

export interface WSMessage {
  type:
    | "agent_status"
    | "new_report"
    | "new_decision"
    | "price_update"
    | "analysis_progress";
  payload: Record<string, any>;
  timestamp: string;
}

export interface ScheduleEntry {
  name: string;
  task: string;
  schedule: string;
  description: string;
}
