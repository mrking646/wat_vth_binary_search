__all__=['AbstractProber']

from abc import ABC, abstractmethod
import attr as  attrs
from typing import Optional, Union, Tuple

class AbstractProber(ABC):
    def connect(self):
        pass
    def __enter__(self):
        pass
    def __exit__(self, type, value, traceback):
        return False
    @abstractmethod
    def getMachineType(self):
        pass
    @abstractmethod
    def getMachineId(self):
        pass
    def getWaferParams(self):
        return ''
    def getDieCoord(self):
        return (0,0)
    def moveToDie(self, x, y):
        pass
    def setChuckTemp(self, T):
        pass
    def getChuckTemp(self):
        return 25.0
    def getChuckTempSetting(self):
        return 25.0
    def downZ(self):
        pass
    def upZ(self):
        pass
    def driveDistanceX(self, dx):
        pass
    def driveDistanceY(self, dy):
        pass
    def unload(self):
        pass
    def endLot(self):
        pass
    def polish(self):
        pass

@attrs.define(slots=True, eq=True)
class ProberStatus:
    die_coord       : Tuple[int,int]  = (0,0)
    coord           : Tuple[int,int]  = (0,0)
    coord_init      : Tuple[int,int]  = (0,0)
    chuck_temp_set  : Optional[float] = None
    chuck_temp_curr : Optional[float] = None