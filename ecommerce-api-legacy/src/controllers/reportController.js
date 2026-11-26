function createReportController({ reportRepository }) {
    return {
        async getFinancialReport() {
            const report = await reportRepository.getFinancialReport();
            return { status: 200, body: report };
        }
    };
}

module.exports = { createReportController };
