/**
 * Privacy gate for the browser agent.
 *
 * URL allowlist + per-domain redaction. The default is deny — anything
 * not in the allowlist is excluded from summarization.
 *
 * Real impl: declarativeNetRequest for fine-grained per-resource
 * blocking; this file is the policy that drives it.
 */
const BLOCKED_DOMAINS = {
  banking: [
    "chase.com", "hsbc.com", "sc.com", "ocbc.com", "dbs.com", "maybank.com",
    "citi.com", "wellsfargo.com", "bankofamerica.com", "barclays.co.uk"
  ],
  health: [
    "mychart.com", "epic.com", "cerner.com", "questdiagnostics.com",
    "labcorp.com", "kaiserpermanente.org"
  ],
  email: [
    "mail.google.com", "outlook.live.com", "outlook.office.com",
    "mail.yahoo.com", "proton.me", "fastmail.com"
  ],
  auth: [
    "accounts.google.com", "login.microsoftonline.com",
    "appleid.apple.com", "github.com/login", "*.sso.*"
  ]
};

function isUrlBlocked(url) {
  try {
    const u = new URL(url);
    const host = u.hostname.toLowerCase();
    for (const cat of Object.keys(BLOCKED_DOMAINS)) {
      for (const d of BLOCKED_DOMAINS[cat]) {
        if (host === d || host.endsWith("." + d)) return { blocked: true, category: cat };
        if (d.startsWith("*.")) {
          const suffix = d.slice(1);  // ".sso.example.com"
          if (host.endsWith(suffix)) return { blocked: true, category: cat };
        }
      }
    }
    return { blocked: false };
  } catch (e) {
    return { blocked: true, category: "parse_error" };
  }
}

function bannerFor(category) {
  switch (category) {
    case "banking": return "Privacy mode: this is a banking site. We will not read its content.";
    case "health":  return "Privacy mode: this is a health site. We will not read its content.";
    case "email":   return "Privacy mode: this is an email site. We will not read its content.";
    case "auth":    return "Privacy mode: this is an auth site. We will not read its content.";
    default:        return "Privacy mode: this site is excluded from summarization.";
  }
}

module.exports = { isUrlBlocked, bannerFor, BLOCKED_DOMAINS };
