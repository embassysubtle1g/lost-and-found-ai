import { useEffect, useRef, useState } from "react";
import { X, Phone, MapPin } from "lucide-react";
import type { Item } from "../types";
import { api, publicImage } from "../services/api";

export function ItemDetail({ id, onClose }: { id: number; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [item, setItem] = useState<Item | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    dialog.current?.showModal();
    let active = true;
    api.detail(id).then((result) => { if (active) setItem(result); })
      .catch((reason) => { if (active) setError(reason.message); });
    return () => { active = false; };
  }, [id]);
  return <dialog ref={dialog} onCancel={onClose} aria-label="物品詳細資訊">
    <div className="row between"><h2>{item?.name || "載入物品"}</h2>
      <button className="icon-button" onClick={onClose} aria-label="關閉"><X /></button></div>
    {error && <p role="alert" className="message error">{error}</p>}
    {item && <>
      <div className="detail-photos">{item.images?.map((photo) =>
        <img key={photo.id} src={publicImage(photo.id)} alt={item.name} />)}</div>
      <p className="muted">物品編號 {item.reference}</p>
      <dl>
        <dt>物品類別</dt><dd>{item.category}</dd>
        <dt>拾獲日期</dt><dd>{item.found_date}</dd>
        <dt>拾獲區域</dt><dd>{item.found_region || "未填寫"}</dd>
        <dt>拾獲地點</dt><dd>{item.found_location}</dd>
      </dl>
      <div className="contact-box"><h3>{item.organization_name}</h3>
        <p><MapPin size={16} />{item.organization_address}</p>
        <p><Phone size={16} />{item.organization_phone}</p>
        <p>請提供物品編號，聯絡保管機構確認領回方式。</p></div>
    </>}
  </dialog>;
}
