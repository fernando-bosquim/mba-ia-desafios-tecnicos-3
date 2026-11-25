const sqlite3 = require("sqlite3");

let transactionChain = Promise.resolve();

function openDatabase() {
    return new sqlite3.Database(":memory:");
}

function run(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function onRun(err) {
            if (err) {
                reject(err);
                return;
            }
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) {
                reject(err);
                return;
            }
            resolve(row);
        });
    });
}

function all(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) {
                reject(err);
                return;
            }
            resolve(rows);
        });
    });
}

function withTransaction(db, fn) {
    const execute = async () => {
        await run(db, "BEGIN TRANSACTION");
        try {
            const result = await fn();
            await run(db, "COMMIT");
            return result;
        } catch (err) {
            try {
                await run(db, "ROLLBACK");
            } catch (_rollbackErr) {
                // preserva o erro original da transação
            }
            throw err;
        }
    };
    const next = transactionChain.then(execute, execute);
    transactionChain = next.catch(() => {});
    return next;
}

async function initDatabase(db) {
    const { hashPassword } = require("./userRepository");

    await run(db, "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)");
    await run(db, "CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)");
    await run(db, "CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)");
    await run(db, "CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)");
    await run(db, "CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)");
    await run(
        db,
        "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
        ["Leonan", "leonan@fullcycle.com.br", hashPassword("123")],
    );
    await run(db, "INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
    await run(db, "INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)");
    await run(db, "INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
}

module.exports = { openDatabase, initDatabase, withTransaction, run, get, all };
