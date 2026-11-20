import { ImageOff, MapPin, Building2 } from "lucide-react";
import type { Item } from "../types";
import { publicImage } from "../services/api";

export function ItemCard({ item, onOpen }: { item: Item; onOpen: () => void }) {
  return <article className="item-card">
    <div className="item-photo">
      {item.cover_id ? <img src={publicImage(item.cover_id)} alt={item.name} loading="lazy" /> : <ImageOff size={38} />}
      <span className="badge">{item.category}</span>
    </div>
    <div className="item-body">
      <h3>{item.name}</h3>
      <p><MapPin size={15} />{item.found_region || item.found_location}</p>
      <p><Building2 size={15} />{item.organization_name}</p>
      <p>拾獲日期 {item.found_date}</p>
      {item.similarity !== undefined && <p className="score">圖片相似度 {(item.similarity * 100).toFixed(1)}%</p>}
      <button className="secondary full" onClick={onOpen}>查看物品與聯絡資訊</button>
    </div>
  </article>;
}
