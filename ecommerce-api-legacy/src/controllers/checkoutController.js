const { findActiveCourseById } = require("../models/courseRepository");
const {
    DEFAULT_PASSWORD,
    hashPassword,
    findUserByEmail,
    createUser,
} = require("../models/userRepository");
const { createEnrollment } = require("../models/enrollmentRepository");
const { createPayment } = require("../models/paymentRepository");
const { createAuditLog } = require("../models/auditLogRepository");

async function checkout(db, cache, body) {
    const name = body.usr;
    const email = body.eml;
    const password = body.pwd;
    const courseId = body.c_id;
    const card = body.card;

    if (!name || !email || !courseId || !card) {
        return { status: 400, text: "Bad Request" };
    }

    const course = await findActiveCourseById(db, courseId);
    if (!course) {
        return { status: 404, text: "Curso não encontrado" };
    }

    const user = await findUserByEmail(db, email);
    let userId = user && user.id;
    if (!userId) {
        userId = await createUser(db, {
            name,
            email,
            passwordHash: hashPassword(password || DEFAULT_PASSWORD),
        });
    }

    const status = String(card).startsWith("4") ? "PAID" : "DENIED";
    if (status === "DENIED") {
        console.log(`Pagamento recusado: usuário ${userId}, curso ${courseId}`);
        return { status: 400, text: "Pagamento recusado" };
    }

    const enrollmentId = await createEnrollment(db, { userId, courseId });
    await createPayment(db, { enrollmentId, amount: course.price, status });
    await createAuditLog(db, `Checkout curso ${courseId} por ${userId}`);

    cache.set(`last_checkout_${userId}`, course.title);
    console.log(`Checkout aprovado: matrícula ${enrollmentId}, status ${status}`);
    return { status: 200, body: { msg: "Sucesso", enrollment_id: enrollmentId } };
}

module.exports = { checkout };
