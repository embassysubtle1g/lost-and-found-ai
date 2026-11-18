export const categories = ["3C電子", "證件錢包", "鑰匙配件", "隨身衣物", "其他"];
export const statusLabels: Record<string, string> = {
  AVAILABLE: "待認領", RETURNED: "已歸還", WITHDRAWN: "已下架",
  PENDING: "等待處理", PROCESSING: "處理中", COMPLETED: "向量已就緒", FAILED: "處理失敗",
};
export interface Organization { id: number; name: string; address: string; phone: string }
export interface Account { id: number; username: string; organization: Organization }
export interface Photo {
  id: number; is_cover: boolean; media_type: string;
  state?: string; error?: string; model?: string; model_version?: string;
}
export interface Item {
  id: number; reference: string; name: string; category: string;
  found_date: string; found_location: string; found_region: string;
  status?: string; private_note?: string; returned_at?: string; returned_by?: number;
  organization_name?: string; organization_address?: string; organization_phone?: string;
  cover_id?: number; images?: Photo[]; similarity?: number;
}
export interface ItemInput {
  name: string; category: string; found_date: string;
  found_location: string; found_region: string; private_note: string;
}
export interface ItemList { items: Item[]; page?: number; has_more?: boolean }
export interface SearchFilters { keyword: string; category: string; location: string; lost_date: string }
export const emptyFilters: SearchFilters = { keyword: "", category: "", location: "", lost_date: "" };
