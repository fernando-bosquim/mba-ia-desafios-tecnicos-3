const { findFinancialReportRows } = require("../models/courseRepository");

async function financialReport(db) {
    const rows = await findFinancialReportRows(db);

    const report = [];
    const byCourse = new Map();
    for (const row of rows) {
        if (!byCourse.has(row.course_id)) {
            const courseData = { course: row.course, revenue: 0, students: [] };
            byCourse.set(row.course_id, courseData);
            report.push(courseData);
        }
        if (row.enrollment_id == null) {
            continue;
        }
        const courseData = byCourse.get(row.course_id);
        if (row.payment_status === "PAID") {
            courseData.revenue += row.paid;
        }
        courseData.students.push({
            student: row.student || "Unknown",
            paid: row.paid || 0,
        });
    }
    return { status: 200, body: report };
}

module.exports = { financialReport };
