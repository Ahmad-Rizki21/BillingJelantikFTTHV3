---
title: Billing System x Payment Xendit
---
&nbsp;

<p align="center"><img src="/.swm/images/image-2025-7-17-15-20-35-478.png"></p>

## **Billing System V2**

Selamat datang! Ini adalah panduan lengkap yang dirancang untuk membantu Anda memahami, menggunakan, dan mengembangkan sistem billing ini secara efisien.

Di dalam dokumentasi ini, Anda akan menemukan:

- **Penjelasan Alur Kerja**: Panduan mendalam tentang proses bisnis utama, mulai dari pendaftaran pelanggan hingga penagihan dan suspensi otomatis.

- **Referensi API**: Detail setiap endpoint, termasuk *request body*, parameter, dan contoh respons.

- **Struktur Database**: Penjelasan setiap tabel dan relasinya dalam bentuk diagram dan tabel.

- **Panduan Konfigurasi**: Penjelasan lengkap tentang variabel lingkungan (`.env`) dan cara menyiapkan proyek.

&nbsp;

&nbsp;================================================================================================

&nbsp;

File `.env` ini adalah **brankas** atau **ruang rahasia** untuk aplikasi Anda. Tujuannya adalah untuk menyimpan semua informasi sensitif dan konfigurasi penting di satu tempat yang aman, terpisah dari kode utama.

> **PERINGATAN KEAMANAN PENTING** 🚨 File `.env` ini **TIDAK BOLEH** diunggah ke GitHub atau repositori publik lainnya. Pastikan nama file `.env` sudah ada di dalam file `.gitignore` Anda untuk mencegah kebocoran data sensitif.

&nbsp;

### **Penjelasan Variabel**

&nbsp;

Berikut adalah penjelasan untuk setiap variabel yang ada di dalam file `.env` Anda:

| Variabel                  | Contoh Isi                            | Deskripsi                                                                                                                                     |
| ------------------------- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `DATABASE_URL`            | `mysql+aiomysql://root:@localhost...` | Alamat lengkap untuk menyambung ke database. Berisi username, password, host, dan nama database.                                              |
| `XENDIT_API_URL`          | `https://api.xendit.co/...`           | Alamat server API Xendit yang menjadi tujuan semua permintaan terkait pembayaran.                                                             |
| `XENDIT_API_KEY_JAKINET`  | `xnd_development_...`                 | Kunci rahasia (seperti password) untuk mengakses API Xendit atas nama brand **Jakinet**.                                                      |
| `XENDIT_API_KEY_JELANTIK` | `xnd_development_...`                 | Kunci rahasia untuk mengakses API Xendit atas nama brand **Jelantik**.                                                                        |
| `XENDIT_CALLBACK_TOKEN`   | `TOKENRAHASIA`                        | Kode rahasia yang digunakan untuk memverifikasi bahwa notifikasi pembayaran (callback) benar-benar datang dari Xendit, bukan dari pihak lain. |

### **Cara Penggunaan**

Biasanya, di dalam proyek akan ada file bernama `.env.example` yang berisi daftar variabel yang dibutuhkan, tetapi dengan isi yang kosong.

1. **Salin** file `.env.example`.

2. **Ubah namanya** menjadi `.env`.

3. **Isi semua nilainya** sesuai dengan konfigurasi lokal (untuk development) atau konfigurasi server (untuk produksi)

<SwmSnippet path="/.env.example" line="1">

---

&nbsp;

```example
DATABASE_URL="mysql+aiomysql://root:@localhost:3306/DATABASE_ANDA"

# API
XENDIT_API_URL="https://api.xendit.co/bla-bla-bla"
XENDIT_API_KEY_JAKINET="xnd_development_"
XENDIT_API_KEY_JELANTIK="xnd_development_"
# Callback
XENDIT_CALLBACK_TOKEN="TOKEN"
```

---

</SwmSnippet>

&nbsp;

---

\### \*\*Fungsi Kode: Memberi Izin Akses (Daftar Tamu API)\*\*

Kode ini fungsinya untuk memberi izin ke aplikasi Frontend (VueJS) kita supaya bisa "ngobrol" dengan aplikasi Backend (FastAPI).

Tanpa kode ini, Frontend kamu bakal ditolak mentah-mentah oleh browser karena alasan keamanan. Jadi, kita perlu mendaftarkan alamat Frontend kita sebagai "tamu yang dipercaya".

\#### \*\*Daftar Tamu yang Diizinkan `origins`):\*\*

\* `http://localhost:3000`: Ini adalah alamat yang kita pakai saat menjalankan VueJS di laptop untuk testing.

\* `tauri://localhost`: Ini alamat khusus kalau nanti aplikasi kita diubah jadi aplikasi desktop pakai Tauri.

\* `# https://billingftth.my.id`: Ini adalah contoh alamat website kita kalau sudah online beneran. Tanda pagar `#` artinya untuk sekarang baris ini tidak dipakai.

\*\*Intinya:\*\* Kalau ada permintaan data dari salah satu alamat di atas, backend kita akan menerimanya. Kalau dari alamat lain, akan ditolak.

<SwmSnippet path="app/main.py" line="59">

---

