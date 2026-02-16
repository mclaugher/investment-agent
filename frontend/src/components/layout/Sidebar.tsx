import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Briefcase,
  Bot,
  FileText,
  MessageSquare,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/portfolio", label: "Portfolio", icon: Briefcase },
  { to: "/agents", label: "Agents", icon: Bot },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="fixed inset-y-0 left-0 z-30 w-60 bg-gray-900 text-gray-100 flex flex-col">
      <div className="flex items-center gap-2 px-5 py-5 border-b border-gray-700">
        <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center text-sm font-bold">
          SA
        </div>
        <span className="text-lg font-semibold tracking-tight">
          Alpha Fund
        </span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ to, label, icon: Icon }) => {
          const isActive =
            to === "/"
              ? location.pathname === "/"
              : location.pathname.startsWith(to);

          return (
            <NavLink
              key={to}
              to={to}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
              )}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              {label}
            </NavLink>
          );
        })}
      </nav>

      <div className="px-5 py-4 border-t border-gray-700 text-xs text-gray-500">
        Superhuman Alpha Fund v1.0
      </div>
    </aside>
  );
}
