const $ = (id) => document.getElementById(id);
const apiRoot = "/api/v1";
const statusLabels = {
  AVAILABLE: "待認領", RETURNED: "已歸還", WITHDRAWN: "已下架",
  PENDING: "等待處理", PROCESSING: "處理中", COMPLETED: "向量已就緒", FAILED: "處理失敗",
};
let token = sessionStorage.getItem("staff_token");
let editing = null;
let staffPage = 1;

function notice(message, error = false) {
  $("notice").hidden = !message;
  $("notice").className = error ? "error" : "";
  $("notice").textContent = message || "";
  if (error) $("notice").scrollIntoView({ block: "nearest" });
}

async function api(path, { method = "GET", data, privateRoute = false, blob = false } = {}) {
  const headers = {};
  if (privateRoute && token) headers.Authorization = "Bearer " + token;
  let body = data;
  if (data && !(data instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(data);
  }
  const response = await fetch(apiRoot + path, { method, headers, body });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    if (privateRoute && response.status === 401) signedOut();
    throw new Error(typeof payload.detail === "string" ? payload.detail : "操作失敗（" + response.status + "）");
  }
  if (response.status !== 204) return blob ? response.blob() : response.json();
}

function element(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}

function button(label, action) {
  const node = element("button", label);
  node.type = "button";
  node.className = "secondary";
  node.onclick = async () => {
    node.disabled = true;
    try { await action(); }
    catch (error) { notice(error.message, true); }
    finally { node.disabled = false; }
  };
  return node;
}

function submit(id, action) {
  $(id).onsubmit = async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const buttons = [...form.querySelectorAll("button")];
    buttons.forEach((node) => { node.disabled = true; });
    notice("");
    try { await action(form, event.submitter); }
    catch (error) { notice(error.message, true); }
    finally { buttons.forEach((node) => { node.disabled = false; }); }
  };
}

function itemSummary(item) {
  const card = element("article");
  card.append(element("h3", item.name),
    element("p", item.category + " · " + item.found_date),
    element("p", "拾獲地點：" + item.found_location),
    element("p", "物品編號：" + item.reference));
  return card;
}

function publicImage(id, name) {
  const image = element("img");
  image.src = apiRoot + "/public/images/" + id;
  image.alt = name;
  return image;
}

async function publicDetail(id) {
  const item = await api("/public/items/" + id);
  const card = itemSummary(item);
  card.append(element("p", "保管機構：" + item.organization_name),
    element("p", "領取地址：" + item.organization_address),
    element("p", "電話：" + item.organization_phone));
  for (const photo of item.images) card.append(publicImage(photo.id, item.name));
  $("detail").replaceChildren(card);
  $("details").showModal();
}

function listCards(container, items, render, empty) {
  $(container).replaceChildren(...(items.length ? items.map(render) : [element("p", empty)]));
}

function pages(id, result, load) {
  const controls = [];
  if (result.page > 1) controls.push(button("上一頁", () => load(result.page - 1)));
  if (result.has_more) controls.push(button("下一頁", () => load(result.page + 1)));
  $(id).replaceChildren(...controls);
}

async function publicSearch(mode, page = 1, savedFilters = null) {
  const fields = savedFilters || new FormData($("search"));
  const filters = new URLSearchParams();
  for (const key of ["keyword", "category", "location", "organization", "since", "until"]) {
    if (fields.get(key)) filters.set(key, fields.get(key));
  }
  let result;
  if (mode === "photo") {
    const photo = fields.get("file");
    if (!photo.size) throw new Error("請先選擇查詢照片");
    const request = new FormData();
    for (const [key, value] of filters) if (key !== "keyword") request.set(key, value);
    request.set("file", photo);
    result = await api("/public/search", { method: "POST", data: request });
  } else {
    filters.set("page", page);
    result = await api("/public/items?" + filters);
  }
  $("results-title").textContent = mode === "photo" ? "相似拾獲物候選" : "待認領物品";
  listCards("results", result.items, (item) => {
    const card = itemSummary(item);
    if (item.cover_id) card.prepend(publicImage(item.cover_id, item.name));
    card.append(element("p", "保管機構：" + item.organization_name),
      button("查看聯絡資訊", () => publicDetail(item.id)));
    return card;
  }, "目前沒有符合的物品。");
  pages("public-pages", { page, has_more: result.has_more },
    (next) => publicSearch("text", next, fields));
}

function signedOut() {
  token = null;
  sessionStorage.removeItem("staff_token");
  $("workspace").hidden = true;
  $("login").hidden = false;
  newItem();
  $("staff-results").replaceChildren();
  $("staff-pages").replaceChildren();
}

async function signInView() {
  const account = await api("/auth/me", { privateRoute: true });
  $("identity").textContent = account.organization.name + " · " + account.username;
  for (const key of ["name", "address", "phone"]) {
    $("organization").elements.namedItem(key).value = account.organization[key];
  }
  $("login").hidden = true;
  $("workspace").hidden = false;
  await loadStaff(1);
}

async function loadStaff(page = staffPage) {
  const result = await api("/staff/items?page=" + page, { privateRoute: true });
  staffPage = page;
  listCards("staff-results", result.items, (item) => {
    const card = itemSummary(item);
    card.append(element("p", statusLabels[item.status]),
      button("管理物品", async () => {
        await openItem(item.id);
        $("item-form").scrollIntoView();
      }));
    return card;
  }, "本機構目前沒有拾獲物。");
  pages("staff-pages", result, loadStaff);
}

