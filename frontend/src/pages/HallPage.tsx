import { useEffect, useState, type FormEvent } from "react";
import { Search, ScanLine, ImagePlus, SearchX } from "lucide-react";
import { api } from "../services/api";
import { categories, emptyFilters, type ItemList, type SearchFilters } from "../types";
import { ItemCard } from "../components/ItemCard";
import { ItemDetail } from "../components/ItemDetail";

export function HallPage({ photoMode }: { photoMode: boolean }) {
  const [filters, setFilters] = useState<SearchFilters>({ ...emptyFilters });
  const [applied, setApplied] = useState<SearchFilters>({ ...emptyFilters });
  const [photo, setPhoto] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState<ItemList>({ items: [] });
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<number | null>(null);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    if (!photo) { setPreview(""); return; }
    const url = URL.createObjectURL(photo);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [photo]);
  useEffect(() => {
    let active = true;
    setError("");
    if (photoMode) { setResult({ items: [] }); setSearched(false); return; }
    setBusy(true);
    api.list(applied, page).then((data) => { if (active) { setResult(data); setSearched(true); } })
      .catch((reason) => { if (active) setError(reason.message); })
      .finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [applied, page, photoMode]);

  function update(key: keyof SearchFilters, value: string) {
    setFilters((current) => ({ ...current, [key]: value }));
  }
  async function search(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (!photoMode) { setPage(1); setApplied({ ...filters }); return; }
    if (!photo) { setError("請先上傳查詢照片"); return; }
    if (photo.size > 8 * 1024 * 1024) { setError("照片不可超過 8 MB"); return; }
    setBusy(true);
    setResult({ items: [] });
    setSearched(false);
    try { setResult(await api.search(filters, photo)); setSearched(true); }
    catch (reason) { setError((reason as Error).message); }
    finally { setBusy(false); }
  }
  return <>
    <div className="page-heading">
      <span className="eyebrow">尋物雷達</span>
      <h1>{photoMode ? "用照片尋找你的物品" : "失物大廳"}</h1>
      <p>{photoMode ? "上傳遺失前的物品照片，查看外觀相似的拾獲物。" : "查看機構保管中的拾獲物，找到線索後直接聯絡保管單位。"}</p>
    </div>
    <form className="panel" onSubmit={search}>
      <div className="fields">
        <label>物品名稱（選填）<input value={filters.keyword} maxLength={120}
          onChange={(event) => update("keyword", event.target.value)} placeholder="例如：黑色短夾" /></label>
        <label>物品類別（選填）<select value={filters.category}
          onChange={(event) => update("category", event.target.value)}>
          <option value="">所有類別</option>{categories.map((category) => <option key={category}>{category}</option>)}
        </select></label>
        <label>可能遺失的區域（選填）<input value={filters.location} maxLength={120}
          onChange={(event) => update("location", event.target.value)} placeholder="例如：屏東市、圖書館" /></label>
        <label>大約遺失日期（選填）<input type="date" value={filters.lost_date}
          onChange={(event) => update("lost_date", event.target.value)} /></label>
      </div>
      <p className="muted small">區域會篩選登記的拾獲區域，不確定時可留空。日期會查詢當天及之後的拾獲物。</p>
      {photoMode && <label className="upload"><ImagePlus size={30} />
        <span>上傳查詢照片 <strong className="required">必填</strong></span>
        <span className="muted small">JPEG、PNG、WebP，每張最多 8 MB</span>
        <input required type="file" accept="image/jpeg,image/png,image/webp"
          onChange={(event) => setPhoto(event.target.files?.[0] || null)} />
        {preview && <img src={preview} alt="查詢照片預覽" />}
      </label>}
      <div className="row">
        <button disabled={busy}>{photoMode ? <ScanLine size={18} /> : <Search size={18} />}
          {busy ? "搜尋中…" : photoMode ? "開始圖片比對" : "查詢拾獲物"}</button>
        <button type="button" className="secondary" disabled={busy} onClick={() => {
          setFilters({ ...emptyFilters });
          if (!photoMode) { setApplied({ ...emptyFilters }); setPage(1); }
        }}>清除條件</button>
      </div>
    </form>
    {error && <p role="alert" className="message error">{error}</p>}
    <div className="row between"><h2>{photoMode ? "相似物品候選" : "待認領拾獲物"}</h2>
      {searched && <span className="muted">{photoMode ? "本次找到 " : "本頁 "}{result.items.length} 件</span>}</div>
    <div aria-live="polite" aria-busy={busy}>
      {busy && <p className="message">正在搜尋，請稍候。</p>}
      {!busy && searched && result.items.length === 0 && <div className="empty">
        <SearchX size={36} /><h3>目前沒有符合的物品</h3><p>可以減少篩選條件，或稍後再來查詢。</p></div>}
      {!busy && <div className="cards">{result.items.map((item) =>
        <ItemCard key={item.id} item={item} onOpen={() => setSelected(item.id)} />)}</div>}
    </div>
    {!photoMode && <div className="row pagination">
      {page > 1 && <button disabled={busy} className="secondary" onClick={() => setPage(page - 1)}>上一頁</button>}
      {result.has_more && <button disabled={busy} className="secondary" onClick={() => setPage(page + 1)}>下一頁</button>}
    </div>}
    {selected !== null && <ItemDetail key={selected} id={selected} onClose={() => setSelected(null)} />}
  </>;
}
