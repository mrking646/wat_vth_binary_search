__all__=['P8XL']

from audioop import add
from os import stat
import pyvisa as visa
import time
from enum import IntEnum, IntFlag,Enum, auto
import typing
import logging
import re

from .Base import AbstractProber

logger = logging.getLogger(__name__)

class P8XL(AbstractProber):
    rPair2Dig = re.compile(r'(?P<x>[+-]?\d{2})(?P<y>[+-]?\d{2})')
    rPair3Dig = re.compile(r'(?P<x>[+-]?\d{3})(?P<y>[+-]?\d{3})')
    rPair4Dig = re.compile(r'(?P<x>[+-]?\d{4})(?P<y>[+-]?\d{4})')
    rPair5Dig = re.compile(r'(?P<x>[+-]?\d{5})(?P<y>[+-]?\d{5})')

    MaxSingleDriveDist = 10000
    MAXDISTMULTIPLE = 100

    class FlatDir(IntEnum):
        Top     = 0
        Right   = 3
        Bottom  = 5
        Left    = 7

    class SRQ(IntEnum):
        SRQ0                    = 0x40
        XIndexComplete          = 0x41
        YIndexComplete          = 0x42
        ZUpComplete             = 0x43
        ZDownComplete           = 0x44
        MarkingComplete         = 0x45
        InitialDie              = 0x46
        IndexComplete           = 0x47
        LotEnd                  = 0x48
        TestPrepComplete        = 0x49
        InitialWafer            = 0x4A
        WaferEnd                = 0x4B
        AlignmentError          = 0x4C
        ContinuousFail          = 0x4D
        ProberAssist            = 0x4E
        OutsideProberArea       = 0x4F
        ProberError             = 0x50
        TestPrepNotComplete     = 0x51
        ParamRecvPrepComplete   = 0x52
        ZLimit                  = 0x53
        ProcessComplete         = 0x59
        WaitIntialLoadCmd       = 0x60
        StopStatus              = 0x62
        WaitLoadCmd             = 0x65
        ManualTest              = 0x68
        ParameterError          = 0xFE
        CommandError            = 0xFF

    def __init__(self, address, autoUnload=False):
        self.address = address
        self.com = None
        self.autoUnload = autoUnload

        self.overdrive = None
        self.waferName = None
        self.waferSize = None
        self.flatDir   = None
        self.dieHt  = None
        self.dieWid = None

    def connect(self):
        try:
            rm = visa.ResourceManager()
            self.com = rm.open_resource(self.address)
            print(self.address)
            self.com.read_termination = '\r\n'
            self.com.query_delay = 0.0
            self.com.timeout = 5000
            # self.waitSRQ(self.SRQ.WaitIntialLoadCmd)
        except Exception as e:
            msg = f'Unable to connect to {self.__class__.__name__} at {self.address}, error: {str(e)}'
            raise RuntimeError(msg)
        return self

    def waitSRQ(self, *expected, timeout=None):
        '''When any of the SRQ listed in `expected` is received, return
        all SRQs actually received as a list.
        '''
        SRQThatUnexpectedButDoesNotMatter = set([self.SRQ.OutsideProberArea])
        r, N = 1.3, 50
        dt, t = 0.1, 0
        res = set()
        expected_set = set(expected)
        theQuantum = SRQThatUnexpectedButDoesNotMatter & set(expected)
        #try to remove SRQ from expected
        while expected_set:
            stb = int(self.com.stb)
            print(stb)
            if (stb & self.SRQ.SRQ0): #check if stb is a SRQ
                res.add(self.SRQ(stb))
                expected_set.discard(self.SRQ(stb))
                theQuantum.discard(self.SRQ(stb))
                continue #if it is, continue to check the next SRQ, without this continue, you would never meet the quantum
            time.sleep(dt)
            t += dt  # accumulated waiting time
            if expected_set == theQuantum: # you wait for the quantum but it is not there so...
                break
            if timeout is not None and t > timeout:
                return
        return list(res)

    def __enter__(self):
        if self.com is None:
            self.connect()
            self.getWaferParams()
        return self

    def __exit__(self, type, value, traceback):
        if isinstance(value, Exception) and self.autoUnload:
            try:
                logger.warning(f'Unloading wafer because of unhandled exception: {value}')
                cmd = 'U'
                logger.debug('Sending command: ' + cmd)
                self.com.write(cmd)             # unload
            except Exception as e:
                logger.warning(f'Encountered another exception while handling one: {e}')
        self.com.close()
        return False

    def getMachineType(self):
        # TODO: get exact machine type
        return 'P12XL'

    def getMachineId(self):
        cmd = 'F'
        logger.debug('Sending query: ' + cmd)
        ret = self.com.query(cmd)
        print(ret)
        return ret

    def getWaferParams(self):
        cmd = 'G'
        logger.debug('Sending query: ' + cmd)
        ret = self.com.query(cmd)
        def head(n=None):
            nonlocal ret
            if n is None:
                h = ret
                ret = ''
            else:
                h = ret[0:n]
                ret = ret[n:]
                print(h)
            return h

        dSizes = {'8': 200, 'C': 300}
        self.waferName = head(20).strip()
        self.waferSize = dSizes[head(1)]
        self.flatDir   = self.FlatDir(int(head(1)))
        self.dieWid = int(head(5))
        self.dieHt  = int(head(5))
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
        if   self.flatDir == self.FlatDir.Top:    x, y = -i,  j
        elif self.flatDir == self.FlatDir.Right:  x, y = -j, -i
        elif self.flatDir == self.FlatDir.Bottom: x, y =  i, -j
        elif self.flatDir == self.FlatDir.Left:   x, y =  j,  i
        else: raise ValueError('Unknown wafer orientation.')
        return (x,y)
    
    def moveToDie(self, x, y):
        if   self.flatDir == self.FlatDir.Top:    i, j = -x,  y
        elif self.flatDir == self.FlatDir.Right:  i, j = -y, -x
        elif self.flatDir == self.FlatDir.Bottom: i, j =  x, -y
        elif self.flatDir == self.FlatDir.Left:   i, j =  y,  x
        else: raise ValueError('Unknown wafer orientation.')

        parts = ['b']
        if i>=0: parts.append(f'{abs(i):03d}')
        else:    parts.append(f'-{abs(i):03d}')
        if j>=0: parts.append(f'{abs(j):03d}')
        else:    parts.append(f'-{abs(j):03d}')
        cmd = ''.join(parts)
        logger.debug('Sending command: ' + cmd)
        self.com.write(cmd)
        print("Sending command: ",cmd)

        srq = self.waitSRQ(self.SRQ.IndexComplete, self.SRQ.OutsideProberArea)
        logger.debug(self._formatSRQToStr(srq))
        nx,ny = self.getDieCoord()
        if nx==x and ny==y:
            return # movement actually done
        else:
            raise RuntimeError(f'Failed to move to die ({x},{y}), currently at ({nx},{ny}).')

    def setChuckTemp(self, T):
        parts = ['h']
        if T>=0: parts.append(f'{abs(T):03d}')
        else:    parts.append(f'-{abs(T):03d}')
        cmd = ''.join(parts)
        logger.debug('Sending command: ' + cmd)
        self.com.write(cmd)

        srq = self.waitSRQ(self.SRQ.ProcessComplete)
        logger.debug(self._formatSRQToStr(srq))

    def getChuckTemp(self):
        cmd = 'f1'
        logger.debug('Sending command: ' + cmd)
        ret = self.com.query(cmd)
        return float(ret)

    def getChuckTempSetting(self):
        cmd = 'f2'
        logger.debug('Sending command: ' + cmd)
        ret = self.com.query(cmd)
        return float(ret)
 
    def downZ(self):
        '''separate in z-axis'''
        cmd = 'D'
        logger.debug('Sending command: ' + cmd)
        print('Sending command: ',cmd)
        self.com.write(cmd)

        srq = self.waitSRQ(self.SRQ.ZDownComplete)
        print("srq",srq)
        logger.debug(self._formatSRQToStr(srq))

    def upZ(self):
        '''drive z-axis to contact-position + overdrive'''
        cmd = 'Z'
        logger.debug('Sending command: ' + cmd)
        self.com.write(cmd)

        srq = self.waitSRQ(self.SRQ.ZUpComplete)
        logger.debug(self._formatSRQToStr(srq))

    def driveDistanceX(self, dx):
        '''drives X-axis by dx um'''
        if dx<=self.MaxSingleDriveDist:
            dx, n = round(dx), 1
        else:
            n = int(dx/self.MaxSingleDriveDist)
            print(n)
            while n<=self.MAXDISTMULTIPLE:
                ddx = round(dx/n)
                # print(f"ddx is {ddx}")
                # print(f"distance error is {dx-ddx*n}")
                if abs(dx-ddx*n)<=1.0:   # distance error is less than 1um
                    dx = ddx
                    break
                n += 1
            else:
                raise RuntimeError(f'Unable to find a movement plan for dx={dx}')
        waitType = self.SRQ.XIndexComplete
        if self.flatDir == self.FlatDir.Top:    cmd = f'I{-dx:+06d}{n:02d}'
        elif self.flatDir == self.FlatDir.Right:  
            cmd = f'J{-dx:+06d}{n:02d}'
            waitType = self.SRQ.YIndexComplete
        elif self.flatDir == self.FlatDir.Bottom: cmd = f'I{dx:+06d}{n:02d}'
        elif self.flatDir == self.FlatDir.Left:   
            cmd = f'J{dx:+06d}{n:02d}'
            waitType = self.SRQ.YIndexComplete
        else: raise ValueError('Unknown wafer orientation.')
        logger.debug('Sending command: ' + cmd)
        self.com.write(cmd)
        print("drive x")
        print(dx)
        srq = self.waitSRQ(
                           waitType,
                           self.SRQ.OutsideProberArea,
                           )
        logger.debug(self._formatSRQToStr(srq))

    def driveDistanceY(self, dy):
        '''drives Y-axis by dy um'''
        if dy<=self.MaxSingleDriveDist:
            dy, n = round(dy), 1
        else:
            n = int(dy/self.MaxSingleDriveDist)
            while n<=self.MAXDISTMULTIPLE:
                ddy = round(dy/n)
                if abs(dy-ddy*n)<=1.0:   # distance error is less than 1um
                    dy = ddy
                    break
                n += 1
            else:
                raise RuntimeError(f'Unable to find a movement plan for dy={dy}')
        waitType = self.SRQ.YIndexComplete
        if   self.flatDir == self.FlatDir.Top:    cmd = f"J{dy:+06d}{n:02d}"
        elif self.flatDir == self.FlatDir.Right:  
            cmd = f"I{-dy:+06d}{n:02d}"
            waitType = self.SRQ.XIndexComplete
        elif self.flatDir == self.FlatDir.Bottom: cmd = f'J{-dy:+06d}{n:02d}'
        elif self.flatDir == self.FlatDir.Left:   
            cmd = f'I{dy:+06d}{n:02d}'
            waitType = self.SRQ.XIndexComplete
        else: raise ValueError('Unknown wafer orientation.')
        logger.debug('Sending command: ' + cmd)
        self.com.write(cmd)
        print("drive y")
        print(dy)
        srq = self.waitSRQ(
                           waitType,
                           self.SRQ.OutsideProberArea,
                           )
        logger.debug(self._formatSRQToStr(srq))

    def unload(self):
        cmd = 'U'
        logger.debug('Sending command: ' + cmd)
        self.com.write(cmd)

        srq = self.waitSRQ(self.SRQ.WaitIntialLoadCmd,
                           )
        logger.debug(self._formatSRQToStr(srq))

    def endLot(self):
        cmd = 'l999'
        logger.debug('Sending command: ' + cmd)
        self.com.write(cmd)

        srq = self.waitSRQ(self.SRQ.LotEnd)
        logger.debug(self._formatSRQToStr(srq))

    def load(self, wf):
        cmd = f'l1{wf:02d}'
        logger.debug('Sending command: ' + cmd)
        self.com.write(cmd)

        srq = self.waitSRQ(
                           self.SRQ.InitialDie,
                           )
        logger.debug(self._formatSRQToStr(srq))

    def polish(self):
        cmd = 'p'
        logger.debug('Sending command: ' + cmd)
        self.com.write(cmd)

        srq = self.waitSRQ(self.SRQ.ProcessComplete)
        logger.debug(self._formatSRQToStr(srq))
    
    def _formatSRQToStr(self,srq):
        rText=[]
        if type(srq)==list or type(srq)==set:
            for index,srqItem in enumerate(srq):
                if index==0:
                    rText.append(f'Received SRQ 0x{srqItem.value:02x} ({srqItem.name}).')
                else:
                    rText.append(f'               {srqItem.value:02x} ({srqItem.name}).')
        else:
            f'Received SRQ 0x{srq.value:02x} ({srq.name}).'
        return "\n".join(rText)