function newItem() {
  editing = null;
  $("item-form").reset();
  $("form-title").textContent = "建立拾獲物";
  $("item-form").elements.namedItem("photos").disabled = false;
  $("item-detail").replaceChildren();
}

async function changeItem(path, method, id) {
  await api(path, { method, privateRoute: true });
  if (editing === id) await openItem(id);
  await loadStaff();
}

async function openItem(id) {
  const path = "/staff/items/" + id;
  const item = await api(path, { privateRoute: true });
  editing = id;
  $("form-title").textContent = "編輯拾獲物";
  const form = $("item-form");
  for (const key of ["name", "category", "found_date", "found_location", "private_note"]) {
    form.elements.namedItem(key).value = item[key];
  }
  form.elements.namedItem("photos").value = "";
  form.elements.namedItem("photos").disabled = item.status !== "AVAILABLE";
  const card = element("article");
  card.append(element("p", "物品編號：" + item.reference),
    element("p", "目前狀態：" + statusLabels[item.status]));
  if (item.returned_at) {
    card.append(element("p", "歸還時間：" + new Date(item.returned_at).toLocaleString("zh-TW")),
      element("p", "歸還登記人帳號 ID：" + item.returned_by));
  }
  const controls = element("div");
  controls.className = "actions";
  controls.append(button("重新整理照片狀態", () => openItem(id)));
  if (item.status === "AVAILABLE") {
    controls.append(button("標記為已歸還", () => {
      if (confirm("確認物品已實際交還？")) return changeItem(path + "/return", "POST", id);
    }), button("下架", () => {
      if (confirm("確認將物品移出公開查詢？")) return changeItem(path + "/withdraw", "POST", id);
    }));
  }
  card.append(controls);
  for (const photo of item.images) {
    const photoPath = path + "/images/" + photo.id;
    const row = element("div");
    row.className = "actions";
    row.append(element("span", "照片 " + photo.id + " · " + statusLabels[photo.state] + (photo.is_cover ? " · 封面" : "")));
    if (photo.error) row.append(element("span", photo.error));
    row.append(button("查看照片", async () => {
      const image = element("img");
      const url = URL.createObjectURL(await api("/staff/images/" + photo.id, { privateRoute: true, blob: true }));
      image.src = url;
      image.alt = item.name;
      $("detail").replaceChildren(image);
      $("details").addEventListener("close", () => URL.revokeObjectURL(url), { once: true });
      $("details").showModal();
    }));
    if (!photo.is_cover) row.append(button("設為封面", () => changeItem(photoPath + "/cover", "PUT", id)));
    if (photo.state === "FAILED") row.append(button("重試", () => changeItem(photoPath + "/retry", "POST", id)));
    row.append(button("移除照片", () => {
      if (confirm("確認移除此照片？")) return changeItem(photoPath, "DELETE", id);
    }));
    card.append(row);
  }
  $("item-detail").replaceChildren(card);
}

$("close-details").onclick = () => $("details").close();

async function start() {
  if (location.pathname === "/staff") {
    $("staff").hidden = false;
    submit("login", async (form) => {
      const result = await api("/auth/login", { method: "POST", data: Object.fromEntries(new FormData(form)) });
      token = result.access_token;
      sessionStorage.setItem("staff_token", token);
      form.reset();
      await signInView();
    });
    $("logout").onclick = async () => {
      try { await api("/auth/logout", { method: "POST", privateRoute: true }); }
      catch (error) { notice(error.message, true); return; }
      signedOut();
      notice("已登出");
    };
    $("new-item").onclick = newItem;
    submit("organization", async (form) => {
      await api("/auth/organization", { method: "PUT", data: Object.fromEntries(new FormData(form)), privateRoute: true });
      await signInView();
      notice("機構資訊已更新");
    });
    submit("password", async (form) => {
      await api("/auth/password", { method: "PUT", data: Object.fromEntries(new FormData(form)), privateRoute: true });
      form.reset();
      signedOut();
      notice("密碼已更新，請重新登入");
    });
    submit("item-form", async (form) => {
      const fields = new FormData(form);
      const files = [...form.elements.namedItem("photos").files];
      fields.delete("photos");
      const idAtSubmit = editing;
      const item = await api(idAtSubmit ? "/staff/items/" + idAtSubmit : "/staff/items", {
        method: idAtSubmit ? "PUT" : "POST", data: Object.fromEntries(fields), privateRoute: true,
      });
      editing = item.id;
      const failures = [];
      for (const file of files) {
        const data = new FormData();
        data.set("file", file);
        try { await api("/staff/items/" + item.id + "/images", { method: "POST", data, privateRoute: true }); }
        catch (error) { failures.push(file.name + "：" + error.message); }
      }
      await openItem(item.id);
      await loadStaff(idAtSubmit ? staffPage : 1);
      if (failures.length) notice("物品已儲存，部分照片上傳失敗：" + failures.join("；"), true);
      else notice("物品已儲存");
    });
    if (token) await signInView();
  } else {
    $("public").hidden = false;
    submit("search", (_, submitter) => publicSearch(submitter?.value || "text"));
    const organizations = await api("/public/organizations");
    const selector = $("search").elements.namedItem("organization");
    for (const organization of organizations) selector.add(new Option(organization.name, organization.id));
    await publicSearch("text");
  }
}

start().catch((error) => notice(error.message, true));
