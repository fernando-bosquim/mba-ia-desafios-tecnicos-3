const { run } = require("../models/db");

async function deleteUser(db, userId) {
    try {
        await run(db, "DELETE FROM users WHERE id = ?", [userId]);
    } catch (_err) {
        // a rota original respondia 200 mesmo quando o delete falhava
    }
    return {
        status: 200,
        text: "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.",
    };
}

module.exports = { deleteUser };
