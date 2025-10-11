# app/jobs.py

import logging
import traceback
from datetime import date, timedelta, datetime, timezone
from dateutil.relativedelta import relativedelta
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import joinedload
import uuid
import math
import asyncio

# Impor komponen
from .database import AsyncSessionLocal
from .models import (
    Langganan as LanggananModel,
    Invoice as InvoiceModel,
    Pelanggan as PelangganModel,
    MikrotikServer as MikrotikServerModel,
)
from .services import mikrotik_service, xendit_service
from .logging_config import log_scheduler_event
from .routers.invoice import _process_successful_payment
from .models import DataTeknis as DataTeknisModel

logger = logging.getLogger("app.jobs")


async def job_check_server_connectivity():
    """Tugas untuk memeriksa konektivitas semua server Mikrotik yang aktif."""
    log_scheduler_event(logger, "job_check_server_connectivity", "started")
    total_servers = 0
    successful_checks = 0
    async with AsyncSessionLocal() as db:  # type: ignore
        try:
            stmt = select(MikrotikServerModel).where(MikrotikServerModel.is_active == True)
            result = await db.execute(stmt)
            servers = result.scalars().all()
            total_servers = len(servers)

            for server in servers:
                try:
                    device_details = {
                        "host": server.host_ip,
                        "username": server.username,
                        "password": server.password,
                        "port": server.port,
                    }
                    
                    loop = asyncio.get_event_loop()
                    test_result = await loop.run_in_executor(None, mikrotik_service.perform_routeros_connection, device_details)

                    server.last_connection_status = test_result.get("status", "failure")
                    server.last_connection_message = test_result.get("message", "Unknown error")
                    server.last_connection_time = datetime.now(timezone.utc)

                    if test_result.get("status") == "success":
                        data_result = test_result.get("data", {})
                        if isinstance(data_result, dict):
                            server.ros_version = data_result.get("ros_version")
                        successful_checks += 1

                except Exception as e:
                    server.last_connection_status = "failure"
                    server.last_connection_message = f"Job error: {e}"
                    server.last_connection_time = datetime.now(timezone.utc)
                    logger.error(f"Failed to check server {server.name}: {e}")

            await db.commit()
            log_scheduler_event(
                logger,
                "job_check_server_connectivity",
                "completed",
                f"Checked {total_servers} servers. Successful: {successful_checks}, Failed: {total_servers - successful_checks}."
            )

        except Exception:
            await db.rollback()
            logger.error(f"[FAIL] Scheduler 'job_check_server_connectivity' failed: {traceback.format_exc()}")


