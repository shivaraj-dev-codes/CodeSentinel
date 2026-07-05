import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useRegister } from "../../api/auth";
import { useAuthStore } from "../../store/authStore";

export function Register() {
  const navigate = useNavigate();
  const { mutate: register, isPending } = useRegister();
  const setAuth = useAuthStore((s) => s.setAuth);

  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== passwordConfirm) { setError("Passwords don't match."); return; }
    register(
      { email, password, passwordConfirm, fullName },
      {
        onSuccess: (data) => {
          setAuth(data.data.user, data.data.access, data.data.refresh);
          navigate("/");
        },
        onError: (err: unknown) => {
          const e = err as { response?: { data?: { error?: { message?: string } } } };
          setError(e?.response?.data?.error?.message ?? "Registration failed. Please try again.");
        },
      }
    );
  };

  return (
    <div className="min-h-screen bg-bg-base flex items-center justify-center p-8">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-sm space-y-6">

        <div className="text-center">
          <div className="flex justify-center mb-4">
            <svg viewBox="0 0 32 32" className="w-10 h-10" fill="#7c5cfc">
              <path d="M16 2L4 8v10c0 7.5 5.2 14.5 12 16 6.8-1.5 12-8.5 12-16V8L16 2z"/>
              <path d="M13 18.6l-3.8-3.8 1.9-1.9 1.9 1.9 5.9-5.9 1.9 1.9L13 18.6z" fill="white"/>
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-text-primary">Create your account</h2>
          <p className="text-sm text-text-secondary mt-1">
            Already have an account?{" "}
            <Link to="/login" className="text-text-link hover:underline">Sign in</Link>
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="text-sm text-status-error bg-status-error/10 border border-status-error/30 rounded-md px-3 py-2">
              {error}
            </div>
          )}

          {[
            { label: "Full Name", value: fullName, onChange: setFullName, type: "text", placeholder: "Alex Rivera", required: false },
            { label: "Email", value: email, onChange: setEmail, type: "email", placeholder: "you@example.com", required: true },
            { label: "Password", value: password, onChange: setPassword, type: "password", placeholder: "At least 8 characters", required: true },
            { label: "Confirm Password", value: passwordConfirm, onChange: setPasswordConfirm, type: "password", placeholder: "Repeat your password", required: true },
          ].map(({ label, value, onChange, type, placeholder, required }) => (
            <div key={label}>
              <label className="block text-sm text-text-secondary mb-1.5">{label}</label>
              <input
                type={type} value={value} onChange={(e) => onChange(e.target.value)}
                required={required} placeholder={placeholder}
                className="w-full bg-bg-elevated border border-border-default rounded-md px-3 py-2
                  text-text-primary text-sm placeholder:text-text-muted focus:outline-none focus:border-accent-primary transition-colors"
              />
            </div>
          ))}

          <button
            type="submit" disabled={isPending}
            className="w-full py-2.5 rounded-md bg-accent-primary hover:bg-accent-hover text-white text-sm font-medium
              transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isPending ? "Creating account…" : "Create account"}
          </button>
        </form>
      </motion.div>
    </div>
  );
}
