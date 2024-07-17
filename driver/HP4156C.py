from os import stat
import pyvisa as visa
import time
from enum import IntEnum, IntFlag,Enum
import typing
import logging

logger = logging.getLogger(__name__)

class HP4156C:
    class EventStatus(IntFlag):
        '''ESE/ESR'''
        OperationComplete   = 1
        Error               = 8
        ParameterError      = 16
        SyntaxError         = 32
    class StatusBus(IntFlag):
        '''STB'''
        Emergency           = 1
        MeasurementStress   = 2
        Questionable        = 8
        MessageAvailable    = 16 # MAV
        Event               = 32 # ESB
        RequestService      = 64 # RSQ
    class OutputFormat(IntEnum):
        AsciiWithHeader     = 1
        AsciiNoHeader       = 2
        BinaryWithHeader    = 3
        BinaryNoHeader      = 4
        AsciiWithHeaderComma= 5
    class OutputMode(IntEnum):
        NoSweep         = 0
        PrimarySweep    = 1
        SecondarySweep  = 2
    class IntegrationTime(IntEnum):
        Short       = 1
        Medium      = 2
        Long        = 3
    class Unit(IntEnum):
        SMU1        = 1
        SMU2        = 2
        SMU3        = 3
        SMU4        = 4
        SMU5        = 5  # only if with 41501A/B MPSMU
        SMU6        = 6  # only if with 41501A/B MPSMU, or if with HPSMU
        VSU1        = 21
        VSU2        = 22
        VMU1        = 23
        VMU2        = 24
        GNDU        = 26
        PGU1        = 27
        PGU2        = 28
    class VoltageRange(IntEnum):
        #                      SMU     HPSMU   VSU     VMU     PGU
        Auto        =  0    #
        Limited0p2V = 10    #   X                       X
        Limited2V   = 11    #   X       X
        Limited20V  = 12    #   X       X       X       X       X
        Limited40V  = 13    #   X       X                       X
        Limited100V = 14    #   X       X
        Limited200V = 15    #           X
        FixedMax    = -0    #   X       X
        Fixed0p2V   =-10    #   X       X               X
        Fixed2V     =-11    #   X       X
        Fixed20V    =-12    #   X       X       X       X       X
        Fixed40V    =-13    #   X       X                       X
        Fixed100V   =-14    #   X       X
        Fixed200V   =-15    #           X
    class CurrentRange(IntEnum):
        Auto            =   0
        Limited10pA     =   9   # 4156-only
        Limited100pA    =  10   # 4156-only
        Limited1nA      =  11
        Limited10nA     =  12
        Limited100nA    =  13
        Limited1uA      =  14
        Limited10uA     =  15
        Limited100uA    =  16
        Limited1mA      =  17
        Limited10mA     =  18
        Limited100mA    =  19
        Limited1A       =  20   # HPSMU-only
        Fixed10pA       =  -9   # 4156-only
        Fixed100pA      = -10   # 4156-only
        Fixed1nA        = -11
        Fixed10nA       = -12
        Fixed100nA      = -13
        Fixed1uA        = -14
        Fixed10uA       = -15
        Fixed100uA      = -16
        Fixed1mA        = -17
        Fixed10mA       = -18
        Fixed100mA      = -19
        Fixed1A         = -20   # HPSMU-only
    class MeasureMode(IntEnum):
        Spot                =  1
        StaircaseSweep      =  2
        OneChPulsedSpot     =  3
        PulsedSpot          =  4
        StaircaseSweepPulsed=  5
        Sampling            = 10
        Stress              = 11
        QuasiStaticCV       = 13
        LinearSearch        = 14
        BinarySearch        = 15
    class AbortCondition(IntFlag):
        Disabled            =  1
        All                 =  2
        ComplianceOnBias    =  4
        ComplianceOnMeas    =  8
        OverflowedADC       = 16
        Oscillation         = 32
    class PostCondition(IntEnum):
        StartValue  = 1
        StopValue   = 2
    class ResultStatus(IntFlag):
        OverflowedADC       =   1
        Oscillation         =   2
        ComplianceOtherUnit =   4
        ComplianceThisUnit  =   8
        IntegTimeTooShort   =   8 # capacitance measurement
        CompliancePGU       =  16
        Stopped             =  32
        InvalidData         =  64
        EndOfData           = 128
        Other               = 256
    class ResultDataType(Enum):
        VoltageMeasured     = 'V'
        VoltageForced       = 'v'
        CurrentMeasured     = 'I'
        CurrentForced       = 'i'
        CapacitanceMeasured = 'C'
        SamplingPointIndex  = 'p'
        Time                = 'T'
        Status              = 'S'
        Invalid             = 'Z'
        Invalid1            = 'z'

    class SMUMode(IntEnum):
        ComplianceSide      = 0 # compliance-side measurement, i.e.,
                                # measure current if forcing a voltage, or
                                # measure voltage if forcing a current.
        MeasureCurrent      = 1 # measure current
        MeasureVoltage      = 2 # measure voltage
        ForceSide           = 3 # force-side measurement, i.e.,
                                # measure voltage if forcing a voltage, or
                                # measure current if forcing a current.
        Default             = 0
    class SweepMode(IntEnum):
        SingleLinearSweep   = 1
        SingleLogSweep      = 2
        DoubleLinearSweep   = 3
        DoubleLogSweep      = 4
    class SweepRangeMode(IntEnum):
        Fixed   = 0
        Auto    = 1
    class MeasureRangeMode(IntEnum):
        Auto        = 0
        LimitedAuto = 1
        Fixed       = 2
        Compliance  = 3

    def __init__(self, address, flexMode=True, is4156=True):
        self.address = address
        self.com = None
        self.flexMode = flexMode
        self._outputFormat = None
        self._outputMode   = None

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
        if self.flexMode:
            self.com.write('US')
        return self

    def __exit__(self, type, value, traceback):
        if isinstance(value, Exception):
            try:
                logger.warning(f'Reset instrument due to unhandled exception: {value}')
                self.reset()
            except Exception as e:
                logger.warning(f'Encountered another exception while handling one: {e}')
        else:
            self.com.write('CL')
            if self.flexMode:
                self.com.write(':PAGE')
        self.com.close()
        return False

    def reset(self):
        for _ in range(3):
            self.com.write('AB')
            self.com.write('*RST')
            time.sleep(5)
            if bool(self.com.query('*OPC?')):
                logger.info(f'Reset complete, device ready.')
                break
        else:
            raise RuntimeError('Reset failed')

    def enableUnit(self, *channels):
        ''' CN command in Flex mode
        '''
        assert self.com is not None
        assert self.flexMode
        lst = []
        for c in channels:
            assert isinstance(c, self.Unit)
            lst.append(str(c.value))
        cmd = 'CN ' + ','.join(lst)
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def disableUnit(self, *channels):
        assert self.com is not None
        assert self.flexMode
        lst = []
        for c in channels:
            assert isinstance(c, self.Unit)
            lst.append(str(c.value))
        cmd = 'CL ' + ','.join(lst)
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def outputFormat(self,
            fmt  : OutputFormat,
            mode : typing.Optional[OutputMode] = None,
            ):
        assert self.com is not None
        assert self.flexMode
        self._outputFormat = fmt
        self._outputMode   = mode
        cmd = f'FMT {fmt.value:d}'
        if mode is not None:
            cmd += f',{mode.value:d}'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def setAverage(self, num : int):
        assert self.com is not None
        assert self.flexMode
        cmd = f'AV {num}'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def setIntegrationTime(self,
            type : IntegrationTime,
            time : float,
            ):
        assert self.com is not None
        assert self.flexMode
        if type==self.IntegrationTime.Short:
            assert time>=80e-6 and time<=10.16e-3
        elif type==self.IntegrationTime.Long:
            assert time>=16.7e-3 and time<=2
        else:
            raise ValueError
        cmd = f'SIT {type.value:d},{time:.4g}'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def selectIntegrationTime(self,
            type : IntegrationTime,
            ):
        assert self.com is not None
        assert self.flexMode
        cmd = f'SLI {type.value:d}'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def setFilter(self, mode : bool, *channels):
        assert self.com is not None
        assert self.flexMode
        lst = [str(int(mode))]
        for c in channels:
            assert isinstance(c, self.Unit)
            assert c >= self.Unit.SMU1 and c <= self.Unit.SMU4
            lst.append(str(c.value))
        cmd = 'FL ' + ','.join(lst)
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def forceVoltage(self,
                channel         : Unit,
                range           : VoltageRange,
                voltage         : float,
                Icomp           : typing.Optional[float] = None,
                compPolarity    : typing.Optional[bool]  = False,
                ):
        assert self.com is not None
        assert self.flexMode
        cmd = f'DV {channel.value:d},{range.value:d},{voltage:.4g}'
        if channel>=self.Unit.SMU1 and channel<=self.Unit.SMU6:
            if Icomp is not None:
                cmd += f',{Icomp:.4g}'
                if compPolarity:
                    cmd += ',1'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def forceCurrent(self,
                channel         : Unit,
                range           : CurrentRange,
                current         : float,
                Vcomp           : typing.Optional[float] = None,
                compPolarity    : typing.Optional[bool]  = False,
                ):
        assert self.com is not None
        assert self.flexMode
        assert channel>=self.Unit.SMU1 and channel<=self.Unit.SMU6
        cmd = f'DI {channel.value:d},{range.value:d},{current:.4g}'
        if Vcomp is not None:
            cmd += f',{Vcomp:.4g}'
            if compPolarity:
                cmd += ',1'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)
    
    def selectMeasurementMode(self,
                mode    : MeasureMode,
                *channels,
                ):
        assert self.com is not None
        assert self.flexMode
        lst = [str(mode.value)]
        for c in channels:
            # print({c: c.value})
            # print(c >= self.Unit.SMU1 and c <= self.Unit.SMU6 or c == self.Unit.VMU1 or c == self.Unit.VMU2)

            assert isinstance(c, self.Unit)

            assert c >= self.Unit.SMU1 and c <= self.Unit.SMU6 or c == self.Unit.VMU1 or c == self.Unit.VMU2
            lst.append(str(c.value))
        cmd = 'MM ' + ','.join(lst)
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def selectSMUMode(self,
                channel :  Unit,
                mode    :  SMUMode,
                ):
        assert self.com is not None
        assert self.flexMode
        cmd = f'CMM {channel.value:d},{mode:d}'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def selectAbortCondition(self,
                abort   : AbortCondition,
                post    : typing.Optional[PostCondition] = None
                ):
        assert self.com is not None
        assert self.flexMode
        cmd = f'WM {abort.value:d}'
        if post is not None:
            cmd += f',{post.value:d}'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def sweepVoltageStaircase(self,
                channel : Unit,
                mode    : SweepMode,
                range   : VoltageRange,
                start   : float,
                stop    : float,
                step    : int,
                Icomp   : typing.Optional[float] = None,
                Pcomp   : typing.Optional[float] = None,
                Rmode   : typing.Optional[SweepRangeMode] = None,
                ):
        assert self.com is not None
        assert self.flexMode
        cmd = f'WV {channel.value:d},{mode.value:d},{range.value:d},{start:.4g},{stop:.4g},{step:.4g}'
        if channel >= self.Unit.SMU1 and channel <= self.Unit.SMU6:
            if Icomp is not None:
                cmd += f',{Icomp:.4g}'
                if Pcomp is not None:
                    cmd += f',{Pcomp:.4g}'
                    if Rmode is not None:
                        cmd += f',{Rmode.value:d}'
        elif channel == self.Unit.VSU1 and channel == self.Unit.VSU2:
            pass
        else:
            raise ValueError
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def sweepVoltageStaircaseSync(self,
                channel : Unit,
                range   : VoltageRange,
                start   : float,
                stop    : float,
                Icomp   : typing.Optional[float] = None,
                Pcomp   : typing.Optional[float] = None,
                Rmode   : typing.Optional[SweepRangeMode] = None,
                ):
        assert self.com is not None
        assert self.flexMode
        cmd = f'WSV {channel.value:d},{range.value:d},{start:.4g},{stop:.4g}'
        if channel >= self.Unit.SMU1 and channel <= self.Unit.SMU6:
            if Icomp is not None:
                cmd += f',{Icomp:.4g}'
                if Pcomp is not None:
                    cmd += f',{Pcomp:.4g}'
                    if Rmode is not None:
                        cmd += f',{Rmode.value:d}'
        elif channel == self.Unit.VSU1 and channel == self.Unit.VSU2:
            pass
        else:
            raise ValueError
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def sweepCurrentStaircase(self,
                channel : Unit,
                mode    : SweepMode,
                range   : CurrentRange,
                start   : float,
                stop    : float,
                step    : int,
                Vcomp   : typing.Optional[float] = None,
                Pcomp   : typing.Optional[float] = None,
                Rmode   : typing.Optional[SweepRangeMode] = None,
                ):
        assert self.com is not None
        assert self.flexMode
        cmd = f'WI {channel.value:d},{mode.value:d},{range.value:d},{start:.4g},{stop:.4g},{step:.4g}'
        if channel >= self.Unit.SMU1 and channel <= self.Unit.SMU6:
            if Vcomp is not None:
                cmd += f',{Vcomp:.4g}'
                if Pcomp is not None:
                    cmd += f',{Pcomp:.4g}'
                    if Rmode is not None:
                        cmd += f',{Rmode.value:d}'
        else:
            raise ValueError(f'Channel {channel} is not supported for current sweep.')
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def sweepCurrentStaircaseSync(self,
                channel : Unit,
                range   : CurrentRange,
                start   : float,
                stop    : float,
                Vcomp   : typing.Optional[float] = None,
                Pcomp   : typing.Optional[float] = None,
                Rmode   : typing.Optional[SweepRangeMode] = None,
                ):
        assert self.com is not None
        assert self.flexMode
        cmd = f'WSI {channel.value:d},{range.value:d},{start:.4g},{stop:.4g}'
        if channel >= self.Unit.SMU1 and channel <= self.Unit.SMU6:
            if Vcomp is not None:
                cmd += f',{Vcomp:.4g}'
                if Pcomp is not None:
                    cmd += f',{Pcomp:.4g}'
                    if Rmode is not None:
                        cmd += f',{Rmode.value:d}'
        else:
            raise ValueError(f'Channel {channel} is not supported for current sweep.')
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)


    def setCurrentRanging(self,
                channel : Unit,
                range   : CurrentRange,
                Rmode   : typing.Optional[MeasureRangeMode] = None,
                ):
        assert self.com is not None
        assert self.flexMode
        cmd = f'RI {channel.value:d},{range.value:d}'
        if Rmode is not None:
            cmd += f',{Rmode.value:d}'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def setVoltageRanging(self,
                channel : Unit,
                range   : VoltageRange,
                Rmode   : typing.Optional[MeasureRangeMode] = None,
                ):
        assert self.com is not None
        assert self.flexMode
        cmd = f'RV {channel.value:d},{range.value:d}'
        if Rmode is not None:
            cmd += f',{Rmode.value:d}'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def setSweepTiming(self,
                hold        : float,
                delay       : float,
                stepDelay   : typing.Optional[float] = None
                ):
        assert self.com is not None
        assert self.flexMode
        cmd = f'WT {hold:.5g},{delay:.5g}'
        if stepDelay is not None:
            cmd += f',{stepDelay:.5g}'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

    def measureCurrentHighSpeedSpot(self,
                channel : Unit,
                range   : typing.Optional[CurrentRange] = None,
                ):
        assert self.com is not None
        assert self.flexMode
        cmd = f'TI? {channel.value:d}'
        if range is not None:
            cmd += f',{range.value:d}'
        logger.debug('sending command: ' + cmd)
        ret = self.com.query(cmd)
        return self.parseData(ret)

    def operationComplete(self):
        assert self.com is not None
        ret = self.com.query('*OPC?')
        return bool(int(ret))

    def errorMessage(self):
        assert self.com is not None
        code,msg = self.com.query(':SYST:ERR?').split(',')
        return int(code),msg

    def execute(self, wait=True):
        assert self.com is not None
        assert self.flexMode

        # only wait for OPC event
        evt = self.EventStatus.OperationComplete | self.EventStatus.Error | self.EventStatus.ParameterError | self.EventStatus.SyntaxError
        cmd = f'*ESE {evt.value:d}'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

        # clear registers in case there is any remaining
        # data left from the previous session
        cmd = '*CLS'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)

        # execute
        cmd = '*OPC;XE'
        logger.debug('sending command: ' + cmd)
        self.com.write(cmd)
        tdelay,tdacc = 0.1,0
        for i in range(20):
            time.sleep(tdelay)
            if self.com.stb & self.StatusBus.Event:
                break
            if i>5:
                logger.debug(f'have waited for {tdacc} seconds..., stb=0x{self.com.stb:x}')
            tdacc += tdelay
            tdelay *= 1.5

        cmd = '*ESR?'
        logger.debug('sending command: ' + cmd)
        ret = int(self.com.query(cmd))
        logger.debug(f'got return: 0x{ret:x}')
        ret &= ~self.EventStatus.OperationComplete
        return ret

    def numberOfData(self):
        assert self.com is not None
        assert self.flexMode
        return int(self.com.query('NUB?'))

    def readMeasuredData(self, num=None):
        assert self.com is not None
        assert self.flexMode
        if num is None:
            cmd = f'RMD?'
        else:
            cmd = f'RMD? {num:d}'
        logger.debug('sending command: ' + cmd)
        ret = self.com.query(cmd)
        return self.parseData(ret)

    def identNumber(self):
        assert self.com is not None
        return self.com.query('*IDN?')

    def parseData(self, s):
        retData, retStatus = {}, {}
        chnCode = {
            'A' : self.Unit.SMU1,
            'B' : self.Unit.SMU2,
            'C' : self.Unit.SMU3,
            'D' : self.Unit.SMU4,
            'E' : self.Unit.SMU5,
            'F' : self.Unit.SMU6,
            'Q' : self.Unit.VSU1,
            'R' : self.Unit.VSU2,
            'S' : self.Unit.VMU1,
            'T' : self.Unit.VMU2,
            'V' : self.Unit.GNDU,
            'W' : self.Unit.PGU1,
            'X' : self.Unit.PGU2,
            'Z' : None,
        }
        if self._outputFormat==self.OutputFormat.AsciiWithHeader:
            for data in s.split(','):
                data = data.rstrip()
                if not len(data)==18:
                    raise ValueError
                status = data[:3]
                chn    = data[3]
                dtype  = data[4]
                val    = data[5:18]

                if status=='  W' or status=='  E':
                    # sweep step
                    status = self.ResultStatus(0)
                else:
                    # measurement result
                    status = self.ResultStatus(int(status)) & (~self.ResultStatus.EndOfData)
                dtype  = self.ResultDataType(dtype)
                chn    = chnCode[chn]
                val    = float(val)

                key = (chn,dtype)
                if not key in retData:
                    retData[key]   = []
                    retStatus[key] = []
                retData[key].append(val)
                retStatus[key].append(status)
        elif self._outputFormat==self.OutputFormat.AsciiNoHeader:
            raise ValueError
        else:
            raise ValueError

        return retData,retStatus