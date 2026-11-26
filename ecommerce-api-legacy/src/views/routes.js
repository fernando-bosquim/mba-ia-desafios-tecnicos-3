const express = require('express');
const { requireAdmin } = require('../middlewares/authMiddleware');

function sendResult(res, result) {
    if (result.text !== undefined) {
        return res.status(result.status).send(result.text);
    }
    return res.status(result.status).json(result.body);
}

function createRoutes({ checkoutController, reportController, userController }) {
    const router = express.Router();

    router.post('/api/checkout', async (req, res, next) => {
        try {
            const result = await checkoutController.checkout(req.body);
            return sendResult(res, result);
        } catch (err) {
            return next(err);
        }
    });

    router.get('/api/admin/financial-report', requireAdmin, async (req, res, next) => {
        try {
            const result = await reportController.getFinancialReport();
            return sendResult(res, result);
        } catch (err) {
            return next(err);
        }
    });

    router.delete('/api/users/:id', requireAdmin, async (req, res, next) => {
        try {
            const result = await userController.deleteUser(req.params.id);
            return sendResult(res, result);
        } catch (err) {
            return next(err);
        }
    });

    return router;
}

module.exports = { createRoutes };
