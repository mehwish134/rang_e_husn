const cart = new Map();
const countEl = document.getElementById("cartCount");
const itemsEl = document.getElementById("cartItems");
const totalEl = document.getElementById("cartTotal");
const dataEl = document.getElementById("cartData");
function renderCart() {
  if (!countEl || !itemsEl || !totalEl || !dataEl) return;
  const items = [...cart.values()];
  countEl.textContent = items.reduce((s, i) => s + i.qty, 0);
  const total = items.reduce((s, i) => s + i.price * i.qty, 0);
  totalEl.textContent = "Rs. " + total.toLocaleString("en-PK");
  dataEl.value = JSON.stringify(items.map(i => ({id:i.id, qty:i.qty})));
  itemsEl.replaceChildren();
  if (!items.length) { itemsEl.textContent = "Your cart is empty."; return; }
  items.forEach(item => {
    const row = document.createElement("div"); row.className = "cart-row";
    const label = document.createElement("span");
    label.textContent = `${item.name} × ${item.qty} — Rs. ${(item.price*item.qty).toLocaleString("en-PK")}`;
    const remove = document.createElement("button"); remove.type = "button"; remove.className = "remove-item"; remove.textContent = "Remove";
    remove.addEventListener("click", () => { cart.delete(item.id); renderCart(); });
    row.append(label, remove); itemsEl.appendChild(row);
  });
}
document.querySelectorAll(".add-btn").forEach(btn => btn.addEventListener("click", () => {
  const id = Number(btn.dataset.id), stock = Number(btn.dataset.stock || 999);
  const old = cart.get(id);
  if (old && old.qty >= stock) { alert("This is the available stock limit."); return; }
  if (old) old.qty += 1;
  else cart.set(id, {id, name:btn.dataset.name, price:Number(btn.dataset.price), qty:1});
  renderCart(); btn.textContent = "Added ✓"; setTimeout(()=>btn.textContent="Add +",800);
}));
const checkoutForm = document.getElementById("checkoutForm");
if (checkoutForm) checkoutForm.addEventListener("submit", e => {
  if (!cart.size) { e.preventDefault(); alert("Please add a product to your cart first."); }
});
const toggle = document.getElementById("menuToggle"), nav = document.getElementById("navLinks");
if (toggle && nav) { toggle.addEventListener("click",()=>nav.classList.toggle("open")); nav.querySelectorAll("a").forEach(a=>a.addEventListener("click",()=>nav.classList.remove("open"))); }
const year = document.getElementById("year"); if (year) year.textContent = new Date().getFullYear();
const dateInput = document.getElementById("appointmentDate");
if (dateInput) { const now = new Date(); dateInput.min = new Date(now.getTime()-now.getTimezoneOffset()*60000).toISOString().split("T")[0]; }
document.querySelectorAll(".show-items").forEach(btn => btn.addEventListener("click", () => {
  const script = btn.parentElement.querySelector(".order-items");
  try { const items = JSON.parse(script.textContent); alert(items.map(i=>`${i.name} x ${i.qty} — Rs. ${Number(i.line_total).toLocaleString("en-PK")}`).join("\n")); }
  catch { alert("Order item details are unavailable."); }
}));
renderCart();
