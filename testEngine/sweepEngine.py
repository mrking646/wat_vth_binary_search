import csv
# from dataclasses import KW_ONLY
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
import contextlib
from funcs.tools import check_compliance

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
def fetch_multiple(self, chn, count, timeout=hightime.timedelta(seconds=1.0)):
    import collections
    Measurement = collections.namedtuple('Measurement', ['chn', 'voltage', 'current', 'in_compliance'])
    voltage_measurements, current_measurements, in_compliance = self._fetch_multiple(timeout, count)
    return [Measurement(chn=chn, voltage=voltage_measurements[i], current=current_measurements[i],
                        in_compliance=in_compliance[i]) for i in range(count)]


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


def emit(lstMeas, filename):
    with open(filename, "a", newline='') as csv_obj:
        writer = csv.writer(csv_obj)
        writer.writerow(lstMeas)







def runIVSweeps_softwareAutoRange(*lstIVSweep : IVSweep, CSV_name, channel_read):

    # beat(1)

    current_ranges = tuple([10e-6, 100e-6, 1e-3, 10e-3, 50e-3])
    
    resources: dict[tuple[str, int], IVSweep] = {}

    def takeSecond(elem):
        return int(elem[1])

    def chnKey(chn):
        key = chn.split('/')
        if len(key) == 1:
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
    sorted_resources = sorted(resources)
    sorted_resources.sort(key=takeSecond)
    resources = [resources[key] for key in sorted_resources] # sorted channel names
    print("resources", resources)
    session = nidcpower.Session(resource_name=resources, reset=True,  options = {'simulate': True, 'driver_setup': {'Model': '4163', 'BoardType': 'PXIe', }, })

    session.power_line_frequency = 50
    session.aperture_time_units = nidcpower.ApertureTimeUnits.SECONDS
    session.samples_to_average = 1
    session.measure_when = nidcpower.MeasureWhen.ON_DEMAND
    session.source_mode = nidcpower.SourceMode.SINGLE_POINT
    session.sense = nidcpower.Sense.LOCAL
    session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
    session.voltage_level_autorange = True
    # session.voltage_level_range = 6
    session.voltage_level = 0.0
    session.output_connected = True
    session.output_enabled = True
    session.current_limit_autorange = True
    aperture_time = 5e-3
    vSteps_dict = {}
    numOfSteps = 0
    for ivSweep in lstIVSweep:

        chnSweep = session.channels[ivSweep.sweep.resource]
        if ivSweep.sweep.remote_sense == True:
            chnSweep.sense = nidcpower.Sense.REMOTE
        chnSweep.aperture_time = ivSweep.apertureTime
        # chnSweep.current_limit_range = ivSweep.sweep.I_compl
        # chnSweep.source_trigger_type = nidcpower.TriggerType.SOFTWARE_EDGE  # software trigger
        chnSweep.current_limit       = current_ranges[0] # 10uA range default
        chnSweep.current_limit_range = current_ranges[0] # 10uA range default
        chnSweep.measure_complete_event_delay = 5e-3
        V_start, V_stop, V_step = ivSweep.sweep.V_start, ivSweep.sweep.V_stop, ivSweep.sweep.V_step
        numStep = round(abs((V_stop-V_start)/V_step))+1
        # print(numStep)
        
        # vSteps = np.zeros(numStep+1)
        vSteps = np.linspace(V_start, V_stop, numStep, endpoint=True)
        vSteps = np.append(vSteps, 0)
        vSteps_dict[ivSweep.sweep.resource] = vSteps
        numOfSteps  = len(vSteps)
        chnSweep.source_delay = ivSweep.sourceDelay
  
        for bias in ivSweep.biases:
            if bias.VoltSense:
                chnBias = session.channels[bias.resource]
                chnBias.output_function = nidcpower.OutputFunction.DC_CURRENT
                chnBias.current_level_autorange = True
                chnBias.voltage_limit_range = bias.V_compl
                chnBias.measure_when = nidcpower.MeasureWhen.ON_DEMAND
                # chnBias.source_trigger_type = nidcpower.TriggerType.SOFTWARE_EDGE
                # chnBias.measure_trigger_type = nidcpower.TriggerType.SOFTWARE_EDGE
                chnBias.aperture_time = bias.apertureTime
                chnBias.voltage_limit       = bias.V_compl
                chnBias.source_delay = bias.source_delay
                chnBias.current_level = bias.I_force
                # vSteps = np.zeros(numStep + 1)
                # vSteps[:-1] = bias.I_force
                # chnBias.set_sequence(vSteps, tSteps)
            else:
                chnBias = session.channels[bias.resource]
                if bias.remote_sense == True:
                    chnBias.sense = nidcpower.Sense.REMOTE
                chnBias.aperture_time = ivSweep.apertureTime
                chnBias.source_delay = bias.source_delay


                chnBias.current_limit       = current_ranges[0]
                chnBias.voltage_level = bias.V_force
                chnBias.measure_when = nidcpower.MeasureWhen.ON_DEMAND
                # chnBias.source_trigger_type = nidcpower.TriggerType.SOFTWARE_EDGE
                # chnBias.measure_trigger_type = nidcpower.TriggerType.SOFTWARE_EDGE
                chnBias.current_limit_range = current_ranges[0]
                vSteps = np.zeros(numStep+1)
                vSteps[:-1] = bias.V_force
                vSteps_dict[bias.resource] = vSteps

    timeout = hightime.timedelta(seconds=1000)

    df_meas_list = []
    # for ivsweep in lstIVSweep:
    #     for bias in ivsweep.biases:
    #         chnBias = session.channels[bias.resource]

    #         chnBias.initiate() # slave initiate
    #     chnSweep = session.channels[ivSweep.sweep.resource]
    #     chnSweep.initiate() # master initiate
    with session.initiate():
        # session.wait_for_event(nidcpower.Event.SOURCE_COMPLETE, timeout=timeout)
    # dump vSteps
        for i in range(numOfSteps):
            for ivsweep in lstIVSweep:
                chnSweep = session.channels[ivsweep.sweep.resource]
                # chnSweep.send_software_edge_trigger(nidcpower.SendSoftwareEdgeTriggerType.SOURCE)
                chnSweep.voltage_level = vSteps_dict[ivsweep.sweep.resource][i] # set voltage level for sweep chn
                for bias in ivsweep.biases:
                    chnBias = session.channels[bias.resource]
                    chnBias.voltage_level = vSteps_dict[bias.resource][i] # set voltage level for bias chn
                    # chnBias.send_software_edge_trigger(nidcpower.SendSoftwareEdgeTriggerType.SOURCE) # send source trigger to bias chn

            # chnSweep.send_software_edge_trigger(nidcpower.SendSoftwareEdgeTriggerType.SOURCE) # send source trigger to sweep chn
            session.wait_for_event(nidcpower.Event.SOURCE_COMPLETE, timeout=timeout)
            check_compliance(session)

            
            

            
            measurements = session.channels[channel_read].measure_multiple()[0]
            df_meas_list.append(measurements.current)
            
    # print(session.get_channel_names("0:10"))
    session.close()


