const crypto = require("crypto");
const { config } = require("../config/settings");

function extractAdminKey(req) {
    const authHeader = req.headers.authorization || "";
    const bearer = authHeader.startsWith("Bearer ") ? authHeader.slice(7).trim() : "";
    return req.headers["x-admin-key"] || bearer || "";
}

function keysMatch(provided, expected) {
    const providedBuf = Buffer.from(String(provided));
    const expectedBuf = Buffer.from(String(expected));
    if (providedBuf.length !== expectedBuf.length) {
        return false;
    }
    return crypto.timingSafeEqual(providedBuf, expectedBuf);
}

function requireAdmin(req, res, next) {
    const provided = extractAdminKey(req);
    if (!provided) {
        return res.status(401).json({ error: "Credencial administrativa obrigatória" });
    }
    if (!keysMatch(provided, config.adminApiKey)) {
        return res.status(403).json({ error: "Credencial administrativa inválida" });
    }
    return next();
}

module.exports = { requireAdmin };
