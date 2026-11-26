const { hashPassword } = require('../models/passwordHash');

const APPROVED_CARD_PREFIX = '4';
const DEFAULT_USER_PASSWORD = '123456';
const PAYMENT_STATUS_PAID = 'PAID';
const PAYMENT_STATUS_DENIED = 'DENIED';

function createCheckoutController({
    courseRepository,
    userRepository,
    enrollmentRepository,
    paymentRepository,
    auditLogRepository,
    checkoutCache
}) {
    return {
        async checkout(payload) {
            const {
                usr: userName,
                eml: email,
                pwd: password,
                c_id: courseId,
                card: cardNumber
            } = payload || {};

            if (!userName || !email || !courseId || !cardNumber) {
                return { status: 400, text: 'Bad Request' };
            }

            const course = await courseRepository.findActiveById(courseId);
            if (!course) {
                return { status: 404, text: 'Curso não encontrado' };
            }

            const paymentStatus = String(cardNumber).startsWith(APPROVED_CARD_PREFIX)
                ? PAYMENT_STATUS_PAID
                : PAYMENT_STATUS_DENIED;

            if (paymentStatus === PAYMENT_STATUS_DENIED) {
                return { status: 400, text: 'Pagamento recusado' };
            }

            let user = await userRepository.findByEmail(email);
            let userId;
            if (!user) {
                const passwordHash = hashPassword(password || DEFAULT_USER_PASSWORD);
                userId = await userRepository.create(userName, email, passwordHash);
            } else {
                userId = user.id;
            }

            const enrollmentId = await enrollmentRepository.create(userId, courseId);
            await paymentRepository.create(enrollmentId, course.price, paymentStatus);
            await auditLogRepository.create(`Checkout curso ${courseId} por ${userId}`);

            checkoutCache.set(`last_checkout_${userId}`, course.title);

            return {
                status: 200,
                body: { msg: 'Sucesso', enrollment_id: enrollmentId }
            };
        }
    };
}

module.exports = { createCheckoutController };