def runIVsweep_fixRange(*lstIVSweep : IVSweep):
    resources: dict[tuple[str, int], IVSweep] = {}

    def takeSecond(elem):
        return int(elem[1])

    def chnKey(chn):
        key = chn.split('/')
        if len(key) == 1:
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
    sorted_resources = sorted(resources)
    sorted_resources.sort(key=takeSecond)
    resources = [resources[key] for key in sorted_resources] # sorted channel names
    print("resources", resources)
    session = nidcpower.Session(resource_name=resources, reset=True,  options = {'simulate': True, 'driver_setup': {'Model': '4163', 'BoardType': 'PXIe', }, })

    session.power_line_frequency = 50
    session.aperture_time_units = nidcpower.ApertureTimeUnits.SECONDS
    session.samples_to_average = 1
    session.measure_when = nidcpower.MeasureWhen.ON_DEMAND
    session.source_mode = nidcpower.SourceMode.SINGLE_POINT
    session.sense = nidcpower.Sense.LOCAL
    session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
    session.voltage_level_autorange = True
    # session.voltage_level_range = 6
    session.voltage_level = 0.0
    session.output_connected = True
    session.output_enabled = True
    session.current_limit_autorange = True
    aperture_time = 5e-3
    vSteps_dict = {}
    numOfSteps = 0
    for ivSweep in lstIVSweep:

        chnSweep = session.channels[ivSweep.sweep.resource]
        if ivSweep.sweep.remote_sense == True:
            chnSweep.sense = nidcpower.Sense.REMOTE
        chnSweep.aperture_time = ivSweep.apertureTime
        # chnSweep.current_limit_range = ivSweep.sweep.I_compl
        # chnSweep.source_trigger_type = nidcpower.TriggerType.SOFTWARE_EDGE  # software trigger
        chnSweep.current_limit       = ivSweep.sweep.I_compl 
        # chnSweep.current_limit_range = current_ranges[0] 
        chnSweep.measure_complete_event_delay = 5e-3
        V_start, V_stop, V_step = ivSweep.sweep.V_start, ivSweep.sweep.V_stop, ivSweep.sweep.V_step
        numStep = round(abs((V_stop-V_start)/V_step))+1
        # print(numStep)
        
        # vSteps = np.zeros(numStep+1)
        vSteps = np.linspace(V_start, V_stop, numStep, endpoint=True)
        vSteps = np.append(vSteps, 0)
        vSteps_dict[ivSweep.sweep.resource] = vSteps
        numOfSteps  = len(vSteps)
        chnSweep.source_delay = ivSweep.sourceDelay
  
        for bias in ivSweep.biases:
            if bias.VoltSense:
                chnBias = session.channels[bias.resource]
                chnBias.output_function = nidcpower.OutputFunction.DC_CURRENT
                chnBias.current_level_autorange = True
                chnBias.voltage_limit_range = bias.V_compl
                chnBias.measure_when = nidcpower.MeasureWhen.ON_DEMAND
                # chnBias.source_trigger_type = nidcpower.TriggerType.SOFTWARE_EDGE
                # chnBias.measure_trigger_type = nidcpower.TriggerType.SOFTWARE_EDGE
                chnBias.aperture_time = bias.apertureTime
                chnBias.voltage_limit       = bias.V_compl
                chnBias.source_delay = bias.source_delay
                chnBias.current_level = bias.I_force
                # vSteps = np.zeros(numStep + 1)
                # vSteps[:-1] = bias.I_force
                # chnBias.set_sequence(vSteps, tSteps)
            else:
                chnBias = session.channels[bias.resource]
                if bias.remote_sense == True:
                    chnBias.sense = nidcpower.Sense.REMOTE
                chnBias.aperture_time = ivSweep.apertureTime
                chnBias.source_delay = bias.source_delay


                chnBias.current_limit       = bias.I_compl
                chnBias.voltage_level = bias.V_force
                chnBias.measure_when = nidcpower.MeasureWhen.ON_DEMAND
                # chnBias.source_trigger_type = nidcpower.TriggerType.SOFTWARE_EDGE
                # chnBias.measure_trigger_type = nidcpower.TriggerType.SOFTWARE_EDGE
                # chnBias.current_limit_range = 
                chnBias.current_limit_autorange = True
                vSteps = np.zeros(numStep+1)
                vSteps[:-1] = bias.V_force
                vSteps_dict[bias.resource] = vSteps

    timeout = hightime.timedelta(seconds=1000)

    df_meas_list = []
    for ivsweep in lstIVSweep:
        for bias in ivsweep.biases:
            chnBias = session.channels[bias.resource]

            chnBias.initiate() # slave initiate
        chnSweep = session.channels[ivSweep.sweep.resource]
        chnSweep.initiate() # master initiate
    
       