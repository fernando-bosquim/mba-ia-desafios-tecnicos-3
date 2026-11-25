const { run } = require("./db");

async function createAuditLog(db, action) {
    const result = await run(
        db,
        "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
        [action],
    );
    return result.lastID;
}

module.exports = { createAuditLog };
