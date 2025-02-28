import sys
import os
import time
import json
import asyncio
import logging
import aiohttp
import discord
from datetime import datetime
from dotenv import load_dotenv
import pyfiglet

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.live import Live
from rich.text import Text
from rich.prompt import Prompt, Confirm

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("UltimateDiscordCloner")

load_dotenv()
USER_TOKEN = os.getenv("USER_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not USER_TOKEN or not BOT_TOKEN:
    print("Error: USER_TOKEN and BOT_TOKEN must be set in your environment.")
    sys.exit(1)

console = Console()
RAINBOW_COLORS = ["red", "dark_orange", "yellow", "green", "blue", "magenta"]

class BannerAnimator:
    """
    Displays an animated banner with a smooth rainbow effect.
    """
    def __init__(self, text="Flames", font="slant", duration=3.0, delay=0.15):
        self.text = text
        self.font = font
        self.duration = duration
        self.delay = delay

    def generate_banner(self, color: str) -> Text:
        ascii_art = pyfiglet.figlet_format(self.text, font=self.font)
        return Text(ascii_art, style=color)

    def animate(self):
        end_time = time.time() + self.duration
        with Live(console=console, refresh_per_second=8) as live:
            color_index = 0
            while time.time() < end_time:
                current_color = RAINBOW_COLORS[color_index % len(RAINBOW_COLORS)]
                banner = self.generate_banner(current_color)
                panel = Panel(banner,
                              border_style=current_color,
                              title="[bold]Welcome!",
                              subtitle="Ultimate Discord Server Cloner",
                              expand=True)
                live.update(panel)
                time.sleep(self.delay)
                color_index += 1

class FancyMenu:
    """
    Renders a detailed interactive menu using rich Panels and Tables.
    """
    def display_menu(self):
        table = Table(title="Main Menu", show_header=True, header_style="bold cyan")
        table.add_column("Option", justify="center", style="bold magenta")
        table.add_column("Description", justify="left", style="white")
        table.add_row("1", "Fetch Server Data")
        table.add_row("2", "Clone Server Data")
        table.add_row("3", "View Logs")
        table.add_row("4", "Clear Cache")
        table.add_row("5", "Instructions")
        table.add_row("Q", "Quit Application")
        console.print(Panel(table, border_style="magenta"))
        choice = Prompt.ask("[bold magenta]Enter your choice[/]", choices=["1", "2", "3", "4", "5", "Q", "q"], default="Q")
        return choice.lower()

    def display_status(self, message: str, style: str = "magenta"):
        console.print(Panel(message, style=style, expand=False))

    def display_error(self, message: str):
        console.print(Panel(message, style="bold red", expand=False))

    def display_success(self, message: str):
        console.print(Panel(message, style="bold green", expand=False))

    def wait_for_user(self):
        Prompt.ask("[bold magenta]Press Enter to return to the main menu[/]", default="")

class InstructionsViewer:
    """
    Displays detailed instructions and usage guidelines for the user.
    """
    def show_instructions(self):
        instructions = (
            "[bold underline magenta]Welcome to Flames Discord Server Cloner![/]\n\n"
            "[bold cyan]Overview:[/]\n"
            "This tool helps you clone Discord server configurations, including roles, channels, and emojis.\n\n"
            "[bold cyan]Prerequisites:[/]\n"
            "1. Python 3.8+ must be installed on your system.\n"
            "2. Install required packages using: [green]pip install rich pyfiglet discord aiohttp python-dotenv[/]\n"
            "3. Set your environment variables [yellow]USER_TOKEN[/] and [yellow]BOT_TOKEN[/] appropriately.\n\n"
            "[bold cyan]How to Use:[/]\n"
            "• Choose [bold]Fetch Server Data[/] to collect data from a source server using your user token.\n"
            "  - You will be prompted to enter the source server ID.\n"
            "  - The data is saved as a JSON file in the working directory.\n\n"
            "• Choose [bold]Clone Server Data[/] to clone a server using your bot token.\n"
            "  - You will select the JSON file created from the fetch operation.\n"
            "  - Enter the target server ID (the bot must be in that server).\n\n"
            "• [bold]View Logs[/] allows you to view the application logs for debugging or verification purposes.\n\n"
            "• [bold]Clear Cache[/] simulates clearing of temporary data used by the application.\n\n"
            "• [bold]Instructions[/] (this option) displays this help message.\n\n"
            "[bold cyan]Additional Tips:[/]\n"
            "- Always double-check that your tokens are correct and have the required permissions.\n"
            "- If an error occurs, view the logs for more information.\n"
            "- This tool is intended for educational purposes; use it responsibly.\n\n"
            "[bold underline magenta]Enjoy![/]"
        )
        console.print(Panel(instructions, title="[bold magenta]Instructions", border_style="magenta", expand=True))
        Prompt.ask("[bold magenta]Press Enter to return to the main menu[/]", default="")

class ServerDataCollector:
    """
    Uses a user token to collect a server's data (roles, channels, emojis, etc.).
    """
    def __init__(self, user_token: str, guild_id: str):
        self.user_token = user_token
        self.guild_id = guild_id
        self.headers = {"Authorization": self.user_token, "Content-Type": "application/json"}
        self.base_url = "https://discord.com/api/v9"

    async def fetch_data(self, endpoint: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}{endpoint}", headers=self.headers) as response:
                    if response.status != 200:
                        logger.error(f"Error fetching {endpoint}: HTTP {response.status}")
                        return {}
                    return await response.json()
        except Exception as e:
            logger.exception(f"Exception fetching {endpoint}: {e}")
            return {}

    async def collect_server_data(self):
        server_data = {}
        progress = Progress(
            SpinnerColumn(style="magenta"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None, style="magenta"),
            transient=True,
        )
        task = progress.add_task("[magenta]Collecting Server Data...", total=4)
        with progress:
            server_data["server_info"] = await self.fetch_data(f"/guilds/{self.guild_id}")
            progress.advance(task)
            server_data["roles"] = await self.fetch_data(f"/guilds/{self.guild_id}/roles")
            progress.advance(task)
            server_data["channels"] = await self.fetch_data(f"/guilds/{self.guild_id}/channels")
            progress.advance(task)
            server_data["emojis"] = await self.fetch_data(f"/guilds/{self.guild_id}/emojis")
            progress.advance(task)
        server_name = server_data.get("server_info", {}).get("name", f"server_{self.guild_id}")
        filename = f"{server_name}_clone_data.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(server_data, f, indent=4, ensure_ascii=False)
        return filename

class ServerCloner(discord.Client):
    """
    Clones a Discord server from collected data.
    """
    def __init__(self, bot_token: str, target_guild_id: int, json_file: str):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        super().__init__(intents=intents)
        self.bot_token = bot_token
        self.target_guild_id = target_guild_id
        self.json_file = json_file

    async def on_ready(self):
        console.print(Panel(f"Logged in as {self.user}", style="magenta"))
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                server_data = json.load(f)
        except Exception as e:
            console.print(Panel(f"Error reading JSON file: {e}", style="bold red"))
            await self.close()
            return

        target_guild = self.get_guild(self.target_guild_id)
        if not target_guild:
            console.print(Panel("Target guild not found! Ensure the bot is in the server.", style="bold red"))
            await self.close()
            return

        await self.clone_roles(target_guild, server_data.get("roles", []))
        await self.clone_channels(target_guild, server_data.get("channels", []))
        await self.clone_emojis(target_guild, server_data.get("emojis", []))
        console.print(Panel("Server cloning completed!", style="bold green"))
        await self.close()

    async def clone_roles(self, target_guild, roles):
        console.print(Panel("Cloning roles...", style="magenta"))
        for role in roles[::-1]:
            if role.get("name") == "@everyone":
                continue
            try:
                await target_guild.create_role(
                    name=role.get("name", "Unnamed Role"),
                    color=discord.Color(role.get("color", 0)),
                    hoist=role.get("hoist", False),
                    mentionable=role.get("mentionable", False)
                )
            except Exception as e:
                logger.exception(f"Error cloning role {role.get('name')}: {e}")
        console.print(Panel("Roles cloned!", style="bold green"))

    async def clone_channels(self, target_guild, channels):
        console.print(Panel("Cloning channels...", style="magenta"))
        category_map = {}
        for channel in channels:
            if channel.get("type") == 4:
                try:
                    new_category = await target_guild.create_category(channel.get("name", "Unnamed Category"))
                    category_map[channel.get("id")] = new_category
                except Exception as e:
                    logger.exception(f"Error cloning category {channel.get('name')}: {e}")
        for channel in channels:
            if channel.get("type") in [0, 2]:
                category = category_map.get(channel.get("parent_id"))
                try:
                    if channel.get("type") == 0:
                        await target_guild.create_text_channel(channel.get("name", "Unnamed Channel"), category=category)
                    else:
                        await target_guild.create_voice_channel(channel.get("name", "Unnamed Channel"), category=category)
                except Exception as e:
                    logger.exception(f"Error cloning channel {channel.get('name')}: {e}")
        console.print(Panel("Channels cloned!", style="bold green"))

    async def clone_emojis(self, target_guild, emojis):
        console.print(Panel("Cloning emojis...", style="magenta"))
        for emoji in emojis:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(emoji.get("url")) as resp:
                        emoji_img = await resp.read()
                await target_guild.create_custom_emoji(name=emoji.get("name", "emoji"), image=emoji_img)
            except Exception as e:
                logger.exception(f"Error cloning emoji {emoji.get('name')}: {e}")
        console.print(Panel("Emojis cloned!", style="bold green"))

class CacheManager:
    """
    Simulates cache operations.
    """
    def clear_cache(self):
        console.print(Panel("Cache cleared successfully!", style="bold green"))

class LogViewer:
    """
    Displays application logs.
    """
    LOG_FILE = "app.log"

    def view_logs(self):
        if not os.path.exists(self.LOG_FILE):
            console.print(Panel("No logs available.", style="magenta"))
            return
        with open(self.LOG_FILE, "r", encoding="utf-8") as f:
            logs = f.read()
        console.print(Panel(logs, title="Application Logs", style="magenta"))

class MegaDiscordClonerApp:
    def __init__(self):
        self.menu = FancyMenu()
        self.cache_manager = CacheManager()
        self.log_viewer = LogViewer()
        self.instructions_viewer = InstructionsViewer()

    def run(self):
        while True:
            try:
                os.system("cls" if os.name == "nt" else "clear")
                animator = BannerAnimator(text="Flames", font="slant", duration=1.5, delay=0.1)
                animator.animate()
                choice = self.menu.display_menu()
                if choice == "1":
                    self.fetch_server_data()
                elif choice == "2":
                    self.clone_server_data()
                elif choice == "3":
                    self.log_viewer.view_logs()
                    self.menu.wait_for_user()
                elif choice == "4":
                    self.cache_manager.clear_cache()
                    self.menu.wait_for_user()
                elif choice == "5":
                    self.instructions_viewer.show_instructions()
                elif choice == "q":
                    if Confirm.ask("[bold magenta]Are you sure you want to quit?[/]"):
                        console.print(Panel("Exiting the application. Goodbye!", style="bold green"))
                        break
                else:
                    self.menu.display_error("Invalid option. Please try again.")
                    self.menu.wait_for_user()
            except Exception as e:
                logger.exception(f"Unexpected error in main loop: {e}")
                self.menu.display_error("An unexpected error occurred. Please check the logs.")
                self.menu.wait_for_user()

    def fetch_server_data(self):
        guild_id = Prompt.ask("[bold magenta]Enter the source server ID[/]").strip()
        collector = ServerDataCollector(USER_TOKEN, guild_id)
        try:
            json_file = asyncio.run(collector.collect_server_data())
            self.menu.display_success(f"Server data has been saved to {json_file}")
        except Exception as e:
            self.menu.display_error(f"Error during data collection: {e}")
        self.menu.wait_for_user()

    def clone_server_data(self):
        json_files = [f for f in os.listdir() if f.endswith("_clone_data.json")]
        if not json_files:
            self.menu.display_error("No server clone data files found!")
            self.menu.wait_for_user()
            return

        table = Table(title="Available JSON Files", style="magenta")
        table.add_column("Number", justify="center", style="cyan")
        table.add_column("Filename", justify="left", style="white")
        for i, file in enumerate(json_files):
            table.add_row(str(i+1), file)
        console.print(Panel(table, title="Select a JSON File", style="magenta"))

        try:
            file_choice = int(Prompt.ask("[bold magenta]Enter file number[/]")) - 1
            selected_file = json_files[file_choice]
        except (ValueError, IndexError):
            self.menu.display_error("Invalid file selection!")
            self.menu.wait_for_user()
            return

        try:
            target_guild_id = int(Prompt.ask("[bold magenta]Enter the target server ID[/]").strip())
        except ValueError:
            self.menu.display_error("Invalid target server ID!")
            self.menu.wait_for_user()
            return

        client = ServerCloner(BOT_TOKEN, target_guild_id, selected_file)
        try:
            client.run(BOT_TOKEN)
        except Exception as e:
            self.menu.display_error(f"Error during server cloning: {e}")
        self.menu.wait_for_user()

if __name__ == "__main__":
    app = MegaDiscordClonerApp()
    app.run()
