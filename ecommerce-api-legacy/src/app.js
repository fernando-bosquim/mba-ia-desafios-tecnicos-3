const express = require("express");
const { config } = require("./config/settings");
const { openDatabase, initDatabase } = require("./models/db");
const { createRouter } = require("./views/routes");
const { errorHandler } = require("./middlewares/errorHandler");

async function main() {
    const app = express();
    app.use(express.json());

    const db = openDatabase();
    await initDatabase(db);
    const cache = new Map();

    app.use(createRouter(db, cache));
    app.use(errorHandler);

    app.listen(config.port, () => {
        console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

main().catch((err) => {
    console.error(err);
    process.exit(1);
});
