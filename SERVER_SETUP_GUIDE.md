# Discord Server Setup Guide

## Bot Role Management Commands

Your bot now includes these role management commands:

### Role Commands (for users with Manage Roles permission)
- `/role-add` - Add a role to a user
- `/role-remove` - Remove a role from a user
- `/role-info` - Get information about a role
- `/role-list` - List all server roles

### Administrator Commands
- `/role-all` - Add or remove a role from all members (Administrator only)

## Manual Server Configuration Steps

Since Discord bots cannot modify server permissions directly, you'll need to do these manually:

### 1. Setting Up Role Hierarchy
1. Go to Server Settings → Roles
2. Create/arrange roles in this order (top to bottom):
   - Bot roles (highest)
   - President
   - [Other staff roles]
   - Members
   - @everyone (lowest)

### 2. Voice Channel Permissions
For each voice channel you want to unlock:
1. Right-click the voice channel → Edit Channel
2. Go to Permissions tab
3. Add the "Members" role
4. Enable these permissions:
   - View Channel
   - Connect
   - Speak
   - Use Voice Activity

### 3. Staff Chat Restrictions
For staff-only channels:
1. Right-click the channel → Edit Channel
2. Go to Permissions tab
3. Set @everyone permissions to:
   - View Channel: ❌ (disabled)
4. Add "President" role with:
   - View Channel: ✅
   - Send Messages: ✅
   - Read Message History: ✅

### 4. Bot Access Configuration
The bot already respects Discord's permission system:
- Commands with `@app_commands.default_permissions()` require specific permissions
- Role hierarchy is automatically respected
- President role and above can use staff commands if they have the required Discord permissions

## Using the Role Commands

### Give roles to all members:
```
/role-all role:Members action:Add
```

### Check who has a specific role:
```
/role-info role:President
```

### Add individual roles:
```
/role-add user:@username role:Members
```

## Important Notes

- The bot cannot override Discord's permission system
- Users need appropriate Discord permissions to use management commands
- President role users will have access based on their Discord permissions
- All commands respect role hierarchy - you cannot manage roles equal to or higher than your own
- The bot's role should be positioned above any roles it needs to manage

Your bot now has 45+ commands including comprehensive role management while maintaining no automated messaging.