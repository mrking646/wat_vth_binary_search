__all__ = ['P8XL']

import pyvisa as visa
# import t2.virtualMachine as visa
import time
import typing
import logging
import re
from os import stat
from enum import IntEnum, IntFlag, Enum, auto

from .Base import AbstractProber

logger = logging.getLogger(__name__)


class P8XL(AbstractProber):
    rPair2Dig = re.compile(r'(?P<x>[+-]?\d{2})(?P<y>[+-]?\d{2})')
    rPair3Dig = re.compile(r'(?P<x>[+-]?\d{3})(?P<y>[+-]?\d{3})')
    rPair4Dig = re.compile(r'(?P<x>[+-]?\d{4})(?P<y>[+-]?\d{4})')
    rPair5Dig = re.compile(r'(?P<x>[+-]?\d{5})(?P<y>[+-]?\d{5})')

    MaxSingleDriveDist = 1000

    class FlatDir(IntEnum):
        Top = 0
        Right = 3
        Bottom = 6
        Left = 7

    def __init__(self, address, autoUnload=False):
        self.address = address
        self.com = None
        self.autoUnload = autoUnload

        self.overdrive = None
        self.waferName = None
        self.waferSize = None
        self.flatDir = None
        self.dieHt = None
        self.dieWid = None

    def connect(self):
        try:
            rm = visa.ResourceManager()
            self.com = rm.open_resource(self.address)
            self.com.read_termination = '\r\n'
            self.com.query_delay = 0.0
            self.com.timeout = 5000
        except Exception as e:
            msg = f'Unable to connect to {self.__class__.__name__} at {self.address}, error: {str(e)}'
            raise RuntimeError(msg)
        return self

    def __enter__(self):
        if self.com is None:
            self.connect()
        return self

    def __exit__(self, type, value, traceback):
        if isinstance(value, Exception) and self.autoUnload:
            try:
                logger.warning(
                    f'Unloading wafer because of unhandled exception: {value}')
                cmd = 'U'
                logger.debug('sending command: ' + cmd)
                self.com.write(cmd)  # unload
            except Exception as e:
                logger.warning(
                    f'Encountered another exception while handling one: {e}')
        self.com.close()
        return False

    def getMachineType(self):
        # TODO: get exact machine type
        return 'P12XL'

    def getMachineId(self):
        cmd = 'F'
        logger.debug('sending query: ' + cmd)
        ret = self.com.query(cmd)
        return ret

    def getWaferParams(self):
        cmd = 'G'
        logger.debug('sending query: ' + cmd)
        ret = self.com.query(cmd)

        def head(n=None):
            nonlocal ret
            if n is None:
                h = ret
                ret = ''
            else:
                h = ret[0:n]
                ret = ret[n:]
            return h

        dSizes = {'8': 200, '12': 300}
        self.waferName = head(20).strip()
        self.waferSize = dSizes[head(1)]
        self.flatDir = self.FlatDir(int(head(1)))
        self.dieWid = int(head(5))
        self.dieHt = int(head(5))
        self.overdrive = int(head(3))

        return f'''Wafer Information:
Wafer name      : {self.waferName}
Wafer size (mm) : {self.waferSize} mm
Notch direction : {self.flatDir}
Die width  (um) : {self.dieWid}
Die height (um) : {self.dieHt}
Overdrive       : {self.overdrive}
'''

    def getDieCoord(self):
        ret = self.com.query("A")
        m = self.rPair3Dig.fullmatch(ret)
        assert m is not None, f'Unexpected return value from prober: {ret}'
        i, j = (int(m['x']), int(m['y']))
        if self.flatDir == self.FlatDir.Top: x, y = -i, j
        elif self.flatDir == self.FlatDir.Right: x, y = -j, -i
        elif self.flatDir == self.FlatDir.Bottom: x, y = i, -j
        elif self.flatDir == self.FlatDir.Left: x, y = j, i
        else: raise ValueError('Unknown wafer orientation.')
        return (x, y)

    def moveToDie(self, x, y):
        if self.flatDir == self.FlatDir.Top: i, j = -x, y
        elif self.flatDir == self.FlatDir.Right: i, j = -y, -x
        elif self.flatDir == self.FlatDir.Bottom: i, j = x, -y
        elif self.flatDir == self.FlatDir.Left: i, j = y, x
        else: raise ValueError('Unknown wafer orientation.')

        parts = ['b']
        if i >= 0: parts.append(f'{abs(i):03d}')
        else: parts.append(f'-{abs(i):03d}')
        if j >= 0: parts.append(f'{abs(j):03d}')
        else: parts.append(f'-{abs(j):03d}')
        cmd = ''.join(parts)
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)
        dt, tMax = 0.1, 10.0
        for i in range(int(tMax / dt)):
            stb = self.com.stb
            if stb == 0x07:
                break
            time.sleep(dt)
        else:
            nx, ny = self.getDieCoord()
            if nx == x and ny == y:
                pass  # movement actually done, nothing too serious
            else:
                raise RuntimeError(
                    f'Failed to move to die ({x},{y}), currently at ({nx},{ny}). Last strobe value {str(stb)}'
                )

    def setChuckTemp(self, T):
        parts = ['h']
        if T >= 0: parts.append(f'{abs(T):03d}')
        else: parts.append(f'-{abs(T):03d}')
        cmd = ''.join(parts)
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)
        dt, tMax = 0.1, 10.0
        for i in range(int(tMax / dt)):
            stb = self.com.stb
            if stb == 0x19:
                break
            time.sleep(dt)
        else:
            raise RuntimeError(str(stb))

    def getChuckTemp(self):
        cmd = 'f1'
        logger.debug('sending command: ' + cmd)
        ret = self.com.query(cmd)
        return float(ret)

    def getChuckTempSetting(self):
        cmd = 'f2'
        logger.debug('sending command: ' + cmd)
        ret = self.com.query(cmd)
        return float(ret)

    def downZ(self):
        '''separate in z-axis'''
        cmd = 'D'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

        dt, tMax = 0.1, 10.0
        for i in range(int(tMax / dt)):
            stb = self.com.stb
            if stb == 0x04:
                print(stb)
                break
            time.sleep(dt)
        else:
            raise RuntimeError(str(stb))

    def upZ(self):
        '''drive z-axis to contact-position + overdrive'''
        cmd = 'Z'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

        dt, tMax = 0.1, 10.0
        for i in range(int(tMax / dt)):
            stb = self.com.stb
            if stb == 0x03:
                print(stb)
                break
            time.sleep(dt)
        else:
            raise RuntimeError(str(stb))

    def driveDistanceX(self, dx):
        '''drives X-axis by dx um'''
        if dx <= self.MaxSingleDriveDist:
            dx, n = round(dx), 1
        else:
            n = int(dx / self.MaxSingleDriveDist)
            while n <= 10:
                ddx = round(dx / n)
                if abs(dx - ddx * n) < 1.0:  # distance error is less than 1um
                    dx = ddx
                    break
                n += 1
            else:
                raise RuntimeError(
                    f'Unable to find a movement plan for dx={dx}')

        if self.flatDir == self.FlatDir.Top: cmd = f'I{-dx:+06d}{n:02d}'
        elif self.flatDir == self.FlatDir.Right: cmd = f'J{-dx:+06d}{n:02d}'
        elif self.flatDir == self.FlatDir.Bottom: cmd = f'I{dx:+06d}{n:02d}'
        elif self.flatDir == self.FlatDir.Left: cmd = f'J{dx:+06d}{n:02d}'
        else: raise ValueError('Unknown wafer orientation.')
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

        dt, tMax = 0.1, 10.0
        for i in range(int(tMax / dt)):
            stb = self.com.stb
            #if stb==0x02 or stb==0x0f:
            if stb == 0x01 or stb == 0x0f:
                break
            time.sleep(dt)
        else:
            raise RuntimeError(str(stb))

    def driveDistanceY(self, dy):
        '''drives Y-axis by dy um'''
        if dy <= self.MaxSingleDriveDist:
            dy, n = round(dy), 1
        else:
            n = int(dy / self.MaxSingleDriveDist)
            while n <= 10:
                ddy = round(dy / n)
                if abs(dy - ddy * n) < 1.0:  # distance error is less than 1um
                    dy = ddy
                    break
                n += 1
            else:
                raise RuntimeError(
                    f'Unable to find a movement plan for dy={dy}')

        if self.flatDir == self.FlatDir.Top: cmd = f"J{dy:+06d}{n:02d}"
        elif self.flatDir == self.FlatDir.Right: cmd = f"I{-dy:+06d}{n:02d}"
        elif self.flatDir == self.FlatDir.Bottom: cmd = f'J{-dy:+06d}{n:02d}'
        elif self.flatDir == self.FlatDir.Left: cmd = f'I{dy:+06d}{n:02d}'
        else: raise ValueError('Unknown wafer orientation.')
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

        dt, tMax = 0.1, 10.0
        for i in range(int(tMax / dt)):
            stb = self.com.stb
            #if stb==0x01 or stb==0x0f:
            if stb == 0x02 or stb == 0x0f:
                break
            time.sleep(dt)
        else:
            raise RuntimeError(str(stb))

    def unload(self):
        cmd = 'U'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)
        dt, tMax = 5.0, 120.0
        for i in range(int(tMax / dt)):
            stb = self.com.stb
            print(stb, end=' ', flush=True)
            if stb == 0x20:
                break
            time.sleep(dt)
        print('', flush=True)
        #DEBUG:driver.P8XL:sending command: U
        #25 25 25 25 25 25 25 25 72 78 14 14 14 14 14 14 14 14 14 14 14 14 14 14

    def endLot(self):
        cmd = 'l999'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)
        dt, tMax = 5.0, 120.0
        for i in range(int(tMax / dt)):
            stb = self.com.stb
            print(stb, end=' ', flush=True)
            if stb == 0x20:
                break
            time.sleep(dt)
        print('', flush=True)

    def load(self, wf):
        cmd = f'l1{wf:02d}'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)
        dt, tMax = 5.0, 300.0
        for i in range(int(tMax / dt)):
            stb = self.com.stb
            print(stb, end=' ', flush=True)
            if i > 1 and stb == 0x06:
                break
            time.sleep(5)
        print('', flush=True)

    def polish(self):
        cmd = 'p'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)
        dt, tMax = 5.0, 120.0
        for i in range(int(tMax / dt)):
            stb = self.com.stb
            print(stb, end=' ', flush=True)
            if stb == 0x19:
                break
            time.sleep(dt)
        print('', flush=True)
