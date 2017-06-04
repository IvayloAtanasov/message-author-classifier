const express = require('express');
const bodyParser = require('body-parser');
const PythonShell = require('python-shell');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(bodyParser.urlencoded({ extended: true }));

app.set('x-powered-by', false);

app.get('/', (req, res) => {
    res.sendFile(`${__dirname}/public/index.html`);
});

app.post('/suggest-author', (req, res) => {
    // respond with the first thing we receive through stdout from pyshell
    pyshell.once('message', author => {
        res.send({
            status: 'success',
            author: author
        });
    });

    // pass message to process through pyshell stdin
    pyshell.send(req.body.message);
});

// start python script
const opts = {
  mode: 'text',
  pythonOptions: ['-u'],
  scriptPath: 'processing'
};
const pyshell = new PythonShell('vectorize.py', opts);
pyshell.on('message', msg => {
    console.log(`Python shell: ${msg}`);
    if (msg.trim() === 'Listening for messages...') {
        // classifier setup is done, start server
        app.listen(PORT, err => {
            if (err) throw err;
            console.log(`Server ready and listening on port ${PORT}`);
        });
    }
});