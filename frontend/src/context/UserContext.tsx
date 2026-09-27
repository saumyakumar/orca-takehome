import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { apiFetch } from "../api/client";

// Deliberately fake auth for this take-home: no login, just a dropdown
// that picks which seeded demo user's id gets sent as X-User-Id. Ids
// must match backend/app/auth/fake_users.py.
// `country` mirrors backend/app/auth/fake_users.py exactly ("*" = all
// countries, Admin only) so the frontend can scope assignee options the
// same way the backend validates them (see cases/router.py).
export const DEMO_USERS = [
  { id: "admin-1", label: "Ada — Admin (all countries)", country: "*" },
  { id: "lead-arn", label: "Amara — Country Lead, Arnova", country: "Arnova" },
  { id: "lead-bel", label: "Boris — Country Lead, Belmara", country: "Belmara" },
  { id: "field-cal", label: "Carla — Field Worker, Calduria", country: "Calduria" },
  { id: "audit-arn", label: "Amit — Auditor, Arnova", country: "Arnova" },
];

// Who a case can actually be assigned to - Country Leads and Field
// Workers do case work; Admin/Auditor don't, so they're excluded here
// even though they're valid "viewing as" identities above.
export const ASSIGNABLE_USERS = DEMO_USERS.filter(
  (u) => u.id.startsWith("lead-") || u.id.startsWith("field-")
);

export function assignableUsersForCountry(country: string) {
  return ASSIGNABLE_USERS.filter((u) => u.country === country);
}

export interface CurrentUser {
  id: string;
  name: string;
  role: string;
  country: string;
}

interface UserContextValue {
  userId: string;
  setUserId: (id: string) => void;
  /** The active user's own record, straight from GET /me - the backend's
   * answer to "who is this and what can they do." UI decisions (which
   * filters to show, what country a new case defaults to) should read
   * this, not re-derive a guess from the local DEMO_USERS picker list. */
  currentUser: CurrentUser | null;
}

const UserContext = createContext<UserContextValue | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [userId, setUserId] = useState(DEMO_USERS[1].id);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    let cancelled = false;
    setCurrentUser(null);
    apiFetch<CurrentUser>("/me", userId).then((me) => {
      if (!cancelled) setCurrentUser(me);
    });
    return () => {
      cancelled = true;
    };
  }, [userId]);

  return (
    <UserContext.Provider value={{ userId, setUserId, currentUser }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser(): UserContextValue {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used within UserProvider");
  return ctx;
}
