import { useEffect, useState } from "react";

import { apiFetch } from "../api/client";
import { useUser } from "../context/UserContext";

interface HistoryRow {
  id: string;
  actor_id: string;
  action: string;
  timestamp: string;
}

interface CaseHistoryDrawerProps {
  caseId: string;
  caseTitle: string;
  onClose: () => void;
}

export function CaseHistoryDrawer({ caseId, caseTitle, onClose }: CaseHistoryDrawerProps) {
  const { userId } = useUser();
  const [rows, setRows] = useState<HistoryRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  useEffect(() => {
    apiFetch<HistoryRow[]>(`/cases/${caseId}/history`, userId)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [caseId, userId]);

  return (
    <div
      className="fixed inset-0 z-20 bg-slate-900/40"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="absolute right-0 top-0 h-full w-full max-w-sm overflow-y-auto border-l border-slate-200 bg-white p-5 shadow-xl">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="text-base font-semibold text-slate-900">History</h3>
            <p className="mt-0.5 text-sm text-slate-500">{caseTitle}</p>
          </div>
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>

        {error && (
          <p className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        {!error && rows.length === 0 && (
          <p className="mt-6 text-sm text-slate-400">No history yet.</p>
        )}

        {!error && rows.length > 0 && (
          <ul className="mt-4 space-y-3 border-l-2 border-slate-100 pl-4">
            {rows.map((h) => (
              <li key={h.id} className="relative">
                <span className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-brand-400" />
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium text-slate-700">{h.actor_id}</span>
                  <span className="badge bg-slate-100 text-slate-700">{h.action}</span>
                </div>
                <div className="mt-0.5 text-xs text-slate-400">
                  {new Date(h.timestamp).toLocaleString()}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
