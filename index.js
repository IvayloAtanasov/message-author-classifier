const express = require("express");

const app = express();

app.set("x-powered-by", false);

app.get('/', (req, res) => {
    // TODO: form + form handling
    res.send('server is up!');
});

app.listen(3000);