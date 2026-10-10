"""
lead_store.py — Postgres-backed lead tracking for Avilx.

Stores every lead + send attempt in Postgres so we can:
- Dedup by email, phone, or (company, role)
- Track send history and replies
- Manage opt-outs (anti-spam compliance)
- See open/click tracking if/when we add pixels

Env vars (with defaults):
  AVILX_DB_HOST     = localhost
  AVILX_DB_PORT     = 5433
  AVILX_DB_NAME     = avilx_leads
  AVILX_DB_USER     = avilx
  AVILX_DB_PASSWORD = avilx
"""

import os
import secrets
import string
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    import psycopg2
    import psycopg2.extras
    from psycopg2 import errors as psycopg2_errors
    HAVE_PG = True
except ImportError:
    HAVE_PG = False


def _conn_params() -> dict:
    return {
        "host":     os.getenv("AVILX_DB_HOST", "localhost"),
        "port":     int(os.getenv("AVILX_DB_PORT", "5433")),
        "dbname":   os.getenv("AVILX_DB_NAME", "avilx_leads"),
        "user":     os.getenv("AVILX_DB_USER", "avilx"),
        "password": os.getenv("AVILX_DB_PASSWORD", "avilx"),
    }


def _check_pg():
    if not HAVE_PG:
        raise RuntimeError(
            "psycopg2 not installed. Run: pip install psycopg2-binary"
        )


@contextmanager
def get_cursor(dict_rows: bool = True):
    """Context manager: with get_cursor() as cur: cur.execute(...)"""
    _check_pg()
    conn = psycopg2.connect(**_conn_params())
    factory = psycopg2.extras.RealDictCursor if dict_rows else None
    cur = conn.cursor(cursor_factory=factory)
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def _make_tracking_id(company: str) -> str:
    """Generate a short, public tracking ID like 'avx-7q3k' for the email link."""
    base = "".join(c for c in company.lower() if c.isalnum())[:8] or "lead"
    rand = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(4))
    return f"{base[:4]}-{rand}"


def is_opted_out(email: str) -> bool:
    """Return True if this email has unsubscribed."""
    with get_cursor(dict_rows=False) as cur:
        cur.execute("SELECT 1 FROM opt_outs WHERE email = %s", (email.lower(),))
        return cur.fetchone() is not None


def opt_out(email: str):
    """Mark an email as opted out."""
    with get_cursor(dict_rows=False) as cur:
        cur.execute(
            "INSERT INTO opt_outs (email) VALUES (%s) ON CONFLICT (email) DO NOTHING",
            (email.lower(),),
        )


def find_duplicate(company: str, contact_email: str, role: str = None) -> Optional[Dict]:
    """Return existing lead dict if we already have this lead.

    Order (most specific → least):
      1. (company, role)        — same role posted twice (most common dup)
      2. (company, email)       — same recruiter, same company, different role
      3. NEVER by email alone   — a recruiter changing jobs should NOT
                                  be treated as a duplicate of their old lead.

    Email-alone dedup was the original behavior and it was dangerous: any
    recruiter who moved companies would be falsely deduplicated and never
    re-contacted at their new address. We do not do that anymore.
    """
    if not company:
        return None
    with get_cursor() as cur:
        # 1) Same company + same role (most common)
        if role:
            cur.execute(
                "SELECT * FROM leads "
                "WHERE LOWER(company) = LOWER(%s) AND LOWER(role) = LOWER(%s) "
                "ORDER BY id DESC LIMIT 1",
                (company, role),
            )
            row = cur.fetchone()
            if row:
                return dict(row)
        # 2) Same company + same email (recruiter stayed, role changed)
        if contact_email:
            cur.execute(
                "SELECT * FROM leads "
                "WHERE LOWER(company) = LOWER(%s) AND LOWER(contact_email) = LOWER(%s) "
                "ORDER BY id DESC LIMIT 1",
                (company, contact_email),
            )
            row = cur.fetchone()
            if row:
                return dict(row)
        return None


