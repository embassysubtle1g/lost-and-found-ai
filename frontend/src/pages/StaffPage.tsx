import { useEffect, useRef, useState, type FormEvent } from "react";
import { Plus, LogOut, RefreshCw, ImagePlus, ShieldCheck } from "lucide-react";
import { useSession } from "../hooks/useSession";
import { api, staffImage } from "../services/api";
import { categories, statusLabels, type Item, type ItemInput, type ItemList, type Photo } from "../types";

const blank: ItemInput = {
  name: "", category: categories[0], found_date: "", found_location: "", found_region: "", private_note: "",
};

function StaffPhoto({ photo }: { photo: Photo }) {
  const [src, setSrc] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    let url = "";
    staffImage(photo.id).then((result) => {
      url = result;
      if (active) setSrc(result); else URL.revokeObjectURL(result);
    }).catch((reason) => { if (active) setError(reason.message); });
    return () => { active = false; if (url) URL.revokeObjectURL(url); };
  }, [photo.id]);
  return src ? <img src={src} alt={"建檔照片 " + photo.id} /> : <p>{error || "載入照片…"}</p>;
}

export function StaffPage() {
  const session = useSession();
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [items, setItems] = useState<ItemList>({ items: [] });
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Item | null>(null);
  const [form, setForm] = useState<ItemInput>({ ...blank });
  const [photos, setPhotos] = useState<File[]>([]);
  const fileInput = useRef<HTMLInputElement>(null);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    let active = true;
    if (!session.account) { setItems({ items: [] }); setSelected(null); setForm({ ...blank }); setPage(1); return; }
    setError("");
    api.staffList(page).then((result) => { if (active) setItems(result); })
      .catch((reason) => { if (active) setError(reason.message); });
    return () => { active = false; };
  }, [session.account, page]);

  async function act(action: () => Promise<void>) {
    setBusy(true); setError(""); setNotice("");
    try { await action(); } catch (reason) { setError((reason as Error).message); }
    finally { setBusy(false); }
  }
  async function refresh(id?: number) {
    setItems(await api.staffList(page));
    if (id) await open(id);
  }
  async function open(id: number) {
    const item = await api.staffDetail(id);
    setSelected(item);
    setForm({ name: item.name, category: item.category, found_date: item.found_date,
      found_location: item.found_location, found_region: item.found_region, private_note: item.private_note || "" });
    setPhotos([]);
    if (fileInput.current) fileInput.current.value = "";
  }
  function reset() {
    setSelected(null); setForm({ ...blank }); setPhotos([]);
    if (fileInput.current) fileInput.current.value = "";
  }
  function update(key: keyof ItemInput, value: string) { setForm((current) => ({ ...current, [key]: value })); }
  async function save(event: FormEvent) {
    event.preventDefault();
    await act(async () => {
      if (photos.some((photo) => photo.size > 8 * 1024 * 1024)) throw new Error("每張照片不可超過 8 MB");
      if (photos.length + (selected?.images?.length || 0) > 8) throw new Error("每件物品最多八張照片");
      const item = await api.save(form, selected?.id);
      // Record the saved ID before uploading so a retry never creates a duplicate item.
      setSelected(item);
      const failures: string[] = [];
      for (const photo of photos) {
        try { await api.upload(item.id, photo); }
        catch (reason) { failures.push(photo.name + "：" + (reason as Error).message); }
      }
      await open(item.id);
      setPage(1);
      setItems(await api.staffList(1));
      setNotice("物品已儲存");
      if (failures.length) setError("部分照片上傳失敗，請重新選取這些照片再上傳。" + failures.join("、"));
    });
  }
  const alert = <>{(error || session.error) && <p role="alert" className="message error">{error || session.error}</p>}
    {notice && <p role="status" className="message">{notice}</p>}</>;

  if (session.checking) return <p className="message">確認登入中…</p>;
  if (!session.account) return <div className="login-wrap">
    <div className="page-heading"><ShieldCheck size={32} /><h1>機構承辦人登入</h1><p>登入後管理本機構保管的拾獲物。</p></div>
    {alert}
    <form className="panel" onSubmit={(event) => {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      void act(() => session.login(String(data.get("username")), String(data.get("password"))));
    }}>
      <label>帳號<input name="username" required autoComplete="username" /></label>
      <label>密碼<input name="password" type="password" required autoComplete="current-password" /></label>
      <button disabled={busy}>{busy ? "登入中…" : "登入機構後台"}</button>
    </form>
  </div>;

  return <>
    <div className="row between page-heading"><div><span className="eyebrow">機構後台</span>
      <h1>{session.account.organization.name}</h1><p>承辦人 {session.account.username}</p></div>
      <button className="secondary" disabled={busy} onClick={() => void act(session.logout)}><LogOut size={17} />登出</button></div>
    {alert}
    <details className="panel"><summary>機構聯絡資訊與密碼</summary>
      <form key={JSON.stringify(session.account.organization)} className="fields settings" onSubmit={(event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        void act(async () => {
          await api.organization({ name: String(data.get("name")), address: String(data.get("address")), phone: String(data.get("phone")) });
          await session.refresh(); setNotice("機構資訊已更新");
        });
      }}>
        <label>機構名稱<input name="name" required maxLength={120} defaultValue={session.account.organization.name} /></label>
        <label>對外地址<input name="address" required maxLength={240} defaultValue={session.account.organization.address} /></label>
        <label>對外電話<input name="phone" required maxLength={50} defaultValue={session.account.organization.phone} /></label>
        <div className="row"><button disabled={busy}>儲存機構資訊</button></div>
      </form>
      <form className="fields settings" onSubmit={(event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        void act(async () => {
          await api.password(String(data.get("old")), String(data.get("next")));
          session.signedOut(); setNotice("密碼已更新，請重新登入");
        });
      }}>
        <label>原密碼<input type="password" name="old" required autoComplete="current-password" /></label>
        <label>新密碼（至少 10 字元）<input type="password" name="next" required minLength={10} maxLength={160} autoComplete="new-password" /></label>
        <div className="row"><button disabled={busy}>更新密碼</button></div>
      </form>
    </details>
    <form ref={formRef} className="panel" onSubmit={save}>
      <div className="form-banner"><ImagePlus size={24} /><div><h2>{selected ? "編輯拾獲物" : "拾獲物建檔"}</h2>
        <p>照片上傳後，自動擷取圖片特徵供民眾比對。</p></div></div>
      {selected && <p className="muted small">物品編號 {selected.reference} · {statusLabels[selected.status || "AVAILABLE"]}</p>}
      <div className="fields">
        <label>物品名稱 <span className="required">必填</span><input required maxLength={120} value={form.name} onChange={(event) => update("name", event.target.value)} /></label>
        <label>物品類別 <span className="required">必填</span><select required value={form.category} onChange={(event) => update("category", event.target.value)}>
          {!categories.includes(form.category) && <option>{form.category}</option>}
          {categories.map((category) => <option key={category}>{category}</option>)}</select></label>
        <label>拾獲區域 <span className="required">必填</span><input required maxLength={120} value={form.found_region} placeholder="例如：屏東市、圖書館" onChange={(event) => update("found_region", event.target.value)} /></label>
        <label>拾獲詳細地點 <span className="required">必填</span><input required maxLength={240} value={form.found_location} onChange={(event) => update("found_location", event.target.value)} /></label>
        <label>拾獲日期 <span className="required">必填</span><input required type="date" value={form.found_date} onChange={(event) => update("found_date", event.target.value)} /></label>
        <label>新增照片（選填）<input ref={fileInput} type="file" multiple accept="image/jpeg,image/png,image/webp"
          disabled={busy || Boolean(selected && selected.status !== "AVAILABLE")} onChange={(event) => setPhotos(Array.from(event.target.files || []))} /></label>
        <label className="wide">內部核對備註（選填）<textarea rows={3} maxLength={2000} value={form.private_note} onChange={(event) => update("private_note", event.target.value)} /></label>
      </div>
      <p className="muted small">每件物品最多八張照片，每張最多 8 MB。內部備註僅供本機構承辦人查看。</p>
      <div className="row"><button disabled={busy}>{busy ? "儲存中…" : "儲存物品"}</button>
        <button type="button" disabled={busy} className="secondary" onClick={reset}><Plus size={17} />新增另一件</button></div>
    </form>
    {selected && <section className="panel">
      <div className="row between"><h2>物品狀態與照片</h2><button className="secondary" disabled={busy}
        onClick={() => void act(() => refresh(selected.id))}><RefreshCw size={16} />重新整理</button></div>
      {selected.returned_at && <p>歸還時間 {new Date(selected.returned_at).toLocaleString("zh-TW")} · 登記人帳號 ID {selected.returned_by}</p>}
      {selected.status === "AVAILABLE" && <div className="row">
        <button disabled={busy} onClick={() => {
          if (confirm("確認物品已實際交還？")) void act(async () => { await api.action(selected.id, "return"); await refresh(selected.id); });
        }}>標記為已歸還</button>
        <button disabled={busy} className="secondary" onClick={() => {
          if (confirm("確認將物品下架？")) void act(async () => { await api.action(selected.id, "withdraw"); await refresh(selected.id); });
        }}>下架</button></div>}
      <div className="photo-grid">{selected.images?.map((photo) => <article className="photo-entry" key={photo.id}>
        <StaffPhoto photo={photo} />
        <p>{photo.is_cover && "封面 · "}{statusLabels[photo.state || "PENDING"]}</p>
        {photo.error && <p className="small error-text">{photo.error}</p>}
        <div className="row">
          {!photo.is_cover && <button disabled={busy} className="secondary" onClick={() => void act(async () => {
            await api.imageAction(selected.id, photo.id, "cover"); await open(selected.id);
          })}>設為封面</button>}
          {photo.state === "FAILED" && <button disabled={busy} className="secondary" onClick={() => void act(async () => {
            await api.imageAction(selected.id, photo.id, "retry"); await open(selected.id);
          })}>重試</button>}
          <button disabled={busy} className="secondary" onClick={() => {
            if (confirm("確認移除此照片？")) void act(async () => { await api.imageAction(selected.id, photo.id, "remove"); await open(selected.id); });
          }}>移除</button>
        </div>
      </article>)}</div>
    </section>}
    <h2>本機構拾獲物</h2>
    <div className="staff-list">{items.items.map((item) => <article className="staff-row" key={item.id}>
      <div><h3>{item.name}</h3><p className="muted">{item.found_date} · {item.found_region || item.found_location}</p>
        <span className="badge">{statusLabels[item.status || "AVAILABLE"]}</span></div>
      <button disabled={busy} className="secondary" onClick={() => void act(async () => {
        await open(item.id); formRef.current?.scrollIntoView({ behavior: "smooth" });
      })}>管理物品</button>
    </article>)}</div>
    {items.items.length === 0 && <p className="empty">本機構目前沒有建檔紀錄。</p>}
    <div className="row pagination">
      {page > 1 && <button disabled={busy} className="secondary" onClick={() => setPage(page - 1)}>上一頁</button>}
      {items.has_more && <button disabled={busy} className="secondary" onClick={() => setPage(page + 1)}>下一頁</button>}
    </div>
  </>;
}