# Fungsi generate_single_invoice - OPTIMIZED to avoid N+1 queries
async def generate_single_invoice(db, langganan: LanggananModel):
    try:
        # OPTIMIZATION: Check if relationships are already loaded to avoid N+1 problems
        # If called from job_generate_invoices, relationships should be pre-loaded

        # Check if pelanggan relationship is loaded
        if hasattr(langganan, '_pelanggan') and langganan._pelanggan is not None:
            # Relationships are already loaded (from job_generate_invoices)
            pelanggan = langganan.pelanggan
            paket = langganan.paket_layanan
            brand = pelanggan.harga_layanan
            data_teknis = pelanggan.data_teknis
        else:
            # Relationships not loaded, need to load them efficiently
            from sqlalchemy.future import select

            # Load all required relationships in one query
            stmt = (
                select(LanggananModel)
                .options(
                    joinedload(LanggananModel.pelanggan).options(
                        joinedload(PelangganModel.harga_layanan),
                        joinedload(PelangganModel.data_teknis)
                    ),
                    joinedload(LanggananModel.paket_layanan)
                )
                .where(LanggananModel.id == langganan.id)
            )

            result = await db.execute(stmt)
            langganan_loaded = result.scalars().first()

            if not langganan_loaded:
                logger.error(f"Langganan tidak ditemukan untuk ID {langganan.id}. Skip.")
                return

            pelanggan = langganan_loaded.pelanggan
            paket = langganan_loaded.paket_layanan
            brand = pelanggan.harga_layanan
            data_teknis = pelanggan.data_teknis

        if not all([pelanggan, paket, brand, data_teknis]):
            logger.error(f"Data tidak lengkap untuk langganan ID {langganan.id}. Skip.")
            return

        harga_dasar = float(paket.harga)
        pajak_persen = float(brand.pajak)
        pajak_mentah = harga_dasar * (pajak_persen / 100)
        pajak = math.floor(pajak_mentah + 0.5)
        total_harga = harga_dasar + pajak

        new_invoice_data = {
            "invoice_number": f"INV-{date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            "pelanggan_id": pelanggan.id,
            "id_pelanggan": data_teknis.id_pelanggan,
            "brand": brand.brand,
            "total_harga": total_harga,
            "no_telp": pelanggan.no_telp,
            "email": pelanggan.email,
            "tgl_invoice": date.today(),
            "tgl_jatuh_tempo": langganan.tgl_jatuh_tempo,
            "status_invoice": "Belum Dibayar",
        }

        db_invoice = InvoiceModel(**new_invoice_data)
        db.add(db_invoice)
        await db.flush()

        deskripsi_xendit = ""
        jatuh_tempo_str_lengkap = datetime.combine(db_invoice.tgl_jatuh_tempo, datetime.min.time()).strftime("%d/%m/%Y")  # type: ignore

        if langganan.metode_pembayaran == "Prorate":
            # ▼▼▼ LOGIKA BARU DIMULAI DI SINI ▼▼▼

            # Hitung harga normal untuk perbandingan
            harga_normal_full = float(paket.harga) * (1 + (float(brand.pajak) / 100))

            # Cek apakah ini invoice gabungan
            if db_invoice.total_harga > (harga_normal_full + 1):
                # INI TAGIHAN GABUNGAN
                start_day = db_invoice.tgl_invoice.day  # type: ignore
                end_day = db_invoice.tgl_jatuh_tempo.day  # type: ignore
                periode_prorate_str = datetime.combine(db_invoice.tgl_jatuh_tempo, datetime.min.time()).strftime("%B %Y")  # type: ignore
                periode_berikutnya_str = (
                    datetime.combine(db_invoice.tgl_jatuh_tempo, datetime.min.time()) + relativedelta(months=1)  # type: ignore
                ).strftime("%B %Y")

                deskripsi_xendit = (
                    f"Biaya internet up to {paket.kecepatan} Mbps. "
                    f"Periode Prorate {start_day}-{end_day} {periode_prorate_str} + "
                    f"Periode {periode_berikutnya_str}"
                )
            else:
                # INI TAGIHAN PRORATE BIASA
                start_day = db_invoice.tgl_invoice.day  # type: ignore
                end_day = db_invoice.tgl_jatuh_tempo.day  # type: ignore
                periode_str = datetime.combine(db_invoice.tgl_jatuh_tempo, datetime.min.time()).strftime("%B %Y")  # type: ignore
                deskripsi_xendit = (
                    f"Biaya berlangganan internet up to {paket.kecepatan} Mbps, "
                    f"Periode Tgl {start_day}-{end_day} {periode_str}"
                )

        else:  # Otomatis
            deskripsi_xendit = (
                f"Biaya berlangganan internet up to {paket.kecepatan} Mbps "
                f"jatuh tempo pembayaran tanggal {jatuh_tempo_str_lengkap}"
            )

        # Format nomor telepon untuk Xendit (tanpa '+')
        no_telp_bersih = ""
        if pelanggan.no_telp:
            # Hapus spasi dan karakter non-numerik kecuali '+' di awal
            no_telp_bersih = ''.join(filter(str.isdigit, pelanggan.no_telp))
            # Handle '0' di depan -> '62'
            if no_telp_bersih.startswith('0'):
                no_telp_bersih = '62' + no_telp_bersih[1:]
            # Jika sudah '62' di depan, biarkan
            elif no_telp_bersih.startswith('62'):
                pass
            # Untuk format lain, coba tambahkan '62' (asumsi nomor lokal tanpa 0)
            else:
                no_telp_bersih = '62' + no_telp_bersih

        no_telp_xendit = no_telp_bersih if no_telp_bersih else None

        xendit_response = await xendit_service.create_xendit_invoice(
            db_invoice, pelanggan, paket, deskripsi_xendit, pajak, no_telp_xendit or ""
        )

        db_invoice.payment_link = xendit_response.get(
            "short_url", xendit_response.get("invoice_url")
        )
        db_invoice.xendit_id = xendit_response.get("id")
        db_invoice.xendit_external_id = xendit_response.get("external_id")

        db.add(db_invoice)
        logger.info(
            f"Invoice {db_invoice.invoice_number} berhasil dibuat untuk Langganan ID {langganan.id}"
        )

    except Exception as e:
        logger.error(
            f"Gagal membuat invoice untuk Langganan ID {langganan.id}: {e}\n{traceback.format_exc()}"
        )


