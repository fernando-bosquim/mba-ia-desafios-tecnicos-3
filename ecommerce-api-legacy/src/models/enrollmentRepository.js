function createEnrollmentRepository(db) {
    return {
        async create(userId, courseId) {
            const result = await db.run(
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
                [userId, courseId]
            );
            return result.lastID;
        }
    };
}

module.exports = { createEnrollmentRepository };
