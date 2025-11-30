---
title: Dokumentasi - Otentikasi & Pengguna
---
**Base URL**: <http://127.0.0.1:8000>

**1. Otentikasi**

Saat ini, API belum menerapkan sistem otentikasi. Semua endpoint dapat diakses secara publik. Implementasi token (JWT) akan menjadi langkah selanjutnya.

**2. Manajemen Pengguna & Peran**

**Roles**

Mengelola peran pengguna (misalnya, admin, sales, finance).

**POST /roles/**

Membuat peran baru.

- Request Body:

·         {

·           "name": "finance"

·         }

&nbsp;

- Success Response (201 Created):

·         {

·           "name": "finance",

·           "id": 3

·         }

&nbsp;

- **Error Response (409 Conflict)**: Terjadi jika nama role sudah ada.

·         {

·           "detail": "Role dengan nama 'finance' sudah ada."

·         }

&nbsp;

**GET /roles/**

Mendapatkan semua peran yang ada.

- **Success Response (200 OK)**:

·         \[

·           { "name": "administrator", "id": 1 },

·           { "name": "noc", "id": 2 },

·           { "name": "finance", "id": 3 }

·         \]

&nbsp;

**PATCH /roles/{role_id}**

Memperbarui nama peran.

- **Request Body**:

·         {

·           "name": "finance_staff"

·         }

&nbsp;

- **Success Response (200 OK)**:

·         {

·           "name": "finance_staff",

·           "id": 3

·         }

&nbsp;

**DELETE /roles/{role_id}**

Menghapus sebuah peran.

- **Success Response**: 204 No Content (Tidak ada body respons).

- **Catatan**: Jika ada user yang masih menggunakan role ini, role_id pada user tersebut akan menjadi NULL karena kita menggunakan ON DELETE SET NULL.

**Users**

Mengelola akun pengguna yang dapat mengakses sistem.

**POST /users/**

Membuat pengguna baru.

- **Request Body**:

·         {

·           "name": "Budi Finance",

·           "email": "[budi.finance@example.com](mailto:budi.finance@example.com)",

·           "password": "password_aman_123",

·           "role_id": 3

·         }

&nbsp;

- **Success Response (201 Created)**: (Password tidak pernah dikembalikan)

·         {

·           "name": "Budi Finance",

·           "email": "[budi.finance@example.com](mailto:budi.finance@example.com)",

·           "id": 2,

·           "role_id": 3,

·           "created_at": "2025-07-17T10:30:00.123Z",

·           "updated_at": "2025-07-17T10:30:00.123Z"

·         }

&nbsp;

**GET /users/**

Mendapatkan semua pengguna.

- **Success Response (200 OK)**: Array berisi objek pengguna.

**GET /users/{user_id}**

Mendapatkan detail satu pengguna.

- **Success Response (200 OK)**: Objek pengguna tunggal.

**PATCH /users/{user_id}**

Memperbarui data pengguna.

- **Request Body**:

·         {

·           "name": "Budi Hartono",

·           "role_id": 2

·         }

&nbsp;

- **Success Response (200 OK)**: Objek pengguna yang telah diperbarui.

**DELETE /users/{user_id}**

Menghapus pengguna.

- **Success Response**: 204 No Content.

<SwmMeta version="3.0.0" repo-id="Z2l0aHViJTNBJTNBQmlsbGluZ0Z0dGhWMiUzQSUzQUFobWFkLVJpemtpMjE=" repo-name="BillingFtthV2"><sup>Powered by [Swimm](https://app.swimm.io/)</sup></SwmMeta>
