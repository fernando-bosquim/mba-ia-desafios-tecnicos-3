const { deleteUserWithRelations } = require("../models/userRepository");

async function deleteUser(db, userId) {
    const changes = await deleteUserWithRelations(db, userId);
    if (changes === 0) {
        return { status: 404, body: { error: "Usuário não encontrado" } };
    }
    return {
        status: 200,
        body: { msg: "Usuário e registros vinculados removidos com sucesso" },
    };
}

module.exports = { deleteUser };