# ==========================================================
# --- JOB SCHEDULER YANG SUDAH DIOPTIMALKAN ---
# ==========================================================


async def job_generate_invoices():
    log_scheduler_event(logger, "job_generate_invoices", "started")
    target_due_date = date.today() + timedelta(days=5)
    total_invoices_created = 0
    BATCH_SIZE = 100
    offset = 0

    async with AsyncSessionLocal() as db:  # type: ignore
        while True:
            try:
                base_stmt = (
                    select(LanggananModel)
                    .where(
                        LanggananModel.tgl_jatuh_tempo == target_due_date,
                        LanggananModel.status == "Aktif",
                    )
                    .options(
                        joinedload(LanggananModel.pelanggan).options(
                            joinedload(PelangganModel.harga_layanan),
                            joinedload(PelangganModel.data_teknis)
                        ),
                        joinedload(LanggananModel.paket_layanan),
                    )
                )

                batch_stmt = base_stmt.offset(offset).limit(BATCH_SIZE)
                subscriptions_batch = (
                    (await db.execute(batch_stmt)).scalars().unique().all()
                )

                if not subscriptions_batch:
                    break

                # OPTIMISASI: Ambil semua invoice yang sudah ada untuk batch ini dalam satu query
                pelanggan_ids_in_batch = [s.pelanggan_id for s in subscriptions_batch]
                existing_invoices_stmt = select(InvoiceModel.pelanggan_id).where(
                    InvoiceModel.pelanggan_id.in_(pelanggan_ids_in_batch),
                    InvoiceModel.tgl_jatuh_tempo == target_due_date,
                )
                existing_invoices_pelanggan_ids = {
                    row[0] for row in await db.execute(existing_invoices_stmt)
                }

                for langganan in subscriptions_batch:
                    # Cek dari data yang sudah di-prefetch, bukan query baru
                    if langganan.pelanggan_id not in existing_invoices_pelanggan_ids:
                        await generate_single_invoice(db, langganan)
                        total_invoices_created += 1

                await db.commit()
                offset += BATCH_SIZE

            except Exception as e:
                await db.rollback()
                error_details = traceback.format_exc()
                logger.error(
                    f"[FAIL] Scheduler 'job_generate_invoices' failed at offset {offset}. Details:\n{error_details}"
                )
                break

    if total_invoices_created > 0:
        log_scheduler_event(
            logger,
            "job_generate_invoices",
            "completed",
            f"Berhasil membuat {total_invoices_created} invoice baru.",
        )
    else:
        log_scheduler_event(
            logger,
            "job_generate_invoices",
            "completed",
            "Tidak ada invoice baru yang perlu dibuat.",
        )


