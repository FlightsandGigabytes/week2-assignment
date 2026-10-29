"""Seed library.db with physical copies, members, and borrowings.

All members are fictional (this DB is pushed to a public repo).
Dates are relative to the assignment date 2026-10-29 so that the
borrowing set contains at least one book still out, one overdue,
and one member who has never borrowed anything.

Run with: python3 -I seed_data.py
"""
import sqlite3

DB_PATH = "library.db"
TODAY = "2026-10-29"  # reference "now" for out/overdue


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")  # per-connection; must enable each time
    cur = conn.cursor()

    # ---- 1. Physical copies: every book gets 2, every 3rd book gets 3 ----
    for (book_id,) in cur.execute("SELECT book_id FROM books ORDER BY book_id").fetchall():
        n = 3 if book_id % 3 == 0 else 2
        for _ in range(n):
            cur.execute(
                "INSERT INTO copies (book_id, status) VALUES (?, 'available')",
                (book_id,),
            )

    # ---- 2. Members (all fictional) ----
    members = [
        # id,   name,              type,    join_date,    id_verified, id_type,          guardian_name, guardian_member_id
        (1001, "Marcus Bell",      "adult", "2024-01-15", 1, "drivers_license", None,          None),
        (1002, "Priya Raman",      "adult", "2023-11-02", 1, "drivers_license", None,          None),
        (1003, "Dolores Ortiz",    "adult", "2025-03-20", 1, "state_id",        None,          None),
        (1004, "Tommy Bell",       "minor", "2025-06-01", 0, None,              "Marcus Bell", 1001),
        (1005, "Henry Whitfield",  "adult", "2026-02-10", 1, "passport",        None,          None),  # never borrows
    ]
    cur.executemany(
        "INSERT INTO members (member_id, full_name, member_type, join_date, "
        "id_verified, id_type, guardian_name, guardian_member_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        members,
    )

    # ---- 3. Borrowings ----
    # Grab enough distinct copy_ids to assign loans.
    copy_ids = [r[0] for r in cur.execute(
        "SELECT copy_id FROM copies ORDER BY copy_id"
    ).fetchall()]

    # (member_id, copy_index, checkout_date, due_date, return_date)
    #   return_date = None  -> still out (overdue if due_date < TODAY)
    borrowings = [
        (1001, 0,  "2026-09-01", "2026-09-15", "2026-09-12"),  # returned on time
        (1001, 1,  "2026-10-25", "2026-11-08", None),          # STILL OUT (due in future)
        (1002, 2,  "2026-09-20", "2026-10-04", None),          # OVERDUE (due has passed)
        (1002, 3,  "2026-08-10", "2026-08-24", "2026-08-22"),  # returned
        (1003, 4,  "2026-10-01", "2026-10-15", "2026-10-14"),  # returned
        (1003, 5,  "2026-09-05", "2026-09-19", "2026-09-25"),  # returned late
        (1004, 6,  "2026-10-20", "2026-11-03", None),          # STILL OUT (minor)
        (1004, 7,  "2026-07-01", "2026-07-15", "2026-07-10"),  # returned
        (1001, 8,  "2026-06-15", "2026-06-29", "2026-06-28"),  # returned
        (1002, 9,  "2026-10-10", "2026-10-24", "2026-10-23"),  # returned
        (1003, 10, "2026-05-01", "2026-05-15", "2026-05-14"),  # returned
    ]
    for member_id, idx, checkout, due, ret in borrowings:
        cur.execute(
            "INSERT INTO borrowings (member_id, copy_id, checkout_date, due_date, return_date) "
            "VALUES (?, ?, ?, ?, ?)",
            (member_id, copy_ids[idx], checkout, due, ret),
        )

    # ---- 4. Mark a couple of copies removed, to exercise copy status ----
    # Use high-index copies that are NOT tied to an open loan.
    cur.execute("UPDATE copies SET status = 'lost'    WHERE copy_id = ?", (copy_ids[20],))
    cur.execute("UPDATE copies SET status = 'damaged' WHERE copy_id = ?", (copy_ids[21],))

    conn.commit()

    # ---- report ----
    for tbl in ("copies", "members", "borrowings"):
        n = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"{tbl:12s}: {n}")
    never = cur.execute(
        "SELECT full_name FROM members m WHERE NOT EXISTS "
        "(SELECT 1 FROM borrowings b WHERE b.member_id = m.member_id)"
    ).fetchall()
    print("never borrowed:", ", ".join(r[0] for r in never) or "(none)")
    conn.close()


if __name__ == "__main__":
    main()
