const express = require('express');
const { Pool } = require('pg');
const router = express.Router();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

// Dashboard main page
router.get('/', async (req, res) => {
  try {
    // Get bot statistics
    const statsResult = await pool.query('SELECT * FROM bot_stats ORDER BY updated_at DESC LIMIT 1');
    const stats = statsResult.rows[0] || {
      guild_count: 0,
      user_count: 0,
      message_count: 0,
      command_count: 0,
      uptime: 0
    };

    // Get server configurations count
    const serverResult = await pool.query('SELECT COUNT(*) as server_count FROM server_configs');
    const serverCount = serverResult.rows[0].server_count || 0;

    res.render('dashboard/index', {
      title: 'Dashboard - UltraBot',
      page: 'dashboard',
      stats: stats,
      serverCount: serverCount
    });
  } catch (error) {
    console.error('Dashboard error:', error);
    res.render('dashboard/index', {
      title: 'Dashboard - UltraBot',
      page: 'dashboard',
      stats: {
        guild_count: 0,
        user_count: 0,
        message_count: 0,
        command_count: 0,
        uptime: 0
      },
      serverCount: 0,
      error: 'Unable to load statistics'
    });
  }
});

// Server management
router.get('/servers', async (req, res) => {
  try {
    const serversResult = await pool.query('SELECT * FROM server_configs ORDER BY guild_name ASC');
    const servers = serversResult.rows;

    res.render('dashboard/servers', {
      title: 'Server Management - UltraBot',
      page: 'dashboard',
      servers: servers
    });
  } catch (error) {
    console.error('Servers page error:', error);
    res.render('dashboard/servers', {
      title: 'Server Management - UltraBot',
      page: 'dashboard',
      servers: [],
      error: 'Unable to load servers'
    });
  }
});

// Individual server settings
router.get('/servers/:guildId', async (req, res) => {
  try {
    const { guildId } = req.params;
    const serverResult = await pool.query('SELECT * FROM server_configs WHERE guild_id = $1', [guildId]);
    
    if (serverResult.rows.length === 0) {
      return res.status(404).render('404', {
        title: 'Server Not Found',
        message: 'The requested server configuration was not found.'
      });
    }

    const server = serverResult.rows[0];

    res.render('dashboard/server-config', {
      title: `${server.guild_name} Settings - UltraBot`,
      page: 'dashboard',
      server: server
    });
  } catch (error) {
    console.error('Server config error:', error);
    res.status(500).render('error', {
      error: 'Unable to load server configuration',
      message: error.message
    });
  }
});

// Analytics page
router.get('/analytics', async (req, res) => {
  try {
    // Get recent statistics for charts
    const recentStats = await pool.query(`
      SELECT * FROM bot_stats 
      ORDER BY updated_at DESC 
      LIMIT 30
    `);

    res.render('dashboard/analytics', {
      title: 'Analytics - UltraBot',
      page: 'dashboard',
      statsData: JSON.stringify(recentStats.rows)
    });
  } catch (error) {
    console.error('Analytics error:', error);
    res.render('dashboard/analytics', {
      title: 'Analytics - UltraBot',
      page: 'dashboard',
      statsData: JSON.stringify([]),
      error: 'Unable to load analytics data'
    });
  }
});

// Settings page
router.get('/settings', (req, res) => {
  res.render('dashboard/settings', {
    title: 'Bot Settings - UltraBot',
    page: 'dashboard'
  });
});

module.exports = router;