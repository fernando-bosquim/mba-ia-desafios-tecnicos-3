const { run } = require("./db");

async function createPayment(db, { enrollmentId, amount, status }) {
    const result = await run(
        db,
        "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
        [enrollmentId, amount, status],
    );
    return result.lastID;
}

module.exports = { createPayment };
