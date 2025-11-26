from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from werkzeug.utils import secure_filename
import hashlib
import json
import os
from datetime import datetime
from typing import List, Dict, Any


EVENTS_FILE = "events.json"
USERS_FILE = "users.json"
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def create_app() -> Flask:
    """Factory untuk membuat instance Flask app."""
    app = Flask(__name__)
    app.secret_key = "dev-secret-key"  # untuk flash message & session (demo sederhana)

    # Konfigurasi upload folder
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    # Pastikan file events.json ada
    if not os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)

    # Pastikan file users.json ada, lalu pastikan user default (admin, user, attacker) tersedia
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)

    # Tambahkan user default jika belum ada
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            existing_users = json.load(f)
    except json.JSONDecodeError:
        existing_users = []

    def ensure_default_user(username: str, password: str, role: str) -> None:
        nonlocal existing_users
        for u in existing_users:
            if u.get("username") == username:
                return
        existing_users.append({"username": username, "password": password, "role": role})

    ensure_default_user("admin", "admin123", "admin")
    ensure_default_user("user", "user123", "user")
    ensure_default_user("attacker", "attacker123", "attacker")

    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_users, f, indent=2, ensure_ascii=False)

    # ---------- Helper fungsi untuk blockchain & event ----------

    def load_events() -> List[Dict[str, Any]]:
        """Membaca semua event dari file JSON."""
        if not os.path.exists(EVENTS_FILE):
            return []
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def save_events(events: List[Dict[str, Any]]) -> None:
        """Menyimpan semua event ke file JSON."""
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, ensure_ascii=False)

    def find_event(events: List[Dict[str, Any]], event_id: str) -> Dict[str, Any] | None:
        """Mencari event berdasarkan event_id."""
        for e in events:
            if e.get("event_id") == event_id:
                return e
        return None

    def allowed_file(filename: str) -> bool:
        """Cek ekstensi file yang diizinkan untuk upload gambar."""
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    # ---------- Helper fungsi untuk users ----------

    def load_users() -> List[Dict[str, Any]]:
        """Membaca semua user dari file JSON."""
        if not os.path.exists(USERS_FILE):
            return []
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def save_users(users: List[Dict[str, Any]]) -> None:
        """Menyimpan semua user ke file JSON."""
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)

    def find_user(username: str) -> Dict[str, Any] | None:
        """Mencari user berdasarkan username."""
        users = load_users()
        for u in users:
            if u.get("username") == username:
                return u
        return None

    def calculate_hash(index: int, timestamp: str, voter_id: str, candidate: str, previous_hash: str) -> str:
        """Menghitung hash SHA-256 berdasarkan field blok."""
        raw = f"{index}{timestamp}{voter_id}{candidate}{previous_hash}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def create_genesis_block() -> Dict[str, Any]:
        """Membuat genesis block untuk event baru."""
        index = 0
        timestamp = datetime.utcnow().isoformat()
        voter_id = "GENESIS"
        candidate = "-"
        previous_hash = "0"
        block_hash = calculate_hash(index, timestamp, voter_id, candidate, previous_hash)
        return {
            "index": index,
            "timestamp": timestamp,
            "voter_id": voter_id,
            "candidate": candidate,
            "previous_hash": previous_hash,
            "hash": block_hash,
        }

    def add_block_to_event(event: Dict[str, Any], voter_id: str, candidate: str) -> None:
        """Menambahkan blok baru ke blockchain suatu event."""
        chain = event.setdefault("blockchain", [])
        if not chain:
            # jika belum ada genesis (harusnya tidak terjadi untuk event valid)
            chain.append(create_genesis_block())

        last_block = chain[-1]
        index = last_block["index"] + 1
        timestamp = datetime.utcnow().isoformat()
        previous_hash = last_block["hash"]
        block_hash = calculate_hash(index, timestamp, voter_id, candidate, previous_hash)
        new_block = {
            "index": index,
            "timestamp": timestamp,
            "voter_id": voter_id,
            "candidate": candidate,
            "previous_hash": previous_hash,
            "hash": block_hash,
        }
        chain.append(new_block)

    def has_user_voted(event: Dict[str, Any], username: str) -> bool:
        """Cek apakah user sudah pernah melakukan voting pada event ini.

        Dicek pada seluruh blok (kecuali genesis) berdasarkan voter_id.
        """
        chain = event.get("blockchain", [])
        for block in chain:
            # Lewati genesis block
            if block.get("index") == 0:
                continue
            if block.get("voter_id") == username:
                return True
        return False

    def summarize_votes(event: Dict[str, Any]) -> Dict[str, Any]:
        """Membuat ringkasan hasil voting untuk sebuah event.

        Menghasilkan:
        - counts: dict kandidat -> jumlah suara
        - total: total suara (tanpa genesis)
        - winners: list kandidat dengan suara terbanyak (bisa lebih dari satu jika seri)
        """
        counts: Dict[str, int] = {c: 0 for c in event.get("candidates", [])}
        chain = event.get("blockchain", [])
        for block in chain:
            if block.get("index") == 0:
                continue
            cand = block.get("candidate")
            if cand in counts:
                counts[cand] += 1
        total = sum(counts.values())
        max_votes = max(counts.values()) if counts else 0
        winners = [c for c, v in counts.items() if v == max_votes and max_votes > 0]
        return {"counts": counts, "total": total, "winners": winners}

    def is_chain_valid(chain: List[Dict[str, Any]]) -> bool:
        """Validasi integritas blockchain."""
        if not chain:
            return True

        for i in range(1, len(chain)):
            current = chain[i]
            prev = chain[i - 1]
            # cek previous_hash
            if current.get("previous_hash") != prev.get("hash"):
                return False
            # cek perhitungan hash
            recalculated = calculate_hash(
                current.get("index"),
                current.get("timestamp"),
                current.get("voter_id"),
                current.get("candidate"),
                current.get("previous_hash"),
            )
            if recalculated != current.get("hash"):
                return False
        # Optionally: cek genesis block konsisten (index 0, previous_hash '0')
        genesis = chain[0]
        if genesis.get("index") != 0 or genesis.get("previous_hash") != "0":
            return False
        return True

    # ---------- Helper untuk autentikasi ----------

    def get_current_user() -> Dict[str, Any] | None:
        """Mengambil data user yang sedang login dari session."""
        user = session.get("user")
        return user

    def login_required():
        """Helper sederhana: jika belum login, redirect ke halaman login."""
        if not get_current_user():
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        return None

    # ---------- Routes ----------

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Halaman login: mendukung admin dan user biasa."""
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            user_data = find_user(username)
            if not user_data or user_data.get("password") != password:
                flash("Username atau password salah.", "danger")
                return redirect(url_for("login"))

            # Simpan info user di session
            session["user"] = {"username": username, "role": user_data.get("role", "user")}
            flash(f"Berhasil login sebagai {username} ({user_data['role']}).", "success")
            return redirect(url_for("index"))

        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        """Halaman registrasi user baru (role default: user)."""
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            confirm = request.form.get("confirm", "").strip()

            if not username or not password:
                flash("Username dan password tidak boleh kosong.", "danger")
                return redirect(url_for("register"))

            if password != confirm:
                flash("Konfirmasi password tidak sama.", "danger")
                return redirect(url_for("register"))

            # Cek apakah username sudah dipakai
            if find_user(username):
                flash("Username sudah digunakan, silakan pilih yang lain.", "warning")
                return redirect(url_for("register"))

            users = load_users()
            users.append(
                {
                    "username": username,
                    "password": password,
                    "role": "user",  # user biasa
                }
            )
            save_users(users)
            flash("Registrasi berhasil! Silakan login.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/admin/users")
    def admin_users():
        """Halaman admin: melihat daftar user yang terdaftar."""
        need_login = login_required()
        if need_login:
            return need_login

        user = get_current_user()
        if not user or user.get("role") != "admin":
            flash("Hanya admin yang dapat melihat daftar user.", "danger")
            return redirect(url_for("index"))

        users = load_users()
        # Jangan tampilkan password di UI (meski di file tetap plain text untuk demo)
        safe_users = [
            {"username": u.get("username", ""), "role": u.get("role", "user")}
            for u in users
        ]
        return render_template("admin_users.html", user=user, users=safe_users)

    @app.route("/logout")
    def logout():
        """Logout user saat ini."""
        session.pop("user", None)
        flash("Anda telah logout.", "info")
        return redirect(url_for("login"))

    @app.route("/", methods=["GET", "POST"])
    def index():
        """Halaman utama: list event + form create event."""
        # Wajib login
        need_login = login_required()
        if need_login:
            return need_login

        user = get_current_user()
        events = load_events()

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            candidates_raw = request.form.get("candidates", "").strip()

            if not name or not candidates_raw:
                flash("Nama event dan daftar kandidat tidak boleh kosong.", "danger")
                return redirect(url_for("index"))

            candidates = [c.strip() for c in candidates_raw.split(",") if c.strip()]
            if not candidates:
                flash("Minimal harus ada satu kandidat yang valid.", "danger")
                return redirect(url_for("index"))

            # Hanya admin yang boleh membuat event
            if not user or user.get("role") != "admin":
                flash("Hanya admin yang boleh membuat event.", "danger")
                return redirect(url_for("index"))

            event_id = f"event-{int(datetime.utcnow().timestamp())}"
            created_at = datetime.utcnow().isoformat()

            new_event = {
                "event_id": event_id,
                "name": name,
                "candidates": candidates,
                "created_at": created_at,
                # mapping kandidat -> nama file gambar (di dalam static/uploads), dikosongkan dulu
                "candidate_images": {},
                # mapping kandidat -> deskripsi, dikelola di halaman khusus admin
                "candidate_descriptions": {},
                "blockchain": [create_genesis_block()],
            }
            events.append(new_event)
            save_events(events)
            flash("Event baru berhasil dibuat.", "success")
            return redirect(url_for("index"))

        return render_template("index.html", events=events, user=user)

    @app.route("/event/<event_id>/delete", methods=["POST"])
    def delete_event(event_id: str):
        """Menghapus event tertentu (hanya admin)."""
        need_login = login_required()
        if need_login:
            return need_login

        user = get_current_user()
        if not user or user.get("role") != "admin":
            flash("Anda tidak memiliki hak untuk menghapus event.", "danger")
            return redirect(url_for("index"))

        events = load_events()
        new_events = [e for e in events if e.get("event_id") != event_id]

        if len(new_events) == len(events):
            flash("Event tidak ditemukan.", "warning")
        else:
            save_events(new_events)
            flash("Event berhasil dihapus.", "success")

        return redirect(url_for("index"))

    @app.route("/event/<event_id>", methods=["GET", "POST"])
    def event_page(event_id: str):
        """Halaman voting untuk event tertentu."""
        need_login = login_required()
        if need_login:
            return need_login

        user = get_current_user()
        events = load_events()
        event = find_event(events, event_id)
        if not event:
            flash("Event tidak ditemukan.", "danger")
            return redirect(url_for("index"))

        # Admin hanya boleh melihat, tidak boleh melakukan voting
        if request.method == "POST":
            if user and user.get("role") == "admin":
                flash("Admin tidak diperbolehkan melakukan voting. Gunakan akun user biasa untuk vote.", "warning")
                return redirect(url_for("event_page", event_id=event_id))

            candidate = request.form.get("candidate")
            # voter_id diambil dari user yang sedang login
            voter_id = user.get("username", "anonymous") if user else "anonymous"

            # Cegah user voting lebih dari satu kali di event yang sama
            if user and has_user_voted(event, user["username"]):
                flash("Anda sudah memberikan suara pada event ini. Voting hanya boleh sekali.", "warning")
                return redirect(url_for("event_page", event_id=event_id))

            if candidate not in event.get("candidates", []):
                flash("Kandidat tidak valid.", "danger")
                return redirect(url_for("event_page", event_id=event_id))

            add_block_to_event(event, voter_id=voter_id, candidate=candidate)
            save_events(events)
            flash("Vote berhasil direkam di blockchain.", "success")
            return redirect(url_for("event_page", event_id=event_id))

        # Untuk tampilan: informasi apakah user sudah pernah vote (hanya relevan untuk non-admin)
        already_voted = False
        if user and user.get("role") != "admin":
            already_voted = has_user_voted(event, user["username"])
        return render_template("event.html", event=event, user=user, already_voted=already_voted)

    @app.route("/event/<event_id>/blockchain")
    def view_blockchain(event_id: str):
        """Halaman untuk melihat blockchain suatu event."""
        need_login = login_required()
        if need_login:
            return need_login

        user = get_current_user()
        events = load_events()
        event = find_event(events, event_id)
        if not event:
            flash("Event tidak ditemukan.", "danger")
            return redirect(url_for("index"))

        chain = event.get("blockchain", [])
        valid = is_chain_valid(chain)
        summary = summarize_votes(event)
        return render_template(
            "blockchain.html",
            event=event,
            chain=chain,
            is_valid=valid,
            user=user,
            summary=summary,
        )

    @app.route("/event/<event_id>/candidates", methods=["GET", "POST"])
    def manage_candidates(event_id: str):
        """Halaman admin untuk mengelola kandidat (gambar & deskripsi)."""
        need_login = login_required()
        if need_login:
            return need_login

        user = get_current_user()
        if not user or user.get("role") != "admin":
            flash("Hanya admin yang dapat mengelola kandidat.", "danger")
            return redirect(url_for("index"))

        events = load_events()
        event = find_event(events, event_id)
        if not event:
            flash("Event tidak ditemukan.", "danger")
            return redirect(url_for("index"))

        candidates = event.get("candidates", [])
        candidate_images = event.setdefault("candidate_images", {})
        candidate_descriptions = event.setdefault("candidate_descriptions", {})

        if request.method == "POST":
            for idx, cand in enumerate(candidates):
                desc_field = f"desc_{idx}"
                file_field = f"img_{idx}"

                # update deskripsi
                desc_val = request.form.get(desc_field, "").strip()
                if desc_val:
                    candidate_descriptions[cand] = desc_val
                else:
                    # kalau dikosongkan, hapus deskripsi
                    candidate_descriptions.pop(cand, None)

                # update gambar jika ada file baru
                file = request.files.get(file_field)
                if file and file.filename:
                    if not allowed_file(file.filename):
                        flash(f"File gambar untuk kandidat '{cand}' tidak didukung.", "warning")
                    else:
                        filename_raw = secure_filename(file.filename)
                        ext = filename_raw.rsplit(".", 1)[1].lower()
                        safe_cand = "".join(ch for ch in cand if ch.isalnum() or ch in ("-", "_")).strip("_")
                        unique_name = f"{event_id}_{safe_cand}.{ext}"
                        save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
                        file.save(save_path)
                        candidate_images[cand] = unique_name

            save_events(events)
            flash("Data kandidat berhasil diperbarui.", "success")
            return redirect(url_for("manage_candidates", event_id=event_id))

        return render_template(
            "manage_candidates.html",
            event=event,
            candidates=candidates,
            candidate_images=candidate_images,
            candidate_descriptions=candidate_descriptions,
            user=user,
        )

    @app.route("/event/<event_id>/blockchain/export_csv")
    def export_blockchain_csv(event_id: str):
        """Ekspor data blockchain (tanpa genesis) menjadi file CSV untuk Excel/analisis."""
        need_login = login_required()
        if need_login:
            return need_login

        events = load_events()
        event = find_event(events, event_id)
        if not event:
            flash("Event tidak ditemukan.", "danger")
            return redirect(url_for("index"))

        chain = event.get("blockchain", [])
        # Bangun CSV secara manual
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        # Header
        writer.writerow(
            ["event_id", "event_name", "index", "timestamp", "voter_id", "candidate", "previous_hash", "hash"]
        )
        # Data (skip genesis block)
        for block in chain:
            if block.get("index") == 0:
                continue
            writer.writerow(
                [
                    event.get("event_id"),
                    event.get("name"),
                    block.get("index"),
                    block.get("timestamp"),
                    block.get("voter_id"),
                    block.get("candidate"),
                    block.get("previous_hash"),
                    block.get("hash"),
                ]
            )

        csv_data = output.getvalue()
        output.close()

        filename = f"{event.get('event_id', 'event')}_blockchain.csv"
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    @app.route("/event/<event_id>/block/<int:block_index>/tamper", methods=["GET", "POST"])
    def tamper_block(event_id: str, block_index: int):
        """Halaman untuk attacker memodifikasi blok tertentu.

        Hanya user dengan role 'attacker' yang boleh mengakses.
        Modifikasi: mengubah candidate dan/atau voter_id pada blok,
        lalu hanya menghitung ulang hash blok itu saja TANPA memperbarui blok-blok sesudahnya.
        Akibatnya, previous_hash di blok berikutnya tidak cocok dan chain menjadi invalid.
        """
        need_login = login_required()
        if need_login:
            return need_login

        user = get_current_user()
        if not user or user.get("role") != "attacker":
            flash("Hanya user attacker yang boleh memodifikasi blok (demo serangan).", "danger")
            return redirect(url_for("view_blockchain", event_id=event_id))

        events = load_events()
        event = find_event(events, event_id)
        if not event:
            flash("Event tidak ditemukan.", "danger")
            return redirect(url_for("index"))

        chain = event.get("blockchain", [])
        # Pastikan index valid dan bukan genesis block
        if block_index < 1 or block_index >= len(chain):
            flash("Blok tidak valid atau tidak dapat dimodifikasi (genesis block dilindungi).", "warning")
            return redirect(url_for("view_blockchain", event_id=event_id))

        block = chain[block_index]

        if request.method == "POST":
            new_candidate = request.form.get("candidate", "").strip()
            new_voter_id = request.form.get("voter_id", "").strip()

            if not new_candidate and not new_voter_id:
                flash("Isi minimal salah satu field (candidate atau voter_id) untuk memodifikasi blok.", "warning")
                return redirect(url_for("tamper_block", event_id=event_id, block_index=block_index))

            # Jika kosong, pertahankan nilai lama
            if new_candidate:
                block["candidate"] = new_candidate
            if new_voter_id:
                block["voter_id"] = new_voter_id

            # Hitung ulang hash blok ini saja (tidak menyentuh blok berikutnya)
            block["hash"] = calculate_hash(
                block["index"],
                block["timestamp"],
                block["voter_id"],
                block["candidate"],
                block["previous_hash"],
            )

            save_events(events)
            flash("Blok berhasil dimodifikasi oleh attacker. Chain kemungkinan menjadi INVALID.", "warning")
            return redirect(url_for("view_blockchain", event_id=event_id))

        return render_template("tamper_block.html", event=event, block=block, user=user)

    return app


if __name__ == "__main__":
    app = create_app()
    # debug=True untuk demo di kelas, bisa dimatikan untuk produksi
    app.run(host="0.0.0.0", port=5000, debug=True)


