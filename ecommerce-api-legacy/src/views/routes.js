const express = require("express");
const { checkout } = require("../controllers/checkoutController");
const { financialReport } = require("../controllers/reportController");
const { deleteUser } = require("../controllers/userController");
const { requireAdmin } = require("../middlewares/authMiddleware");

function send(res, result) {
    if (result.text !== undefined) {
        return res.status(result.status).send(result.text);
    }
    return res.status(result.status).json(result.body);
}

function createRouter(db, cache) {
    const router = express.Router();

    router.post("/api/checkout", async (req, res, next) => {
        try {
            send(res, await checkout(db, cache, req.body || {}));
        } catch (err) {
            next(err);
        }
    });

    router.get("/api/admin/financial-report", requireAdmin, async (req, res, next) => {
        try {
            send(res, await financialReport(db));
        } catch (err) {
            next(err);
        }
    });

    router.delete("/api/users/:id", requireAdmin, async (req, res, next) => {
        try {
            send(res, await deleteUser(db, req.params.id));
        } catch (err) {
            next(err);
        }
    });

    return router;
}

module.exports = { createRouter };
