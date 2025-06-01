import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import json
import base64
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

class WebTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="website-screenshot", description="Take screenshots of websites")
    @app_commands.describe(
        url="Website URL to screenshot",
        full_page="Capture full page or just viewport",
        device="Device type for responsive design"
    )
    @app_commands.choices(device=[
        app_commands.Choice(name="Desktop", value="desktop"),
        app_commands.Choice(name="Mobile", value="mobile"),
        app_commands.Choice(name="Tablet", value="tablet")
    ])
    async def website_screenshot(self, interaction: discord.Interaction, url: str, 
                               full_page: bool = False, device: str = "desktop"):
        await interaction.response.defer()
        
        try:
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # For demonstration - in production you'd use a headless browser service
            embed = discord.Embed(
                title="📸 Website Screenshot",
                description=f"**URL:** {url}\n**Device:** {device.title()}\n**Full Page:** {'Yes' if full_page else 'No'}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Status", value="Screenshot functionality requires a headless browser service", inline=False)
            embed.add_field(name="Alternative", value="You can use online services like:\n• Screenshot API\n• Puppeteer Cloud\n• BrowserStack", inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            await interaction.followup.send("Failed to capture screenshot.")

    @app_commands.command(name="url-info", description="Get detailed information about any URL")
    @app_commands.describe(url="URL to analyze")
    async def url_info(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.head(url, timeout=10) as response:
                        headers = dict(response.headers)
                        status_code = response.status
                        
                    # Get page content for title extraction
                    async with session.get(url, timeout=10) as response:
                        content = await response.text()
                        
                except Exception as e:
                    await interaction.followup.send(f"Failed to fetch URL: {str(e)}")
                    return
            
            # Extract title from HTML
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            page_title = title_match.group(1).strip() if title_match else "No title found"
            
            # Extract meta description
            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', content, re.IGNORECASE)
            description = desc_match.group(1) if desc_match else "No description found"
            
            embed = discord.Embed(
                title="🔍 URL Analysis",
                description=f"**URL:** {url}",
                color=discord.Color.green() if status_code == 200 else discord.Color.red()
            )
            
            embed.add_field(name="Status Code", value=str(status_code), inline=True)
            embed.add_field(name="Page Title", value=page_title[:100] + "..." if len(page_title) > 100 else page_title, inline=False)
            embed.add_field(name="Description", value=description[:200] + "..." if len(description) > 200 else description, inline=False)
            
            # Server info
            server = headers.get('server', 'Unknown')
            content_type = headers.get('content-type', 'Unknown')
            content_length = headers.get('content-length', 'Unknown')
            
            embed.add_field(name="Server", value=server, inline=True)
            embed.add_field(name="Content Type", value=content_type, inline=True)
            embed.add_field(name="Content Length", value=content_length, inline=True)
            
            # Security headers
            security_headers = {
                'X-Frame-Options': headers.get('x-frame-options'),
                'X-Content-Type-Options': headers.get('x-content-type-options'),
                'Strict-Transport-Security': headers.get('strict-transport-security'),
                'Content-Security-Policy': headers.get('content-security-policy')
            }
            
            security_info = []
            for header, value in security_headers.items():
                if value:
                    security_info.append(f"✅ {header}")
                else:
                    security_info.append(f"❌ {header}")
            
            embed.add_field(name="Security Headers", value="\n".join(security_info[:4]), inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"URL info error: {e}")
            await interaction.followup.send("Failed to analyze URL.")

    @app_commands.command(name="domain-whois", description="Get WHOIS information for domains")
    @app_commands.describe(domain="Domain name to lookup")
    async def domain_whois(self, interaction: discord.Interaction, domain: str):
        await interaction.response.defer()
        
        try:
            # Clean domain input
            domain = domain.lower().strip()
            if domain.startswith(('http://', 'https://')):
                domain = domain.split('://')[1].split('/')[0]
            
            # For demonstration - real implementation would use a WHOIS API
            embed = discord.Embed(
                title="🌐 Domain WHOIS Lookup",
                description=f"**Domain:** {domain}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Status", value="WHOIS lookup requires a dedicated WHOIS API service", inline=False)
            embed.add_field(name="Suggested Services", value="• WHOIS API\n• DomainTools API\n• WhoisXML API", inline=False)
            embed.add_field(name="Information Available", value="• Registration date\n• Expiration date\n• Registrar\n• DNS servers\n• Contact information", inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"WHOIS error: {e}")
            await interaction.followup.send("Failed to perform WHOIS lookup.")

    @app_commands.command(name="ip-lookup", description="Get detailed information about IP addresses")
    @app_commands.describe(ip="IP address to lookup")
    async def ip_lookup(self, interaction: discord.Interaction, ip: str):
        await interaction.response.defer()
        
        try:
            # Validate IP format
            ip_pattern = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
            if not ip_pattern.match(ip):
                await interaction.followup.send("Invalid IP address format.")
                return
            
            # Use a free IP geolocation service
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"http://ip-api.com/json/{ip}") as response:
                        if response.status == 200:
                            data = await response.json()
                        else:
                            await interaction.followup.send("Failed to fetch IP information.")
                            return
                except Exception as e:
                    await interaction.followup.send(f"Error fetching IP data: {str(e)}")
                    return
            
            if data.get('status') == 'fail':
                await interaction.followup.send(f"Failed to lookup IP: {data.get('message', 'Unknown error')}")
                return
            
            embed = discord.Embed(
                title="🌍 IP Address Lookup",
                description=f"**IP Address:** {ip}",
                color=discord.Color.blue()
            )
            
            # Location information
            country = data.get('country', 'Unknown')
            region = data.get('regionName', 'Unknown')
            city = data.get('city', 'Unknown')
            
            embed.add_field(name="Location", value=f"{city}, {region}, {country}", inline=False)
            embed.add_field(name="Latitude", value=str(data.get('lat', 'Unknown')), inline=True)
            embed.add_field(name="Longitude", value=str(data.get('lon', 'Unknown')), inline=True)
            embed.add_field(name="Timezone", value=data.get('timezone', 'Unknown'), inline=True)
            
            # ISP information
            embed.add_field(name="ISP", value=data.get('isp', 'Unknown'), inline=True)
            embed.add_field(name="Organization", value=data.get('org', 'Unknown'), inline=True)
            embed.add_field(name="AS Number", value=data.get('as', 'Unknown'), inline=True)
            
            # Additional info
            embed.add_field(name="ZIP Code", value=data.get('zip', 'Unknown'), inline=True)
            embed.add_field(name="Mobile", value="Yes" if data.get('mobile') else "No", inline=True)
            embed.add_field(name="Proxy/VPN", value="Yes" if data.get('proxy') else "No", inline=True)
            
            embed.set_footer(text="Data provided by ip-api.com")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"IP lookup error: {e}")
            await interaction.followup.send("Failed to lookup IP address.")

    @app_commands.command(name="speed-test", description="Test internet connection speed")
    async def speed_test(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Simulate speed test by downloading a small file and measuring time
            test_url = "https://httpbin.org/bytes/1048576"  # 1MB test file
            
            start_time = datetime.now()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        end_time = datetime.now()
                        
                        # Calculate speed
                        duration = (end_time - start_time).total_seconds()
                        size_mb = len(content) / (1024 * 1024)
                        speed_mbps = (size_mb * 8) / duration  # Convert to Mbps
                        
                        embed = discord.Embed(
                            title="⚡ Speed Test Results",
                            color=discord.Color.green()
                        )
                        embed.add_field(name="Download Speed", value=f"{speed_mbps:.2f} Mbps", inline=True)
                        embed.add_field(name="Test Size", value=f"{size_mb:.1f} MB", inline=True)
                        embed.add_field(name="Duration", value=f"{duration:.2f}s", inline=True)
                        embed.add_field(name="Server Location", value="Bot's Server", inline=True)
                        embed.set_footer(text="Note: This tests the bot's connection, not yours")
                        
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send("Failed to perform speed test.")
                        
        except Exception as e:
            logger.error(f"Speed test error: {e}")
            await interaction.followup.send("Failed to perform speed test.")

    @app_commands.command(name="http-headers", description="Analyze HTTP headers of any website")
    @app_commands.describe(url="Website URL to analyze")
    async def http_headers(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    headers = dict(response.headers)
                    status_code = response.status
            
            embed = discord.Embed(
                title="📋 HTTP Headers Analysis",
                description=f"**URL:** {url}\n**Status Code:** {status_code}",
                color=discord.Color.blue()
            )
            
            # Group headers by category
            security_headers = {}
            cache_headers = {}
            server_headers = {}
            other_headers = {}
            
            for key, value in headers.items():
                key_lower = key.lower()
                if any(sec in key_lower for sec in ['security', 'frame', 'xss', 'content-security', 'transport']):
                    security_headers[key] = value
                elif any(cache in key_lower for cache in ['cache', 'expires', 'etag', 'last-modified']):
                    cache_headers[key] = value
                elif any(server in key_lower for server in ['server', 'powered', 'x-served']):
                    server_headers[key] = value
                else:
                    other_headers[key] = value
            
            # Add fields for each category
            if security_headers:
                sec_text = "\n".join([f"**{k}:** {v[:50]}..." if len(v) > 50 else f"**{k}:** {v}" 
                                     for k, v in list(security_headers.items())[:3]])
                embed.add_field(name="🔒 Security Headers", value=sec_text, inline=False)
            
            if cache_headers:
                cache_text = "\n".join([f"**{k}:** {v[:50]}..." if len(v) > 50 else f"**{k}:** {v}" 
                                       for k, v in list(cache_headers.items())[:3]])
                embed.add_field(name="💾 Cache Headers", value=cache_text, inline=False)
            
            if server_headers:
                server_text = "\n".join([f"**{k}:** {v[:50]}..." if len(v) > 50 else f"**{k}:** {v}" 
                                        for k, v in list(server_headers.items())[:3]])
                embed.add_field(name="🖥️ Server Headers", value=server_text, inline=False)
            
            embed.add_field(name="📊 Total Headers", value=str(len(headers)), inline=True)
            embed.set_footer(text="Only showing first 3 headers per category")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"HTTP headers error: {e}")
            await interaction.followup.send("Failed to analyze HTTP headers.")

    @app_commands.command(name="ssl-check", description="Check SSL certificate information")
    @app_commands.describe(domain="Domain to check SSL certificate")
    async def ssl_check(self, interaction: discord.Interaction, domain: str):
        await interaction.response.defer()
        
        try:
            # Clean domain input
            if domain.startswith(('http://', 'https://')):
                domain = domain.split('://')[1].split('/')[0]
            
            # For demonstration - real implementation would use SSL certificate checking
            embed = discord.Embed(
                title="🔒 SSL Certificate Check",
                description=f"**Domain:** {domain}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Status", value="SSL certificate checking requires specialized libraries", inline=False)
            embed.add_field(name="Implementation Note", value="Would use `ssl` module and `socket` to connect and retrieve certificate details", inline=False)
            embed.add_field(name="Information Available", value="• Certificate validity\n• Expiration date\n• Issuer\n• Subject\n• Signature algorithm\n• Key size", inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"SSL check error: {e}")
            await interaction.followup.send("Failed to check SSL certificate.")

async def setup(bot):
    await bot.add_cog(WebTools(bot))