async def job_suspend_services():
    """
    Tugas untuk men-suspend layanan pelanggan yang belum bayar sampai tanggal 4.
    Berjalan tepat tanggal 5 jam 00:00 setiap bulan untuk menangguhkan layanan
    pelanggan yang telat bayar dari jatuh tempo tanggal 1.
    """
    log_scheduler_event(logger, "job_suspend_services", "started")
    total_services_suspended = 0
    total_invoices_overdue = 0
    current_date = date.today()
    BATCH_SIZE = 50
    offset = 0

    # Logika bisnis: Jatuh tempo tanggal 1, suspend tanggal 5 jam 00:00
    # Cari invoice yang jatuh tempo tanggal 1 bulan ini dan masih belum dibayar
    current_month = current_date.month
    current_year = current_date.year

    # Buat tanggal jatuh tempo (tanggal 1 bulan ini)
    due_date_this_month = date(current_year, current_month, 1)

    log_scheduler_event(
        logger,
        "job_suspend_services",
        "info",
        f"Mencari invoice dengan jatuh tempo {due_date_this_month} untuk di-suspend"
    )

    async with AsyncSessionLocal() as db:  # type: ignore
        while True:
            try:
                base_stmt = (
                    select(LanggananModel)
                    .join(
                        InvoiceModel,
                        LanggananModel.pelanggan_id == InvoiceModel.pelanggan_id,
                    )
                    .where(
                        InvoiceModel.tgl_jatuh_tempo == due_date_this_month,
                        LanggananModel.status == "Aktif",
                        InvoiceModel.status_invoice == "Belum Dibayar",
                    )
                    .distinct(
                        LanggananModel.id
                    )  # Pastikan setiap langganan hanya diproses sekali
                    .options(
                        joinedload(LanggananModel.pelanggan).joinedload(
                            PelangganModel.data_teknis
                        )
                    )
                )

                batch_stmt = base_stmt.offset(offset).limit(BATCH_SIZE)
                overdue_batch = (await db.execute(batch_stmt)).scalars().unique().all()

                if not overdue_batch:
                    break

                for langganan in overdue_batch:
                    logger.warning(
                        f"Melakukan suspend layanan untuk Langganan ID: {langganan.id} - Pelanggan: {langganan.pelanggan.nama if langganan.pelanggan else 'Unknown'}..."
                    )

                    # 1. Ubah status invoice terkait menjadi 'Kadaluarsa'
                    update_invoice_stmt = (
                        update(InvoiceModel)
                        .where(InvoiceModel.pelanggan_id == langganan.pelanggan_id)
                        .where(InvoiceModel.status_invoice == "Belum Dibayar")
                        .where(InvoiceModel.tgl_jatuh_tempo == due_date_this_month)
                        .values(status_invoice="Kadaluarsa")
                    )
                    invoice_update_result = await db.execute(update_invoice_stmt)
                    total_invoices_overdue += invoice_update_result.rowcount

                    # 2. Ubah status langganan menjadi 'Suspended'
                    langganan.status = "Suspended"
                    db.add(langganan)

                    data_teknis = langganan.pelanggan.data_teknis
                    if data_teknis:
                        try:
                            await mikrotik_service.trigger_mikrotik_update(
                                db, langganan, data_teknis, data_teknis.id_pelanggan
                            )
                            total_services_suspended += 1
                            logger.info(
                                f"✓ Berhasil suspend Mikrotik untuk Langganan ID: {langganan.id}"
                            )
                        except Exception as e:
                            logger.error(
                                f"✗ Gagal suspend Mikrotik untuk Langganan ID {langganan.id}: {e}"
                            )
                    else:
                        logger.error(
                            f"Data Teknis tidak ditemukan untuk langganan ID {langganan.id}, skip update Mikrotik."
                        )

                await db.commit()
                offset += BATCH_SIZE

            except Exception as e:
                await db.rollback()
                logger.error(
                    f"[FAIL] Scheduler 'job_suspend_services' failed at offset {offset}. Details: {traceback.format_exc()}"
                )
                break

    if total_services_suspended > 0:
        log_scheduler_event(
            logger,
            "job_suspend_services",
            "completed",
            f"Berhasil suspend {total_services_suspended} layanan dan mengubah {total_invoices_overdue} invoice menjadi Kadaluarsa.",
        )
    else:
        log_scheduler_event(
            logger,
            "job_suspend_services",
            "completed",
            f"Tidak ada layanan baru untuk di-suspend. Total invoice kadaluarsa: {total_invoices_overdue}",
        )


async def job_send_payment_reminders():
    log_scheduler_event(logger, "job_send_payment_reminders", "started")
    total_reminders_sent = 0
    target_due_date = date.today() + timedelta(days=3)
    BATCH_SIZE = 100
    offset = 0

    async with AsyncSessionLocal() as db:  # type: ignore
        while True:
            try:
                base_stmt = (
                    select(LanggananModel)
                    .where(
                        LanggananModel.tgl_jatuh_tempo == target_due_date,
                        LanggananModel.status == "Aktif",
                    )
                    .options(joinedload(LanggananModel.pelanggan))
                )

                batch_stmt = base_stmt.offset(offset).limit(BATCH_SIZE)
                reminder_batch = (await db.execute(batch_stmt)).scalars().unique().all()

                if not reminder_batch:
                    break

                for langganan in reminder_batch:
                    pelanggan = langganan.pelanggan
                    logger.info(
                        f"Mengirim pengingat pembayaran untuk pelanggan ID: {pelanggan.id} ({pelanggan.nama})"
                    )
                    # Di sini Anda bisa menambahkan logika pengiriman notifikasi (WA, Email, dll)
                    total_reminders_sent += 1

                # Tidak ada db.commit() karena kita hanya membaca data
                offset += BATCH_SIZE

            except Exception as e:
                logger.error(
                    f"[FAIL] Scheduler 'job_send_payment_reminders' failed at offset {offset}. Details: {traceback.format_exc()}"
                )
                break

    if total_reminders_sent > 0:
        log_scheduler_event(
            logger,
            "job_send_payment_reminders",
            "completed",
            f"Berhasil mengirim {total_reminders_sent} pengingat pembayaran.",
        )
    else:
        log_scheduler_event(
            logger,
            "job_send_payment_reminders",
            "completed",
            "Tidak ada pelanggan untuk dikirim pengingat hari ini.",
        )


