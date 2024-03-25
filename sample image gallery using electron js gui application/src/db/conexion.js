const {createConnection} = require('promise-mysql');
require('dotenv').config();

const connection = createConnection({
    host: process.env.HOST,
    user: process.env.USER,
    password: process.env.PASSWORD,
    database: process.env.DATABASE
});

module.exports = { connection };