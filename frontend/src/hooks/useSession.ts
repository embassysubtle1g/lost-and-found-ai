import { useCallback, useEffect, useState } from "react";
import { api, getToken, setToken } from "../services/api";
import type { Account } from "../types";

export function useSession() {
  const [account, setAccount] = useState<Account | null>(null);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState("");
  const refresh = useCallback(async () => {
    const result = await api.me();
    setAccount(result);
  }, []);
  useEffect(() => {
    let active = true;
    const expired = () => { setAccount(null); setError("登入已到期，請重新登入"); };
    window.addEventListener("radar-session-expired", expired);
    if (getToken()) api.me().then((result) => { if (active) setAccount(result); })
      .catch((reason) => { if (active) setError(reason.message); })
      .finally(() => { if (active) setChecking(false); });
    else setChecking(false);
    return () => { active = false; window.removeEventListener("radar-session-expired", expired); };
  }, []);
  async function login(username: string, password: string) {
    const result = await api.login(username, password);
    setToken(result.access_token);
    await refresh();
    setError("");
  }
  async function logout() {
    await api.logout();
    setToken(null);
    setAccount(null);
  }
  function signedOut() { setToken(null); setAccount(null); }
  return { account, checking, error, login, logout, refresh, signedOut };
}
