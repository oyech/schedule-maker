# ShiftMaster - Aplikasi Jadwal Kerja Engineering TAR

Aplikasi web modern untuk mengelola Jadwal Kerja (Shift Roster) Engineering Department Taman Anggrek Residence, mendukung rotasi 24 jam otomatis berkesinambungan serta format khusus HRIS GreatDay.

## Fitur Utama

1. **Jadwal Kerja Engineering 24 Jam (`/schedule` atau `/`)**
   - Pemilihan **Bulan** & **Tahun** dinamis menyesuaikan jumlah hari kalender (28-31 hari), nama hari (`Sn`, `Sl`, `Rb`, `Km`, `Jm`, `Sb`, `Mg`), dan hari libur nasional otomatis.
   - Pembagian 3 kelompok kerja:
     1. **Staff & Supervisor (Reguler)**: `R1` (08:30 - 17:00) pada hari kerja, giliran piket `R3` / `OFF` pada Sabtu, dan `OFF` pada Minggu serta Libur Nasional.
     2. **Engineering Shift (24 Jam)**: Siklus rotasi `P, P, S, S, M, M, OFF, OFF` otomatis bergulir (*continuous rollover*) lintas bulan.
     3. **Daily Worker (DW)**: `R4` (Senin-Sabtu) dan `OFF` (Minggu).
   - **Fitur Rolling Shift**: Tombol **Putar Maju ▶** / **◀ Putar Mundur** untuk menggulirkan posisi shift 24 jam secara instan.
   - **Kelola Personil**: Tambah personil baru, edit Nama/Jabatan langsung (*inline edit*), atau hapus personil dengan penyimpanan otomatis di browser.
   - **Tukar Jaga & Cuti Interaktif**: Klik sel shift harian di layar untuk mengubah shift (*quick picker popover*).
   - **Pencarian Cepat**: Filter pencarian instan nama karyawan atau jabatan secara real-time.
   - **Salin ke Excel (Ctrl+V)**: Salin seluruh matriks tabel langsung siap paste ke Excel.
   - **Export Excel Resmi (.xlsx)**: Template Excel resmi instansi lengkap dengan header, ringkasan jam kerja, legenda, dan kolom tanda tangan.

2. **Schedule GreatDay HRIS (`/schedule-greatday`)**
   - Format khusus dengan penamaan shift resmi GreatDay:
     - `Shift 3` (Pagi, 07:00 - 15:00)
     - `Shift 41` (Siang, 15:00 - 23:00)
     - `Shift 52` (Malam, 23:00 - 07:00)
     - `Shift 14` (Reguler, 08:30 - 17:00)
     - `Shift 12` (Piket Sabtu, 08:30 - 13:30)
     - `OFF` (Libur Jaga / Akhir Pekan)
     - `R4` (Daily Worker, 08:30 - 17:30)
   - Kolom matriks tanggal otomatis disesuaikan agar teks shift GreatDay pas dan terbaca jelas.
   - Ekspor Excel dan Salin ke Excel (Ctrl+V) langsung dalam format nama GreatDay.

## Cara Menjalankan

Jalankan perintah:
```bash
cd "/Volumes/CrossDATA/myProject/extract-report"
./run.sh
```
atau
```bash
.venv/bin/python app.py
```
Akses di browser: `http://localhost:5006`
