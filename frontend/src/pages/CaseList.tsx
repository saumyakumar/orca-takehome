import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "../api/client";
import { CaseFormModal, CaseFormValues } from "../components/CaseFormModal";
import { CaseHistoryDrawer } from "../components/CaseHistoryDrawer";
import { ASSIGNABLE_USERS, assignableUsersForCountry, useUser } from "../context/UserContext";

interface Case {
  id: string;
  country: string;
  title: string;
  description: string | null;
  status: string;
  status_label: string;
  assigned_to: string | null;
}

interface CaseListResponse {
  items: Case[];
  total: number;
  limit: number;
  offset: number;
}

const PAGE_SIZE = 5;
const COUNTRIES = ["Arnova", "Belmara", "Calduria"];
const EMPTY_FORM: CaseFormValues = { title: "", description: "", assigned_to: "" };

function assigneeLabel(id: string | null): string {
  if (!id) return "Unassigned";
  return ASSIGNABLE_USERS.find((u) => u.id === id)?.label.split(" —")[0] ?? id;
}

export function CaseList() {
  const { userId, currentUser } = useUser();
  // Sourced from GET /me (see UserContext) - not re-derived from the
  // local "Viewing as" picker list - so UI decisions actually reflect
  // what the backend says this user is, not a frontend guess.
  const isAdmin = currentUser?.role === "admin";
  // Mirrors create_case's own default exactly (Admin-created cases land
  // in Arnova) so the modal's assignee options always match what the
  // backend will actually accept.
  const newCaseCountry = isAdmin ? "Arnova" : currentUser?.country ?? "Arnova";

  const [cases, setCases] = useState<Case[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [countryFilter, setCountryFilter] = useState("");
  const [assigneeFilter, setAssigneeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [locale, setLocale] = useState<"en" | "fr">("en");
  const [modal, setModal] = useState<{ mode: "create" | "edit"; caseId?: string; country: string } | null>(
    null
  );
  const [modalValues, setModalValues] = useState<CaseFormValues>(EMPTY_FORM);
  const [historyCase, setHistoryCase] = useState<Case | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Only Admin gets the Country/Assigned-to filters at all (see below) -
  // this list only matters while isAdmin is true, so it only needs to
  // handle the "narrow by selected country, else show everyone" case.
  const assigneeFilterOptions = countryFilter
    ? assignableUsersForCountry(countryFilter)
    : ASSIGNABLE_USERS;

  const load = useCallback(() => {
    const params = new URLSearchParams({
      locale,
      limit: String(PAGE_SIZE),
      offset: String(offset),
    });
    if (search.trim()) params.set("search", search.trim());
    if (countryFilter) params.set("country", countryFilter);
    if (assigneeFilter) params.set("assigned_to", assigneeFilter);
    if (statusFilter) params.set("status", statusFilter);
    apiFetch<CaseListResponse>(`/cases?${params}`, userId)
      .then((res) => {
        setCases(res.items);
        setTotal(res.total);
      })
      .catch((e) => setError(e.message));
  }, [userId, locale, offset, search, countryFilter, assigneeFilter, statusFilter]);

  useEffect(() => {
    setError(null);
    load();
  }, [load]);

  // Reset to page 1 whenever any filter changes.
  useEffect(() => {
    setOffset(0);
  }, [search, countryFilter, assigneeFilter, statusFilter]);

  // If narrowing the country filter makes the current assignee selection
  // invalid (e.g. switching from "All countries" to Belmara while
  // "Amara" was selected), clear it rather than silently keep filtering
  // by someone who can't appear in that country's results.
  useEffect(() => {
    if (assigneeFilter && assigneeFilter !== "unassigned") {
      const stillValid = assigneeFilterOptions.some((u) => u.id === assigneeFilter);
      if (!stillValid) setAssigneeFilter("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [countryFilter]);

  function openCreateModal() {
    setModalValues(EMPTY_FORM);
    setModal({ mode: "create", country: newCaseCountry });
  }

  function openEditModal(c: Case) {
    setModalValues({
      title: c.title,
      description: c.description ?? "",
      assigned_to: c.assigned_to ?? "",
    });
    setModal({ mode: "edit", caseId: c.id, country: c.country });
  }

  async function handleModalSubmit(values: CaseFormValues) {
    try {
      if (modal?.mode === "create") {
        await apiFetch("/cases", userId, {
          method: "POST",
          body: JSON.stringify({
            title: values.title,
            description: values.description || null,
            assigned_to: values.assigned_to || null,
          }),
        });
      } else if (modal?.mode === "edit" && modal.caseId) {
        await apiFetch(`/cases/${modal.caseId}`, userId, {
          method: "PATCH",
          body: JSON.stringify({
            title: values.title,
            description: values.description || null,
            assigned_to: values.assigned_to || null,
          }),
        });
      }
      setModal(null);
      load();
    } catch (e: any) {
      setError(e.message);
      setModal(null);
    }
  }

  async function handleClose(caseId: string) {
    try {
      await apiFetch(`/cases/${caseId}/close`, userId, { method: "POST" });
      load();
    } catch (e: any) {
      setError(e.message);
    }
  }

  const rangeStart = total === 0 ? 0 : offset + 1;
  const rangeEnd = Math.min(offset + PAGE_SIZE, total);

  return (
    <div>
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Care Companion — Cases</h2>
          <p className="mt-1 text-sm text-slate-500">
            Cases visible to the current role, filtered at the database query level.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-600">
            Language
            <select
              className="input"
              value={locale}
              onChange={(e) => setLocale(e.target.value as "en" | "fr")}
            >
              <option value="en">English</option>
              <option value="fr">Français</option>
            </select>
          </label>
          <button className="btn-primary whitespace-nowrap" onClick={openCreateModal}>
            + New case
          </button>
        </div>
      </div>

      {error && (
        <p className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <div className="mb-4 flex flex-wrap gap-2">
        <input
          className="input flex-1 min-w-[180px]"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by title…"
        />
        {isAdmin && (
          <select
            className="input"
            value={countryFilter}
            onChange={(e) => setCountryFilter(e.target.value)}
          >
            <option value="">All countries</option>
            {COUNTRIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        )}
        {isAdmin && (
          <select
            className="input"
            value={assigneeFilter}
            onChange={(e) => setAssigneeFilter(e.target.value)}
          >
            <option value="">Anyone</option>
            <option value="unassigned">Unassigned</option>
            {assigneeFilterOptions.map((u) => (
              <option key={u.id} value={u.id}>
                {u.label}
              </option>
            ))}
          </select>
        )}
        <select
          className="input"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">Any status</option>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-3 py-2">Title</th>
              <th className="px-3 py-2">Country</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Assigned to</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {cases.map((c) => (
              <tr key={c.id} className="hover:bg-slate-50">
                <td className="px-3 py-2 font-medium text-slate-800">{c.title}</td>
                <td className="px-3 py-2 text-slate-600">{c.country}</td>
                <td className="px-3 py-2">
                  <span className={c.status === "open" ? "badge-open" : "badge-closed"}>
                    {c.status_label}
                  </span>
                </td>
                <td className="px-3 py-2 text-slate-600">
                  {c.assigned_to ? (
                    assigneeLabel(c.assigned_to)
                  ) : (
                    <span className="italic text-slate-400">Unassigned</span>
                  )}
                </td>
                <td className="whitespace-nowrap px-3 py-2">
                  <div className="flex gap-2">
                    <button className="btn-secondary" onClick={() => setHistoryCase(c)}>
                      History
                    </button>
                    <button className="btn-secondary" onClick={() => openEditModal(c)}>
                      Edit
                    </button>
                    {c.status === "open" && (
                      <button className="btn-danger" onClick={() => handleClose(c.id)}>
                        Close
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {cases.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-slate-400">
                  No cases match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-3 flex items-center justify-between text-sm text-slate-500">
        <span>{total === 0 ? "0 cases" : `${rangeStart}–${rangeEnd} of ${total}`}</span>
        <div className="flex gap-2">
          <button
            className="btn-secondary"
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
          >
            Previous
          </button>
          <button
            className="btn-secondary"
            disabled={rangeEnd >= total}
            onClick={() => setOffset(offset + PAGE_SIZE)}
          >
            Next
          </button>
        </div>
      </div>

      {modal && (
        <CaseFormModal
          mode={modal.mode}
          country={modal.country}
          initialValues={modalValues}
          onSubmit={handleModalSubmit}
          onClose={() => setModal(null)}
        />
      )}

      {historyCase && (
        <CaseHistoryDrawer
          caseId={historyCase.id}
          caseTitle={historyCase.title}
          onClose={() => setHistoryCase(null)}
        />
      )}
    </div>
  );
}
