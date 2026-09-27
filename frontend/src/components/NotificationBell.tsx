import { useEffect, useRef, useState } from "react";

import { apiFetch } from "../api/client";
import { useUser } from "../context/UserContext";

interface Notification {
  id: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

const POLL_MS = 5000;

export function NotificationBell() {
  const { userId } = useUser();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const load = () => {
    apiFetch<Notification[]>("/notifications", userId).then(setNotifications).catch(() => {});
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, POLL_MS);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  async function markRead(id: string) {
    await apiFetch(`/notifications/${id}/read`, userId, { method: "POST" });
    load();
  }

  async function markAllRead() {
    await apiFetch("/notifications/read-all", userId, { method: "POST" });
    load();
  }

  return (
    <div className="relative" ref={containerRef}>
      <button
        className="btn-secondary relative"
        onClick={() => setOpen((v) => !v)}
        aria-label="Notifications"
      >
        🔔
        {unreadCount > 0 && (
          <span className="absolute -right-1.5 -top-1.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-10 mt-2 w-80 rounded-lg border border-slate-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-100 px-3 py-2">
            <span className="text-sm font-semibold text-slate-700">Notifications</span>
            {unreadCount > 0 && (
              <button className="text-xs text-brand-600 hover:underline" onClick={markAllRead}>
                Mark all read
              </button>
            )}
          </div>
          <ul className="max-h-80 overflow-y-auto">
            {notifications.length === 0 && (
              <li className="px-3 py-4 text-center text-xs text-slate-400">No notifications.</li>
            )}
            {notifications.map((n) => (
              <li
                key={n.id}
                className={`cursor-pointer border-b border-slate-50 px-3 py-2 text-sm last:border-0 hover:bg-slate-50 ${
                  n.is_read ? "text-slate-400" : "font-medium text-slate-700"
                }`}
                onClick={() => !n.is_read && markRead(n.id)}
              >
                <div>{n.message}</div>
                <div className="mt-0.5 text-[11px] text-slate-400">
                  {new Date(n.created_at).toLocaleTimeString()}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
