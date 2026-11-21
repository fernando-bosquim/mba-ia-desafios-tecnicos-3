const { run } = require("../models/db");
const {
    DEFAULT_PASSWORD,
    hashPassword,
    findCourse,
    findUserByEmail,
} = require("../models/repositories");

async function checkout(db, cache, body) {
    const name = body.usr;
    const email = body.eml;
    const password = body.pwd;
    const courseId = body.c_id;
    const card = body.card;

    if (!name || !email || !courseId || !card) {
        return { status: 400, text: "Bad Request" };
    }

    let course;
    try {
        course = await findCourse(db, courseId);
    } catch (_err) {
        return { status: 404, text: "Curso não encontrado" };
    }
    if (!course) {
        return { status: 404, text: "Curso não encontrado" };
    }

    let user;
    try {
        user = await findUserByEmail(db, email);
    } catch (_err) {
        return { status: 500, text: "Erro DB" };
    }

    let userId = user && user.id;
    if (!userId) {
        try {
            const created = await run(
                db,
                "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
                [name, email, hashPassword(password || DEFAULT_PASSWORD)],
            );
            userId = created.lastID;
        } catch (_err) {
            return { status: 500, text: "Erro ao criar usuário" };
        }
    }

    const status = String(card).startsWith("4") ? "PAID" : "DENIED";
    if (status === "DENIED") {
        return { status: 400, text: "Pagamento recusado" };
    }

    let enrollmentId;
    try {
        const enrollment = await run(
            db,
            "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
            [userId, courseId],
        );
        enrollmentId = enrollment.lastID;
    } catch (_err) {
        return { status: 500, text: "Erro Matrícula" };
    }

    try {
        await run(
            db,
            "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
            [enrollmentId, course.price, status],
        );
    } catch (_err) {
        return { status: 500, text: "Erro Pagamento" };
    }

    try {
        await run(
            db,
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [`Checkout curso ${courseId} por ${userId}`],
        );
    } catch (_err) {
        // o fluxo original respondia 200 mesmo se a auditoria falhasse
    }

    cache.set(`last_checkout_${userId}`, course.title);
    return { status: 200, body: { msg: "Sucesso", enrollment_id: enrollmentId } };
}

module.exports = { checkout };
