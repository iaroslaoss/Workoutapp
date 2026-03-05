import { createContext, useContext, useMemo, useState } from "react";

type AuthContextShape = {
  token: string | null;
  setToken: (token: string | null) => void;
  isAuthenticated: boolean;
};

const AuthContext = createContext<AuthContextShape | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => localStorage.getItem("liftmove_token"));

  const setToken = (next: string | null) => {
    setTokenState(next);
    if (next) {
      localStorage.setItem("liftmove_token", next);
    } else {
      localStorage.removeItem("liftmove_token");
    }
  };

  const value = useMemo(
    () => ({ token, setToken, isAuthenticated: Boolean(token) }),
    [token]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
