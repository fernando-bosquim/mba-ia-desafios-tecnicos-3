const crypto = require('crypto');
const { config } = require('../config/settings');

function requireAdmin(req, res, next) {
    const authHeader = req.headers.authorization || '';
    const bearer = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : '';
    const provided = req.headers['x-admin-key'] || bearer;

    if (!provided) {
        return res.status(401).json({ error: 'Credencial administrativa obrigatória' });
    }

    const providedBuf = Buffer.from(String(provided));
    const expectedBuf = Buffer.from(String(config.adminApiKey));

    if (providedBuf.length !== expectedBuf.length || !crypto.timingSafeEqual(providedBuf, expectedBuf)) {
        return res.status(403).json({ error: 'Credencial administrativa inválida' });
    }

    return next();
}

module.exports = { requireAdmin };
