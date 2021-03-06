import discord
from discord.ext import commands
import youtube_dl
import contextlib
import asyncio
import time
import wave
import os

## Class Async Timer
class Timer:
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback()

    def cancel(self):
        self._task.cancel()

## Class Player
class Player:
    ### __init__(self)
    def __init__(self): 
        # Check if music folder exists
        if not os.path.exists('music'):
            os.mkdir('music')
        else:
            for file in os.listdir("music"):
                if file.endswith(".wav"):
                    os.remove("music\\{0}".format(file))

        # INITIALIZE MEMORY
        self.invoked = False
        self.id = 0
        self.timer = Timer(1, None)
        self.voice = None
        self.mus_list = list()

    def __del__(self):
        # CLEAR MEMORY
        self.timer.cancel()
        self.invoked = False
        self.id = 0
        self.voice = None

        time.sleep(1)
        for file in self.mus_list:
            os.remove(file)

        self.mus_list.clear()

    ### Download Youtube Content
    async def download(self, url):
        opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': '\\music\\%(id)s.%(ext)s',      
            'noplaylist' : True,        
            'progress_hooks': [self.my_hook]
        }
        with youtube_dl.YoutubeDL(opts) as ydl:
            ydl.download([url])

        if self.voice.is_playing() != True:
            await self.play()

    ### Youtube download's hook
    def my_hook(self, d):
        if d['status'] == 'finished':
            filename = "{0}.wav".format(d['filename'].split('.')[0])
            try:
                self.mus_list.index(filename)
            except:    
                self.mus_list.append(filename)
            # print('Done downloading, now converting ...')

    ### 'Play music' function definition
    async def play(self):
        with contextlib.closing(wave.open(self.mus_list[self.id],'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
        # print("Duration: {0}".format(duration))

        source = discord.FFmpegPCMAudio(self.mus_list[self.id])
        self.voice.play(source)
        self.timer = Timer(duration, self.next)

    ### 'Next track' function
    async def next(self):
        self.timer.cancel()
        self.voice.stop()
        self.id = self.id + 1

        if len(self.mus_list) < 1:
            print("ERROR: There is nothing to play.")
            return

        if len(self.mus_list) <= self.id:
            self.id = 0

        print('LOG: Current track id: {0}. Current track dir: {1}'.format(self.id, self.mus_list[self.id]))
        await self.play()

    ### remove one song from current playlist
    async def remove(self):
        temp = self.mus_list[self.id]
        self.timer.cancel()
        self.voice.stop()

        if len(self.mus_list) > 1:  
            await self.next()
        else:
            await self.voice.disconnect()
            self.invoked = False

        time.sleep(1) 
        os.remove(temp)
        self.mus_list.remove(temp)
        self.id = self.id - 1

        if self.id < 0:
            self.id = 0