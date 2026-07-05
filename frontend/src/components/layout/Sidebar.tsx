import { Link, useLocation } from "react-router-dom";
import { clsx } from "clsx";
import { useAuthStore } from "../../store/authStore";
import { authApi } from "../../api/auth";

const NAV_ITEMS = [
  { label: "Dashboard",     path: "/",              icon: GridIcon },
  { label: "Repositories",  path: "/repositories",  icon: RepoIcon },
  { label: "All Findings",  path: "/findings",      icon: BugIcon },
  { label: "Analytics",     path: "/analytics",     icon: ChartIcon },
  { label: "Settings",      path: "/settings",      icon: GearIcon },
];

export function Sidebar() {
  const location = useLocation();
  const { user, logout, refreshToken } = useAuthStore();

  const handleLogout = async () => {
    try {
      if (refreshToken) await authApi.logout(refreshToken);
    } finally {
      logout();
    }
  };

  return (
    <aside className="w-60 flex-shrink-0 flex flex-col bg-bg-surface border-r border-border-default h-screen sticky top-0">
      {/* Logo */}
      <div className="px-5 py-4 border-b border-border-default">
        <div className="flex items-center gap-2">
          <ShieldIcon className="w-6 h-6 text-accent-primary flex-shrink-0" />
          <span className="font-semibold text-text-primary tracking-tight">CodeSentinel</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ label, path, icon: Icon }) => {
          const isActive = path === "/"
            ? location.pathname === "/"
            : location.pathname.startsWith(path);

          return (
            <Link
              key={path}
              to={path}
              className={clsx(
                "flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors duration-100",
                isActive
                  ? "bg-bg-elevated text-text-primary border-l-4 border-accent-primary pl-[10px]"
                  : "text-text-secondary hover:text-text-primary hover:bg-bg-elevated border-l-4 border-transparent pl-[10px]"
              )}
            >
              <Icon className={clsx("w-4 h-4 flex-shrink-0", isActive ? "text-accent-primary" : "")} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="px-3 py-3 border-t border-border-default">
        <div className="flex items-center gap-2.5">
          {user?.github_avatar_url ? (
            <img src={user.github_avatar_url} alt="" className="w-7 h-7 rounded-full flex-shrink-0" />
          ) : (
            <div className="w-7 h-7 rounded-full bg-accent-primary flex items-center justify-center text-xs font-semibold flex-shrink-0">
              {user?.email?.[0]?.toUpperCase() ?? "?"}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="text-sm text-text-primary truncate">{user?.full_name || user?.email}</div>
            {user?.github_username && (
              <div className="text-xs text-text-muted truncate">@{user.github_username}</div>
            )}
          </div>
          <button
            onClick={handleLogout}
            className="text-text-muted hover:text-text-secondary text-xs flex-shrink-0 transition-colors"
            title="Sign out"
          >
            <SignOutIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}

// ── SVG Icons ─────────────────────────────────────────────────────────────────
function ShieldIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2L4 6v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V6l-8-4z" />
      <path d="M10 14.42l-2.83-2.83 1.41-1.41L10 11.59l4.42-4.42 1.41 1.41L10 14.42z" fill="white" />
    </svg>
  );
}

function GridIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
    </svg>
  );
}
function RepoIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path d="M3 3h6v18H3zM15 3h6v18h-6zM9 12h6" />
    </svg>
  );
}
function BugIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}
function ChartIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" /><line x1="2" y1="20" x2="22" y2="20" />
    </svg>
  );
}
function GearIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" />
    </svg>
  );
}
function SignOutIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
    </svg>
  );
}
