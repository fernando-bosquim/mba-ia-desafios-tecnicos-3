function createUserController({ userRepository }) {
    return {
        async deleteUser(userId) {
            const deletedCount = await userRepository.deleteWithDependencies(userId);
            if (deletedCount === 0) {
                return { status: 404, text: 'Usuário não encontrado' };
            }
            return { status: 200, text: 'Usuário deletado com sucesso.' };
        }
    };
}

module.exports = { createUserController };
