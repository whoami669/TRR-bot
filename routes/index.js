const express = require('express');
const router = express.Router();

// Home page
router.get('/', (req, res) => {
  res.render('index', {
    title: 'UltraBot - Advanced Discord Server Management',
    page: 'home'
  });
});

// Features page
router.get('/features', (req, res) => {
  res.render('features', {
    title: 'Features - UltraBot',
    page: 'features'
  });
});

// Commands page
router.get('/commands', (req, res) => {
  res.render('commands', {
    title: 'Commands - UltraBot',
    page: 'commands'
  });
});

// Invite page
router.get('/invite', (req, res) => {
  res.render('invite', {
    title: 'Invite UltraBot',
    page: 'invite'
  });
});

module.exports = router;