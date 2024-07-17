from audioop import bias
from multiprocessing.sharedctypes import Value
import attrs
import enum
from typing import Union, Optional

import numpy as np
import nidcpower
import hightime

class SMUType(enum.Enum):
    HP_415x     = 1
    NI_PXIe41xx = 2

@attrs.define
class ChnVoltBias:
    resource    : str
    V_force     : float                 # voltage forced by SMU on this channel [V]
    I_compl     : float = attrs.field(  # compliance current allowed on this channel [A]
                            default = 0.1,
                            kw_only = True,
                            )

@attrs.define
class ChnVoltSweep:
    resource    : str
    V_start     : float
    V_stop      : float
    V_step      : float
    I_compl     : float = attrs.field(  # compliance current allowed on this channel [A]
                            default = 0.1,
                            kw_only = True,
                            )

@attrs.define
class IVSweep:
    # channel on which voltage is swept
    sweep           : ChnVoltSweep

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
                                    default = 1e-3,
                                    kw_only = True,
                                    )

    # integration time
    apertureTime    : float = attrs.field(
                                default = 100e-6,
                                kw_only = True,
                                )


def runIVSweeps(*lstIVSweep : IVSweep):
    resources : dict[tuple[str,int],IVSweep]= {}

    def chnKey(chn):
        key = chn.split('/')
        if len(key)==1:
            key.append(0)
        return tuple(key)

    for ivSweep in lstIVSweep:
        key = chnKey(ivSweep.sweep.resource)
        if key in resources:
            raise ValueError(f'SMU {ivSweep.sweep.resource} used more than once')
        resources[key] = ivSweep.sweep.resource
        for bias in ivSweep.biases:
            key = chnKey(bias.resource)
            if key in resources:
                raise ValueError(f'SMU {bias.resource} used more than once')
            resources[key] = bias.resource
    resources = [resources[key] for key in sorted(resources)]   # sorted channel names 

    session = nidcpower.Session(resource_name=resources)

    session.power_line_frequency = 50
    session.aperture_time_units = nidcpower.ApertureTimeUnits.SECONDS
    session.samples_to_average = 1
    session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE

    session.source_mode = nidcpower.SourceMode.SEQUENCE
    session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
    session.voltage_level_autorange = True
    session.voltage_level = 0.0
    session.output_connected = True
    session.output_enabled = True

    for ivSweep in lstIVSweep:
        chnSweep = session.channels[ivSweep.sweep.resource]
        chnSweep.aperture_time = ivSweep.apertureTime
        chnSweep.current_limit_range = ivSweep.sweep.I_compl
        chnSweep.current_limit       = ivSweep.sweep.I_compl

        V_start, V_stop, V_step = ivSweep.sweep.V_start, ivSweep.sweep.V_stop, ivSweep.sweep.V_step
        numStep = round((V_stop+V_step/2 - V_start)/V_step)+1
        tSteps = np.ones(numStep+1)
        vSteps = np.zeros(numStep+1)

        vSteps[:-1] = range(numStep)
        vSteps *= V_step
        tSteps *= ivSweep.sourceDelay
        chnSweep.set_sequence(vSteps, tSteps)

        for bias in ivSweep.biases:
            chnBias = session.channels[bias.resource]
            chnBias.aperture_time = ivSweep.apertureTime
            chnBias.current_limit_range = bias.I_compl
            chnBias.current_limit       = bias.I_compl

            vSteps = np.zeros(numStep+1)
            vSteps[:-1] = bias.V_force
            chnBias.set_sequence(vSteps, tSteps)

    timeout = hightime.timedelta(seconds=10)

    with session.initiate():
        session.wait_for_event(nidcpower.Event.SEQUENCE_ENGINE_DONE)

        for ivSweep in lstIVSweep:
            chnSweep = session.channels[ivSweep.sweep.resource]
            num  = chnSweep.fetch_backlog
            meas = chnSweep.fetch_multiple(num, timeout=timeout)[:-1]
            print(ivSweep.sweep.resource, meas)

            for bias in ivSweep.biases:
                chnBias = session.channels[bias.resource]
                num  = chnBias.fetch_backlog
                meas = chnBias.fetch_multiple(num, timeout=timeout)[:-1]
                print(bias.resource, meas)

def _test():
    with nidcpower.Session(resource_name='SMU1', reset=True) as session:
        print('xxxx', session.instrument_model)
        print('xxxx', session.channel_count)
        print('xxxx', session.current_limit_range)
        #session.output_connected = False
        #session.output_enabled = False

    import datetime

    iv1 = IVSweep(ChnVoltSweep('SMU1/0', V_start=0.0, V_stop=1.0, V_step=0.1, I_compl=30e-3),
                  [ChnVoltBias ('SMU1/1', 0.0, I_compl=30e-3)],
                  apertureTime=100e-6,
                  sourceDelay=1e-3,
                  )
    iv2 = IVSweep(ChnVoltSweep('SMU1/2', V_start=0.0, V_stop=1.0, V_step=0.05, I_compl=30e-3),
                  [ChnVoltBias ('SMU1/3', 0.0, I_compl=30e-3)],
                  apertureTime=100e-6,
                  sourceDelay=1e-3,
                  )
    iv3 = IVSweep(ChnVoltSweep('SMU1/6', V_start=0.0, V_stop=-1.0, V_step=-0.1, I_compl=1e-6),
                  [ChnVoltBias ('SMU1/7', 0.0, I_compl=1e-6)],
                  apertureTime=100e-6,
                  sourceDelay=1e-3,
                  )
    iv4 = IVSweep(ChnVoltSweep('SMU1/9', V_start=0.0, V_stop=1.0, V_step=0.1, I_compl=1e-6),
                  [ChnVoltBias ('SMU1/8', 0.0, I_compl=1e-6)],
                  apertureTime=100e-6,
                  sourceDelay=1e-3,
                  )

    t0 = datetime.datetime.now()
    runIVSweeps(iv1, iv2,iv3,iv4)
    #runIVSweeps(iv4,iv3)
    t1 = datetime.datetime.now()
    print(f'elapased time {(t1-t0).total_seconds()*1000}ms.')

if __name__=='__main__':
    _test()


