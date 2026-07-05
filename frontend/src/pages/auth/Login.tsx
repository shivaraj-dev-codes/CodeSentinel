import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useLogin } from "../../api/auth";
import { useAuthStore } from "../../store/authStore";

export function Login() {
  const navigate = useNavigate();
  const { mutate: login, isPending, error } = useLogin();
  const setAuth = useAuthStore((s) => s.setAuth);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    login(
      { email, password },
      {
        onSuccess: (data) => {
          setAuth(data.data.user, data.data.access, data.data.refresh);
          navigate("/");
        },
        onError: (err: unknown) => {
          const e = err as { response?: { data?: { error?: { message?: string } } } };
          setFormError(e?.response?.data?.error?.message ?? "Invalid email or password.");
        },
      }
    );
  };

  return (
    <div className="min-h-screen bg-bg-base flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex flex-1 flex-col justify-between p-12 relative overflow-hidden"
        style={{ background: "linear-gradient(135deg, #0d1117 0%, #161b22 100%)" }}>

        {/* Grid background */}
        <div className="absolute inset-0 opacity-5"
          style={{ backgroundImage: "linear-gradient(#30363d 1px, transparent 1px), linear-gradient(90deg, #30363d 1px, transparent 1px)", backgroundSize: "40px 40px" }} />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-16">
            <svg viewBox="0 0 32 32" className="w-10 h-10" fill="#7c5cfc">
              <path d="M16 2L4 8v10c0 7.5 5.2 14.5 12 16 6.8-1.5 12-8.5 12-16V8L16 2z"/>
              <path d="M13 18.6l-3.8-3.8 1.9-1.9 1.9 1.9 5.9-5.9 1.9 1.9L13 18.6z" fill="white"/>
            </svg>
            <span className="text-xl font-semibold text-text-primary">CodeSentinel</span>
          </div>

          <div className="space-y-6">
            <h1 className="text-2xl font-bold text-text-primary leading-tight">
              Stop shipping vulnerabilities.<br />
              <span className="text-accent-primary">Start shipping confidence.</span>
            </h1>
            <p className="text-text-secondary leading-relaxed max-w-sm">
              AI-powered security scanner that analyzes your Python repositories for
              vulnerabilities before they reach production.
            </p>
          </div>
        </div>

        {/* Stat counters */}
        <div className="relative z-10 space-y-4">
          {[
            { value: "47,291", label: "vulnerabilities detected" },
            { value: "1,204",  label: "repositories scanned" },
            { value: "99.2%",  label: "developer satisfaction" },
          ].map(({ value, label }) => (
            <motion.div key={label}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
              className="flex items-baseline gap-3">
              <span className="text-2xl font-bold text-accent-primary font-mono">{value}</span>
              <span className="text-text-secondary text-sm">{label}</span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Right panel — auth form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-sm space-y-6">

          <div>
            <h2 className="text-xl font-semibold text-text-primary">Sign in to CodeSentinel</h2>
            <p className="text-sm text-text-secondary mt-1">
              Don't have an account?{" "}
              <Link to="/register" className="text-text-link hover:underline">Create one</Link>
            </p>
          </div>

          {/* GitHub OAuth button */}
          <a
            href={`https://github.com/login/oauth/authorize?client_id=${import.meta.env.VITE_GITHUB_CLIENT_ID}&scope=repo`}
            className="flex items-center justify-center gap-3 w-full py-2.5 px-4 rounded-md border border-border-default
              text-text-primary text-sm font-medium hover:bg-bg-elevated transition-colors"
          >
            <GitHubIcon className="w-5 h-5" />
            Continue with GitHub
          </a>

          <div className="flex items-center gap-3">
            <div className="flex-1 border-t border-border-default" />
            <span className="text-xs text-text-muted">or</span>
            <div className="flex-1 border-t border-border-default" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {(formError) && (
              <div className="text-sm text-status-error bg-status-error/10 border border-status-error/30 rounded-md px-3 py-2">
                {formError}
              </div>
            )}

            <div>
              <label className="block text-sm text-text-secondary mb-1.5">Email</label>
              <input
                type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
                placeholder="you@example.com"
                className="w-full bg-bg-elevated border border-border-default rounded-md px-3 py-2
                  text-text-primary text-sm placeholder:text-text-muted focus:outline-none focus:border-accent-primary transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm text-text-secondary mb-1.5">Password</label>
              <input
                type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
                placeholder="••••••••"
                className="w-full bg-bg-elevated border border-border-default rounded-md px-3 py-2
                  text-text-primary text-sm placeholder:text-text-muted focus:outline-none focus:border-accent-primary transition-colors"
              />
            </div>

            <button
              type="submit" disabled={isPending}
              className="w-full py-2.5 rounded-md bg-accent-primary hover:bg-accent-hover text-white text-sm font-medium
                transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPending ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="text-xs text-text-muted text-center">
            Demo: demo@codesentinel.dev / DemoPass123!
          </p>
        </motion.div>
      </div>
    </div>
  );
}

function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
    </svg>
  );
}
