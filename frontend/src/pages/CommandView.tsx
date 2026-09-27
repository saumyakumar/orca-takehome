import { useEffect, useState } from "react";

import { apiFetch } from "../api/client";
import { useUser } from "../context/UserContext";

interface CountryStats {
  id: string;
  country: string;
  open_case_count: number;
  updated_at: string;
}

// Polls every few seconds instead of a manual refresh button, so closing
// a case in CaseList visibly updates this view without user action -
// that's the "no human refreshing it" requirement from the brief.
const POLL_MS = 3000;

export function CommandView() {
  const { userId } = useUser();
  const [stats, setStats] = useState<CountryStats[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      apiFetch<CountryStats[]>("/country-stats", userId)
        .then((data) => {
          if (!cancelled) setStats(data);
        })
        .catch((e) => !cancelled && setError(e.message));
    };
    load();
    const interval = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [userId]);

  return (
    <div>
      <h2 className="text-lg font-semibold text-slate-900">Command View — Open Case Counts</h2>
      <p className="mt-1 text-sm text-slate-500">
        Updates automatically (polling every {POLL_MS / 1000}s) when a Case is closed elsewhere.
      </p>

      {error && (
        <p className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {!error && stats.length === 0 && (
        <p className="mt-6 text-sm text-slate-400">No stats visible for this role yet.</p>
      )}

      <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
        {stats.map((s) => (
          <div key={s.id} className="card p-4">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              {s.country}
            </div>
            <div className="mt-2 text-3xl font-bold text-brand-600">{s.open_case_count}</div>
            <div className="mt-1 text-xs text-slate-400">open cases</div>
            <div className="mt-3 border-t border-slate-100 pt-2 text-xs text-slate-400">
              Last updated {new Date(s.updated_at).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
