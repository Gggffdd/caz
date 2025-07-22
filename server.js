const express = require('express');
const path = require('path');
const app = express();

// Middleware
app.use(express.json());
app.use(express.static('public'));

// CORS
app.use((req, res, next) => {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
    next();
});

// Mock database
const users = {};

// API Endpoints
app.get('/api/user/:id', (req, res) => {
    if (!users[req.params.id]) {
        users[req.params.id] = {
            balance: 1000,
            current_bet: 10,
            total_spins: 0,
            total_wins: 0
        };
    }
    res.json(users[req.params.id]);
});

app.post('/api/spin', (req, res) => {
    const { userId, bet } = req.body;
    
    if (!users[userId]) {
        return res.status(404).json({ error: "User not found" });
    }
    
    if (users[userId].balance < bet) {
        return res.status(400).json({ error: "Not enough balance" });
    }
    
    // Имитация игры
    users[userId].balance -= bet;
    const win = Math.random() > 0.4 ? bet * 2 : 0;
    users[userId].balance += win;
    users[userId].total_spins += 1;
    
    if (win > 0) {
        users[userId].total_wins += 1;
    }
    
    res.json({
        success: true,
        balance: users[userId].balance,
        win: win
    });
});

app.post('/api/change_bet', (req, res) => {
    const { userId, bet } = req.body;
    
    if (!users[userId]) {
        return res.status(404).json({ error: "User not found" });
    }
    
    users[userId].current_bet = bet;
    res.json({ success: true });
});

// Serve static files
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

module.exports = app;