def find_by_email_any_company(email: str) -> Optional[Dict]:
    """Optional escape hatch: look up by email across companies.

    Use this ONLY when you intend to actually email that person (e.g. a
    follow-up sequence). Do NOT use as a dedup key.
    """
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM leads WHERE LOWER(contact_email) = LOWER(%s) "
            "ORDER BY id DESC LIMIT 1",
            (email,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def insert_lead(lead: dict, source: str = "jd_inbox") -> int:
    """Insert a new lead. Returns lead ID.

    Catches UniqueViolation gracefully: if a parallel insert beat us to the
    unique (company, email) row, we look up the existing row and return its
    id instead of bubbling an opaque `duplicate key value` error.
    """
    tracking_id = _make_tracking_id(lead.get("company", "lead"))
    company = lead.get("company", "Unknown")
    role = lead.get("role", "Role TBD")
    email = lead.get("contact_email")

    # First pass: just the leads table insert
    try:
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO leads (
                    tracking_id, company, role, contact_email, contact_phone,
                    stack, rate, resume_file, source_url, source,
                    cover_letter_subject, cover_letter_body, jd_text, status
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
            """, (
                tracking_id,
                company,
                role,
                email,
                lead.get("contact_phone"),
                lead.get("stack", ""),
                lead.get("rate", "Not listed"),
                lead.get("resume_file", "Prem_Resume_2026.pdf"),
                lead.get("source_url", ""),
                source,
                lead.get("cover_letter_subject", ""),
                lead.get("cover_letter_body", ""),
                lead.get("jd_text", ""),
                "pending",
            ))
            lead_id = cur.fetchone()["id"]
    except psycopg2_errors.UniqueViolation:
        # Lost the race — find the winner and return that id
        existing = find_duplicate(company, email or "", role)
        if existing:
            return existing["id"]
        # Couldn't find it (very rare): re-raise so caller sees the error
        raise

    # Second pass: phone table (independent, won't lose the lead if it fails)
    phone = (lead.get("contact_phone") or "").strip()
    if phone:
        try:
            with get_cursor() as cur:
                cur.execute("""
                    INSERT INTO phones (phone, company, contact_email, lead_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (phone) DO UPDATE SET
                        company = EXCLUDED.company,
                        contact_email = EXCLUDED.contact_email,
                        lead_id = EXCLUDED.lead_id
                """, (phone, company, email, lead_id))
        except psycopg2_errors.IntegrityError:
            # Phone is best-effort metadata; racing with another lead is OK.
            pass
        except Exception as e:
            # Surface programming / connection errors loudly so we notice
            import sys
            print(f"  ⚠️  phone insert failed for lead {lead_id}: {e}", file=sys.stderr)
    return lead_id


def update_status(lead_id: int, status: str, error: str = None):
    """Update lead status (pending → sent_email, sent_email → replied, etc)."""
    with get_cursor(dict_rows=False) as cur:
        if status == "sent_email":
            cur.execute(
                "UPDATE leads SET status = %s, sent_at = NOW(), send_count = send_count + 1, last_error = %s WHERE id = %s",
                (status, error, lead_id),
            )
        else:
            cur.execute(
                "UPDATE leads SET status = %s, last_error = %s WHERE id = %s",
                (status, error, lead_id),
            )


def log_send(lead_id: int, to_email: str, subject: str, status: str, error: str = None, smtp_message_id: str = None):
    """Append to send_log table."""
    with get_cursor(dict_rows=False) as cur:
        cur.execute("""
            INSERT INTO send_log (lead_id, to_email, subject, status, error, smtp_message_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (lead_id, to_email, subject, status, error, smtp_message_id))


def get_pending_leads() -> List[Dict]:
    """Return all leads with status=pending and not opted out.

    Excludes `bounced` addresses too — once a recipient server has told us
    the address is dead, re-sending just spams the dead-letter office.
    """
    with get_cursor() as cur:
        cur.execute("""
            SELECT l.* FROM leads l
            WHERE l.status = 'pending'
              AND LOWER(l.contact_email) NOT IN (SELECT email FROM opt_outs)
              AND l.status != 'bounced'
            ORDER BY l.id ASC
        """)
        return [dict(r) for r in cur.fetchall()]


def get_by_email(email: str) -> Optional[Dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM leads WHERE LOWER(contact_email) = LOWER(%s) ORDER BY id DESC LIMIT 1", (email,))
        row = cur.fetchone()
        return dict(row) if row else None


def stats() -> Dict[str, Any]:
    """Return high-level stats."""
    with get_cursor() as cur:
        cur.execute("SELECT status, COUNT(*) AS n FROM leads GROUP BY status ORDER BY status")
        by_status = {r["status"]: r["n"] for r in cur.fetchall()}
        cur.execute("SELECT COUNT(*) AS n FROM send_log WHERE sent_at > NOW() - INTERVAL '24 hours'")
        sent_24h = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM opt_outs")
        optouts = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(DISTINCT company) AS n FROM leads")
        companies = cur.fetchone()["n"]
        return {
            "by_status": by_status,
            "sent_last_24h": sent_24h,
            "opt_outs": optouts,
            "unique_companies": companies,
        }


def cli():
    """Tiny CLI: `python3 -m db.lead_store status`."""
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        s = stats()
        print("📊 Avilx leads DB")
        print(f"   By status: {s['by_status']}")
        print(f"   Sent (24h): {s['sent_last_24h']}")
        print(f"   Opt-outs:  {s['opt_outs']}")
        print(f"   Companies: {s['unique_companies']}")
    elif cmd == "init":
        with get_cursor(dict_rows=False) as cur:
            with open(os.path.join(os.path.dirname(__file__), "schema.sql")) as f:
                cur.execute(f.read())
        print("✅ Schema applied")
    elif cmd == "test":
        try:
            with get_cursor() as cur:
                cur.execute("SELECT 1 AS ok")
                print("✅ Connected:", cur.fetchone())
        except Exception as e:
            print(f"❌ Connection failed: {e}")


# =========================================
# LinkedIn DM tracking
# =========================================

def log_dm(handle: str, name: str = None, company: str = None, title: str = None,
           region: str = None, template_used: str = None, dm_text: str = None,
           linkedin_url: str = None) -> int:
    """Log a new LinkedIn DM. Returns the DM id."""
    handle = handle.lstrip("@").lower()
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO linkedin_dms (handle, name, company, title, region, template_used, dm_text, linkedin_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (handle) DO UPDATE SET
                name = COALESCE(EXCLUDED.name, linkedin_dms.name),
                company = COALESCE(EXCLUDED.company, linkedin_dms.company),
                title = COALESCE(EXCLUDED.title, linkedin_dms.title),
                region = COALESCE(EXCLUDED.region, linkedin_dms.region),
                template_used = COALESCE(EXCLUDED.template_used, linkedin_dms.template_used),
                dm_text = COALESCE(EXCLUDED.dm_text, linkedin_dms.dm_text),
                last_touch_at = NOW(),
                touch_count = linkedin_dms.touch_count + 1
            RETURNING id
        """, (handle, name, company, title, region, template_used, dm_text, linkedin_url))
        return cur.fetchone()["id"]


def log_dm_followup(handle: str, message: str) -> int:
    """Log a follow-up bump to an existing DM (day 3, day 7, etc)."""
    handle = handle.lstrip("@").lower()
    with get_cursor() as cur:
        cur.execute("SELECT id FROM linkedin_dms WHERE handle = %s", (handle,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"No DM found for handle @{handle}")
        dm_id = row["id"]
        cur.execute("""
            INSERT INTO linkedin_followups (dm_id, message)
            VALUES (%s, %s) RETURNING id
        """, (dm_id, message))
        cur.execute("""
            UPDATE linkedin_dms SET touch_count = touch_count + 1, last_touch_at = NOW()
            WHERE id = %s
        """, (dm_id,))
        return cur.fetchone()["id"]


def update_dm_status(handle: str, status: str, notes: str = None):
    """Mark a DM's status (sent → replied → meeting → won)."""
    handle = handle.lstrip("@").lower()
    with get_cursor(dict_rows=False) as cur:
        if status == "replied":
            cur.execute("""
                UPDATE linkedin_dms SET status = %s, replied_at = NOW(), notes = COALESCE(%s, notes)
                WHERE handle = %s
            """, (status, notes, handle))
        else:
            cur.execute("""
                UPDATE linkedin_dms SET status = %s, notes = COALESCE(%s, notes)
                WHERE handle = %s
            """, (status, notes, handle))


def dm_stats() -> dict:
    """Return LinkedIn DM campaign stats."""
    with get_cursor() as cur:
        cur.execute("SELECT status, COUNT(*) AS n FROM linkedin_dms GROUP BY status ORDER BY status")
        by_status = {r["status"]: r["n"] for r in cur.fetchall()}
        cur.execute("""
            SELECT COUNT(*) AS n FROM linkedin_dms
            WHERE sent_at > NOW() - INTERVAL '7 days'
        """)
        sent_7d = cur.fetchone()["n"]
        cur.execute("""
            SELECT COUNT(*) AS n FROM linkedin_dms
            WHERE replied_at > NOW() - INTERVAL '7 days'
        """)
        replied_7d = cur.fetchone()["n"]
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'sent') AS pending_reply,
                COUNT(*) FILTER (WHERE status = 'replied') AS replied,
                COUNT(*) FILTER (WHERE status IN ('intro','meeting','won')) AS advanced,
                COUNT(*) AS total
            FROM linkedin_dms
            WHERE sent_at > NOW() - INTERVAL '14 days'
        """)
        funnel = dict(cur.fetchone())
        return {
            "by_status": by_status,
            "sent_7d": sent_7d,
            "replied_7d": replied_7d,
            "funnel_14d": funnel,
        }


def list_pending_followups() -> list:
    """Return DMs that need a follow-up bump (sent 3+ days ago, no reply)."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT handle, name, company, sent_at, touch_count, last_touch_at
            FROM linkedin_dms
            WHERE status = 'sent'
              AND (
                (touch_count = 1 AND sent_at < NOW() - INTERVAL '3 days')
                OR (touch_count = 2 AND last_touch_at < NOW() - INTERVAL '4 days')
                OR (touch_count = 3 AND last_touch_at < NOW() - INTERVAL '7 days')
              )
            ORDER BY sent_at
        """)
        return [dict(r) for r in cur.fetchall()]


if __name__ == "__main__":
    cli()
