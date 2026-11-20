import { useCallback, useEffect, useState } from "react";
import { api, getOrganizationId, setOrganizationId } from "../services/api";
import type { Organization } from "../types";

export function useOrganization() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const reload = useCallback(async (preferred?: number) => {
    setError("");
    try {
      const result = await api.organizations();
      const wanted = preferred ?? Number(getOrganizationId());
      const selected = result.find((organization) => organization.id === wanted) || result[0];
      if (selected) setOrganizationId(selected.id);
      setOrganizations(result);
      setSelectedId(selected?.id ?? null);
    } catch (reason) { setError((reason as Error).message); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void reload(); }, [reload]);
  function select(id: number) { setOrganizationId(id); setSelectedId(id); }
  return {
    organizations, organization: organizations.find((organization) => organization.id === selectedId) || null,
    loading, error, reload, select,
  };
}
