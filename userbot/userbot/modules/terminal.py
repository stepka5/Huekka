import asyncio
import logging
import os
import subprocess
from telethon import events
from pathlib import Path

logger = logging.getLogger("UserBot.Terminal")

class TerminalModule:
    def __init__(self, bot):
        self.bot = bot
        self.active_processes = {}
        self.flood_wait = 2  # Delay between output updates
        self.termux_emoji_id = 5253647504485941212  # Termux emoji ID
        
        bot.register_command(
            cmd="terminal",
            handler=self.run_terminal,
            description="Execute system commands in Termux",
            module_name="Terminal",
            aliases=["term", "cmd"]
        )
        
        bot.register_command(
            cmd="terminate",
            handler=self.terminate_process,
            description="Terminate running command",
            module_name="Terminal"
        )

    async def run_terminal(self, event):
        """Execute system command in Termux"""
        command = event.pattern_match.group(2) or ""
        if not command:
            await event.edit(f"<emoji document_id={self.termux_emoji_id}>⚙</emoji> Please specify a command.\nExample: <code>.terminal ls -la</code>")
            return

        # Create message with Termux emoji
        msg = await event.edit(
            f"<emoji document_id={self.termux_emoji_id}>⚙</emoji> Executing:\n"
            f"<code>{command}</code>\n\n"
            f"<emoji document_id={self.termux_emoji_id}>⚙</emoji> Status: <code>running</code>"
        )
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        self.active_processes[msg.id] = process
        
        output = ""
        last_update = asyncio.get_event_loop().time()
        
        while True:
            data = await asyncio.wait_for(process.stdout.read(1024), timeout=1) or b""
            err_data = await asyncio.wait_for(process.stderr.read(1024), timeout=1) or b""
            
            if not data and not err_data:
                if process.returncode is not None:
                    break
                await asyncio.sleep(0.1)
                continue
            
            output += data.decode(errors="ignore") + err_data.decode(errors="ignore")
            
            current_time = asyncio.get_event_loop().time()
            if current_time - last_update > self.flood_wait:
                await self.update_message(msg, command, output, process.returncode)
                last_update = current_time
        
        await self.update_message(msg, command, output, process.returncode)
        
        if msg.id in self.active_processes:
            del self.active_processes[msg.id]

    async def update_message(self, message, command, output, returncode):
        """Update message with command output"""
        status = "completed" if returncode is not None else "running"
        code = f"<code>{returncode}</code>" if returncode is not None else "<code>-</code>"
        
        max_length = 3900
        if len(output) > max_length:
            output = output[-max_length:]
        
        text = (
            f"<emoji document_id={self.termux_emoji_id}>⚙</emoji> Command:\n"
            f"<code>{command}</code>\n\n"
            f"<emoji document_id={self.termux_emoji_id}>⚙</emoji> Status: <code>{status}</code>\n"
            f"<emoji document_id={self.termux_emoji_id}>⚙</emoji> Result: {code}\n\n"
            f"<emoji document_id={self.termux_emoji_id}>⚙</emoji> Output:\n<code>\n{output}\n</code>"
        )
        
        try:
            await message.edit(text)
        except Exception as e:
            logger.error(f"Error updating message: {str(e)}")

    async def terminate_process(self, event):
        """Terminate running command"""
        reply_msg = await event.get_reply_message()
        if not reply_msg:
            await event.edit(f"<emoji document_id={self.termux_emoji_id}>⚙</emoji> Please reply to the message with running command.")
            return
        
        if reply_msg.id not in self.active_processes:
            await event.edit(f"<emoji document_id={self.termux_emoji_id}>⚙</emoji> No active process for this message.")
            return
        
        try:
            process = self.active_processes[reply_msg.id]
            process.terminate()
            await event.edit(f"<emoji document_id={self.termux_emoji_id}>⚙</emoji> Command terminated.")
            del self.active_processes[reply_msg.id]
        except Exception as e:
            await event.edit(f"<emoji document_id={self.termux_emoji_id}>⚙</emoji> Error terminating: {str(e)}")

def setup(bot):
    bot.set_module_description("Terminal", "Execute system commands in Termux environment")
    TerminalModule(bot)