import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime

import streamlit as st
from web3 import Web3

# =========================================================
# KONFIGURASI
# =========================================================
RPC_URL = "http://127.0.0.1:8545"
CHAIN_ID = 31337

PROJECT_DIR = Path(__file__).resolve().parent
DEPLOYMENT_PATH = PROJECT_DIR / "deployment.json"

# Membaca alamat smart contract dari deployment.json
deployment_error = None

try:
    with DEPLOYMENT_PATH.open("r", encoding="utf-8") as f:
        deployment = json.load(f)

    if int(deployment["chainId"]) != CHAIN_ID:
        raise ValueError("Chain ID pada deployment.json tidak sesuai.")

    CONTRACT_ADDRESS = Web3.to_checksum_address(
        deployment["address"]
    )

except Exception as e:
    CONTRACT_ADDRESS = None
    deployment_error = str(e)

ABI_PATH = (
    PROJECT_DIR
    / "artifacts"
    / "contracts"
    / "LandRegistration.sol"
    / "LandRegistration.json"
)
FRONTEND_HOST = "127.0.0.1"
FRONTEND_PORT = 8502

st.set_page_config(
    page_title="Land Registration",
    page_icon="🏡",
    layout="wide",
)
if deployment_error:
    st.error(
        f"Gagal membaca deployment.json: {deployment_error}"
    )
    st.info(
        "Pastikan deployment.json tersedia dan lakukan deployment ulang jika diperlukan."
    )
    st.stop()

