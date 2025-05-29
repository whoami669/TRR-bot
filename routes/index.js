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
    const features = [
        {
            category: 'AI Intelligence',
            icon: 'fas fa-brain',
            color: 'primary',
            items: [
                'Custom AI personalities with memory system',
                'Real-time sentiment analysis',
                'Intelligent behavior monitoring',
                'AI-powered moderation coaching',
                'Multi-language translation',
                'Collaborative storytelling',
                'Visual mood representation',
                'Server memory storage'
            ]
        },
        {
            category: 'Advanced Moderation',
            icon: 'fas fa-shield-alt',
            color: 'danger',
            items: [
                'AI-driven user behavior review',
                'Intelligent server lockdown system',
                'Smart content filtering',
                'Automated ban appeal system',
                'Suspicious behavior detection',
                'Risk scoring algorithms',
                'Moderation coaching assistant',
                'Real-time threat analysis'
            ]
        },
        {
            category: 'Gaming & Entertainment',
            icon: 'fas fa-gamepad',
            color: 'success',
            items: [
                'Comprehensive gamer profile system',
                'Game statistics tracking',
                'Tournament organization tools',
                'Achievement system',
                'Gaming event scheduling',
                'Leaderboards and rankings',
                'Game recommendation engine',
                'Automated gaming questions'
            ]
        },
        {
            category: 'Community Engagement',
            icon: 'fas fa-users',
            color: 'info',
            items: [
                'Activity boosters and waves',
                'Engagement multiplier systems',
                'Community revival tools',
                'Conversation starters',
                'Activity rewards system',
                'Member spotlight features',
                'Community challenges',
                'Social interaction tracking'
            ]
        },
        {
            category: 'Content Creation',
            icon: 'fas fa-video',
            color: 'warning',
            items: [
                'Stream announcement system',
                'Content scheduling tools',
                'Collaboration request management',
                'Milestone celebration automation',
                'Content feedback collection',
                'Sponsorship opportunity tracking',
                'Tutorial request system',
                'Analytics sharing tools'
            ]
        },
        {
            category: 'Developer Tools',
            icon: 'fas fa-code',
            color: 'secondary',
            items: [
                'Code review system',
                'Bug tracking and management',
                'Project showcase platform',
                'Career advice and mentoring',
                'Tech interview preparation',
                'Open source contribution tracking',
                'Learning resource sharing',
                'Developer community building'
            ]
        }
    ];

    res.render('features', { 
        title: 'Features - UltraBot',
        page: 'features',
        features: features
    });
});

// Commands page
router.get('/commands', (req, res) => {
    const commandCategories = [
        {
            name: 'AI Intelligence',
            commands: [
                { name: '/ai_persona', description: 'Set custom AI personality with memory system' },
                { name: '/ai_memory', description: 'Store important server memories' },
                { name: '/ai_recall', description: 'Recall stored memories by search terms' },
                { name: '/ai_sentiment', description: 'Analyze community sentiment' },
                { name: '/ai_story', description: 'Start collaborative storytelling' },
                { name: '/ai_translate', description: 'Translate text between languages' },
                { name: '/ai_summarize', description: 'Summarize channel activity' },
                { name: '/ai_moodboard', description: 'Create visual mood representation' }
            ]
        },
        {
            name: 'Advanced Moderation',
            commands: [
                { name: '/ai_review', description: 'AI-driven user behavior analysis' },
                { name: '/lockdown', description: 'Intelligent server lockdown system' },
                { name: '/content_filter', description: 'Manage intelligent content filters' },
                { name: '/ban_appeal', description: 'AI-assisted ban appeal system' },
                { name: '/suspicious_alert', description: 'Configure behavior detection' },
                { name: '/mod_coach', description: 'AI-powered moderation coaching' }
            ]
        },
        {
            name: 'Server Management',
            commands: [
                { name: '/server_takeover', description: 'Complete server restructuring' },
                { name: '/auto_setup', description: 'Automated server configuration' },
                { name: '/role_management', description: 'Advanced role management tools' },
                { name: '/channel_organization', description: 'Smart channel organization' }
            ]
        },
        {
            name: 'Gaming & Entertainment',
            commands: [
                { name: '/gamer_profile', description: 'Create comprehensive gamer profiles' },
                { name: '/tournament', description: 'Organize gaming tournaments' },
                { name: '/leaderboard', description: 'Display gaming leaderboards' },
                { name: '/achievement', description: 'Manage achievement systems' },
                { name: '/game_stats', description: 'Track detailed game statistics' }
            ]
        },
        {
            name: 'Content Creation',
            commands: [
                { name: '/stream_announcement', description: 'Announce live streams' },
                { name: '/content_schedule', description: 'Schedule content creation' },
                { name: '/collab_request', description: 'Request collaborations' },
                { name: '/milestone_celebration', description: 'Celebrate achievements' },
                { name: '/content_feedback', description: 'Request community feedback' }
            ]
        }
    ];

    res.render('commands', { 
        title: 'Commands - UltraBot',
        page: 'commands',
        commandCategories: commandCategories
    });
});

// Bot invite redirect
router.get('/invite', (req, res) => {
    const botId = process.env.BOT_CLIENT_ID || '1037399271735054387';
    const permissions = '8'; // Administrator permissions
    const scopes = 'bot%20applications.commands';
    
    const inviteUrl = `https://discord.com/api/oauth2/authorize?client_id=${botId}&permissions=${permissions}&scope=${scopes}`;
    res.redirect(inviteUrl);
});

module.exports = router;