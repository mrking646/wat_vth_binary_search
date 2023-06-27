import csv
import time
from audioop import bias
from multiprocessing.sharedctypes import Value
import attrs
import enum
from typing import Union, Optional
from functools import wraps
import numpy as np
import nidcpower
import hightime
# import matplotlib.pyplot as plt
import multiprocessing
from itertools import repeat
import pandas as pd
from change_range_softly import runIVSweeps_softwareAutoRange
from threading import Thread


def ivi_synchronized(f):
    @wraps(f)
    def aux(*xs, **kws):
        session = xs[0]  # parameter 0 is 'self' which is the session object
        with session.lock():
            return f(*xs, **kws)
    return aux


@attrs.define
class ChnVoltBias:
    remarks     : str
    resource    : str

    # GND         : bool  = attrs.field(
    #                         default=True,
    #                         kw_only=True,
    # )
    V_force     : float                 # voltage forced by SMU on this channel [V]
    I_compl     : float = attrs.field(  # compliance current allowed on this channel [A]
                            default = 1e-3,
                            kw_only = True,
                            )
    apertureTime: float = attrs.field(
        default=1e-3,
        kw_only=True,
    )
    VoltSense   : bool = attrs.field(
                            default=False,
                            kw_only=True,
    )
    V_compl     : float = attrs.field(
                            default=3,
                            kw_only=True,
    )
    I_force     : float = attrs.field(
                            default=0,
                            kw_only=True,
    )
    source_delay: float = attrs.field(
                            default=20e-3,
                            kw_only=True,
                            
    )
    remote_sense: bool  = attrs.field(
                            default=False,
                            kw_only=True,
    )

    # V_force_stress: float = attrs.field(
    #                          default = 24,
    #                          kw_only = True,
    #
    # )
    # V_force_SILC: float = attrs.field(
    #                           default=5,
    #                           kw_only=True,
    # )
    # I_init       : float = attrs.field(
    #                            default=10-6,
    #                             kw_only=True,
    # )

@attrs.define
class chnGATE:
    resource                      : str
    vFB: float = attrs.field(
        kw_only=True,
        default=0,
    )
    V_force_stress: float = attrs.field(
        kw_only=True,
        default=0,
    )
    I_force_stress: float = attrs.field(
        kw_only=True,
        default=0,
    )
    V_force_SILC: float = attrs.field(
        kw_only=True,
        default=0,
    )
    I_start     : float
    I_stop      : float
    I_step      : float
    V_compl     : float = attrs.field(  # compliance current allowed on this channel [A]
                            default = 24,
                            kw_only = True,
                            )
    # V_start     : float = attrs.field(
    #     kw_only=True,
    # )
    # V_stop      : float = attrs.field(
    #     kw_only=True,
    # )
    # V_step      : float = attrs.field(
    #     kw_only=True,
    # )

    I_compl: float = attrs.field(
        default=1e-3,
        kw_only=True,
    )
    t_wait_before_SILC_measurement: float = attrs.field(
        default=2,
    )
    t_stress_time: float = attrs.field(
        default=50,
    )


@attrs.define
class TDDB:
    dieName                       : str
    chnStress                     : chnGATE
    biases                        : list[ChnVoltBias] = attrs.field(
                                    validator=attrs.validators.deep_iterable(member_validator=attrs.validators.instance_of(ChnVoltBias)),
                                    )

    @biases.validator
    def _checkNumBiases(self, attribute, value):
        if len(value) < 1 or len(value) > 24:
            raise ValueError

    # delay time after source voltage is applied and before measurement starts
    sourceDelay: float = attrs.field(
        default=30e-3,
        kw_only=True,
    )

    # integration time
    apertureTime: float = attrs.field(
        default=100e-3,
        kw_only=True,
    )

    # VFB                           : float = attrs.field(
    #                                 kw_only=True,
    # )
    # V_force_stress                : float
    # V_force_SILC                  : float

    # I_compl                       : float = attrs.field(
    #                                 default=1e-3,
    #                                 kw_only=True,
    # )
    # t_wait_before_SILC_measurement: float=attrs.field(
    #                                 default=2,
    # )
    # t_stress_time                 : float = attrs.field(
    #                                 default=50,
    # )
    I_SILC                        : float = attrs.field(
                                    default=0,
    )
    I_CVS                         : float = attrs.field(
                                    default=0,
    )
    Failed_in_pre                 : bool = attrs.field(
                                    default=False,
    )
    Failed_in_CSV                 : bool = attrs.field(
                                    default=False,
    )
    Failed_in_SILC                : bool = attrs.field(
                                    default=False,
    )
    Failed_in_post                : bool = attrs.field(
                                    default=False,
    )


