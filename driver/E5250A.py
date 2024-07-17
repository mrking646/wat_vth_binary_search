from os import stat
import pyvisa as visa
import time
from enum import IntEnum, IntFlag,Enum
import typing
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class E5250A_Simple:
    class InputPort(IntEnum):
        SMU1    = 1
        SMU2    = 2
        SMU3    = 3
        SMU4    = 4
        SMU5    = 5
        SMU6    = 6
        HF1     = 7
        HF2     = 8
        CV1     = 9
        CV2     =10

    def __init__(self, address, flexMode=True):
        self.address = address
        self.com = None

    def connect(self):
        try:
            rm = visa.ResourceManager()
            self.com = rm.open_resource(self.address)
            #self.com.read_termination = '\n'
            self.com.query_delay = 0.0
            self.com.timeout = 5000
        except Exception as e:
            msg = f'Unable to connect to {self.__class__.__name__} at {self.address}, error: {str(e)}'
            raise RuntimeError(msg)
        return self

    def __enter__(self):
        if self.com is None:
            self.connect()
        self.com.write('*RST')      # reset
        self.com.write('*CLS')      # clear registers in case there is any remaining
                                    # data left from the previous session
        return self

    def __exit__(self, type, value, traceback):
        self.com.write('*RST')      # reset
        self.com.close()
        return False

    @contextmanager
    def setupPortMap(self, portMap):
        lst = []
        for iPort,oPorts in portMap.items():
            if isinstance(iPort,self.InputPort):
                iPort = iPort.value
            if not isinstance(oPorts, (list,tuple)):
                oPorts = [oPorts]
            for oPort in oPorts:
                if oPort is None: continue
                card,oPort = divmod(oPort-1,12)
                card  +=1
                oPort +=1
                lst.append(f'{card:1d}{iPort:02d}{oPort:02d}')
        lst = ','.join(lst)
        cmd = f':ROUT:CLOS:LIST (@{lst})'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)
        try:
            print(f"E5250 is {self.com.query('*OPC?')}")
        except Exception as e:
            print(e)

        try:
            yield self
        finally:
            cmd = ':ROUT:OPEN:CARD ALL'
            logger.debug('sending command: ' + cmd)
            self.com.write(cmd)     # disconnect everything
