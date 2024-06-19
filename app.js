// const express = require('express');
// const app = express();
// const port = 8080;
// const { spawn } = require('child_process');

// app.use(express.static('public'));

// app.get('/', (req, res) => {
//   res.sendFile(__dirname + '/public/index.html');
// });

// app.get('/chatbot', (req, res) => {
//   // const pythonProcess = spawn('python', [`${__dirname}/chatbot_script.py`]);
//   const pythonProcess = spawn('python', [`${__dirname}/chat_gpt_audio/test_chat.py`]);

//   pythonProcess.stdout.on('data', (data) => {
//     res.send(data.toString());
//   });

//   pythonProcess.stderr.on('data', (data) => {
//     console.error(`stderr: ${data}`);
//   });

//   pythonProcess.on('close', (code) => {
//     console.log(`child process exited with code ${code}`);
//   });
// });

// app.listen(port, () => {
//   console.log(`App running on http://localhost:${port}`);
// });


const express = require('express');
const app = express();
const port = 8080;
const { spawn } = require('child_process');

app.use(express.static('public'));

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/public/index.html');
});

app.get('/chatbot', (req, res) => {
  const pythonProcess = spawn('python', [`${__dirname}/test_chat.py`]);

  pythonProcess.stdout.on('data', (data) => {
    res.send(data.toString());
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`stderr: ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`child process exited with code ${code}`);
  });
});

app.listen(port, () => {
  console.log(`App running on http://localhost:${port}`);
});
