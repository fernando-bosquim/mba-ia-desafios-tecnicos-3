const { scryptSync, randomBytes } = require("crypto");
const { get, all } = require("./db");

const DEFAULT_PASSWORD = "123456";

function hashPassword(password) {
    const salt = randomBytes(16).toString("hex");
    const digest = scryptSync(password, salt, 32).toString("hex");
    return `${salt}:${digest}`;
}

function findCourse(db, courseId) {
    return get(db, "SELECT * FROM courses WHERE id = ? AND active = 1", [courseId]);
}

function findUserByEmail(db, email) {
    return get(db, "SELECT id FROM users WHERE email = ?", [email]);
}

function findUserName(db, userId) {
    return get(db, "SELECT name, email FROM users WHERE id = ?", [userId]);
}

function financialRows(db) {
    return all(
        db,
        `SELECT c.id AS course_id, c.title AS course,
                e.id AS enrollment_id, u.name AS student,
                p.amount AS paid, p.status AS payment_status
         FROM courses c
         LEFT JOIN enrollments e ON e.course_id = c.id
         LEFT JOIN users u ON u.id = e.user_id
         LEFT JOIN payments p ON p.enrollment_id = e.id
         ORDER BY c.id, e.id`,
    );
}

module.exports = {
    DEFAULT_PASSWORD,
    hashPassword,
    findCourse,
    findUserByEmail,
    findUserName,
    financialRows,
};
