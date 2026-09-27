import { useEffect, useState } from "react";

import { apiFetch } from "../api/client";
import { useUser } from "../context/UserContext";

interface AuditLogRow {
  id: string;
  actor_id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  country: string | null;
  timestamp: string;
}

export function AuditLog() {
  const { userId } = useUser();
  const [rows, setRows] = useState<AuditLogRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    apiFetch<AuditLogRow[]>("/audit-logs", userId)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [userId]);

  return (
    <div>
      <h2 className="text-lg font-semibold text-slate-900">Audit Log</h2>
      <p className="mt-1 text-sm text-slate-500">
        Admin/Auditor only — other roles get a 403, shown below as an error message.
      </p>

      {error && (
        <p className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {!error && (
        <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-2">Time</th>
                <th className="px-3 py-2">Actor</th>
                <th className="px-3 py-2">Action</th>
                <th className="px-3 py-2">Entity</th>
                <th className="px-3 py-2">Country</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((r, i) => (
                <tr key={r.id} className={i % 2 === 0 ? "bg-white" : "bg-slate-50/60"}>
                  <td className="px-3 py-2 text-slate-400">
                    {new Date(r.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="px-3 py-2 font-medium text-slate-700">{r.actor_id}</td>
                  <td className="px-3 py-2">
                    <span className="badge bg-slate-100 text-slate-700">{r.action}</span>
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-slate-500">
                    {r.entity_type}/{r.entity_id.slice(0, 8)}
                  </td>
                  <td className="px-3 py-2 text-slate-600">{r.country ?? "—"}</td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-slate-400">
                    No audit entries yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
