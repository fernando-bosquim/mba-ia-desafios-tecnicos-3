const config = {
    port: Number(process.env.PORT || 3000),
    dbUser: process.env.DB_USER || "dev-user",
    dbPass: process.env.DB_PASS || "dev-only-change-me",
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || "dev-only-change-me",
    smtpUser: process.env.SMTP_USER || "dev-smtp",
};

module.exports = { config };
