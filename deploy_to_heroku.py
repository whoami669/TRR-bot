#!/usr/bin/env python3
"""
Ultra Bot Heroku Deployment Script
Packages the bot for deployment to existing Heroku app
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_deployment_package():
    """Create a deployment package for Heroku"""
    
    # Create deployment directory
    deploy_dir = Path("heroku_deployment")
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()
    
    # Files to include in deployment
    files_to_copy = [
        "main.py",
        "Procfile",
        "runtime.txt",
        ".env.example"
    ]
    
    # Copy main files
    for file in files_to_copy:
        if Path(file).exists():
            shutil.copy2(file, deploy_dir)
    
    # Copy cogs directory
    if Path("cogs").exists():
        shutil.copytree("cogs", deploy_dir / "cogs")
    
    # Create requirements.txt from heroku_requirements.txt
    if Path("heroku_requirements.txt").exists():
        shutil.copy2("heroku_requirements.txt", deploy_dir / "requirements.txt")
    
    # Create deployment README
    readme_content = """# Ultra Bot Deployment Package

## Quick Deployment to Existing Heroku App

1. Extract this package to your local machine
2. Navigate to the deployment folder
3. Login to Heroku: `heroku login`
4. Add your existing app remote: `heroku git:remote -a your-app-name`
5. Deploy:
   ```bash
   git init
   git add .
   git commit -m "Deploy Ultra Bot v2.0 with 94 commands"
   git push heroku main --force
   heroku ps:scale worker=1
   ```

## Environment Variables Required
- DISCORD_TOKEN (your Discord bot token)
- OPENAI_API_KEY (your OpenAI API key)

## Bot Features (94 Commands)
- AI conversation system
- Advanced moderation
- Reaction roles
- Giveaway management
- Enhanced utilities
- Weather API
- QR code generation
- And much more...

Your Ultra Bot will be running 24/7 with maximum Discord functionality.
"""
    
    with open(deploy_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    # Create .env template
    env_template = """# Ultra Bot Environment Variables
# Copy this to .env and fill in your actual tokens

DISCORD_TOKEN=your_discord_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
"""
    
    with open(deploy_dir / ".env.template", "w") as f:
        f.write(env_template)
    
    # Create ZIP package
    zip_path = "ultra_bot_heroku_deployment.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(deploy_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ Deployment package created: {zip_path}")
    print(f"✅ Deployment folder created: {deploy_dir}")
    print("\n📦 Package contents:")
    
    for root, dirs, files in os.walk(deploy_dir):
        level = root.replace(str(deploy_dir), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")
    
    return zip_path, deploy_dir

if __name__ == "__main__":
    create_deployment_package()