# =========================================================
# HALAMAN DAPP STANDALONE 
# =========================================================
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Land Registration DApp</title>
<script src="https://cdn.jsdelivr.net/npm/ethers@6.13.5/dist/ethers.umd.min.js"></script>
<style>
:root{font-family:Inter,Segoe UI,Arial,sans-serif;color:#17231c;background:#f5f8f6}
*{box-sizing:border-box}body{margin:0}.wrap{max-width:1120px;margin:auto;padding:28px 20px 50px}
header{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:20px}
.brand{font-size:24px;font-weight:800}.sub{color:#68766e;font-size:13px;margin-top:5px}
button{border:0;border-radius:9px;padding:11px 15px;background:#168653;color:white;font-weight:700;cursor:pointer}
button:hover{filter:brightness(.96)}button:disabled{opacity:.55;cursor:not-allowed}
.secondary{background:#e6f1eb;color:#17633f}.danger{background:#fff0ee;color:#a52d25}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0;border-bottom:1px solid #dce6df;padding-bottom:12px}
.tab{background:#e9efeb;color:#34483b}.tab.active{background:#168653;color:white}
.panel{display:none}.panel.active{display:block}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
.card{background:white;border:1px solid #e0e9e3;border-radius:14px;padding:18px;margin-bottom:14px;box-shadow:0 2px 8px #17231c08}
.card h3{font-size:16px;margin:0 0 12px}.metric{font-size:20px;font-weight:750;overflow-wrap:anywhere}
label{display:block;font-size:13px;font-weight:700;margin:12px 0 6px}
input{width:100%;padding:12px;border:1px solid #cbd8cf;border-radius:8px;font-size:14px;background:white}
input:focus{outline:2px solid #b9e2ca;border-color:#168653}
.document-section{margin-top:20px;padding:16px;border:1px solid #e0e9e3;border-radius:12px;background:#f9fbf9}
.document-section h3{margin:0 0 12px;font-size:16px}
.document-option{display:flex;align-items:flex-start;gap:10px;padding:12px;margin:9px 0;border:1px solid #dce6df;border-radius:9px;background:white;cursor:pointer}
.document-option input[type=checkbox]{width:17px;height:17px;margin:2px 0 0;flex:0 0 auto;accent-color:#168653}
.document-option span{display:block}
.document-option small{display:block;margin-top:5px;color:#68766e;font-weight:400;line-height:1.45}
.required-tag,.optional-tag{display:inline-block;margin-left:6px;padding:3px 7px;border-radius:20px;font-size:10px;font-weight:700;vertical-align:middle}
.required-tag{background:#fff0ee;color:#a52d25}
.optional-tag{background:#e6f6ec;color:#17633f}
.status{padding:12px 14px;border-radius:9px;background:#eef3ef;color:#45554a;margin:12px 0;font-size:13px;overflow-wrap:anywhere}
.ok{background:#e6f6ec;color:#17633f}.err{background:#fff0ee;color:#a52d25}.warn{background:#fff6e5;color:#80550d}
.muted{color:#68766e;font-size:13px;line-height:1.55}.small{font-size:12px;overflow-wrap:anywhere;color:#68766e}
.row{display:flex;gap:9px;flex-wrap:wrap;margin-top:12px}.kv{display:grid;grid-template-columns:145px 1fr;gap:9px;margin:9px 0;font-size:13px;overflow-wrap:anywhere}.kv b{color:#68766e}
code{overflow-wrap:anywhere}.hide{display:none}
@media(max-width:600px){.wrap{padding:18px 12px}.brand{font-size:20px}.kv{grid-template-columns:1fr;gap:3px}}
</style>
</head>
<body>
<div class="wrap">
<header>
 <div><div class="brand">🏡 Land Registration</div><div class="sub">Sistem registrasi dan perpindahan kepemilikan tanah berbasis blockchain</div></div>
 <button id="connect">Hubungkan MetaMask</button>
</header>
<div id="walletStatus" class="status">Wallet belum terhubung. Pastikan MetaMask aktif.</div>
<div id="roleInfo" class="muted">Hubungkan wallet untuk memeriksa hak akses.</div>

<nav class="tabs">
 <button class="tab active" data-tab="dashboard">Dashboard</button>
 <button class="tab" data-tab="register">Pendaftaran</button>
 <button class="tab" data-tab="verify">Verifikasi PPAT</button>
 <button class="tab" data-tab="certificate">Sertifikat BPN</button>
 <button class="tab" data-tab="sale">Jual Beli</button>
 <button class="tab" data-tab="lookup">Data Tanah</button>
 <button class="tab" data-tab="portfolio">Wallet NFT Portfolio</button>
</nav>

<section id="dashboard" class="panel active">
 <div class="grid">
  <div class="card"><h3>Jaringan</h3><div id="network" class="metric">Belum terhubung</div></div>
  <div class="card"><h3>Wallet Aktif</h3><div id="account" class="small">-</div></div>
  <div class="card"><h3>Peran Wallet</h3><div id="roles" class="metric">-</div></div>
 </div>
 <div class="card"><h3>Alur Sistem</h3><p class="muted">Pemilik mendaftarkan tanah → PPAT memverifikasi → BPN mencatat sertifikat dan mencetak NFT → pemilik dapat melakukan jual beli kepada pembeli baru.</p><p class="muted">Setiap transaksi meminta persetujuan melalui MetaMask. Gunakan jaringan Hardhat Local dengan Chain ID 31337.</p></div>
</section>

<section id="register" class="panel">
 <div class="card"><h3>📝 Pendaftaran Tanah</h3><p class="muted">Fungsi kontrak: AdaftarTanah(). Pendaftaran dapat dikirim oleh wallet mana pun sesuai aturan kontrak saat ini.</p>
 <label>ID Tanah</label><input id="regId" placeholder="Contoh: TNH001">
 <label>Alamat Wallet Pemilik</label><input id="regOwner" placeholder="0x...">
 <label>Luas Tanah (m²)</label><input id="regArea" type="number" min="1" placeholder="Contoh: 250">
 <label>Lokasi Tanah</label><input id="regLocation" placeholder="Desa, kecamatan, kabupaten">
 <div class="document-section">
  <h3>Dokumen Pendukung</h3>
  <label class="document-option"><input type="checkbox" id="ownershipProof"> <span><strong>Bukti Kepemilikan Tanah</strong> <span class="required-tag">Wajib</span><small>Centang jika bukti kepemilikan tanah tersedia.</small></span></label>
  <label class="document-option"><input type="checkbox" id="landMeasurement"> <span><strong>Surat Ukur / Gambar Bidang Tanah</strong> <span class="optional-tag">Opsional</span><small>Centang jika dokumen pengukuran atau gambar bidang tanah tersedia.</small></span></label>
  <p class="muted">Pernyataan ini digunakan sebagai kelengkapan administrasi simulasi. Dokumen tidak diunggah atau disimpan oleh aplikasi.</p>
 </div>
 <div class="row"><button id="registerBtn">Daftarkan Tanah</button></div><div id="registerMsg" class="status">Lengkapi data dan centang bukti kepemilikan tanah sebelum mendaftar.</div></div>
</section>

<section id="verify" class="panel">
 <div class="card"><h3>🔎 Verifikasi PPAT</h3><p class="muted">Fungsi BverifikasiTanah(). Hanya wallet yang sudah diberi peran PPAT yang dapat menjalankan proses ini.</p>
 <label>ID Tanah</label><input id="verifyId" placeholder="Contoh: TNH001"><div class="row"><button id="verifyBtn">Verifikasi Tanah</button></div><div id="verifyMsg" class="status">Status tanah harus TERDAFTAR.</div></div>
</section>

<section id="certificate" class="panel">
 <div class="card"><h3>📜 Pencatatan Sertifikat BPN</h3><p class="muted">Fungsi CcatatSertifikat(). Hanya wallet BPN yang berwenang. Proses ini mencetak NFT sertifikat untuk pemilik.</p>
 <label>ID Tanah</label><input id="certId" placeholder="Contoh: TNH001"><label>Nomor Sertifikat</label><input id="certNumber" placeholder="Contoh: SHM-001">
 <div class="row"><button id="certificateBtn">Catat Sertifikat</button></div><div id="certificateMsg" class="status">Status tanah harus TERVERIFIKASI.</div></div>
</section>

<section id="sale" class="panel">
 <div class="card"><h3>🤝 Jual Beli Tanah</h3><p class="muted">Fungsi DjualBeliTanah(). Hanya wallet pemilik saat ini yang dapat melakukan jual beli.</p>
 <label>ID Tanah</label><input id="saleId" placeholder="Contoh: TNH001"><label>Alamat Wallet Pembeli Baru</label><input id="buyer" placeholder="0x...">
 <div class="row"><button id="saleBtn">Proses Jual Beli</button></div><div id="saleMsg" class="status">Tanah harus berstatus BERSERTIFIKAT.</div></div>
</section>

<section id="lookup" class="panel">
 <div class="card"><h3>📂 Data Tanah</h3><label>ID Tanah</label><input id="lookupId" placeholder="Contoh: TNH001">
 <div class="row"><button id="lookupBtn" class="secondary">Cari Data Tanah</button></div><div id="lookupMsg" class="status">Masukkan ID tanah untuk membaca data dari blockchain.</div><div id="landData"></div></div>
</section>

<section id="portfolio" class="panel">
 <div class="card">
  <h3>👛 Wallet NFT Portfolio</h3>
  <p class="muted">Lihat jumlah dan daftar NFT sertifikat tanah yang saat ini dimiliki suatu wallet. Data dibaca langsung dari blockchain.</p>
  <label>Alamat Wallet</label>
  <input id="portfolioAddress" placeholder="Kosongkan untuk menggunakan wallet aktif">
  <div class="row">
   <button id="portfolioCurrent" class="secondary">Gunakan Wallet Aktif</button>
   <button id="portfolioSearch">Lihat Portfolio</button>
  </div>
  <div id="portfolioMsg" class="status">Hubungkan MetaMask atau masukkan alamat wallet yang ingin diperiksa.</div>
  <div id="portfolioSummary"></div>
  <div id="portfolioList"></div>
 </div>
</section>
</div>

<script>
const ABI = __ABI__;
const CONTRACT_ADDRESS = "__ADDRESS__";
let provider, signer, account, contract;
const $ = id => document.getElementById(id);
function message(id,text,type=""){const el=$(id);el.className="status "+type;el.textContent=text;}
function shortAddress(a){return a?a.slice(0,8)+"..."+a.slice(-6):"-";}
function escapeHtml(v){return String(v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));}
function showTab(name){document.querySelectorAll(".panel").forEach(p=>p.classList.toggle("active",p.id===name));document.querySelectorAll(".tab").forEach(b=>b.classList.toggle("active",b.dataset.tab===name));}
document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>showTab(b.dataset.tab)));

async function connectWallet(){
 try{
  if(!window.ethereum)throw new Error("MetaMask tidak terdeteksi. Buka halaman ini di Chrome/Brave dengan ekstensi MetaMask aktif.");
  if(typeof ethers==="undefined")throw new Error("Library ethers.js gagal dimuat. Periksa koneksi internet lalu muat ulang halaman.");
  const accounts=await window.ethereum.request({method:"eth_requestAccounts"});
  if(!accounts.length)throw new Error("Tidak ada akun MetaMask yang dipilih.");
  provider=new ethers.BrowserProvider(window.ethereum);
  signer=await provider.getSigner();account=await signer.getAddress();
  const network=await provider.getNetwork();
  contract=new ethers.Contract(CONTRACT_ADDRESS,ABI,signer);
  $("account").textContent=account;$("network").textContent="Chain ID "+network.chainId.toString();
  if(network.chainId!==31337n){
   message("walletStatus","Wallet terdeteksi, tetapi jaringan salah. Pilih Hardhat Local (Chain ID 31337).","warn");
   $("roles").textContent="-";return;
  }
  const [admin,ppat,bpn]=await Promise.all([contract.admin(),contract.isPPAT(account),contract.isBPN(account)]);
  const roles=[];if(account.toLowerCase()===admin.toLowerCase())roles.push("Admin");if(ppat)roles.push("PPAT");if(bpn)roles.push("BPN");if(!roles.length)roles.push("Pemilik/Pengguna");
  $("roles").textContent=roles.join(", ");$("roleInfo").textContent="Wallet aktif: "+shortAddress(account)+" · "+roles.join(", ");
  message("walletStatus","MetaMask berhasil terhubung dan jaringan sesuai.","ok");
 }catch(e){message("walletStatus",e.shortMessage||e.message||String(e),"err");}
}
$("connect").addEventListener("click",connectWallet);

async function ensureReady(){
 if(!window.ethereum)throw new Error("MetaMask tidak terdeteksi.");
 if(!contract||!account)await connectWallet();
 if(!contract||!account)throw new Error("Hubungkan MetaMask terlebih dahulu.");
 const net=await provider.getNetwork();
 if(net.chainId!==31337n)throw new Error("Pilih jaringan Hardhat Local (Chain ID 31337) di MetaMask.");
}
async function sendTransaction(method,args,msgId){
 try{
  await ensureReady();
  message(msgId,"Menyiapkan transaksi...");
  const tx=await contract[method](...args);
  message(msgId,"Transaksi dikirim: "+tx.hash+". Menunggu konfirmasi...");
  const receipt=await tx.wait();
  message(msgId,"Transaksi berhasil! Block: "+receipt.blockNumber+" · Hash: "+tx.hash,"ok");
  return true;
 }catch(e){
  message(msgId,e.shortMessage||e.reason||e.message||String(e),"err");
  return false;
 }
}

// Metadata checkbox disimpan di browser, bukan di blockchain.
function saveDocumentChecklist(landId,ownershipProof,landMeasurement){
 const all=JSON.parse(localStorage.getItem("landDocumentChecklist")||"{}");
 all[landId]={ownershipProof,landMeasurement};
 localStorage.setItem("landDocumentChecklist",JSON.stringify(all));
}
function getDocumentChecklist(landId){
 const all=JSON.parse(localStorage.getItem("landDocumentChecklist")||"{}");
 return all[landId]||null;
}
$("registerBtn").addEventListener("click",async()=>{
 const id=$("regId").value.trim(),owner=$("regOwner").value.trim(),area=$("regArea").value,loc=$("regLocation").value.trim();
 const ownershipProof=$("ownershipProof").checked;
 if(!ownershipProof){message("registerMsg","Bukti Kepemilikan Tanah wajib dicentang sebelum pendaftaran.","err");return;}
 if(!id||!owner||!area||!loc||Number(area)<=0){message("registerMsg","Lengkapi semua data. Luas harus lebih dari 0.","err");return;}
 if(!ethers.isAddress(owner)){message("registerMsg","Alamat wallet pemilik tidak valid.","err");return;}
 const landMeasurement=$("landMeasurement").checked;
 const success=await sendTransaction("AdaftarTanah",[id,owner,BigInt(area),loc],"registerMsg");
 if(success){
  try{
   saveDocumentChecklist(id,ownershipProof,landMeasurement);
   message("registerMsg","Tanah berhasil didaftarkan. Status dokumen pendukung tersimpan untuk ditampilkan pada Data Tanah.","ok");
  }catch(storageError){
   message("registerMsg","Transaksi berhasil, tetapi status checklist tidak dapat disimpan di browser: "+storageError.message,"warn");
  }
 }
});
$("verifyBtn").addEventListener("click",async()=>{const id=$("verifyId").value.trim();if(!id){message("verifyMsg","Masukkan ID tanah.","err");return;}await sendTransaction("BverifikasiTanah",[id],"verifyMsg");});
$("certificateBtn").addEventListener("click",async()=>{const id=$("certId").value.trim(),num=$("certNumber").value.trim();if(!id||!num){message("certificateMsg","ID tanah dan nomor sertifikat wajib diisi.","err");return;}await sendTransaction("CcatatSertifikat",[id,num],"certificateMsg");});
$("saleBtn").addEventListener("click",async()=>{const id=$("saleId").value.trim(),buyer=$("buyer").value.trim();if(!id||!buyer){message("saleMsg","ID tanah dan wallet pembeli wajib diisi.","err");return;}if(!ethers.isAddress(buyer)){message("saleMsg","Alamat wallet pembeli tidak valid.","err");return;}await sendTransaction("DjualBeliTanah",[id,buyer],"saleMsg");});
$("lookupBtn").addEventListener("click",async()=>{
 try{await ensureReady();const id=$("lookupId").value.trim();if(!id)throw new Error("Masukkan ID tanah.");
 const t=await contract.dataTanah(id);if(BigInt(t.luas)===0n)throw new Error("Data tanah tidak ditemukan.");
 const nftOwner=BigInt(t.tokenId)>0n?await contract.ownerOf(t.tokenId):"-";
 $("landData").innerHTML='<div class="card">'+
 '<div class="kv"><b>ID Tanah</b><span>'+escapeHtml(t.idTanah)+'</span></div>'+
 '<div class="kv"><b>Pemilik</b><span>'+escapeHtml(t.pemilik)+'</span></div>'+
 '<div class="kv"><b>Luas</b><span>'+t.luas.toString()+' m²</span></div>'+
 '<div class="kv"><b>Lokasi</b><span>'+escapeHtml(t.lokasi)+'</span></div>'+
 '<div class="kv"><b>Status</b><span>'+escapeHtml(t.status)+'</span></div>'+
 '<div class="kv"><b>No. Sertifikat</b><span>'+escapeHtml(t.nomorSertifikat||"-")+'</span></div>'+
 '<div class="kv"><b>Token ID</b><span>'+t.tokenId.toString()+'</span></div>'+
 '<div class="kv"><b>Pemilik NFT</b><span>'+escapeHtml(nftOwner)+'</span></div></div>';
 const documents=getDocumentChecklist(id);
 let documentHtml='<div class="card"><h3>📎 Dokumen Pendukung</h3>';
 if(documents){
  documentHtml+='<div class="kv"><b>Bukti Kepemilikan Tanah</b><span>'+(documents.ownershipProof?'Tersedia (dinyatakan saat pendaftaran)':'Tidak dilampirkan')+'</span></div>'+
   '<div class="kv"><b>Surat Ukur / Gambar Bidang Tanah</b><span>'+(documents.landMeasurement?'Tersedia (dinyatakan saat pendaftaran)':'Tidak dilampirkan')+'</span></div>';
 }else{
  documentHtml+='<p class="muted">Informasi checklist dokumen tidak tersedia di browser ini. Tanah mungkin didaftarkan sebelum fitur checklist ditambahkan atau menggunakan browser/perangkat lain.</p>';
 }
 $("landData").innerHTML+=documentHtml;
 message("lookupMsg","Data tanah berhasil dibaca dari blockchain.","ok");
 }catch(e){$("landData").innerHTML="";message("lookupMsg",e.shortMessage||e.reason||e.message||String(e),"err");}
});
async function loadPortfolio(){
 try{
  await ensureReady();  
  const target=$("portfolioAddress").value.trim()||account;
  if(!ethers.isAddress(target))throw new Error("Alamat wallet tidak valid.");
  const wallet=ethers.getAddress(target);
  message("portfolioMsg","Membaca jumlah NFT dan riwayat penerbitan sertifikat...");
  $("portfolioSummary").innerHTML="";
  $("portfolioList").innerHTML="";

  const total=await contract.balanceOf(wallet);
  const events=await contract.queryFilter(contract.filters.SertifikatDicatat(),0,"latest");
  const tokenIds=[...new Set(events.map(ev=>ev.args.tokenId.toString()))];
  const owned=[];

  for(const tokenText of tokenIds){
   const tokenId=BigInt(tokenText);
   try{
    const currentOwner=await contract.ownerOf(tokenId);
    if(currentOwner.toLowerCase()!==wallet.toLowerCase())continue;
    const ev=events.find(item=>item.args.tokenId.toString()===tokenText);
    const landId=ev.args.idTanah;
    const land=await contract.dataTanah(landId);
    owned.push({
     tokenId:tokenText,
     landId:land.idTanah,
     area:land.luas.toString(),
     location:land.lokasi,
     status:land.status,
     certificate:land.nomorSertifikat,
     owner:currentOwner
    });
   }catch(readError){
    console.warn("Token tidak dapat dibaca:",tokenText,readError);
   }
  }

  owned.sort((a,b)=>BigInt(a.tokenId)<BigInt(b.tokenId)?-1:1);
  $("portfolioSummary").innerHTML=
   '<div class="grid">'+
   '<div class="card"><h3>Total NFT pada wallet</h3><div class="metric">'+total.toString()+'</div></div>'+
   '<div class="card"><h3>Detail NFT ditemukan</h3><div class="metric">'+owned.length+'</div></div>'+
   '</div>'+
   '<div class="card"><div class="kv"><b>Alamat wallet</b><span>'+escapeHtml(wallet)+'</span></div></div>';

  if(owned.length===0){
   $("portfolioList").innerHTML='<div class="status">Wallet ini belum memiliki NFT sertifikat tanah, atau belum ditemukan riwayat penerbitannya.</div>';
  }else{
   $("portfolioList").innerHTML=owned.map(item=>
    '<div class="card">'+
    '<h3>🏡 NFT Sertifikat #'+escapeHtml(item.tokenId)+'</h3>'+
    '<div class="kv"><b>ID Tanah</b><span>'+escapeHtml(item.landId)+'</span></div>'+
    '<div class="kv"><b>Token ID</b><span>'+escapeHtml(item.tokenId)+'</span></div>'+
    '<div class="kv"><b>Luas Tanah</b><span>'+escapeHtml(item.area)+' m²</span></div>'+
    '<div class="kv"><b>Lokasi</b><span>'+escapeHtml(item.location)+'</span></div>'+
    '<div class="kv"><b>Status</b><span>'+escapeHtml(item.status)+'</span></div>'+
    '<div class="kv"><b>No. Sertifikat</b><span>'+escapeHtml(item.certificate||"-")+'</span></div>'+
    '<div class="kv"><b>Pemilik NFT</b><span>'+escapeHtml(item.owner)+'</span></div>'+
    '</div>'
   ).join("");
  }
  message("portfolioMsg","Portfolio berhasil dibaca dari blockchain.","ok");
 }catch(e){
  $("portfolioSummary").innerHTML="";
  $("portfolioList").innerHTML="";
  message("portfolioMsg",e.shortMessage||e.reason||e.message||String(e),"err");
 }
}
$("portfolioSearch").addEventListener("click",loadPortfolio);
$("portfolioCurrent").addEventListener("click",()=>{
 if(account)$("portfolioAddress").value=account;
 else message("portfolioMsg","Hubungkan MetaMask terlebih dahulu.","warn");
});

if(window.ethereum){
 window.ethereum.on("accountsChanged",()=>{account=null;contract=null;message("walletStatus","Akun berubah. Hubungkan kembali wallet.","warn");$("account").textContent="-";$("roles").textContent="-";});
 window.ethereum.on("chainChanged",()=>{account=null;contract=null;message("walletStatus","Jaringan berubah. Hubungkan kembali wallet.","warn");$("network").textContent="Belum terhubung";});
}
</script>
</body></html>"""

def build_html(abi):
    return HTML_TEMPLATE.replace("__ABI__", json.dumps(abi)).replace(
        "__ADDRESS__", Web3.to_checksum_address(CONTRACT_ADDRESS)
    )

@st.cache_resource
def start_frontend_server(page_html):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = page_html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer((FRONTEND_HOST, FRONTEND_PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

# =========================================================
# DASHBOARD STREAMLIT
# =========================================================
st.title("🏡 Land Registration System")
st.caption("Dashboard blockchain untuk registrasi, verifikasi, sertifikat, dan jual beli tanah.")

w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 4}))
rpc_connected = w3.is_connected()

col1, col2, col3 = st.columns(3)
with col1:
    if rpc_connected:
        st.success("Hardhat: Terhubung")
    else:
        st.error("Hardhat: Tidak terhubung")
with col2:
    st.metric("Chain ID", w3.eth.chain_id if rpc_connected else "-")
with col3:
    st.metric("Block Terbaru", w3.eth.block_number if rpc_connected else "-")

st.write("**RPC URL**")
st.code(RPC_URL)
st.write("**Alamat Smart Contract**")
st.code(CONTRACT_ADDRESS)

if not ABI_PATH.exists():
    st.error("ABI belum ditemukan. Jalankan `npx hardhat compile` dari folder project.")
    st.stop()

with ABI_PATH.open("r", encoding="utf-8") as f:
    artifact = json.load(f)
abi = artifact["abi"]

if not rpc_connected:
    st.warning("Jalankan `npx hardhat node` pada terminal lain. Frontend tetap dapat disiapkan setelah node aktif.")
    st.stop()

contract_read = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=abi,
)



def get_land_history(contract, w3, land_id):
    """
    Membaca riwayat kepemilikan tanah
    berdasarkan event blockchain.
    """

    history = []

    # Membaca event pendaftaran
    registrations = contract.events.TanahDidaftarkan.get_logs(
        from_block=0,
        to_block="latest"
    )

    for event in registrations:
        args = event["args"]

        if args["idTanah"] == land_id:
            block_number = event["blockNumber"]
            block = w3.eth.get_block(block_number)

            history.append({
                "block": block_number,
                "log_index": event["logIndex"],
                "Aktivitas": "Pendaftaran Tanah",
                "Pemilik Sebelumnya": "-",
                "Pemilik Baru": args["pemilik"],
                "Waktu": datetime.fromtimestamp(
                    block["timestamp"]
                ).strftime("%d-%m-%Y %H:%M:%S"),
                "Transaction Hash": event["transactionHash"].hex()
            })

    # Membaca event jual beli
    sales = contract.events.TanahDijual.get_logs(
        from_block=0,
        to_block="latest"
    )

    for event in sales:
        args = event["args"]

        if args["idTanah"] == land_id:
            block_number = event["blockNumber"]
            block = w3.eth.get_block(block_number)

            history.append({
                "block": block_number,
                "log_index": event["logIndex"],
                "Aktivitas": "Peralihan Kepemilikan",
                "Pemilik Sebelumnya": args["pemilikLama"],
                "Pemilik Baru": args["pembeliBaru"],
                "Waktu": datetime.fromtimestamp(
                    block["timestamp"]
                ).strftime("%d-%m-%Y %H:%M:%S"),
                "Transaction Hash": event["transactionHash"].hex()
            })

    # Mengurutkan berdasarkan block dan posisi log
    history.sort(
        key=lambda item: (item["block"], item["log_index"])
    )

    # Menghapus kolom internal pengurutan
    for item in history:
        item.pop("block")
        item.pop("log_index")
        
    return history

if not w3.eth.get_code(contract_read.address):
    st.error("Smart contract tidak ditemukan pada alamat tersebut. Periksa alamat atau lakukan deployment ulang.")
    st.stop()

st.success("Smart contract LandRegistration ditemukan di blockchain lokal.")


# =========================================================
# OWNERSHIP HISTORY
# =========================================================
st.divider()
st.subheader("📜 Ownership History")
st.caption(
    "Telusuri riwayat perpindahan kepemilikan tanah "
    "berdasarkan catatan transaksi blockchain."
)

land_id_search = st.text_input(
    "Masukkan ID Tanah",
    placeholder="Contoh: TNH001",
    key="history_land_id"
)

if st.button("Cari Riwayat Kepemilikan"):
    if not land_id_search.strip():
        st.warning("Masukkan ID tanah terlebih dahulu.")
    else:
        try:
            history_data = get_land_history(
                contract_read,
                w3,
                land_id_search.strip()
            )

            if history_data:
                st.success(
                    f"Ditemukan {len(history_data)} catatan riwayat."
                )

                st.dataframe(
                    history_data,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info(
                    "Belum ditemukan riwayat untuk ID tanah tersebut."
                )

        except Exception as e:
            st.error(f"Gagal membaca riwayat: {e}")

try:
    frontend_url = f"http://127.0.0.1:{FRONTEND_PORT}"
    start_frontend_server(build_html(abi))
    st.subheader("Aplikasi DApp")
    st.markdown(
        f'<a href="{frontend_url}" target="_blank" '
        'style="display:inline-block;background:#168653;color:white;'
        'padding:12px 18px;border-radius:9px;text-decoration:none;font-weight:700">'
        'Buka Frontend Land Registration ↗</a>',
        unsafe_allow_html=True,
    )
    st.caption("Frontend dibuka sebagai halaman browser biasa, bukan iframe. Karena itu MetaMask dapat terdeteksi langsung.")
except OSError as e:
    st.error(f"Tidak dapat menjalankan frontend pada port {FRONTEND_PORT}: {e}")
    st.info("Pastikan port 8502 tidak sedang dipakai aplikasi lain.")

st.divider()
st.subheader("Alur dan aturan hak akses")
st.markdown(
    """
    1. **Pendaftaran:** wallet pengguna mendaftarkan ID tanah, alamat pemilik, luas, dan lokasi.
    2. **Verifikasi:** hanya wallet yang diberi peran PPAT.
    3. **Pencatatan sertifikat:** hanya wallet yang diberi peran BPN; kontrak mencetak NFT sertifikat.
    4. **Jual beli:** hanya pemilik tanah saat ini yang dapat mengalihkan kepemilikan.
    """
)
st.warning(
    "Catatan: Hardhat Local hanya untuk pengujian. Jangan gunakan private key akun Hardhat "
    "pada jaringan publik atau untuk menyimpan aset sungguhan."
)
