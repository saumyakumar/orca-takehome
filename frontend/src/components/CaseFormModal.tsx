import { useEffect, useState } from "react";

import { assignableUsersForCountry } from "../context/UserContext";

export interface CaseFormValues {
  title: string;
  description: string;
  assigned_to: string;
}

interface CaseFormModalProps {
  mode: "create" | "edit";
  /** The country this case belongs to (or will, on create) - the
   * "Assigned to" options are scoped to this country's staff only, since
   * the backend rejects a cross-country assignee. */
  country: string;
  initialValues: CaseFormValues;
  onSubmit: (values: CaseFormValues) => Promise<void> | void;
  onClose: () => void;
}

export function CaseFormModal({ mode, country, initialValues, onSubmit, onClose }: CaseFormModalProps) {
  const assignableUsers = assignableUsersForCountry(country);
  const [values, setValues] = useState<CaseFormValues>(initialValues);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!values.title.trim()) return;
    setSubmitting(true);
    try {
      await onSubmit(values);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-20 flex items-center justify-center bg-slate-900/40 px-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <form
        onSubmit={handleSubmit}
        className="card w-full max-w-md p-5"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 className="text-base font-semibold text-slate-900">
          {mode === "create" ? "New case" : "Edit case"}
        </h3>

        <label className="mt-4 block text-xs font-medium text-slate-500">Title</label>
        <input
          autoFocus
          className="input mt-1 w-full"
          value={values.title}
          onChange={(e) => setValues({ ...values, title: e.target.value })}
          placeholder="Case title"
        />

        <label className="mt-3 block text-xs font-medium text-slate-500">
          Description (optional)
        </label>
        <input
          className="input mt-1 w-full"
          value={values.description}
          onChange={(e) => setValues({ ...values, description: e.target.value })}
          placeholder="Description"
        />

        <label className="mt-3 block text-xs font-medium text-slate-500">Assigned to</label>
        <select
          className="input mt-1 w-full"
          value={values.assigned_to}
          onChange={(e) => setValues({ ...values, assigned_to: e.target.value })}
        >
          <option value="">Unassigned</option>
          {assignableUsers.map((u) => (
            <option key={u.id} value={u.id}>
              {u.label}
            </option>
          ))}
        </select>

        <div className="mt-5 flex justify-end gap-2">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={submitting}>
            {mode === "create" ? "Add case" : "Save"}
          </button>
        </div>
      </form>
    </div>
  );
}