[Main.py](http://Main.py)

```python
origins = [
    
    # "http://192.168.222.20",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "tauri://localhost",
    # "http://tauri.localhost"
]
```

---

</SwmSnippet>

### **Daftar Tugas Saat Server Dinyalakan**

Kode ini berisi serangkaian perintah yang dijalankan **hanya satu kali**, tepat saat aplikasi server pertama kali dihidupkan. Anggap saja ini seperti daftar persiapan otomatis sebelum server siap bekerja.

#### **Urutan Tugasnya:**

1. **Menyiapkan Pencatatan (Logging)** 📝 Pertama, aplikasi akan mengaktifkan sistem pencatatan. Fungsinya adalah untuk mencatat semua aktivitas penting dan error yang terjadi di server, agar mudah dilacak jika ada masalah.

2. **Mengecek & Membuat Tabel Database** 🗄️ Selanjutnya, kode ini akan memeriksa database. Jika tabel-tabel yang dibutuhkan (seperti tabel `invoices`, `customers`, dll.) belum ada, maka akan dibuat secara otomatis.

3. **Mengatur Jadwal Tugas Otomatis (Scheduler)** ⏰ Bagian ini menyiapkan "alarm" untuk tugas-tugas yang akan berjalan secara otomatis di latar belakang. Saat ini, tugas-tugas tersebut sedang **dinonaktifkan** (ditandai dengan `#`), tetapi rencananya adalah:

   - **Membuat Tagihan Baru** (`job_generate_invoices`)

   - **Menonaktifkan Layanan Pelanggan** (`job_suspend_services`)

   - **Mengecek Status Pembayaran** (`job_verify_payments`)

4. **Menyalakan Mesin Penjadwal** ▶️ Terakhir, setelah semua jadwal diatur, mesin penjadwal ini dinyalakan. Ia akan terus berjalan selama server hidup untuk menjalankan tugas-tugas di atas sesuai waktunya.

<SwmSnippet path="/app/main.py" line="151">

---

&nbsp;

```python
@app.on_event("startup")
async def startup_event():
    setup_logging() # <-- Panggil fungsi setup
    logger = logging.getLogger('app.main')

    # 1. Buat tabel di database
    await create_tables()
    print("Tabel telah diperiksa/dibuat.")

    # 2. Tambahkan tugas-tugas ke scheduler untuk berjalan setiap hari
    #    (Ganti 'hour' dan 'minute' sesuai kebutuhan Anda)
    
    # scheduler.add_job(job_generate_invoices, 'cron', hour=1, minute=0, timezone='Asia/Jakarta') #Real
    
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================
     #scheduler.add_job(job_generate_invoices, 'cron', hour=10, minute=0, timezone='Asia/Jakarta', id="generate_invoices_job")
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================

    # scheduler.add_job(job_suspend_services, 'cron', hour=2, minute=0, timezone='Asia/Jakarta') #Real
    
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================
     #scheduler.add_job(job_suspend_services, 'interval', minutes=20, id="suspend_services_job")

    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================
    
    
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================
    # job verifikasi Pembayaran setiap jam, di menit ke-15
    # scheduler.add_job(job_verify_payments, 'cron', hour='*', minute=15, timezone='Asia/Jakarta', id="verify_payments_job") #Cek pembayaran setiap jam menit ke-15.
    
    #scheduler.add_job(job_verify_payments, 'interval', minutes=1, id="verify_payments_job")
     #scheduler.add_job(job_verify_payments, 'interval', minutes=20, id="verify_payments_job")
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================


    # 3. Mulai scheduler
    scheduler.start()
    print("Scheduler telah dimulai...")
    logger.info("Application startup complete")
```

---

</SwmSnippet>

### **Pusat Kontrol & Ruang Rahasia Aplikasi** ⚙️

Kode ini berfungsi sebagai **pusat pengaturan** untuk seluruh aplikasi. Anggap saja ini seperti ruang mesin atau panel kontrol, tempat semua informasi penting, konfigurasi, dan rahasia disimpan di satu tempat.

#### **Konsep Utama: File Rahasia** `.env`

Hal terpenting dari kode ini adalah ia mengambil semua nilainya dari sebuah file tersembunyi bernama `.env`. Tujuannya adalah untuk **keamanan**. Kita tidak menulis informasi sensitif (seperti password database atau API key) langsung di dalam kode, melainkan di file `.env` yang tidak akan pernah diunggah ke GitHub.

#### **Isi dari Pengaturan Ini.**

1. **Daftar Menu (**`MENUS`**)** 📜 Ini adalah daftar menu utama yang akan ditampilkan di *sidebar* aplikasi. Dengan menyimpannya di sini, kita bisa dengan mudah mengubah urutan atau nama menu dari satu tempat saja.

2. **Informasi Sensitif & Konfigurasi** 🔑 Ini adalah variabel-variabel penting yang nilainya diambil dari file `.env`, contohnya:

   - `DATABASE_URL`: Alamat untuk menyambung ke database.

   - `XENDIT...`: Berbagai kunci rahasia (API Key & Token) untuk berkomunikasi dengan layanan pembayaran Xendit.

   - `SECRET_KEY`: Kunci super rahasia yang digunakan untuk keamanan, misalnya untuk mengamankan data login pengguna.

3. **Pintasan Cerdas (**`@property`**)** ✨ Bagian `XENDIT_API_KEYS` dan `XENDIT_CALLBACK_TOKENS` adalah "pintasan" cerdas. Mereka mengelompokkan beberapa kunci API yang berbeda (misalnya untuk "JAKINET" dan "JELANTIK") ke dalam satu wadah. Ini membuat kode di bagian lain menjadi lebih rapi dan mudah saat perlu memilih kunci mana yang akan digunakan.

<SwmSnippet path="/app/config.py" line="9">

---

&nbsp;

```python
class Settings(BaseSettings):
    # --- PERPINDAHAN VARIABEL MENUS ---
    # Pindahkan MENUS ke sini
    MENUS: List[str] = [
        "Pelanggan", "Langganan", "Data Teknis", "Brand & Paket",
        "Invoices", "Mikrotik Servers", "Users", "Roles", "Permissions"
    ]
    # -----------------------------------
    
    DATABASE_URL: str
    XENDIT_CALLBACK_TOKEN_ARTACOMINDO: str
    XENDIT_CALLBACK_TOKEN_JELANTIK: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    XENDIT_API_KEY_JAKINET: str
    XENDIT_API_KEY_JELANTIK: str
    XENDIT_API_URL: str = "https://api.xendit.co/v2/invoices"

    @property
    def XENDIT_API_KEYS(self) -> dict:
        return {"JAKINET": self.XENDIT_API_KEY_JAKINET, "JELANTIK": self.XENDIT_API_KEY_JELANTIK}
    
    @property
    def XENDIT_CALLBACK_TOKENS(self) -> dict:
        return {"ARTACOMINDO": self.XENDIT_CALLBACK_TOKEN_ARTACOMINDO, "JELANTIK": self.XENDIT_CALLBACK_TOKEN_JELANTIK}

    class Config:
        env_file = ".env"

settings = Settings()
```

---

</SwmSnippet>

### **Komunikasi dengan Payment Gateway (Xendit)**

Kode ini berisi dua fungsi utama yang menjadi jembatan antara aplikasi Anda dengan layanan pembayaran Xendit: satu untuk **membuat tagihan**, dan satu lagi untuk **mengecek status pembayaran**.

---

&nbsp;

### **1. Membuat Tagihan Baru di Xendit (**`create_xendit_invoice`**)** 💸

Fungsi ini bertugas untuk mengirim semua detail tagihan ke Xendit agar Xendit bisa membuat halaman pembayaran untuk pelanggan.

Prosesnya seperti mengisi formulir digital dan mengirimkannya secara online.

#### **Langkah-langkahnya:**

&nbsp;

1. **Pilih Kunci API yang Tepat**: Pertama, fungsi ini secara cerdas memilih kunci API (API Key) yang benar sesuai dengan brand pelanggan (misalnya, kunci untuk "Jakinet" atau "Jelantik").

2. **Validasi Data**: Sebelum mengirim, fungsi ini akan memeriksa ulang untuk memastikan data-data penting seperti total harga, nama, dan email pelanggan sudah terisi dengan benar.

3. **Siapkan "Paket Data" (**`payload`**)**: Semua informasi tagihan—seperti nomor invoice, jumlah tagihan, detail pelanggan, dan rincian item—dikemas menjadi satu paket data (`payload`). Di sini juga ID unik yang informatif (`external_id`) dibuat.

4. **Kirim ke Xendit**: Menggunakan `httpx`, paket data tersebut dikirim ke server Xendit.

5. **Tangani Jawaban**: Fungsi ini akan menunggu balasan dari Xendit. Jika berhasil, ia akan mengembalikan detail invoice yang baru dibuat. Jika gagal, ia akan mencatat errornya dengan lengkap agar mudah diperbaiki.

---

&nbsp;

### **2. Mengecek Pembayaran yang Sudah Lunas (**`get_paid_invoice_ids_since`**)** ✅

Fungsi ini bertugas seperti seorang auditor yang bertanya ke Xendit: "Siapa saja yang sudah bayar lunas dalam beberapa hari terakhir?"

#### **Langkah-langkahnya:**

&nbsp;

1. **Periksa Semua Brand**: Fungsi ini akan memeriksa satu per satu brand yang Anda miliki (Jakinet, Jelantik, dll). Ini seperti mengunjungi setiap "kantor cabang" untuk meminta laporan pembayaran.

2. **Buat Kriteria Pencarian**: Untuk setiap brand, fungsi ini menentukan kriteria pencarian yang spesifik:

   - Status harus `PAID` (Lunas).

   - Dibayar setelah tanggal yang ditentukan (misalnya, 7 hari terakhir).

3. **Ambil Daftar dari Xendit**: Permintaan dikirim ke Xendit untuk mengambil daftar semua invoice yang cocok dengan kriteria tersebut.

4. **Kumpulkan Semua ID**: Dari daftar yang diterima, fungsi ini hanya akan mengambil `external_id`-nya saja dan mengumpulkannya menjadi satu daftar besar. Daftar ID inilah yang nantinya akan digunakan oleh aplikasi Anda untuk menandai tagihan mana saja yang sudah lunas.

<SwmSnippet path="app/services/xendit_service.py" line="16">

---

&nbsp;

```python
async def create_xendit_invoice(invoice: Invoice, pelanggan: Pelanggan, paket: PaketLayanan, deskripsi_xendit: str, pajak: float, no_telp_xendit: str = None) -> dict:
    """Mengirim request ke Xendit untuk membuat invoice baru."""
    target_key_name = pelanggan.harga_layanan.xendit_key_name
    api_key = settings.XENDIT_API_KEYS.get(target_key_name)
    if not api_key:
        raise ValueError(f"Kunci API Xendit untuk '{target_key_name}' tidak ditemukan.")

    encoded_key = base64.b64encode(f"{api_key}:".encode('utf-8')).decode('utf-8')
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_key}"
    }

    brand_info = pelanggan.harga_layanan
    jatuh_tempo_str = invoice.tgl_jatuh_tempo.strftime('%d/%m/%Y')

    # Validasi data
    if not invoice.total_harga or invoice.total_harga <= 0:
        raise ValueError("Total harga invoice tidak valid")
    if not paket.harga or float(paket.harga) <= 0:
        raise ValueError("Harga paket tidak valid")
    if not pelanggan.nama or not pelanggan.email:
        raise ValueError("Data pelanggan (nama atau email) tidak lengkap")

    # Hitung harga dasar
    harga_dasar = float(invoice.total_harga) - pajak
    if harga_dasar < 0:
        raise ValueError("Harga dasar tidak boleh negatif")

    # Siapkan payload
    payload = {
        "external_id": invoice.invoice_number,
        "amount": float(invoice.total_harga),
        "description": deskripsi_xendit,
        "invoice_duration": 86400 * 7,
        "customer": {
            "given_names": pelanggan.nama,
            "email": pelanggan.email,
            "mobile_number": no_telp_xendit if no_telp_xendit else pelanggan.no_telp
        },
        "currency": "IDR",
        "with_short_url": True,
        "items": [
            {
                "name": f"Biaya berlangganan internet up to {paket.kecepatan} Mbps",
                "price": harga_dasar,
                "quantity": 1,
                "description": deskripsi_xendit,
                "currency": "IDR",
                "type": "PRODUCT"
            }
        ],
        "fees": [{"type": "Tax", "value": pajak}]
    }

    # Logika external_id dinamis
    brand_prefix_map = {
        "ajn-01": "Jakinet",
        "ajn-02": "Jelantik",
        "ajn-03": "Nagrak"
    }

    id_brand_pelanggan = brand_info.id_brand
    brand_prefix = brand_prefix_map.get(id_brand_pelanggan, brand_info.brand)
    nama_user = pelanggan.nama.replace(' ', '')
    lokasi_singkat = pelanggan.alamat.split(' ')[0] if pelanggan.alamat else 'Lokasi'
    bulan_tagihan_sebenarnya = invoice.tgl_jatuh_tempo + relativedelta(months=1)
    bulan_tahun = bulan_tagihan_sebenarnya.strftime('%B-%Y')

    payload["external_id"] = f"{brand_prefix}/ftth/{nama_user}/{bulan_tahun}/{lokasi_singkat}/{invoice.id}"
    # bulan_tahun = invoice.tgl_jatuh_tempo.strftime('%B-%Y')
    # payload["external_id"] = f"{brand_prefix}/ftth/{nama_user}/{bulan_tahun}/{invoice.id}"

    logger.info(f"Payload yang dikirim ke Xendit: {json.dumps(payload, indent=2)}")

    async with httpx.AsyncClient(timeout=30.0) as client:  # Tambahkan timeout
        try:
            response = await client.post(settings.XENDIT_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Respons dari Xendit: {json.dumps(result, indent=2)}")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"Error saat membuat invoice Xendit. Payload: {json.dumps(payload, indent=2)}")
            logger.error(f"Respons Error dari Xendit: {e.response.text}")
            raise e
        except httpx.RequestError as e:
            logger.error(f"Kesalahan jaringan ke Xendit: {str(e)}")
            raise ValueError(f"Kesalahan jaringan ke Xendit: {str(e)}")

async def get_paid_invoice_ids_since(days: int) -> list[str]:
    """
    Mengambil daftar external_id dari semua invoice PAID dari SEMUA BRAND.
    """
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    all_paid_ids = []

    for brand_name, api_key in settings.XENDIT_API_KEYS.items():
        if not api_key:
            logger.warning(f"Kunci API Xendit untuk brand '{brand_name}' tidak ditemukan, dilewati.")
            continue

        logger.info(f"Memeriksa pembayaran lunas untuk brand: {brand_name}")
        encoded_key = base64.b64encode(f"{api_key}:".encode('utf-8')).decode('utf-8')
        headers = {"Authorization": f"Basic {encoded_key}"}
        
        base_url = "https://api.xendit.co/v2/invoices"
        query_params = {
            "statuses[]": "PAID",
            "paid_after": start_date,
            "limit": 1000 
        }
        
        # Gunakan httpx dengan params, ini cara yang lebih modern dan aman
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # httpx akan meng-encode 'statuses[]' dengan benar menjadi statuses%5B%5D=PAID
                response = await client.get(base_url, headers=headers, params=query_params)
                response.raise_for_status()
                
                # Cek apakah response.json() menghasilkan dict dan punya key 'data'
                response_data = response.json()
                invoices_data = response_data.get("data", []) if isinstance(response_data, dict) else []

                brand_paid_ids = [inv.get("external_id") for inv in invoices_data if inv.get("external_id")]
                all_paid_ids.extend(brand_paid_ids)
                logger.info(f"Ditemukan {len(brand_paid_ids)} pembayaran lunas untuk brand {brand_name}.")
            except httpx.HTTPStatusError as e:
                logger.error(f"Error saat mengambil data dari Xendit untuk brand {brand_name}: {e.response.text}")
    
    return all_paid_ids
```

---

</SwmSnippet>

### **Menyambungkan Aplikasi ke Server Mikrotik** 📡

Fungsi ini tugasnya seperti **penelepon otomatis** ke server Mikrotik Anda. Tujuannya adalah untuk membuka jalur komunikasi (koneksi API) yang aman agar aplikasi bisa memberi perintah ke server.

&nbsp;

#### **Cara Kerjanya:**

1. **Mencoba Menghubungi** 📞 Fungsi ini mengambil detail server (alamat IP, username, password, port) dan mencoba "menelepon" atau menghubunginya menggunakan pustaka `routeros_api`.

2. **Jika Berhasil Terhubung** ✅ Jika server "mengangkat telepon" (koneksi berhasil), fungsi ini akan mencatat pesan sukses, lalu mengembalikan **objek koneksi** yang aktif. Objek inilah yang akan digunakan oleh fungsi lain untuk mengirim perintah, seperti menonaktifkan atau mengaktifkan internet pelanggan.

3. **Jika Gagal Terhubung** ❌ Jika karena alasan apapun koneksi gagal (misalnya, password salah, IP tidak bisa dihubungi, atau server mati), fungsi ini memiliki jaring pengaman (`try...except`). Ia akan mencatat pesan error dan mengembalikan `None` (kosong), menandakan bahwa komunikasi ke server Mikrotik gagal.

### **Otak Otomatisasi Mikrotik: Mengelola Pelanggan**

&nbsp;

Kode ini adalah kumpulan fungsi yang bertindak sebagai **jembatan** antara aplikasi billing Anda dengan server Mikrotik. Tugas utamanya adalah secara otomatis **membuat**, **mengaktifkan**, dan **menonaktifkan** akun internet pelanggan di router Mikrotik.

Ada dua alur kerja utama di sini:

---

&nbsp;

### **Alur 1: Mengubah Status Pelanggan (Aktif / Suspended)** 🔄

Ini adalah proses yang terjadi ketika status langganan pelanggan berubah, misalnya dari "Aktif" menjadi "Suspended" karena telat bayar.

1. `trigger_mikrotik_update` **(Sang Pemicu)** Ini adalah fungsi utama yang memulai proses. Ia akan mengumpulkan semua data yang diperlukan dari database (info pelanggan, data teknis, dan detail server Mikrotik yang dituju).

2. `update_pppoe_secret` **(Sang Eksekutor Perubahan)** Setelah terhubung ke Mikrotik, fungsi ini akan mencari akun pelanggan berdasarkan `id_pelanggan`. Kemudian, ia akan mengubah statusnya:

   - Jika status baru **"Aktif"**, akun di Mikrotik akan di-set `disabled='no'` dan profil kecepatannya dikembalikan seperti semula.

   - Jika status baru **"Suspended"**, akun akan di-set `disabled='yes'` dan profilnya diubah menjadi `SUSPENDED` (yang biasanya berarti internet diblokir).

3. `remove_active_connection` **(Sang Pemutus Paksa)** Khusus untuk status "Suspended", fungsi ini punya tugas tambahan: mencari sesi internet pelanggan yang sedang aktif dan **memutusnya secara paksa**. Ini memastikan internet pelanggan langsung mati saat itu juga, tanpa harus menunggu mereka login ulang.

---

&nbsp;

### **Alur 2: Mendaftarkan Pelanggan Baru** 🆕

Ini adalah proses yang dijalankan saat Anda menambahkan data teknis untuk pelanggan baru.

1. `trigger_mikrotik_create` **(Pemicu Pendaftaran)** Sama seperti pemicu update, fungsi ini mengumpulkan data teknis pelanggan dan detail server Mikrotik, lalu membuka koneksi.

2. `create_pppoe_secret` **(Sang Pendaftar)** Fungsi ini mengambil data teknis pelanggan (username, password, profil kecepatan, IP statis jika ada) dan mengirimkannya ke Mikrotik untuk membuat akun PPPoE baru. Akun ini langsung siap digunakan oleh pelanggan.

---

&nbsp;

#### **Prinsip Penting: Selalu Menutup Koneksi** 🚪

Di kedua fungsi pemicu (`trigger_...`), Anda akan melihat blok `try...finally`. Ini adalah praktik yang sangat baik. Artinya, **apapun yang terjadi**—baik prosesnya berhasil maupun gagal di tengah jalan—aplikasi akan **selalu memastikan koneksi ke Mikrotik ditutup** dengan aman. Ini mencegah koneksi "menggantung" yang bisa membebani server.

<SwmSnippet path="app/services/mikrotik_service.py" line="18">

---

&nbsp;

```python
def get_api_connection(server_info: MikrotikServerModel):
    """Membuka koneksi API ke server Mikrotik."""
    try:
        connection = routeros_api.RouterOsApiPool(
            server_info.host_ip,
            username=server_info.username,
            password=server_info.password,
            port=int(server_info.port), # Pastikan port adalah integer
            plaintext_login=True
        )
        api = connection.get_api()
        logger.info(f"Berhasil terhubung ke Mikrotik {server_info.name}")
        return api, connection
    except Exception as e:
        logger.error(f"Gagal terhubung ke Mikrotik {server_info.name}: {e}")
        return None, None

def update_pppoe_secret(api, data_teknis: DataTeknisModel, new_status: str):
    """Mengubah status PPPoE secret di Mikrotik."""
    try:
        ppp_secrets = api.get_resource('/ppp/secret')
        
        # Cari user berdasarkan 'name' yang merujuk ke id_pelanggan Anda
        target_secret = ppp_secrets.get(name=data_teknis.id_pelanggan)

        if not target_secret:
            logger.warning(f"PPPoE secret untuk '{data_teknis.id_pelanggan}' tidak ditemukan di Mikrotik.")
            return

        # Ambil ID internal dari secret yang ditemukan
        user_id = target_secret[0]['id']

        if new_status == "Aktif":
            logger.info(f"Mengaktifkan '{data_teknis.id_pelanggan}', profil diubah ke '{data_teknis.profile_pppoe}'")
            # --- PERBAIKAN DI SINI: Gunakan .set() ---
            ppp_secrets.set(id=user_id, disabled='no', profile=data_teknis.profile_pppoe)
        
        elif new_status == "Suspended":
            logger.info(f"Menonaktifkan '{data_teknis.id_pelanggan}', profil diubah ke 'SUSPENDED'")
            # --- PERBAIKAN DI SINI: Gunakan .set() ---
            ppp_secrets.set(id=user_id, disabled='yes', profile='SUSPENDED')
        
        logger.info(f"Update PPPoE secret untuk '{data_teknis.id_pelanggan}' berhasil.")

    except Exception as e:
        logger.error(f"Terjadi error saat update PPPoE secret: {e}")
        raise e
    


def remove_active_connection(api, id_pelanggan: str):
    """Mencari dan menghapus koneksi PPPoE yang sedang aktif."""
    try:
        ppp_active = api.get_resource('/ppp/active')
        active_connections = ppp_active.get(name=id_pelanggan)

        if active_connections:
            connection_id = active_connections[0]['id']
            ppp_active.remove(id=connection_id)
            logger.info(f"Berhasil menghapus koneksi aktif untuk '{id_pelanggan}'.")
        else:
            logger.info(f"Tidak ada koneksi aktif yang ditemukan untuk '{id_pelanggan}'.")
    except Exception as e:
        logger.error(f"Gagal menghapus koneksi aktif untuk '{id_pelanggan}': {e}")
        # Tidak perlu 'raise e' agar proses suspend utama tidak gagal total
        # jika hanya gagal menghapus koneksi aktif.



async def trigger_mikrotik_update(db: AsyncSession, langganan: LanggananModel):
    """Fungsi utama yang dipanggil dari router atau job untuk trigger update ke Mikrotik."""
    # Pastikan data yang dibutuhkan sudah di-load
    if not hasattr(langganan, 'pelanggan') or not hasattr(langganan.pelanggan, 'data_teknis'):
         logger.error(f"Gagal trigger Mikrotik: Relasi 'pelanggan' atau 'data_teknis' tidak di-load untuk langganan ID {langganan.id}")
         return

    data_teknis = langganan.pelanggan.data_teknis

    if not data_teknis or not data_teknis.id_pelanggan:
        logger.warning(f"Data teknis atau id_pelanggan untuk pelanggan ID {langganan.pelanggan_id} tidak ditemukan.")
        return

    server_id = data_teknis.mikrotik_server_id 
    if not server_id:
        logger.error(f"mikrotik_server_id tidak di-set untuk pelanggan ID {langganan.pelanggan_id}. Skip update.")
        return
        
    mikrotik_server_info = await db.get(MikrotikServerModel, server_id)
    
    if not mikrotik_server_info:
        logger.error(f"Server Mikrotik dengan ID {server_id} tidak ditemukan di database.")
        return

    api, connection = get_api_connection(mikrotik_server_info)
    if not api:
        return

    try:
        update_pppoe_secret(api, data_teknis, langganan.status)

    # Jika statusnya adalah Suspended, panggil juga fungsi untuk remove active connection
        if langganan.status == "Suspended":
            remove_active_connection(api, data_teknis.id_pelanggan)

    finally:
        if connection:
            logger.info("Menutup koneksi Mikrotik.")
            connection.disconnect()


# --- FUNGSI BARU UNTUK MEMBUAT SECRET ---
def create_pppoe_secret(api, data_teknis: DataTeknisModel):
    """Menambahkan PPPoE secret baru di Mikrotik."""
    try:
        ppp_secrets = api.get_resource('/ppp/secret')
        
        # Siapkan data untuk secret baru
        secret_payload = {
            'name': data_teknis.id_pelanggan,
            'password': data_teknis.password_pppoe,
            'profile': data_teknis.profile_pppoe,
            'service': 'pppoe',
            'comment': f"Created by Billing API on {datetime.now().strftime('%Y-%m-%d')}"
        }

        # Tambahkan IP Address jika ada
        if data_teknis.ip_pelanggan:
            secret_payload['remote-address'] = data_teknis.ip_pelanggan

        ppp_secrets.add(**secret_payload)
        logger.info(f"Berhasil membuat PPPoE secret untuk '{data_teknis.id_pelanggan}'.")

    except Exception as e:
        logger.error(f"Gagal membuat PPPoE secret untuk '{data_teknis.id_pelanggan}': {e}")
        raise e

# --- FUNGSI BARU SEBAGAI TRIGGER ---
async def trigger_mikrotik_create(db: AsyncSession, data_teknis: DataTeknisModel):
    """Fungsi utama yang dipanggil untuk trigger pembuatan secret di Mikrotik."""
    if not data_teknis or not data_teknis.id_pelanggan:
        logger.warning(f"Data teknis atau id_pelanggan tidak valid. Skip pembuatan secret.")
        return

    server_id = data_teknis.mikrotik_server_id
    if not server_id:
        logger.error(f"mikrotik_server_id tidak di-set untuk data teknis ID {data_teknis.id}. Skip.")
        return

    mikrotik_server_info = await db.get(MikrotikServerModel, server_id)
    if not mikrotik_server_info:
        logger.error(f"Server Mikrotik dengan ID {server_id} tidak ditemukan.")
        return

    api, connection = get_api_connection(mikrotik_server_info)
    if not api:
        return

    try:
        create_pppoe_secret(api, data_teknis)
    finally:
        if connection:
            logger.info("Menutup koneksi Mikrotik.")
            connection.disconnect()
```

---

</SwmSnippet>

### **Jantung Sistem Billing Otomatis: Tiga Pekerja Robot**

&nbsp;

Kode ini berisi tiga fungsi utama (`job_...`) yang bekerja seperti "robot" terjadwal. Masing-masing memiliki tugas spesifik untuk memastikan siklus penagihan berjalan secara otomatis tanpa campur tangan manusia.

---

&nbsp;

### **1. Si Pembuat Tagihan (**`job_generate_invoices`**)** 🧾

Fungsi ini bertindak seperti staf administrasi yang rajin bekerja setiap hari.

- **Tugasnya**: Setiap hari, ia akan memeriksa kalender dan mencari semua pelanggan aktif yang tanggal jatuh temponya adalah **5 hari dari sekarang**.

- **Prosesnya**:

  1. Untuk setiap pelanggan yang ditemukan, ia akan memeriksa terlebih dahulu: "Apakah tagihan untuk periode ini sudah pernah dibuat?". Ini penting untuk **mencegah tagihan ganda**.

  2. Jika belum ada, ia akan memanggil "asisten"-nya, yaitu fungsi `generate_single_invoice`.

  3. Si asisten inilah yang melakukan pekerjaan detail: menghitung total harga ditambah pajak dengan pembulatan yang benar, membuat nomor invoice unik, menyimpannya ke database, dan terakhir menghubungi Xendit untuk membuat link pembayaran.

---

&nbsp;

### **2. Si Penegak Aturan (**`job_suspend_services`**)** 🔒

Fungsi ini bertindak seperti petugas disiplin yang menjalankan aturan secara otomatis.

- **Tugasnya**: Setiap hari, ia mencari pelanggan yang statusnya masih "Aktif" tetapi memiliki tagihan "Belum Dibayar" dan sudah **terlambat lebih dari 4 hari** dari tanggal jatuh tempo.

- **Tindakannya**:

  1. **Ubah Status di Database**: Status langganan pelanggan diubah dari "Aktif" menjadi "Suspended".

  2. **Perintah ke Mikrotik**: Ia langsung memanggil `mikrotik_service` untuk mengirim perintah ke router Mikrotik agar **memblokir koneksi internet** pelanggan tersebut saat itu juga.

---

&nbsp;

### **3. Si Akuntan Teliti (**`job_verify_payments`**)** ✅

Fungsi ini bertindak seperti seorang akuntan atau auditor yang melakukan rekonsiliasi data setiap hari.

- **Tugasnya**: Memastikan data pembayaran di sistem Anda cocok dengan data di Xendit.

- **Prosesnya dibagi dua:**

  1. **Merapikan Data**: Pertama, ia akan mencari semua tagihan yang "Belum Dibayar" dan sudah lewat tanggalnya, lalu mengubah statusnya menjadi "Kadaluarsa".

  2. **Rekonsiliasi**: Kemudian, ia "menelepon" Xendit dan bertanya, "Siapa saja yang sudah lunas dalam 3 hari terakhir?". Ia membandingkan daftar ini dengan databasenya. Jika ada pelanggan yang ternyata sudah bayar di Xendit tapi status di sistem masih "Belum Dibayar" (mungkin karena notifikasi terlewat), fungsi ini akan **memproses pembayaran tersebut** agar status pelanggan kembali aktif dan datanya akurat.

<SwmSnippet path="/app/jobs.py" line="21">

---

&nbsp;

```python
async def generate_single_invoice(db, langganan: LanggananModel):
    try:
        pelanggan = langganan.pelanggan
        paket = langganan.paket_layanan
        brand = pelanggan.harga_layanan
        data_teknis = pelanggan.data_teknis

        if not all([pelanggan, paket, brand, data_teknis]):
            logger.error(f"Data tidak lengkap untuk langganan ID {langganan.id}. Skip.")
            return

        # --- PERBAIKAN FINAL ---
        
        # 1. Hitung harga dan pajak
        harga_dasar = float(paket.harga)
        pajak_persen = float(brand.pajak)

        # Hitung nilai pajak mentah
        pajak_mentah = harga_dasar * (pajak_persen / 100)

        # Lakukan pembulatan matematis standar (round half up) sesuai aturan finance
        pajak = math.floor(pajak_mentah + 0.5)

        # Total harga adalah harga dasar ditambah pajak yang sudah dibulatkan.
        total_harga = harga_dasar + pajak
        
        # --- PERBAIKAN PADA new_invoice_data ---
        new_invoice_data = {
            "invoice_number": f"INV-{date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            "pelanggan_id": pelanggan.id,
            "id_pelanggan": data_teknis.id_pelanggan,
            "brand": brand.brand,
            "total_harga": total_harga, # Menggunakan total_harga yang sudah dihitung dengan benar
            "no_telp": pelanggan.no_telp,
            "email": pelanggan.email,
            "tgl_invoice": date.today(),
            "tgl_jatuh_tempo": langganan.tgl_jatuh_tempo,
            "status_invoice": "Belum Dibayar",
        }

        db_invoice = InvoiceModel(**new_invoice_data)
        db.add(db_invoice)
        await db.flush()

        # --- PERUBAHAN DIMULAI DI SINI ---
        deskripsi_xendit = ""
        jatuh_tempo_str_lengkap = db_invoice.tgl_jatuh_tempo.strftime('%d/%m/%Y')

        # Cek metode pembayaran dari data langganan
        if langganan.metode_pembayaran == 'Prorate':
            # Jika Prorate, buat deskripsi dengan periode
            start_day = db_invoice.tgl_invoice.day
            end_day = db_invoice.tgl_jatuh_tempo.day
            periode_str = db_invoice.tgl_jatuh_tempo.strftime('%B %Y')
            deskripsi_xendit = (
                f"Biaya berlangganan internet up to {paket.kecepatan} Mbps, "
                f"Periode Tgl {start_day}-{end_day} {periode_str}"
            )
        else: # Otomatis
            # Jika Otomatis, gunakan format deskripsi yang lama
            deskripsi_xendit = (
                f"Biaya berlangganan internet up to {paket.kecepatan} Mbps "
                f"jatuh tempo pembayaran tanggal {jatuh_tempo_str_lengkap}"
            )
            
        no_telp_xendit = f"+62{pelanggan.no_telp.lstrip('0')}" if pelanggan.no_telp else None
        
        # 3. Panggil service Xendit dengan deskripsi yang sudah dinamis
        xendit_response = await xendit_service.create_xendit_invoice(
            db_invoice, 
            pelanggan, 
            paket, 
            deskripsi_xendit,
            pajak,
            no_telp_xendit
        )

        db_invoice.payment_link = xendit_response.get("short_url", xendit_response.get("invoice_url"))
        db_invoice.xendit_id = xendit_response.get("id")
        db_invoice.xendit_external_id = xendit_response.get("external_id")

        db.add(db_invoice)
        logger.info(f"Invoice {db_invoice.invoice_number} berhasil dibuat untuk Langganan ID {langganan.id}")

    except Exception as e:
        import traceback
        logger.error(f"Gagal membuat invoice untuk Langganan ID {langganan.id}: {e}\n{traceback.format_exc()}")

async def job_suspend_services():
    log_scheduler_event(logger, 'job_suspend_services', 'started')
    services_suspended = 0
    current_date = date.today()

    async with SessionLocal() as db:
        try:
            stmt = (
                select(LanggananModel)
                .join(InvoiceModel, LanggananModel.pelanggan_id == InvoiceModel.pelanggan_id)
                .where(
                    # LanggananModel.tgl_jatuh_tempo < current_date, #ini Logic Suspend di tanggal 2
                    LanggananModel.tgl_jatuh_tempo <= current_date - timedelta(days=4), # ini Logic Suspend di tanggal 5
                    LanggananModel.status == "Aktif",
                    InvoiceModel.status_invoice == "Belum Dibayar"
                ).options(
                    selectinload(LanggananModel.pelanggan).selectinload(PelangganModel.data_teknis)
                )
            )
            overdue_subscriptions = (await db.execute(stmt)).scalars().all()

            if not overdue_subscriptions:
                log_scheduler_event(logger, 'job_suspend_services', 'completed', "Tidak ada layanan untuk di-suspend.")
                return

            for langganan in overdue_subscriptions:
                logger.info(f"LOOP SAAT INI UNTUK: Langganan ID {langganan.id}, User PPPoE: {langganan.pelanggan.data_teknis.id_pelanggan}")
                logger.warning(f"Melakukan suspend layanan untuk Langganan ID: {langganan.id} karena terlambat pada {current_date}.")
                langganan.status = "Suspended"
                db.add(langganan)
                await mikrotik_service.trigger_mikrotik_update(db, langganan)
                services_suspended += 1
            
            await db.commit()
            log_scheduler_event(logger, 'job_suspend_services', 'completed', f"Berhasil suspend {services_suspended} layanan.")
        except Exception as e:
            await db.rollback()
            log_scheduler_event(logger, 'job_suspend_services', 'failed', str(e))

async def job_verify_payments():
    """Job untuk rekonsiliasi pembayaran dan menandai invoice kedaluwarsa."""
    log_scheduler_event(logger, 'job_verify_payments', 'started')
    
    async with SessionLocal() as db:
        try:
            # Bagian 1: Tandai Invoice Kedaluwarsa (Batch Update)
            expired_stmt = (
                update(InvoiceModel)
                .where(
                    InvoiceModel.status_invoice == "Belum Dibayar",
                    InvoiceModel.tgl_jatuh_tempo < date.today() - timedelta(days=1)
                )
                .values(status_invoice="Kadaluarsa")
            )
            result = await db.execute(expired_stmt)
            if result.rowcount > 0:
                logger.info(f"[VERIFY] Menandai {result.rowcount} invoice sebagai kedaluwarsa.")

            # Bagian 2: Rekonsiliasi Pembayaran Terlewat (Batch API & SELECT)
            paid_invoice_ids = await xendit_service.get_paid_invoice_ids_since(days=3)

            if not paid_invoice_ids:
                log_scheduler_event(logger, 'job_verify_payments', 'completed', "Tidak ada pembayaran baru di Xendit.")
                await db.commit()
                return

            unprocessed_stmt = (
                select(InvoiceModel)
                .where(
                    InvoiceModel.xendit_external_id.in_(paid_invoice_ids),
                    InvoiceModel.status_invoice == "Belum Dibayar"
                )
            )
            invoices_to_process = (await db.execute(unprocessed_stmt)).scalars().all()

            processed_count = 0
            if invoices_to_process:
                logger.warning(f"[VERIFY] Menemukan {len(invoices_to_process)} pembayaran terlewat. Memproses...")
                for invoice in invoices_to_process:
                    await _process_successful_payment(db, invoice)
                    processed_count += 1
            
            await db.commit()
            log_scheduler_event(logger, 'job_verify_payments', 'completed', f"Memproses {processed_count} pembayaran terlewat.")
            
        except Exception as e:
            await db.rollback()
            error_details = traceback.format_exc()
            logger.error(f"[FAIL] Scheduler 'job_verify_payments' failed. Details:\n{error_details}")

async def job_generate_invoices():
    log_scheduler_event(logger, 'job_generate_invoices', 'started')
    # Penyesuaian: Job ini seharusnya berjalan setiap hari untuk H-5,
    # jadi kita gunakan tanggal hari ini untuk kalkulasi.
    target_due_date = date.today() + timedelta(days=5)
    invoices_created = 0

    async with SessionLocal() as db:
        try:
            stmt = (
                select(LanggananModel)
                .where(
                    LanggananModel.tgl_jatuh_tempo == target_due_date,
                    LanggananModel.status == "Aktif"
                ).options(
                    selectinload(LanggananModel.pelanggan).selectinload(PelangganModel.harga_layanan),
                    selectinload(LanggananModel.pelanggan).selectinload(PelangganModel.data_teknis),
                    selectinload(LanggananModel.paket_layanan)
                )
            )
            subscriptions_to_invoice = (await db.execute(stmt)).scalars().unique().all()

            if not subscriptions_to_invoice:
                log_scheduler_event(logger, 'job_generate_invoices', 'completed', "Tidak ada invoice untuk dibuat hari ini.")
                return

            for langganan in subscriptions_to_invoice:
                # Cek apakah invoice untuk periode ini sudah ada
                existing_invoice_stmt = (
                    select(InvoiceModel.id).where(
                        InvoiceModel.pelanggan_id == langganan.pelanggan_id,
                        InvoiceModel.tgl_jatuh_tempo == langganan.tgl_jatuh_tempo
                    ).limit(1)
                )
                existing_invoice = (await db.execute(existing_invoice_stmt)).scalar_one_or_none()

                if not existing_invoice:
                    await generate_single_invoice(db, langganan)
                    invoices_created += 1
                else:
                    logger.debug(f"Invoice untuk langganan ID {langganan.id} dengan jatuh tempo {langganan.tgl_jatuh_tempo} sudah ada, dilewati.")
            
            await db.commit()
            if invoices_created > 0:
                log_scheduler_event(logger, 'job_generate_invoices', 'completed', f"Berhasil membuat {invoices_created} invoice baru.")
            else:
                log_scheduler_event(logger, 'job_generate_invoices', 'completed', "Tidak ada invoice baru yang perlu dibuat (semua sudah ada).")

        except Exception as e:
            await db.rollback()
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"[FAIL] Scheduler 'job_generate_invoices' failed. Details:\n{error_details}")
```

---

</SwmSnippet>

### **Satpam Pintar untuk Komunikasi API** 👮‍♂️

Anggap saja file ini adalah **kantor pusat komunikasi** untuk aplikasi frontend Anda. Semua permintaan data ke backend harus melewati "satpam" yang ada di sini.

Kode ini menyiapkan dua "satpam" atau *interceptor* yang punya tugas berbeda: satu saat permintaan **pergi**, dan satu lagi saat jawaban **datang**.

---

&nbsp;

#### **1. Satpam Pintu Keluar (**`interceptors.request`**)**

&nbsp;

Ini adalah satpam yang memeriksa setiap permintaan **sebelum** dikirim ke server.

- **Tugasnya**: "Setiap kali kamu mau minta data ke server, saya akan periksa dulu apakah kamu punya kartu akses (`access_token`) di `localStorage`. Kalau ada, kartu itu akan saya tempelkan di permintaanmu (`Authorization header`). Kalau tidak ada, ya sudah, pergi saja dengan tangan kosong."

- **Tujuannya**: Ini memastikan bahwa setiap permintaan yang butuh otentikasi (izin) akan selalu membawa "kartu akses" yang benar secara otomatis. Kita tidak perlu menempelkannya manual di setiap fungsi API.

---

&nbsp;

#### **2. Satpam Pintu Masuk (**`interceptors.response`**) - INI BAGIAN BARUNYA**

Ini adalah satpam yang lebih pintar. Ia memeriksa setiap jawaban yang **datang dari server**.

- **Tugasnya**: "Saya akan lihat semua balasan dari server."

  - **Jika Balasan Sukses (Kode 200-an)**: "Oke, balasannya aman. Silakan lanjutkan."

  - **Jika Balasan Gagal (Error)**: "Tunggu dulu, saya periksa jenis errornya."

    - **Jika Errornya Kode 401 (Tidak Punya Izin)**: "Aha! Ini artinya kartu aksesmu sudah tidak berlaku atau kadaluarsa. Server tidak mengenalimu lagi."

- **Tindakan Saat Menemukan Error 401**:

  1. **Buang Kartu Akses Lama**: Satpam ini akan langsung mengambil kartu akses yang sudah tidak valid dari `localStorage` dan membuangnya (`localStorage.removeItem`).

  2. **Usir ke Halaman Login**: Kemudian, ia akan secara paksa mengarahkan pengguna kembali ke halaman login (`router.push('/login')`).

- **Tujuannya**: Ini adalah **penanganan sesi kadaluarsa otomatis**. Pengguna tidak akan terjebak di halaman yang error karena sesinya habis. Sebaliknya, aplikasi akan secara otomatis mengembalikannya ke halaman login untuk masuk kembali. Ini memberikan pengalaman pengguna yang jauh lebih baik.

<SwmSnippet path="/frontend/src/services/api.ts" line="7">

---

&nbsp;

```typescript
const apiClient = axios.create({
  // baseURL: '/api', // Jika ingin build lalu Upload ke Server
  baseURL: 'http://127.0.0.1:8000', // Local
  timeout: 30000,
});

// Interceptor untuk MENAMBAHKAN token ke setiap request (Ini sudah ada)
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ==========================================================
// --- TAMBAHAN BARU: Interceptor untuk MEMERIKSA setiap response ---
// ==========================================================
apiClient.interceptors.response.use(
  (response) => {
    // Jika response sukses (status 2xx), lanjutkan seperti biasa
    return response;
  },
  (error) => {
    // Jika response dari server adalah error
    if (error.response && error.response.status === 401) {
      // 2. Cek apakah status errornya adalah 401 (Unauthorized)
      console.error("Sesi tidak valid atau telah berakhir. Mengarahkan ke halaman login.");
      
      // 3. Hapus token yang sudah tidak valid dari penyimpanan
      localStorage.removeItem('access_token');
      // Anda juga bisa membersihkan data user dari state management (Pinia) di sini jika perlu
      
      // 4. Arahkan pengguna ke halaman login
      router.push('/login');
    }
    
    // Kembalikan error agar bisa ditangani lebih lanjut jika ada logic lain
    return Promise.reject(error);
  }
);
// ==========================================================

export default apiClient;
```

---

</SwmSnippet>

&nbsp;

---

## **Daftar Isi End Point API**

&nbsp;

 1. [Endpoint Pelanggan (](https://www.google.com/search?q=%23endpoint-pelanggan-pelanggan)`/pelanggan`[)](https://www.google.com/search?q=%23endpoint-pelanggan-pelanggan)

 2. [Endpoint Langganan (](https://www.google.com/search?q=%23endpoint-langganan-langganan)`/langganan`[)](https://www.google.com/search?q=%23endpoint-langganan-langganan)

 3. [Endpoint Data Teknis (](https://www.google.com/search?q=%23endpoint-data-teknis-data_teknis)`/data_teknis`[)](https://www.google.com/search?q=%23endpoint-data-teknis-data_teknis)

 4. [Endpoint Invoice (](https://www.google.com/search?q=%23endpoint-invoice-invoices)`/invoices`[)](https://www.google.com/search?q=%23endpoint-invoice-invoices)

 5. [Endpoint Dashboard (](https://www.google.com/search?q=%23endpoint-dashboard-dashboard)`/dashboard`[)](https://www.google.com/search?q=%23endpoint-dashboard-dashboard)

 6. [Endpoint Server Mikrotik (](https://www.google.com/search?q=%23endpoint-server-mikrotik-mikrotik_servers)`/mikrotik_servers`[)](https://www.google.com/search?q=%23endpoint-server-mikrotik-mikrotik_servers)

 7. [Endpoint Paket Layanan (](https://www.google.com/search?q=%23endpoint-paket-layanan-paket_layanan)`/paket_layanan`[)](https://www.google.com/search?q=%23endpoint-paket-layanan-paket_layanan)

 8. [Endpoint Harga Layanan / Brand (](https://www.google.com/search?q=%23endpoint-harga-layanan-brand-harga_layanan)`/harga_layanan`[)](https://www.google.com/search?q=%23endpoint-harga-layanan-brand-harga_layanan)

 9. [Endpoint Pengguna (](https://www.google.com/search?q=%23endpoint-pengguna-users)`/users`[)](https://www.google.com/search?q=%23endpoint-pengguna-users)

10. [Endpoint Peran (](https://www.google.com/search?q=%23endpoint-peran-roles)`/roles`[)](https://www.google.com/search?q=%23endpoint-peran-roles)

---

&nbsp;

### **Endpoint:** `/pelanggan`

&nbsp;

| Endpoint       | Deskripsi Singkat                                     | Request Body                       | Respons Sukses                            |
| -------------- | ----------------------------------------------------- | ---------------------------------- | ----------------------------------------- |
| `POST /`       | Membuat pelanggan baru & mengirim notifikasi.         | Data pelanggan (nama, email, dll). | `201` - Data pelanggan baru.              |
| `GET /`        | Mengambil daftar semua pelanggan (paginasi & filter). | Tidak ada.                         | `200` - Daftar pelanggan.                 |
| `GET /{id}`    | Mengambil satu pelanggan spesifik.                    | Tidak ada.                         | `200` - Satu data pelanggan.              |
| `PATCH /{id}`  | Memperbarui data pelanggan.                           | Data pelanggan yang ingin diubah.  | `200` - Data pelanggan yang sudah diubah. |
| `DELETE /{id}` | Menghapus pelanggan.                                  | Tidak ada.                         | `204` - Tidak ada konten.                 |
| `POST /import` | Mengimpor pelanggan dari file CSV.                    | File `.csv`.                       | `200` - Hasil dan laporan impor.          |

---

&nbsp;

### **Endpoint:** `/langganan`

&nbsp;

| Endpoint                | Deskripsi Singkat                                    | Request Body                                             | Respons Sukses                            |
| ----------------------- | ---------------------------------------------------- | -------------------------------------------------------- | ----------------------------------------- |
| `POST /`                | Membuat langganan baru & menghitung harga awal.      | `pelanggan_id`, `paket_layanan_id`, `metode_pembayaran`. | `201` - Data langganan baru.              |
| `GET /`                 | Mengambil daftar semua langganan (filter).           | Tidak ada.                                               | `200` - Daftar langganan.                 |
| `PATCH /{id}`           | Memperbarui data langganan.                          | Data langganan yang ingin diubah.                        | `200` - Data langganan yang sudah diubah. |
| `DELETE /{id}`          | Menghapus langganan.                                 | Tidak ada.                                               | `204` - Tidak ada konten.                 |
| `POST /calculate-price` | Kalkulator untuk menghitung harga & tgl jatuh tempo. | Detail paket & metode pembayaran.                        | `200` - Hasil perhitungan.                |
| `POST /import/csv`      | Mengimpor langganan dari file CSV.                   | File `.csv`.                                             | `200` - Hasil dan laporan impor.          |

---

&nbsp;

### **Endpoint:** `/data_teknis`

&nbsp;

| Endpoint           | Deskripsi Singkat                                   | Request Body                            | Respons Sukses                         |
| ------------------ | --------------------------------------------------- | --------------------------------------- | -------------------------------------- |
| `POST /`           | Membuat data teknis & membuat *secret* di Mikrotik. | Data teknis (username PPPoE, OLT, dll). | `201` - Data teknis baru.              |
| `GET /`            | Mengambil daftar semua data teknis.                 | Tidak ada.                              | `200` - Daftar data teknis.            |
| `GET /{id}`        | Mengambil satu data teknis spesifik.                | Tidak ada.                              | `200` - Satu data teknis.              |
| `PATCH /{id}`      | Memperbarui data teknis.                            | Data teknis yang ingin diubah.          | `200` - Data teknis yang sudah diubah. |
| `DELETE /{id}`     | Menghapus data teknis.                              | Tidak ada.                              | `204` - Tidak ada konten.              |
| `POST /import/csv` | Mengimpor data teknis dari file CSV.                | File `.csv`.                            | `200` - Hasil dan laporan impor.       |

---

&nbsp;

### **Endpoint:** `/invoices`

&nbsp;

| Endpoint                  | Deskripsi Singkat                                           | Request Body               | Respons Sukses                            |
| ------------------------- | ----------------------------------------------------------- | -------------------------- | ----------------------------------------- |
| `POST /generate`          | Membuat tagihan manual untuk satu langganan.                | `langganan_id`.            | `201` - Data invoice baru.                |
| `GET /`                   | Mengambil daftar semua invoice (filter).                    | Tidak ada.                 | `200` - Daftar invoice.                   |
| `POST /xendit-callback`   | **\[Webhook\]** Menerima notifikasi pembayaran dari Xendit. | Data callback dari Xendit. | `200` - OK.                               |
| `POST /{id}/mark-as-paid` | Menandai invoice sebagai "Lunas" secara manual.             | Tidak ada.                 | `200` - Data invoice yang sudah diupdate. |
| `DELETE /{id}`            | Menghapus invoice.                                          | Tidak ada.                 | `204` - Tidak ada konten.                 |

---

&nbsp;

### **Endpoint:** `/dashboard`

&nbsp;

| Endpoint               | Deskripsi Singkat                                     | Request Body | Respons Sukses                                  |
| ---------------------- | ----------------------------------------------------- | ------------ | ----------------------------------------------- |
| `GET /`                | Mengambil semua data untuk kartu statistik & grafik.  | Tidak ada.   | `200` - Objek JSON berisi semua data dashboard. |
| `GET /mikrotik-status` | Mengecek status online/offline semua server Mikrotik. | Tidak ada.   | `200` - `{"online": X, "offline": Y}`.          |
| `GET /sidebar-badges`  | Mengambil angka notifikasi untuk sidebar menu.        | Tidak ada.   | `200` - Jumlah suspended, unpaid, dll.          |

---

&nbsp;

### **Endpoint:** `/mikrotik_servers`

&nbsp;

| Endpoint                     | Deskripsi Singkat                       | Request Body                           | Respons Sukses                         |
| ---------------------------- | --------------------------------------- | -------------------------------------- | -------------------------------------- |
| `POST /`                     | Menambahkan server Mikrotik baru.       | Data server (nama, IP, username, dll). | `201` - Data server baru.              |
| `GET /`                      | Mengambil daftar semua server Mikrotik. | Tidak ada.                             | `200` - Daftar server.                 |
| `GET /{id}`                  | Mengambil satu server spesifik.         | Tidak ada.                             | `200` - Satu data server.              |
| `PATCH /{id}`                | Memperbarui data server.                | Data server yang ingin diubah.         | `200` - Data server yang sudah diubah. |
| `DELETE /{id}`               | Menghapus server.                       | Tidak ada.                             | `204` - Tidak ada konten.              |
| `POST /{id}/test_connection` | Menguji koneksi ke server Mikrotik.     | Tidak ada.                             | `200` - Pesan koneksi berhasil.        |

---

&nbsp;

### **Endpoint:** `/paket_layanan`

&nbsp;

| Endpoint       | Deskripsi Singkat                      | Request Body                         | Respons Sukses                        |
| -------------- | -------------------------------------- | ------------------------------------ | ------------------------------------- |
| `POST /`       | Menambahkan paket internet baru.       | Data paket (nama, kecepatan, harga). | `201` - Data paket baru.              |
| `GET /`        | Mengambil daftar semua paket internet. | Tidak ada.                           | `200` - Daftar paket.                 |
| `PATCH /{id}`  | Memperbarui data paket.                | Data paket yang ingin diubah.        | `200` - Data paket yang sudah diubah. |
| `DELETE /{id}` | Menghapus paket.                       | Tidak ada.                           | `204` - Tidak ada konten.             |

---

&nbsp;

### **Endpoint:** `/harga_layanan` **(Brand)**

&nbsp;

| Endpoint       | Deskripsi Singkat             | Request Body                       | Respons Sukses                        |
| -------------- | ----------------------------- | ---------------------------------- | ------------------------------------- |
| `POST /`       | Menambahkan data brand baru.  | Data brand (ID, nama, pajak, dll). | `201` - Data brand baru.              |
| `GET /`        | Mengambil daftar semua brand. | Tidak ada.                         | `200` - Daftar brand.                 |
| `PATCH /{id}`  | Memperbarui data brand.       | Data brand yang ingin diubah.      | `200` - Data brand yang sudah diubah. |
| `DELETE /{id}` | Menghapus brand.              | Tidak ada.                         | `204` - Tidak ada konten.             |

---

&nbsp;

### **Endpoint:** `/users`

&nbsp;

| Endpoint                | Deskripsi Singkat                                 | Request Body                                 | Respons Sukses                           |
| ----------------------- | ------------------------------------------------- | -------------------------------------------- | ---------------------------------------- |
| `POST /token`           | Login untuk mendapatkan token akses.              | `username` & `password`.                     | `200` - `access_token`.                  |
| `GET /me`               | Mengambil info detail pengguna yang sedang login. | Tidak ada.                                   | `200` - Data pengguna.                   |
| `POST /`                | Membuat pengguna baru.                            | Data pengguna (nama, email, password, role). | `201` - Data pengguna baru.              |
| `GET /`                 | Mengambil daftar semua pengguna.                  | Tidak ada.                                   | `200` - Daftar pengguna.                 |
| `PATCH /{id}`           | Memperbarui data pengguna.                        | Data pengguna yang ingin diubah.             | `200` - Data pengguna yang sudah diubah. |
| `DELETE /{id}`          | Menghapus pengguna.                               | Tidak ada.                                   | `204` - Tidak ada konten.                |
| `POST /forgot-password` | Meminta token reset password via email.           | `email`.                                     | `200` - Pesan sukses.                    |
| `POST /reset-password`  | Mereset password dengan token dari email.         | `token`, `email`, `new_password`.            | `200` - Pesan sukses.                    |

---

&nbsp;

### **Endpoint:** `/roles`

| Endpoint       | Deskripsi Singkat                            | Request Body                   | Respons Sukses                        |
| -------------- | -------------------------------------------- | ------------------------------ | ------------------------------------- |
| `POST /`       | Membuat peran (role) baru.                   | `name` & daftar `permissions`. | `201` - Data peran baru.              |
| `GET /`        | Mengambil daftar semua peran & hak aksesnya. | Tidak ada.                     | `200` - Daftar peran.                 |
| `PATCH /{id}`  | Memperbarui nama peran dan hak aksesnya.     | `name` & daftar `permissions`. | `200` - Data peran yang sudah diubah. |
| `DELETE /{id}` | Menghapus peran.                             | Tidak ada.                     | `204` - Tidak ada konten.             |

&nbsp;

---

## **Endpoint Pelanggan (**`/pelanggan`**)**

Mengelola semua data dasar pelanggan.

### `POST /`

- **Deskripsi**: Membuat data pelanggan baru.

- **Fitur Tambahan**: Setelah pelanggan dibuat, endpoint ini akan mengirim notifikasi via WebSocket ke semua pengguna dengan peran 'NOC', 'CS', dan 'Admin' untuk memberitahu bahwa ada pelanggan baru yang perlu dibuatkan data teknis.

- **Request Body**: Objek JSON berisi data pelanggan seperti `nama`, `email`, `no_telp`, `alamat`, `id_brand`, dll.

- **Respons Sukses**: `201 Created` - Mengembalikan data pelanggan yang baru saja dibuat.

### `GET /`

- **Deskripsi**: Mengambil daftar semua pelanggan dengan filter dan paginasi.

- **Query Parameters**:

  - `skip` (opsional): Jumlah data yang akan dilewati (untuk paginasi).

  - `limit` (opsional): Jumlah maksimal data yang akan diambil.

  - `search` (opsional): Mencari pelanggan berdasarkan nama, email, atau nomor telepon.

  - `id_brand` (opsional): Memfilter pelanggan berdasarkan brand.

- **Respons Sukses**: `200 OK` - Mengembalikan daftar objek pelanggan.

### `GET /{pelanggan_id}`

- **Deskripsi**: Mengambil satu data pelanggan spesifik berdasarkan ID-nya.

- **Respons Sukses**: `200 OK` - Mengembalikan satu objek pelanggan.

- **Respons Error**: `404 Not Found` - Jika pelanggan dengan ID tersebut tidak ditemukan.

### `PATCH /{pelanggan_id}`

- **Deskripsi**: Memperbarui data pelanggan yang sudah ada. Hanya field yang dikirim yang akan diubah.

- **Request Body**: Objek JSON berisi data yang ingin diubah.

- **Respons Sukses**: `200 OK` - Mengembalikan data pelanggan yang sudah diperbarui.

### `DELETE /{pelanggan_id}`

- **Deskripsi**: Menghapus data pelanggan berdasarkan ID.

- **Respons Sukses**: `204 No Content` - Tidak ada body respons.

### `GET /template/csv`

- **Deskripsi**: Mengunduh file template CSV yang bisa digunakan untuk mengimpor data pelanggan baru.

### `GET /export/csv`

- **Deskripsi**: Mengekspor semua data pelanggan yang ada di database ke dalam sebuah file CSV.

### `POST /import`

- **Deskripsi**: Mengimpor banyak data pelanggan baru dari sebuah file CSV.

- **Fitur Tambahan**: Dilengkapi validasi mendalam per baris dan akan memberikan laporan error yang spesifik jika ada data yang tidak valid.

- **Request Body**: `multipart/form-data` yang berisi file `.csv`.

---

&nbsp;

## **Endpoint Langganan (**`/langganan`**)**

Mengelola paket langganan yang dimiliki oleh setiap pelanggan.

&nbsp;

### `POST /`

- **Deskripsi**: Membuat langganan baru untuk seorang pelanggan.

- **Fitur Tambahan**: Otomatis menghitung harga dan tanggal jatuh tempo pertama berdasarkan metode pembayaran yang dipilih ('Otomatis' atau 'Prorate').

- **Request Body**: Objek JSON berisi `pelanggan_id`, `paket_layanan_id`, `status`, dan `metode_pembayaran`.

- **Respons Sukses**: `201 Created` - Mengembalikan data langganan yang baru dibuat.

### `GET /`

- **Deskripsi**: Mengambil daftar semua langganan dengan filter.

- **Query Parameters**:

  - `search` (opsional): Mencari berdasarkan nama pelanggan.

  - `status` (opsional): Filter berdasarkan status langganan (misal: "Aktif", "Suspended").

  - `paket_layanan_id` (opsional): Filter berdasarkan paket yang digunakan.

- **Respons Sukses**: `200 OK` - Mengembalikan daftar objek langganan.

### `PATCH /{langganan_id}`

- **Deskripsi**: Memperbarui data langganan yang sudah ada.

- **Respons Sukses**: `200 OK` - Mengembalikan data langganan yang sudah diubah.

### `DELETE /{langganan_id}`

- **Deskripsi**: Menghapus data langganan.

- **Respons Sukses**: `204 No Content`.

### `POST /calculate-price`

- **Deskripsi**: Endpoint khusus untuk frontend yang berfungsi sebagai "kalkulator". Frontend mengirim detail paket dan metode pembayaran, backend akan mengembalikan hasil perhitungan harga dan tanggal jatuh tempo tanpa menyimpan apapun.

### CSV (Template, Export, Import)

- Endpoint untuk mengunduh template (`GET /template/csv`), mengekspor semua data (`GET /export/csv`), dan mengimpor data langganan dari file CSV (`POST /import/csv`).

---

## **Endpoint Data Teknis (**`/data_teknis`**)**

&nbsp;

Mengelola informasi teknis pelanggan (akun PPPoE, detail OLT, dll).

### `POST /`

- **Deskripsi**: Membuat data teknis baru untuk seorang pelanggan.

- **Fitur Tambahan**: Setelah data teknis disimpan di database, endpoint ini akan secara otomatis memanggil `mikrotik_service` untuk membuat *secret* PPPoE baru di server Mikrotik yang sesuai.

- **Respons Sukses**: `201 Created` - Mengembalikan data teknis yang baru dibuat.

- **Respons Error**: `409 Conflict` - Jika pelanggan tersebut sudah memiliki data teknis.

### CRUD & CSV

- Sama seperti endpoint lain, menyediakan fungsi `GET /` (daftar), `GET /{id}` (detail), `PATCH /{id}` (update), `DELETE /{id}` (hapus), serta `GET /template/csv`, `GET /export/csv`, dan `POST /import/csv` untuk manajemen data teknis.

---

&nbsp;

## **Endpoint Invoice (**`/invoices`**)**

Mengelola semua hal terkait tagihan dan pembayaran.

### `POST /generate`

- **Deskripsi**: Membuat satu tagihan (invoice) secara manual untuk langganan tertentu.

- **Proses**: Menghitung total harga, menyimpan invoice ke database, lalu memanggil `xendit_service` untuk membuat link pembayaran. Link ini kemudian disimpan kembali ke data invoice.

- **Respons Error**: `409 Conflict` - Jika invoice untuk periode tersebut sudah ada.

### `GET /`

- **Deskripsi**: Mengambil daftar semua invoice dengan berbagai filter.

- **Query Parameters**:

  - `search` (opsional): Cari berdasarkan nomor invoice, nama pelanggan, atau ID PPPoE.

  - `status_invoice` (opsional): Filter berdasarkan status (misal: "Lunas", "Belum Dibayar").

  - `start_date` & `end_date` (opsional): Filter berdasarkan rentang tanggal jatuh tempo.

- **Respons Sukses**: `200 OK` - Mengembalikan daftar objek invoice.

### `POST /xendit-callback`

- **Deskripsi**: Endpoint **penting** yang tidak diakses oleh pengguna, melainkan oleh server Xendit. Xendit akan mengirim notifikasi ke alamat ini setiap kali ada perubahan status pembayaran (misalnya, saat pelanggan berhasil membayar).

- **Proses**:

  1. Memvalidasi token keamanan dari Xendit.

  2. Mencari invoice di database berdasarkan `external_id`.

  3. Jika statusnya `PAID`, endpoint ini akan memanggil fungsi `_process_successful_payment` untuk:

     - Mengubah status invoice menjadi "Lunas".

     - Mengubah status langganan menjadi "Aktif".

     - Menghitung dan mengatur tanggal jatuh tempo berikutnya.

     - Mengirim perintah ke Mikrotik untuk mengaktifkan kembali internet pelanggan.

     - Mengirim notifikasi pembayaran ke frontend via WebSocket.

&nbsp;

### `POST /{invoice_id}/mark-as-paid`

- **Deskripsi**: Menandai sebuah invoice sebagai "Lunas" secara manual (misalnya untuk pembayaran via transfer bank atau tunai).

- **Proses**: Memanggil fungsi `_process_successful_payment` yang sama dengan callback Xendit.

### `DELETE /{invoice_id}`

&nbsp;

- **Deskripsi**: Menghapus data invoice.

---

## **Endpoint Dashboard (**`/dashboard`**)**

Menyediakan data teragregasi untuk ditampilkan di halaman utama.

&nbsp;

### `GET /`

- **Deskripsi**: Mengambil semua data yang dibutuhkan untuk mengisi kartu statistik dan grafik di dashboard.

- **Proses**: Melakukan beberapa query ke database secara bersamaan untuk menghitung:

  - Jumlah total pelanggan per brand.

  - Jumlah total server Mikrotik.

  - 5 lokasi pelanggan terbanyak.

  - Distribusi jumlah pelanggan per paket internet.

  - Ringkasan status invoice (total, lunas, menunggu) selama 6 bulan terakhir.

- **Respons Sukses**: `200 OK` - Mengembalikan satu objek JSON besar berisi semua data dashboard.

### `GET /mikrotik-status`

- **Deskripsi**: Endpoint terpisah yang khusus untuk memeriksa status online/offline semua server Mikrotik secara *real-time*.

- **Proses**: Melakukan iterasi ke setiap server yang terdaftar, mencoba membuka koneksi, lalu menghitung berapa yang berhasil (online) dan gagal (offline).

### `GET /sidebar-badges`

- **Deskripsi**: Endpoint ringan yang dipanggil untuk menampilkan angka notifikasi di sidebar menu.

- **Proses**: Menghitung jumlah langganan dengan status "Suspended", "Berhenti", dan jumlah invoice yang "Belum Dibayar".

---

&nbsp;

## **Endpoint Server Mikrotik (**`/mikrotik_servers`**)**

Mengelola data server Mikrotik yang terhubung ke sistem.

### `POST /{server_id}/test_connection`

- **Deskripsi**: Menguji koneksi ke server Mikrotik yang dipilih.

- **Proses**: Mengambil data kredensial server dari database, mencoba membuka koneksi, dan mengambil versi RouterOS sebagai bukti koneksi berhasil.

- **Respons Sukses**: `200 OK` - Dengan pesan koneksi berhasil.

- **Respons Error**: `503 Service Unavailable` - Jika koneksi gagal.

### CRUD

- Menyediakan fungsi standar `POST /` (membuat), `GET /` (daftar), `GET /{id}` (detail), `PATCH /{id}` (update), dan `DELETE /{id}` (hapus) untuk mengelola data server Mikrotik.

---

&nbsp;

## **Endpoint Paket Layanan (**`/paket_layanan`**)**

Mengelola daftar paket internet yang ditawarkan.

### CRUD

- Menyediakan fungsi standar `POST /` (membuat), `GET /` (daftar), `GET /{id}` (detail), `PATCH /{id}` (update), dan `DELETE /{id}` (hapus) untuk mengelola data paket layanan.

---

&nbsp;

## **Endpoint Harga Layanan / Brand (**`/harga_layanan`**)**

Mengelola data brand, termasuk persentase pajak dan kunci API Xendit yang digunakan.

### CRUD

- Menyediakan fungsi standar `POST /` (membuat), `GET /` (daftar), `GET /{id}` (detail), `PATCH /{id}` (update), dan `DELETE /{id}` (hapus) untuk mengelola data brand.

---

## **Endpoint Pengguna (**`/users`**)**

Mengelola akun pengguna yang dapat login ke sistem.

### `POST /token`

- **Deskripsi**: Endpoint untuk login. Pengguna mengirim `username` (email) dan `password`.

- **Respons Sukses**: `200 OK` - Mengembalikan `access_token` yang digunakan untuk otentikasi.

- **Respons Error**: `401 Unauthorized` - Jika email atau password salah.

### `GET /me`

- **Deskripsi**: Mengambil informasi detail tentang pengguna yang sedang login saat ini.

### CRUD

- Menyediakan fungsi standar `POST /` (membuat user baru), `GET /` (daftar semua user), `GET /{id}` (detail), `PATCH /{id}` (update), dan `DELETE /{id}` (hapus).

### Lupa & Reset Password

- `POST /forgot-password`: Meminta token reset password dengan mengirimkan email.

- `POST /reset-password`: Mengatur password baru dengan menggunakan email dan token yang didapat dari langkah sebelumnya.

---

## **Endpoint Peran (**`/roles`**)**

Mengelola peran (Role) pengguna, seperti 'Admin', 'NOC', atau 'CS', beserta hak akses (Permissions) yang dimilikinya.

### CRUD

- Menyediakan fungsi standar `POST /` (membuat), `GET /` (daftar), `PATCH /{id}` (update), dan `DELETE /{id}` (hapus) untuk mengelola data peran dan hak aksesnya.

&nbsp;

---

&nbsp;

&nbsp;

### **Daftar Isi**

1. [Model: ](https://www.google.com/search?q=%23model-pelanggan)`Pelanggan`

2. [Model: ](https://www.google.com/search?q=%23model-langganan)`Langganan`

3. [Model: ](https://www.google.com/search?q=%23model-datateknis)`DataTeknis`

4. [Model: ](https://www.google.com/search?q=%23model-invoice)`Invoice`

5. [Model: ](https://www.google.com/search?q=%23model-mikrotikserver)`MikrotikServer`

6. [Model: ](https://www.google.com/search?q=%23model-paketlayanan)`PaketLayanan`

7. [Model: ](https://www.google.com/search?q=%23model-hargalayanan-brand)`HargaLayanan`[ (Brand)](https://www.google.com/search?q=%23model-hargalayanan-brand)

8. [Model: ](https://www.google.com/search?q=%23model-user)`User`

9. [Model: ](https://www.google.com/search?q=%23model-role)`Role`

---

&nbsp;

### **Model:** `Pelanggan`

&nbsp;

Tabel ini menyimpan data inti dari setiap pelanggan.

| Nama Kolom      | Tipe Data    | Deskripsi                                  | Keterangan                         |
| --------------- | ------------ | ------------------------------------------ | ---------------------------------- |
| `id`            | Integer      | ID unik untuk setiap pelanggan.            | **Primary Key**, Index             |
| `no_ktp`        | String       | Nomor KTP pelanggan.                       |                                    |
| `nama`          | String       | Nama lengkap pelanggan.                    | Index                              |
| `alamat`        | String       | Alamat utama pelanggan.                    | Index                              |
| `alamat_custom` | String       | Alamat tambahan atau custom.               | Opsional                           |
| `alamat_2`      | Teks Panjang | Detail alamat kedua atau catatan alamat.   | Opsional                           |
| `tgl_instalasi` | Tanggal      | Tanggal saat layanan diinstalasi.          | Opsional                           |
| `blok`          | String       | Informasi blok perumahan pelanggan.        |                                    |
| `unit`          | String       | Informasi unit atau nomor rumah pelanggan. |                                    |
| `no_telp`       | String       | Nomor telepon aktif pelanggan.             | Index                              |
| `email`         | String       | Alamat email aktif pelanggan.              | **Unique**, Index                  |
| `id_brand`      | String       | ID yang menghubungkan ke tabel Brand.      | **Foreign Key** ke `harga_layanan` |
| `layanan`       | String       | Jenis layanan yang digunakan.              | Opsional                           |
| `brand_default` | String       | Nama brand default untuk pelanggan.        | Opsional                           |

Ekspor ke Spreadsheet

**Relasi:**

- `data_teknis`: Terhubung ke satu `DataTeknis`.

- `langganan`: Terhubung ke banyak `Langganan`.

- `invoices`: Terhubung ke banyak `Invoice`.

- `harga_layanan`: Terhubung ke satu `HargaLayanan` (Brand).

---

&nbsp;

### **Model:** `Langganan`

&nbsp;

Tabel ini mencatat status langganan aktif setiap pelanggan terhadap suatu paket layanan.

| Nama Kolom             | Tipe Data       | Deskripsi                                         | Keterangan                         |
| ---------------------- | --------------- | ------------------------------------------------- | ---------------------------------- |
| `id`                   | Integer         | ID unik untuk setiap langganan.                   | **Primary Key**                    |
| `pelanggan_id`         | Integer         | ID yang menghubungkan ke pelanggan.               | **Foreign Key** ke `pelanggan`     |
| `paket_layanan_id`     | Integer         | ID yang menghubungkan ke paket layanan.           | **Foreign Key** ke `paket_layanan` |
| `tanggal_mulai`        | Tanggal         | Tanggal langganan ini dimulai.                    | Opsional                           |
| `status`               | String          | Status langganan (misal: "Aktif", "Suspended").   | Default: "Aktif"                   |
| `tgl_jatuh_tempo`      | Tanggal         | Tanggal jatuh tempo pembayaran berikutnya.        | Opsional                           |
| `tgl_invoice_terakhir` | Tanggal         | Tanggal invoice terakhir dibuat.                  | Opsional                           |
| `metode_pembayaran`    | String          | Metode pembayaran (misal: "Otomatis", "Prorate"). | Default: "Otomatis"                |
| `harga_awal`           | Angka Desimal   | Harga awal saat langganan dibuat.                 | Opsional                           |
| `created_at`           | Waktu & Tanggal | Waktu data dibuat.                                | Otomatis                           |
| `updated_at`           | Waktu & Tanggal | Waktu data terakhir diubah.                       | Otomatis                           |

Ekspor ke Spreadsheet

**Relasi:**

- `pelanggan`: Terhubung ke satu `Pelanggan`.

- `paket_layanan`: Terhubung ke satu `PaketLayanan`.

---

&nbsp;

### **Model:** `DataTeknis`

&nbsp;

Tabel ini menyimpan semua informasi teknis yang berhubungan dengan layanan pelanggan.

| Nama Kolom                 | Tipe Data | Deskripsi                                            | Keterangan                            |
| -------------------------- | --------- | ---------------------------------------------------- | ------------------------------------- |
| `id`                       | Integer   | ID unik untuk setiap data teknis.                    | **Primary Key**, Index                |
| `pelanggan_id`             | Integer   | ID yang menghubungkan ke pelanggan.                  | **Foreign Key** ke `pelanggan`        |
| `id_vlan`                  | String    | ID VLAN yang digunakan.                              |                                       |
| `id_pelanggan`             | String    | ID pelanggan di sistem lain (misal: username PPPoE). | Index                                 |
| `password_pppoe`           | String    | Password untuk login PPPoE.                          |                                       |
| `ip_pelanggan`             | String    | Alamat IP statis pelanggan.                          | Index                                 |
| `profile_pppoe`            | String    | Nama profil kecepatan di Mikrotik.                   |                                       |
| `olt`                      | String    | Nama atau ID perangkat OLT.                          | Index                                 |
| `olt_custom`               | String    | Nama OLT custom jika berbeda.                        | Opsional                              |
| `pon`, `otb`, `odc`, `odp` | Integer   | Informasi detail jalur fiber optik.                  | Opsional                              |
| `onu_power`                | Integer   | Nilai redaman sinyal optik (ONU Power).              | Opsional                              |
| `sn`                       | String    | Serial Number perangkat modem (ONU).                 | Opsional, Index                       |
| `speedtest_proof`          | String    | Link atau nama file bukti speedtest.                 | Opsional                              |
| `mikrotik_server_id`       | Integer   | ID server Mikrotik yang menangani pelanggan ini.     | **Foreign Key** ke `mikrotik_servers` |

Ekspor ke Spreadsheet

**Relasi:**

- `mikrotik_server`: Terhubung ke satu `MikrotikServer`.

- `pelanggan`: Terhubung ke satu `Pelanggan`.

---

&nbsp;

### **Model:** `Invoice`

&nbsp;

Tabel ini menyimpan riwayat semua tagihan yang dibuat untuk pelanggan.

| Nama Kolom           | Tipe Data       | Deskripsi                                         | Keterangan                     |
| -------------------- | --------------- | ------------------------------------------------- | ------------------------------ |
| `id`                 | Integer         | ID unik untuk setiap invoice.                     | **Primary Key**                |
| `invoice_number`     | String          | Nomor invoice yang unik.                          | **Unique**                     |
| `pelanggan_id`       | Integer         | ID yang menghubungkan ke pelanggan.               | **Foreign Key** ke `pelanggan` |
| `id_pelanggan`       | String          | ID PPPoE pelanggan (untuk kemudahan).             |                                |
| `brand`              | String          | Nama brand saat invoice dibuat.                   |                                |
| `total_harga`        | Angka Desimal   | Jumlah total yang harus dibayar.                  |                                |
| `no_telp`            | String          | Nomor telepon pelanggan saat invoice dibuat.      |                                |
| `email`              | String          | Email pelanggan saat invoice dibuat.              |                                |
| `tgl_invoice`        | Tanggal         | Tanggal invoice ini dibuat.                       |                                |
| `tgl_jatuh_tempo`    | Tanggal         | Batas akhir pembayaran.                           | Index                          |
| `status_invoice`     | String          | Status tagihan (misal: "Lunas", "Belum Dibayar"). | Index                          |
| `payment_link`       | Teks Panjang    | URL/link untuk melakukan pembayaran.              | Opsional                       |
| `metode_pembayaran`  | String          | Metode pembayaran yang digunakan.                 | Opsional                       |
| `expiry_date`        | Waktu & Tanggal | Tanggal kedaluwarsa link pembayaran.              | Opsional                       |
| `xendit_id`          | String          | ID invoice dari sistem Xendit.                    | Opsional                       |
| `xendit_external_id` | String          | ID unik invoice ini di sistem eksternal (Xendit). | Opsional, Index                |
| `paid_amount`        | Angka Desimal   | Jumlah yang dibayarkan.                           | Opsional                       |
| `paid_at`            | Waktu & Tanggal | Waktu saat pembayaran dikonfirmasi lunas.         | Opsional                       |
| `is_processing`      | Boolean         | Penanda jika invoice sedang diproses.             | Default: `False`               |
| `created_at`         | Waktu & Tanggal | Waktu data dibuat.                                | Otomatis                       |
| `updated_at`         | Waktu & Tanggal | Waktu data terakhir diubah.                       | Otomatis                       |
| `deleted_at`         | Waktu & Tanggal | Waktu data dihapus (soft delete).                 | Opsional                       |

Ekspor ke Spreadsheet

**Relasi:**

- `pelanggan`: Terhubung ke satu `Pelanggan`.

---

&nbsp;

### **Model:** `MikrotikServer`

&nbsp;

Tabel ini menyimpan informasi kredensial untuk setiap server Mikrotik yang digunakan.

| Nama Kolom               | Tipe Data       | Deskripsi                                             | Keterangan        |
| ------------------------ | --------------- | ----------------------------------------------------- | ----------------- |
| `id`                     | Integer         | ID unik untuk setiap server.                          | **Primary Key**   |
| `name`                   | String          | Nama server (misal: "Mikrotik-Pusat").                | **Unique**, Index |
| `host_ip`                | String          | Alamat IP atau domain dari server Mikrotik.           | Index             |
| `username`               | String          | Username untuk login ke API Mikrotik.                 |                   |
| `password`               | Teks Panjang    | Password untuk login ke API Mikrotik.                 |                   |
| `port`                   | Integer         | Port API Mikrotik.                                    | Default: 8728     |
| `ros_version`            | String          | Versi RouterOS yang terdeteksi.                       | Opsional          |
| `is_active`              | Boolean         | Menandakan apakah server ini aktif digunakan.         | Default: `True`   |
| `last_connection_status` | String          | Status koneksi terakhir (misal: "Online", "Offline"). | Opsional          |
| `last_connected_at`      | Waktu & Tanggal | Waktu terakhir berhasil terhubung.                    | Opsional          |
| `created_at`             | Waktu & Tanggal | Waktu data dibuat.                                    | Otomatis          |
| `updated_at`             | Waktu & Tanggal | Waktu data terakhir diubah.                           | Otomatis          |

Ekspor ke Spreadsheet

**Relasi:**

- `data_teknis_pelanggan`: Terhubung ke banyak `DataTeknis`.

---

&nbsp;

### **Model:** `PaketLayanan`

&nbsp;

Tabel ini menyimpan daftar semua paket layanan internet yang ditawarkan.

| Nama Kolom   | Tipe Data     | Deskripsi                           | Keterangan                         |
| ------------ | ------------- | ----------------------------------- | ---------------------------------- |
| `id`         | Integer       | ID unik untuk setiap paket.         | **Primary Key**                    |
| `id_brand`   | String        | ID brand pemilik paket ini.         | **Foreign Key** ke `harga_layanan` |
| `nama_paket` | String        | Nama paket (misal: "Home 20 Mbps"). |                                    |
| `kecepatan`  | Integer       | Kecepatan internet dalam Mbps.      |                                    |
| `harga`      | Angka Desimal | Harga dasar paket sebelum pajak.    |                                    |

Ekspor ke Spreadsheet

**Relasi:**

- `harga_layanan`: Terhubung ke satu `HargaLayanan` (Brand).

- `langganan`: Terhubung ke banyak `Langganan`.

---

&nbsp;

### **Model:** `HargaLayanan` **(Brand)**

&nbsp;

Tabel ini berfungsi sebagai tabel "Brand", menyimpan informasi unik per brand seperti pajak.

| Nama Kolom        | Tipe Data     | Deskripsi                                            | Keterangan         |
| ----------------- | ------------- | ---------------------------------------------------- | ------------------ |
| `id_brand`        | String        | ID unik untuk setiap brand (misal: "ajn-01").        | **Primary Key**    |
| `brand`           | String        | Nama brand (misal: "Jakinet").                       |                    |
| `pajak`           | Angka Desimal | Persentase pajak untuk brand ini (misal: 11.00).     |                    |
| `xendit_key_name` | String        | Nama kunci API Xendit yang digunakan oleh brand ini. | Default: "JAKINET" |

Ekspor ke Spreadsheet

**Relasi:**

- `pelanggan`: Terhubung ke banyak `Pelanggan`.

- `paket_layanan`: Terhubung ke banyak `PaketLayanan`.

---

&nbsp;

### **Model:** `User`

&nbsp;

Tabel ini menyimpan data login untuk pengguna sistem (admin, cs, noc).

| Nama Kolom          | Tipe Data       | Deskripsi                        | Keterangan                 |
| ------------------- | --------------- | -------------------------------- | -------------------------- |
| `id`                | Integer         | ID unik untuk setiap pengguna.   | **Primary Key**, Index     |
| `name`              | String          | Nama lengkap pengguna.           |                            |
| `email`             | String          | Alamat email untuk login.        | **Unique**, Index          |
| `email_verified_at` | Waktu & Tanggal | Waktu saat email diverifikasi.   | Opsional                   |
| `password`          | String          | Password yang sudah di-hash.     |                            |
| `remember_token`    | String          | Token untuk fitur "Ingat Saya".  | Opsional                   |
| `created_at`        | Waktu & Tanggal | Waktu akun dibuat.               | Otomatis                   |
| `updated_at`        | Waktu & Tanggal | Waktu akun terakhir diubah.      | Otomatis                   |
| `role_id`           | Integer         | ID peran yang dimiliki pengguna. | **Foreign Key** ke `roles` |

Ekspor ke Spreadsheet

**Relasi:**

- `role`: Terhubung ke satu `Role`.

---

&nbsp;

### **Model:** `Role`

&nbsp;

Tabel ini menyimpan daftar peran (role) yang ada di sistem.

| Nama Kolom | Tipe Data | Deskripsi                                 | Keterangan             |
| ---------- | --------- | ----------------------------------------- | ---------------------- |
| `id`       | Integer   | ID unik untuk setiap peran.               | **Primary Key**, Index |
| `name`     | String    | Nama peran (misal: "Admin", "NOC", "CS"). | **Unique**             |

Ekspor ke Spreadsheet

**Relasi:**

- `users`: Terhubung ke banyak `User`.

- `permissions`: Terhubung ke banyak `Permission` (hak akses).

<SwmMeta version="3.0.0" repo-id="Z2l0aHViJTNBJTNBQmlsbGluZ0Z0dGhWMiUzQSUzQUFobWFkLVJpemtpMjE=" repo-name="BillingFtthV2"><sup>Powered by [Swimm](https://app.swimm.io/)</sup></SwmMeta>
