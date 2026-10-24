/* Copyright (c) 2026 Min SiThu (itsmeminsithu). MIT. */
(()=>{'use strict';
const products=JSON.parse(document.getElementById('catalog-data').textContent),stocks=JSON.parse(document.getElementById('stock-data').textContent);
const $=id=>document.getElementById(id),cart=new Map();let category='All',pending=null,inflight=false;
const storageKey='mm-pos-checkout-'+$('warehouse').options[0]?.value;
const uid=()=>crypto.randomUUID();let requestKey=uid();
const cash=n=>(n/100).toFixed(2),cents=n=>Math.round(Number(n)*100);
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n}
function available(id){return stocks.find(s=>s.product_id===id&&String(s.warehouse_id)===$('warehouse').value)?.quantity||0}
function error(message){$('pos-error').textContent=message;$('pos-error').hidden=!message}
function lock(value){document.body.classList.toggle('busy',value);document.querySelectorAll('.basket input,.basket select,.pos-controls input,.pos-controls select,#clear-cart').forEach(n=>n.disabled=value);$('checkout-button').textContent=value?'Retry same sale →':'Complete sale →'}
function changed(){if(pending)return;requestKey=uid();renderCart()}
function add(p){if(pending)return;if((cart.get(p.id)||0)>=available(p.id)){error('No more stock available for '+p.name+'.');return}cart.set(p.id,(cart.get(p.id)||0)+1);error('');changed()}
function renderProducts(){const root=$('product-grid');root.replaceChildren();const query=$('product-search').value.toLowerCase().trim();const list=products.filter(p=>(category==='All'||p.category===category)&&[p.name,p.sku,p.barcode].some(s=>s.toLowerCase().includes(query)));
 for(const p of list){const button=el('button','product-tile');button.type='button';button.disabled=available(p.id)===0||Boolean(pending);button.append(el('span','tile-art',p.name.slice(0,1)),el('strong','',p.name),el('small','',p.sku+' · '+available(p.id)+' in stock'),el('b','',cash(cents(p.price))));button.addEventListener('click',()=>add(p));root.append(button)}if(!list.length)root.append(el('p','empty','No matching products. Add products from the product library.'))}
function renderCart(){const root=$('cart-lines');root.replaceChildren();let subtotal=0;
 for(const [id,qty]of cart){const p=products.find(p=>p.id===id);if(!p)continue;subtotal+=cents(p.price)*qty;const row=el('div','cart-line'),copy=el('div');copy.append(el('strong','',p.name),el('small','',cash(cents(p.price)*qty)));const controls=el('div','quantity-controls');for(const delta of [-1,1]){const button=el('button','',delta<0?'−':'+');button.type='button';button.disabled=Boolean(pending);button.setAttribute('aria-label',(delta<0?'Remove one ':'Add one ')+p.name);button.addEventListener('click',()=>{if(pending)return;if(delta>0){add(p);return}if(qty===1)cart.delete(id);else cart.set(id,qty-1);changed()});controls.append(button);if(delta<0)controls.append(el('span','',qty))}row.append(copy,controls);root.append(row)}
 if(!cart.size)root.append(el('div','empty','Choose a product to start this sale.'));
 const discount=cents($('discount').value||0),rate=cents($('tax').value||0),tax=Math.round((subtotal-discount)*rate/10000),total=subtotal-discount+tax;
 $('subtotal').textContent=cash(subtotal);$('tax-total').textContent=cash(tax);$('total').textContent=cash(total);
}
for(const name of ['All',...new Set(products.map(p=>p.category))]){const button=el('button',name==='All'?'active':'',name);button.type='button';button.onclick=()=>{category=name;document.querySelectorAll('#categories button').forEach(b=>b.classList.toggle('active',b===button));renderProducts()};$('categories').append(button)}
$('product-search').addEventListener('input',renderProducts);
$('product-search').addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();const query=event.target.value.trim();const found=products.filter(p=>p.barcode===query||p.sku===query);if(found.length===1){add(found[0]);event.target.value='';renderProducts()}else error(found.length>1?'Barcode matches multiple products. Choose the correct item.':'No exact barcode or SKU match.')}});
$('warehouse').onchange=()=>{cart.clear();changed();renderProducts()};$('clear-cart').onclick=()=>{if(!pending){cart.clear();error('');changed()}};
for(const id of ['discount','tax','tendered','customer','reference'])$(id).addEventListener('input',changed);
function paymentFields(){const isCash=$('payment').value==='cash';$('cash-label').hidden=!isCash;$('reference-label').hidden=isCash}
$('payment').onchange=()=>{paymentFields();changed()};
try{pending=JSON.parse(sessionStorage.getItem(storageKey)||'null')}catch{pending=null}
if(pending){$('warehouse').value=String(pending.warehouse);$('customer').value=pending.customer||'';$('discount').value=pending.discount;$('tax').value=pending.tax_rate;$('payment').value=pending.method;$('tendered').value=pending.tendered;$('reference').value=pending.reference;for(const item of pending.items)cart.set(item.id,item.quantity);lock(true);error('A previous checkout is awaiting confirmation. Retry the same sale; do not collect payment again. Check Sales & receipts if it was already recorded.');}
$('checkout-form').addEventListener('submit',async event=>{event.preventDefault();if(inflight)return;if(!pending){if(!cart.size){error('Add a product first.');return}pending={request_key:requestKey,warehouse:$('warehouse').value,customer:$('customer').value,items:[...cart].map(([id,quantity])=>({id,quantity,expected_price:products.find(p=>p.id===id).price})),discount:$('discount').value,tax_rate:$('tax').value,method:$('payment').value,tendered:$('tendered').value,reference:$('reference').value};try{sessionStorage.setItem(storageKey,JSON.stringify(pending))}catch{} }
 inflight=true;lock(true);$('checkout-button').disabled=true;error('');
 try{const response=await fetch('/api/checkout/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]').value},body:JSON.stringify(pending),redirect:'error'});let data;try{data=await response.json()}catch{throw new Error('Unable to read checkout confirmation. Check receipts and retry this same sale.')}
 if(response.ok){sessionStorage.removeItem(storageKey);location.href=data.receipt;return}
 if(response.status===400){pending=null;sessionStorage.removeItem(storageKey);lock(false);requestKey=uid();renderProducts();renderCart()}
 error(data.error||'Checkout could not be confirmed. Retry this same sale.');
 }catch(e){error('Connection interrupted. Retry this same sale to confirm it without duplicating it. Do not collect payment again.')}
 finally{inflight=false;$('checkout-button').disabled=false}
});paymentFields();renderProducts();renderCart();
})();
