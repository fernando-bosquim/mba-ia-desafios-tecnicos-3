function createReportRepository(db) {
    return {
        async getFinancialReport() {
            const rows = await db.all(
                `SELECT
                    c.id AS course_id,
                    c.title AS course_title,
                    e.id AS enrollment_id,
                    u.name AS user_name,
                    p.amount AS payment_amount,
                    p.status AS payment_status
                FROM courses c
                LEFT JOIN enrollments e ON e.course_id = c.id
                LEFT JOIN users u ON u.id = e.user_id
                LEFT JOIN payments p ON p.enrollment_id = e.id
                ORDER BY c.id ASC, e.id ASC`
            );

            const coursesById = new Map();

            for (const row of rows) {
                if (!coursesById.has(row.course_id)) {
                    coursesById.set(row.course_id, {
                        course: row.course_title,
                        revenue: 0,
                        students: []
                    });
                }

                if (row.enrollment_id !== null) {
                    const courseData = coursesById.get(row.course_id);
                    const paidAmount = row.payment_amount || 0;

                    if (row.payment_status === 'PAID') {
                        courseData.revenue += paidAmount;
                    }

                    courseData.students.push({
                        student: row.user_name || 'Unknown',
                        paid: paidAmount
                    });
                }
            }

            return Array.from(coursesById.values());
        }
    };
}

module.exports = { createReportRepository };