async def job_verify_payments():
    """Job HANYA untuk rekonsiliasi pembayaran yang terlewat via Xendit."""
    log_scheduler_event(logger, "job_verify_payments", "started")

    async with AsyncSessionLocal() as db:  # type: ignore
        try:
            # Bagian 1: Logika Kadaluarsa SUDAH DIHAPUS DARI SINI

            # Bagian 2: Rekonsiliasi Pembayaran Terlewat
            paid_invoice_ids = await xendit_service.get_paid_invoice_ids_since(days=3)

            if not paid_invoice_ids:
                log_scheduler_event(
                    logger,
                    "job_verify_payments",
                    "completed",
                    "Tidak ada pembayaran baru di Xendit.",
                )
                await db.commit()  # Tetap commit untuk menutup transaksi
                return

            # PERBAIKAN: Eager load semua relasi yang dibutuhkan oleh _process_successful_payment
            unprocessed_stmt = (
                select(InvoiceModel)
                .where(
                    InvoiceModel.xendit_external_id.in_(paid_invoice_ids),
                    InvoiceModel.status_invoice != "Lunas",
                )
                .options(
                    joinedload(InvoiceModel.pelanggan).options(
                        joinedload(PelangganModel.harga_layanan),
                        joinedload(PelangganModel.langganan).joinedload(
                            LanggananModel.paket_layanan
                        ),
                        joinedload(PelangganModel.data_teknis),
                    )
                )
            )
            invoices_to_process = (
                (await db.execute(unprocessed_stmt)).scalars().unique().all()
            )

            processed_count = 0
            if invoices_to_process:
                logger.warning(
                    f"[VERIFY] Menemukan {len(invoices_to_process)} pembayaran terlewat. Memproses..."
                )
                for invoice in invoices_to_process:
                    await _process_successful_payment(db, invoice)
                    processed_count += 1

            await db.commit()
            log_scheduler_event(
                logger,
                "job_verify_payments",
                "completed",
                f"Memproses {processed_count} pembayaran terlewat.",
            )

        except Exception as e:
            await db.rollback()
            error_details = traceback.format_exc()
            logger.error(
                f"[FAIL] Scheduler 'job_verify_payments' failed. Details:\n{error_details}"
            )


async def job_retry_mikrotik_syncs():
    log_scheduler_event(logger, "job_retry_mikrotik_syncs", "started")
    total_retried = 0
    async with AsyncSessionLocal() as db:  # type: ignore
        try:
            # Cari semua data teknis yang sinkronisasinya tertunda
            stmt = (
                select(DataTeknisModel)
                .where(DataTeknisModel.mikrotik_sync_pending == True)
                .options(
                    joinedload(DataTeknisModel.pelanggan).joinedload(
                        PelangganModel.langganan
                    )
                )
            )
            pending_syncs = (await db.execute(stmt)).scalars().all()

            if not pending_syncs:
                log_scheduler_event(
                    logger,
                    "job_retry_mikrotik_syncs",
                    "completed",
                    "No pending Mikrotik syncs.",
                )
                return

            logger.info(f"Found {len(pending_syncs)} pending Mikrotik syncs to retry.")
            for data_teknis in pending_syncs:
                try:
                    langganan = data_teknis.pelanggan.langganan[0]
                    # Coba jalankan lagi fungsi update ke Mikrotik DENGAN ARGUMEN LENGKAP
                    await mikrotik_service.trigger_mikrotik_update(
                        db, langganan, data_teknis, data_teknis.id_pelanggan
                    )

                    # Jika berhasil, set flag kembali ke False
                    data_teknis.mikrotik_sync_pending = False  # type: ignore
                    db.add(data_teknis)
                    logger.info(
                        f"Successfully synced pending update for Data Teknis ID: {data_teknis.id}"
                    )
                    total_retried += 1
                except Exception as e:
                    # Jika masih gagal, biarkan flag tetap True dan catat error
                    logger.error(
                        f"Still failing to sync Mikrotik for Data Teknis ID {data_teknis.id}: {e}"
                    )

            await db.commit()
            log_scheduler_event(
                logger,
                "job_retry_mikrotik_syncs",
                "completed",
                f"Successfully retried {total_retried} syncs.",
            )
        except Exception:
            await db.rollback()
            logger.error(
                f"[FAIL] Scheduler 'job_retry_mikrotik_syncs' encountered an error: {traceback.format_exc()}"
            )
