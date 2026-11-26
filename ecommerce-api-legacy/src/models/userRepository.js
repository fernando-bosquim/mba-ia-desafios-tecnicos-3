function createUserRepository(db) {
    return {
        findByEmail(email) {
            return db.get('SELECT id FROM users WHERE email = ?', [email]);
        },

        async create(name, email, passwordHash) {
            const result = await db.run(
                'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
                [name, email, passwordHash]
            );
            return result.lastID;
        },

        async deleteWithDependencies(userId) {
            await db.run('BEGIN TRANSACTION');
            try {
                await db.run(
                    'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
                    [userId]
                );
                await db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
                const result = await db.run('DELETE FROM users WHERE id = ?', [userId]);
                await db.run('COMMIT');
                return result.changes;
            } catch (err) {
                await db.run('ROLLBACK');
                throw err;
            }
        }
    };
}

module.exports = { createUserRepository };
