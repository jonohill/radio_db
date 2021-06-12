import asyncio
import json
import logging
from itertools import takewhile
from time import time
from typing import List

import aiohttp
from pydantic import BaseModel
import pydantic

log = logging.getLogger(__name__)

class Stream:

    def __init__(self, stream_url):
        self.stream_url = stream_url

    async def read_song_info(self):
        raise NotImplementedError()

M3U8_MAGIC = '#EXTM3U'.encode()

class FormatError(Exception):
    pass

class M3u8(Stream):

    async def _read_stream_inf(_, url_line):
        """Example:
            #EXT-X-STREAM-INF:BANDWIDTH=33000,CODECS="mp4a.40.5"
            https://url-to-another-stream.m3u8
        """
        m3u8 = M3u8(url_line)
        async for result in m3u8.read_song_info():
            yield result

    def _read_inf(_, tag_line, url_line):
        tag_map = {}
        tag_map['file'] = url_line

        chars = iter(tag_line)
        pop = lambda: next(chars, None)
        until = lambda c: ''.join(takewhile(lambda d: c != d, chars))

        # duration
        tag_map['duration'] = float(until(','))

        eol = False
        while not eol:
            # key
            key = until('=')
            
            # value
            value = ''
            escape = False
            quote = False
            while not eol:
                c = pop()
                if not c:
                    eol = True
                    break
                if escape:
                    value += c
                    escape = False
                elif c == '\\':
                    escape = True
                elif quote:
                    if c == '"':
                        quote = False
                    else:
                        value += c
                elif c == '"':
                    quote = True
                elif c == ',':
                    break

            tag_map[key] = value

        return tag_map

    async def read_song_info(self):
        recent = [None] * 20
        def not_recent(item):
            file = item['file']
            if file in recent:
                return False
            recent.append(file)
            recent.pop(0)
            return True

        async with aiohttp.ClientSession() as http:
            while True:
                target_duration = 5
                response = await http.get(self.stream_url)
                async def read(n=-1): 
                    return (await response.content.read(n)).decode().strip()
                async def readline():
                    return (await response.content.readline()).decode().strip()

                header = await response.content.read(len(M3U8_MAGIC))
                if header != M3U8_MAGIC:
                    raise FormatError('Not an m3u8 stream')

                await readline() # To consume rest of header line
                line2 = await readline()
                while True:
                    line1 = line2
                    line2 = await readline()
                    if not line1:
                        break
                    try:
                        tag, value = tuple(line1.split(':', maxsplit=1))
                    except ValueError:
                        tag, value = line1, ''
                    if tag == '#EXT-X-STREAM-INF':
                        async for item in self._read_stream_inf(line2):
                            if not_recent(item):
                                yield item
                    elif tag == '#EXT-X-TARGETDURATION':
                        target_duration = min(target_duration, max(int(value), 1))
                    elif tag == '#EXTINF': 
                        inf = self._read_inf(value, line2)
                        target_duration = max(0, min(target_duration, inf.get('duration', target_duration)) - 1)
                        if not_recent(inf):
                            start = time()
                            yield inf
                            end = time()
                            target_duration = max(0, target_duration - (end - start))

                await asyncio.sleep(target_duration)

class _FfTags(BaseModel):
    StreamTitle: str

class _FfFormat(BaseModel):
    tags: _FfTags

class _FfOut(BaseModel):
    format: _FfFormat

class Icy(Stream):

    async def read_song_info(self):
        prev_result = {}
        while True:
            proc = await asyncio.create_subprocess_exec('ffprobe', '-v', 'error', '-show_format', '-of', 'json', self.stream_url, stdout=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            try:
                ff_out = _FfOut(**json.loads(stdout.decode()))
            except pydantic.error_wrappers.ValidationError:
                raise FormatError('Not an icy stream')
            song = ff_out.format.tags.StreamTitle.split(' - ', maxsplit=1)
            result = {}
            if len(song) == 2:
                artist, title = tuple(song)
                result['artist'] = artist
                result['title'] = title
            else:
                result['title'] = song[0]
            if prev_result != result:
                prev_result = result
                yield result
            await asyncio.sleep(120)

class _RadioApiNowPlaying(BaseModel):
    name: str
    artist: str

class _RadioApi(BaseModel):
    nowPlaying: List[_RadioApiNowPlaying]

class RadioApi(Stream):
    """As used by Rova"""

    async def read_song_info(self):
        async with aiohttp.ClientSession() as http:
            prev = {}
            while True:
                async with http.get(self.stream_url) as response:
                    resp_data = await response.json()
                    data = {}
                    try:
                        data = _RadioApi(**resp_data)
                    except pydantic.error_wrappers.ValidationError:
                        raise FormatError('Not a RadioApi stream')
                    nowPlaying = data.nowPlaying[0]
                    data_dict = nowPlaying.dict()
                    if data_dict != prev:
                        prev = data_dict
                        yield {
                            'title': nowPlaying.name,
                            'artist': nowPlaying.artist
                        }
                await asyncio.sleep(120)


async def read_song_info(url):
    for stream_class in [M3u8, Icy, RadioApi]:
        stream: Stream = stream_class(url)
        try:
            async for song_info in stream.read_song_info():
                yield song_info
            return
        except FormatError:
            pass
    raise FormatError(f'No compatible parser found for {url}')
    

if __name__ == "__main__":

    async def main():
        async for item in read_song_info('https://radio-api.mediaworks.nz/radio-api/v3/station/georgefm/auckland/web'):
            print(item)

    asyncio.run(main())
