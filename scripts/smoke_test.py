from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from auth import authenticate, seed_default_users
from database import add_entry, get_entries, init_database, remove_entry

init_database()
seed_default_users()
assert authenticate("DAI", "1234")
assert authenticate("CHAIRMAN", "0000")
assert authenticate("STRATEGY_ADMIN", "0000")
entry_id = add_entry({
    "week_id": "2099-W01",
    "department_id": "DAI",
    "direction_id": "1",
    "task_id": "1.1",
    "activity": "Smoke test",
    "result": "OK",
    "deadline": None,
    "status": "done",
    "is_major": False,
    "meeting_date": None,
    "comment": "",
}, "STRATEGY_ADMIN")
assert any(row["id"] == entry_id for row in get_entries("2099-W01", "DAI"))
remove_entry(entry_id, "STRATEGY_ADMIN")
print("SMOKE TEST OK")
