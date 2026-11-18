import type { Account, Item, ItemInput, ItemList, SearchFilters, Organization } from "../types";

const base = "/api/v1";
export function getToken() { return sessionStorage.getItem("radar_staff_token"); }
export function setToken(token: string | null) {
  if (token) sessionStorage.setItem("radar_staff_token", token);
  else sessionStorage.removeItem("radar_staff_token");
}
export async function request<T>(path: string, method = "GET", data?: unknown, staff = false): Promise<T> {
  const headers: Record<string, string> = {};
  if (staff && getToken()) headers.Authorization = "Bearer " + getToken();
  let body: BodyInit | undefined;
  if (data instanceof FormData) body = data;
  else if (data !== undefined) {
    body = JSON.stringify(data);
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(base + path, { method, headers, body });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    if (staff && response.status === 401) {
      setToken(null);
      window.dispatchEvent(new Event("radar-session-expired"));
    }
    const detail = payload.detail;
    throw new Error(typeof detail === "string" ? detail :
      Array.isArray(detail) ? detail.map((error: { msg: string }) => error.msg).join("、") :
      "操作失敗，請稍後再試（" + response.status + "）");
  }
  return response.status === 204 ? undefined as T : response.json();
}
export const api = {
  list: (filters: SearchFilters, page: number) =>
    request<ItemList>("/public/items?" + new URLSearchParams({ ...filters, page: String(page) })),
  search: (filters: SearchFilters, photo: File) => {
    const data = new FormData();
    for (const [key, value] of Object.entries(filters)) if (value) data.append(key, value);
    data.append("file", photo);
    return request<ItemList>("/public/search", "POST", data);
  },
  detail: (id: number) => request<Item>("/public/items/" + id),
  me: () => request<Account>("/auth/me", "GET", undefined, true),
  login: (username: string, password: string) =>
    request<{ access_token: string }>("/auth/login", "POST", { username, password }),
  logout: () => request<void>("/auth/logout", "POST", undefined, true),
  staffList: (page: number) => request<ItemList>("/staff/items?page=" + page, "GET", undefined, true),
  staffDetail: (id: number) => request<Item>("/staff/items/" + id, "GET", undefined, true),
  save: (data: ItemInput, id?: number) =>
    request<Item>("/staff/items" + (id ? "/" + id : ""), id ? "PUT" : "POST", data, true),
  upload: (id: number, photo: File) => {
    const data = new FormData();
    data.append("file", photo);
    return request("/staff/items/" + id + "/images", "POST", data, true);
  },
  action: (id: number, action: "return" | "withdraw") =>
    request("/staff/items/" + id + "/" + action, "POST", undefined, true),
  imageAction: (item: number, image: number, action: "cover" | "retry" | "remove") =>
    request("/staff/items/" + item + "/images/" + image + (action === "remove" ? "" : "/" + action),
      action === "remove" ? "DELETE" : action === "cover" ? "PUT" : "POST", undefined, true),
  organization: (data: Omit<Organization, "id">) => request<Organization>("/auth/organization", "PUT", data, true),
  password: (current_password: string, new_password: string) =>
    request<void>("/auth/password", "PUT", { current_password, new_password }, true),
};
export function publicImage(id: number) { return base + "/public/images/" + id; }
export async function staffImage(id: number): Promise<string> {
  const response = await fetch(base + "/staff/images/" + id, {
    headers: { Authorization: "Bearer " + getToken() },
  });
  if (!response.ok) throw new Error("照片無法讀取");
  return URL.createObjectURL(await response.blob());
}
