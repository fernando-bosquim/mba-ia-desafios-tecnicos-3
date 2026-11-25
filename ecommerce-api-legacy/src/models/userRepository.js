const { scryptSync, randomBytes } = require("crypto");
const { get, run, withTransaction } = require("./db");

const DEFAULT_PASSWORD = "123456";

function hashPassword(password) {
    const salt = randomBytes(16).toString("hex");
    const digest = scryptSync(password, salt, 32).toString("hex");
    return `${salt}:${digest}`;
}

function findUserByEmail(db, email) {
    return get(db, "SELECT id FROM users WHERE email = ?", [email]);
}

async function createUser(db, { name, email, passwordHash }) {
    const result = await run(
        db,
        "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
        [name, email, passwordHash],
    );
    return result.lastID;
}

function deleteUserWithRelations(db, userId) {
    return withTransaction(db, async () => {
        await run(
            db,
            "DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)",
            [userId],
        );
        await run(db, "DELETE FROM enrollments WHERE user_id = ?", [userId]);
        const result = await run(db, "DELETE FROM users WHERE id = ?", [userId]);
        return result.changes;
    });
}

module.exports = {
    DEFAULT_PASSWORD,
    hashPassword,
    findUserByEmail,
    createUser,
    deleteUserWithRelations,
};
