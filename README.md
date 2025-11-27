# ChainVote — Multi-Event Blockchain E-Voting (Flask)

ChainVote is a simple demo e-voting application built with Flask to demonstrate per-event blockchain concepts. Each event stores its own chain of blocks in a JSON file (`events.json`), and each vote is recorded as a new block.

<img width="1231" height="560" alt="image" src="https://github.com/user-attachments/assets/546aa6f9-cebf-4586-8663-2fbb3945ade2" />


Key features
- Multiple events: each event has its own blockchain
- Create events and add candidates from the UI
- Cast votes — every vote becomes a block appended to the event chain
- Blockchain viewer per event with integrity checks (hash & previous_hash)

Technology
- Python 3
- Flask (web framework)
- `hashlib` (SHA-256) for block hashing
- HTML/CSS (+Bootstrap) for UI

Project structure (short)
- `app.py` — Flask application and blockchain logic
- `templates/` — HTML templates for UI
- `static/` — CSS and static assets (`style.css`, `uploads/`)
- `events.json` — Storage for events and their blockchains
- `users.json` — (optional) user data if present

Quickstart (Windows PowerShell)
1. (Optional) Create and activate a virtual environment:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
2. Install dependencies:
```powershell
pip install -r requirements.txt
```
3. Run the app:
```powershell
python app.py
```
4. Open your browser at `http://127.0.0.1:5000`

Note: If PowerShell blocks activation scripts, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first.

Development
- Modify `app.py` or templates in `templates/` and refresh the browser to see changes.

Data files & security
- `events.json` and `users.json` contain local data — do not commit any sensitive data to a public repository.
- `static/uploads/` contains user uploads; it is excluded via `.gitignore` to avoid committing uploaded files.


License & contribution
- License: This project is released under the MIT License — see the `LICENSE` file for details.
- Contribution guide: Fork the repo, create a feature branch, commit changes, push the branch, and open a Pull Request with a clear description of your changes.

Developer notes
- This project is an educational demo. Do not use this system for real-world elections without a proper security audit, real cryptographic protections, and legal review.

Thank you for trying ChainVote!
