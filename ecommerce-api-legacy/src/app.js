const express = require('express');
const { config } = require('./config/settings');
const { createDatabase, initDb } = require('./models/db');
const { createUserRepository } = require('./models/userRepository');
const { createCourseRepository } = require('./models/courseRepository');
const { createEnrollmentRepository } = require('./models/enrollmentRepository');
const { createPaymentRepository } = require('./models/paymentRepository');
const { createAuditLogRepository } = require('./models/auditLogRepository');
const { createReportRepository } = require('./models/reportRepository');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createRoutes } = require('./views/routes');
const { errorHandler } = require('./middlewares/errorHandler');

async function createApp() {
    const app = express();
    app.use(express.json());

    const db = createDatabase(config.dbPath);
    await initDb(db);

    const checkoutCache = new Map();

    const userRepository = createUserRepository(db);
    const courseRepository = createCourseRepository(db);
    const enrollmentRepository = createEnrollmentRepository(db);
    const paymentRepository = createPaymentRepository(db);
    const auditLogRepository = createAuditLogRepository(db);
    const reportRepository = createReportRepository(db);

    const checkoutController = createCheckoutController({
        courseRepository,
        userRepository,
        enrollmentRepository,
        paymentRepository,
        auditLogRepository,
        checkoutCache
    });
    const reportController = createReportController({ reportRepository });
    const userController = createUserController({ userRepository });

    app.use(createRoutes({ checkoutController, reportController, userController }));
    app.use(errorHandler);

    return { app, db };
}

if (require.main === module) {
    createApp()
        .then(({ app }) => {
            app.listen(config.port, () => {
                console.log(`LMS API rodando em http://${config.host}:${config.port}...`);
            });
        })
        .catch((err) => {
            console.error('Falha ao iniciar a aplicação:', err);
            process.exit(1);
        });
}

module.exports = { createApp };
