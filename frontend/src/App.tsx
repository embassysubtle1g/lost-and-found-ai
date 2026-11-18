import { useEffect, useState } from "react";
import { Radar, LayoutGrid, ScanLine, ShieldCheck } from "lucide-react";
import { HallPage } from "./pages/HallPage";
import { StaffPage } from "./pages/StaffPage";

function currentPage() {
  if (location.hash === "#staff" || (!location.hash && location.pathname === "/staff")) return "staff";
  if (location.hash === "#photo") return "photo";
  return "hall";
}
export default function App() {
  const [page, setPage] = useState(currentPage);
  useEffect(() => {
    const changed = () => setPage(currentPage());
    window.addEventListener("hashchange", changed);
    return () => window.removeEventListener("hashchange", changed);
  }, []);
  return <>
    <header className="site-header"><div className="nav-shell">
      <a className="brand" href="#hall"><span className="brand-icon"><Radar size={25} /></span>
        <span>尋物雷達<small>失物招領與圖片搜尋</small></span></a>
      <nav aria-label="主選單">
        <a href="#hall" className={page === "hall" ? "active" : ""}><LayoutGrid size={18} />失物大廳</a>
        <a href="#photo" className={page === "photo" ? "active" : ""}><ScanLine size={18} />照片搜尋</a>
        <a href="#staff" className={page === "staff" ? "active" : ""}><ShieldCheck size={18} />機構後台</a>
      </nav>
    </div></header>
    <main className="shell">{page === "staff" ? <StaffPage /> : <HallPage key={page} photoMode={page === "photo"} />}</main>
    <footer className="shell">尋物雷達 · 找到候選物品後，請聯絡保管機構確認。</footer>
  </>;
}
