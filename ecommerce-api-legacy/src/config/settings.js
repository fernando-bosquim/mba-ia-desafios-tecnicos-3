const config = Object.freeze({
    port: Number(process.env.PORT) || 3000,
    host: process.env.HOST || 'localhost',
    dbPath: process.env.DB_PATH || ':memory:',
    dbUser: process.env.DB_USER || '',
    dbPass: process.env.DB_PASS || '',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'dev-only-payment-key',
    smtpUser: process.env.SMTP_USER || '',
    adminApiKey: process.env.ADMIN_API_KEY || 'dev-only-admin-key-change-me'
});

module.exports = { config };
