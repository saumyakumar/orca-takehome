import { useState } from "react";

import { NotificationBell } from "./components/NotificationBell";
import { DEMO_USERS, UserProvider, useUser } from "./context/UserContext";
import { AuditLog } from "./pages/AuditLog";
import { CaseList } from "./pages/CaseList";
import { CommandView } from "./pages/CommandView";

type Tab = "cases" | "command-view" | "audit";

function RoleSwitcher() {
  const { userId, setUserId } = useUser();
  return (
    <label className="flex items-center gap-2 text-sm text-slate-600">
      Viewing as
      <select
        className="input"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
      >
        {DEMO_USERS.map((u) => (
          <option key={u.id} value={u.id}>
            {u.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function Sidebar({ tab, setTab }: { tab: Tab; setTab: (t: Tab) => void }) {
  // Each entry here is one app plugged into the shared foundation - a new
  // app joining the platform just adds one more entry, same pattern.
  const items: { key: Tab; label: string }[] = [
    { key: "cases", label: "Cases" },
    { key: "command-view", label: "Command View" },
    { key: "audit", label: "Audit Log" },
  ];

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-100 px-4 py-4">
        <h1 className="text-base font-semibold text-slate-900">ORCA Platform</h1>
        <p className="mt-0.5 text-xs text-slate-500">Foundation demo</p>
      </div>
      <nav className="flex flex-1 flex-col gap-1 px-2 py-3">
        {items.map((item) => (
          <button
            key={item.key}
            onClick={() => setTab(item.key)}
            className={tab === item.key ? "nav-item-active" : "nav-item"}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}

function Shell() {
  const [tab, setTab] = useState<Tab>("cases");

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar tab={tab} setTab={setTab} />

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex shrink-0 items-center justify-end gap-3 border-b border-slate-200 bg-white px-6 py-3">
          <NotificationBell />
          <RoleSwitcher />
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-4xl px-4 py-6">
            <div className="card p-5">
              {tab === "cases" && <CaseList />}
              {tab === "command-view" && <CommandView />}
              {tab === "audit" && <AuditLog />}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <UserProvider>
      <Shell />
    </UserProvider>
  );
}