@attrs.define
class ChnVoltSweep:
    remarks: str
    resource    : str
    V_start     : float
    V_stop      : float
    V_step      : float
    I_compl     : float = attrs.field(  # compliance current allowed on this channel [A]
                            default = 1e-3,
                            kw_only = True,
                            )
    remote_sense: bool = attrs.field(
                            default=False,
                            kw_only=True,
    )

@attrs.define
class ChnCurrentSweep:
    resource    : str
    I_start     : float
    I_stop      : float
    I_step      : float
    V_compl     : float = attrs.field(  # compliance current allowed on this channel [A]
                            default = 5,
                            kw_only = True,
                            )

@attrs.define
class IVSweep:
    # channel on which voltage is swept
    sweep           : ChnVoltSweep
    # sweepCurrent    : ChnCurrentSweep   = attrs.field(
    #                                     default=None,
    #
    # )
    # one or more channels on which constant bias is applied
    biases          : list[ChnVoltBias] = attrs.field(
                                    validator=attrs.validators.deep_iterable(member_validator=attrs.validators.instance_of(ChnVoltBias)),
                                    )
    @biases.validator
    def _checkNumBiases(self, attribute, value):
        if len(value)<1 or len(value)>24:
            raise ValueError

    # delay time after source voltage is applied and before measurement starts
    sourceDelay     : float = attrs.field(
                                    default = 5e-3,
                                    kw_only = True,
                                    )
    isMaster        : bool = attrs.field(
                                    default = False,
                                    kw_only = True,
    )

    measure_complete_event_delay : float = attrs.field(
                                    default = 10e-3,
                                    kw_only = True,
    )

    # integration time
    apertureTime    : float = attrs.field(
                                    default = 20e-3,
                                    kw_only = True,
                                    )
    # # integration time
    # apertureTime    : float = attrs.field(
    #                             default = 100e-3,
    #                             kw_only = True,
    #                             )


@attrs.define
class IVSweep_amp:
    # channel on which voltage is swept
    sweep           : ChnCurrentSweep
    # sweepCurrent    : ChnCurrentSweep   = attrs.field(
    #                                     default=None,
    #
    # )
    # one or more channels on which constant bias is applied
    biases          : list[ChnVoltBias] = attrs.field(
                                    validator=attrs.validators.deep_iterable(member_validator=attrs.validators.instance_of(ChnVoltBias)),
                                    )
    @biases.validator
    def _checkNumBiases(self, attribute, value):
        if len(value)<1 or len(value)>24:
            raise ValueError

    # delay time after source voltage is applied and before measurement starts
    sourceDelay     : float = attrs.field(
                                    default = 30e-3,
                                    kw_only = True,
                                    )

    # integration time
    apertureTime    : float = attrs.field(
                                default = 60e-3,
                                kw_only = True,
                                )

vtlin1 = IVSweep(ChnVoltSweep('G', 'SMU1/1', V_start=-0.5, V_stop=1.5, V_step=0.02, I_compl=1e-3),
                  [ChnVoltBias('D', 'SMU1/6', 0.1, I_compl=1e-3),
                  ChnVoltBias('S', 'SMU1/5', 0, I_compl=1e-3),
                  ChnVoltBias('B', 'SMU1/4', 0, I_compl=1e-3),
                   ],
                  apertureTime=20e-3,
                  sourceDelay=5e-5,
                #   isMaster=1,
                  )

vtlin2 = vtlin = IVSweep(ChnVoltSweep('G', 'SMU1/11', V_start=-0.5, V_stop=1.5, V_step=0.02, I_compl=1e-3),
                  [ChnVoltBias('D', 'SMU1/12', 0.1, I_compl=1e-3),
                  ChnVoltBias('S', 'SMU1/13', 0, I_compl=1e-3),
                  ChnVoltBias('B', 'SMU1/14', 0, I_compl=1e-3),
                   ],
                  apertureTime=20e-3,
                  sourceDelay=5e-5,
                #   isMaster=1,
                  )

# use multithread to run runIVSweeps_softwareAutoRange
task1 = Thread(target=runIVSweeps_softwareAutoRange, args=([vtlin1]), kwargs={'CSV_name': 'vtlin1.csv', 'channel_read': 'SMU1/1'})
task2 = Thread(target=runIVSweeps_softwareAutoRange, args=([vtlin2]), kwargs={'CSV_name': 'vtlin2.csv', 'channel_read': 'SMU1/11'})
task1.start()
task2.start()
task1.join()
task2.join()
