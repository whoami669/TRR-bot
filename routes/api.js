const express = require('express');
const { Pool } = require('pg');
const router = express.Router();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

// Get bot statistics
router.get('/stats', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM bot_stats ORDER BY updated_at DESC LIMIT 1');
    const stats = result.rows[0] || {
      guild_count: 0,
      user_count: 0,
      message_count: 0,
      command_count: 0,
      uptime: 0
    };
    res.json(stats);
  } catch (error) {
    console.error('API stats error:', error);
    res.status(500).json({ error: 'Unable to fetch statistics' });
  }
});

// Update bot statistics
router.post('/stats', async (req, res) => {
  try {
    const { guild_count, user_count, message_count, command_count, uptime } = req.body;
    
    await pool.query(`
      INSERT INTO bot_stats (guild_count, user_count, message_count, command_count, uptime, updated_at)
      VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
    `, [guild_count, user_count, message_count, command_count, uptime]);
    
    res.json({ success: true });
  } catch (error) {
    console.error('API stats update error:', error);
    res.status(500).json({ error: 'Unable to update statistics' });
  }
});

// Get server configurations
router.get('/servers', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM server_configs ORDER BY guild_name ASC');
    res.json(result.rows);
  } catch (error) {
    console.error('API servers error:', error);
    res.status(500).json({ error: 'Unable to fetch servers' });
  }
});

// Update server configuration
router.post('/servers/:guildId', async (req, res) => {
  try {
    const { guildId } = req.params;
    const { guild_name, prefix, welcome_channel, log_channel, auto_role, settings } = req.body;
    
    await pool.query(`
      INSERT INTO server_configs (guild_id, guild_name, prefix, welcome_channel, log_channel, auto_role, settings, updated_at)
      VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
      ON CONFLICT (guild_id) 
      DO UPDATE SET 
        guild_name = $2,
        prefix = $3,
        welcome_channel = $4,
        log_channel = $5,
        auto_role = $6,
        settings = $7,
        updated_at = CURRENT_TIMESTAMP
    `, [guildId, guild_name, prefix, welcome_channel, log_channel, auto_role, JSON.stringify(settings)]);
    
    res.json({ success: true });
  } catch (error) {
    console.error('API server config error:', error);
    res.status(500).json({ error: 'Unable to update server configuration' });
  }
});

// Get analytics data
router.get('/analytics', async (req, res) => {
  try {
    const { days = 30 } = req.query;
    const result = await pool.query(`
      SELECT * FROM bot_stats 
      WHERE updated_at >= NOW() - INTERVAL '${parseInt(days)} days'
      ORDER BY updated_at ASC
    `);
    res.json(result.rows);
  } catch (error) {
    console.error('API analytics error:', error);
    res.status(500).json({ error: 'Unable to fetch analytics data' });
  }
});

module.exports = router;