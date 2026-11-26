const sqlite3 = require('sqlite3');
const { hashPassword } = require('./passwordHash');

function createDatabase(dbPath) {
    const rawDb = new sqlite3.Database(dbPath);

    return {
        run(sql, params = []) {
            return new Promise((resolve, reject) => {
                rawDb.run(sql, params, function onRun(err) {
                    if (err) return reject(err);
                    resolve({ lastID: this.lastID, changes: this.changes });
                });
            });
        },

        get(sql, params = []) {
            return new Promise((resolve, reject) => {
                rawDb.get(sql, params, (err, row) => {
                    if (err) return reject(err);
                    resolve(row);
                });
            });
        },

        all(sql, params = []) {
            return new Promise((resolve, reject) => {
                rawDb.all(sql, params, (err, rows) => {
                    if (err) return reject(err);
                    resolve(rows);
                });
            });
        },

        close() {
            return new Promise((resolve, reject) => {
                rawDb.close((err) => {
                    if (err) return reject(err);
                    resolve();
                });
            });
        }
    };
}

async function initDb(db) {
    await db.run('PRAGMA foreign_keys = ON');
    await db.run('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
    await db.run('CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
    await db.run('CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
    await db.run('CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
    await db.run('CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');

    const seedPasswordHash = hashPassword('123');
    await db.run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        ['Leonan', 'leonan@fullcycle.com.br', seedPasswordHash]
    );
    await db.run(
        "INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)"
    );
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
    await db.run(
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [1, 997.00, 'PAID']
    );
}

module.exports = { createDatabase, initDb };
