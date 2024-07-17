import csv
from dataclasses import KW_ONLY
from email.policy import default
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

def ivi_synchronized(f):
    @wraps(f)
    def aux(*xs, **kws):
        session = xs[0]  # parameter 0 is 'self' which is the session object
        with session.lock():
            return f(*xs, **kws)
    return aux

class SMUType(enum.Enum):
    HP_415x     = 1
    NI_PXIe41xx = 2

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
        default=20e-3,
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
                            default=3e-5,
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
                            default = 0.1,
                            kw_only = True,
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
                                    default = 10e-3,
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
                                    default = 5e-3,
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


def runTimming(*lstTDDB: TDDB, CSV_name):
    resources: dict[tuple[str,int],TDDB]= {}

    def chnKey(chn):
        key = chn.split('/')
        if len(key)==1:
            key.append(0)
        return tuple(key)
    for tddb in lstTDDB:
        key = chnKey(tddb.chnStress.resource)
        if key in resources:
            raise ValueError(f'SMU {tddb.chnStress.resource} used more than once')
        resources[key] = tddb.chnStress.resource
        for bias in tddb.biases:
            key = chnKey(bias.resource)
            if key in resources:
                raise ValueError(f'SMU {bias.resource} used more than once')
            resources[key] = bias.resource

    resources = [resources[key] for key in resources]  # sorted channel names
    session = nidcpower.Session(resource_name=resources)

    session.power_line_frequency = 50
    session.aperture_time_units = nidcpower.ApertureTimeUnits.SECONDS
    session.samples_to_average = 1
    session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
    session.measure_record_length_is_finite = True
    session.source_mode = nidcpower.SourceMode.SEQUENCE
    session.output_function = nidcpower.OutputFunction.DC_CURRENT
    session.current_autorange = True
    session.current_level = 0.0
    session.output_connected = True
    session.output_enabled = True
    # session.source_delay = hightime.timedelta(seconds=0.5)
    session.measure_complete_event_delay = 0.0
    # session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
    #PreTest Ramp
    for tddb in lstTDDB:
        chnSweep = session.channels[tddb.chnStress.resource]
        chnSweep.aperture_time = tddb.apertureTime
        chnSweep.current_limit_range = tddb.chnStress.I_compl
        chnSweep.current_limit = tddb.chnStress.I_compl

        V_start, V_stop, V_step = tddb.chnStress.V_start, tddb.chnStress.V_stop, tddb.chnStress.V_step
        numStep = round((V_stop - V_start) / V_step) + 1
        tSteps = np.ones(numStep + 1)
        vSteps = np.zeros(numStep + 1)

        vSteps[:-1] = range(numStep)
        vSteps *= V_step
        tSteps *= tddb.sourceDelay
        chnSweep.set_sequence(vSteps, tSteps)

        for bias in tddb.biases:
            chnBias = session.channels[bias.resource]
            chnBias.aperture_time = tddb.apertureTime
            chnBias.current_limit_range = bias.I_compl
            chnBias.current_limit = bias.I_compl
            chnBias.voltage_level = bias.V_force
            vSteps = np.zeros(numStep + 1)
            vSteps[:-1] = bias.V_force
            chnBias.set_sequence(vSteps, tSteps)


    timeout = hightime.timedelta(seconds=50)
    # print('Effective measurement rate: {0} S/s'.format(session.measure_record_delta_time / 1))

    print('Channel           Num  Voltage    Current    In Compliance')
    row_format = '{0:15} {1:3d}    {2:8.6f}   {3:8.6f}   {4}'
    with session.initiate():
        # Pre Test
        pretest_temp_list = []

        session.wait_for_event(nidcpower.Event.SEQUENCE_ENGINE_DONE)
        for TDDBSweep in lstTDDB:

            chnSweep = session.channels[TDDBSweep.chnStress.resource]
            num  = chnSweep.fetch_backlog
            measurements = chnSweep.fetch_multiple(num, timeout=timeout)[:-1]
            df_gate_pre_test = pd.DataFrame(measurements)
            max_current_in_pre_test = df_gate_pre_test['current'].abs().max()
            # print(df_gate_pre_test)
            TDDBSweep.I_SILC = max_current_in_pre_test

            if not df_gate_pre_test['in_compliance'].eq(False).all(): # check compliance
                TDDBSweep.Failed_in_pre = True


            for i in range(len(measurements)):

                # lstSingleMeasurement.append()
                temp_list = [TDDBSweep.chnStress.resource, i, measurements[i].voltage, measurements[i].current,
                                        measurements[i].in_compliance]
                print(row_format.format(TDDBSweep.chnStress.resource, i, measurements[i].voltage, measurements[i].current,
                                        measurements[i].in_compliance))
                pretest_temp_list.append(temp_list)






            for bias in TDDBSweep.biases:
                chnBias = session.channels[bias.resource]
                num = chnBias.fetch_backlog
                measurements = chnBias.fetch_multiple(num, timeout=timeout)[:-1]


                for i in range(len(measurements)):
                    temp_list = [bias.resource, i, measurements[i].voltage, measurements[i].current,
                                 measurements[i].in_compliance]

                    print(row_format.format(bias.resource, i, measurements[i].voltage, measurements[i].current,
                                            measurements[i].in_compliance))
                    pretest_temp_list.append(temp_list)
        pretest_df = pd.DataFrame(pretest_temp_list, columns=["Channel", "Num", "Voltage", "Current", "In Compliance"])
        pretest_df.to_csv(CSV_name)




        #### now we ride!!!!!!!  go to timming samples
    session.source_mode = nidcpower.SourceMode.SINGLE_POINT
    session.measure_when = nidcpower.MeasureWhen.ON_DEMAND

    for tddb in lstTDDB:
        chnStress = session.channels[tddb.chnStress.resource]
        chnStress.aperture_time = tddb.apertureTime
        chnStress.current_limit_range = tddb.chnStress.I_compl
        chnStress.current_limit = tddb.chnStress.I_compl
        chnStress.voltage_level = tddb.chnStress.V_force_stress



        for bias in tddb.biases:
            chnBias = session.channels[bias.resource]
            chnBias.aperture_time = tddb.apertureTime
            chnBias.current_limit_range = bias.I_compl
            chnBias.current_limit = bias.I_compl
            chnBias.voltage_level = bias.V_force

    with session.initiate():
        session.wait_for_event(nidcpower.Event.SOURCE_COMPLETE)

        # print(pretest_df)
        measurements = session.measure_multiple()
        for i in range(len(measurements)):
            if i % 3 == 0:
                tddb = lstTDDB[int(i/3)]
                tddb.I_CVS = measurements[i].current     #record first I_CVS
                if not (tddb.Failed_in_pre or tddb.Failed_in_CSV or tddb.Failed_in_SILC):
                    if abs(tddb.I_CVS) / tddb.chnStress.I_compl >= 0.95:   # if I_CVS is greater than 95% of I_compl we define it as CVS fail
                        tddb.Failed_in_CSV = True

        t_stress_begin = time.time()
        all_devices_failed = False
        while not all_devices_failed:
            # t_a_cycle_begin = time.time()

            all_devices_failed_lst = []
            tic = time.time()
            lstTempMeas = []
            measurements = session.measure_multiple()

            toc = time.time()
            for i in range(len(measurements)):
                for k in range(len(measurements[i])):
                    lstTempMeas.append(measurements[i][k])
                if i % 3 == 0:
                    tddb = lstTDDB[int(i / 3)]
                    lstTempMeas.append(tddb.dieName)
                    lstTempMeas.append(tddb.Failed_in_pre)
                    lstTempMeas.append(tddb.Failed_in_CSV)
                    lstTempMeas.append(tddb.Failed_in_SILC)
            emit(lstTempMeas, CSV_name)
            print("############CVS#############")
            print(measurements)
            print("############CVS#############")
            # fetch multiple channels' measurements

            for i in range(len(measurements)):
                if i % 3 == 0:
                    tddb = lstTDDB[int(i / 3)]
                    single_device_failed = (tddb.Failed_in_CSV or tddb.Failed_in_pre or tddb.Failed_in_SILC)
                    current_I_CVS = measurements[i].current
                    try:
                        if abs(current_I_CVS) / tddb.I_CVS >= 10 or abs(current_I_CVS) / tddb.chnStress.I_compl >= 0.96:
                            tddb.Failed_in_CSV = True
                            session.channels[tddb.chnStress.resource].output_enabled = False
                            session.channels[tddb.chnStress.resource].output_connected = False
                            session.channels[tddb.chnStress.resource].voltage_level = 0
                            print("channel {} has been closed for CVS fail".format(tddb.chnStress.resource))
                        else:
                            tddb.I_CVS = current_I_CVS
                    except ZeroDivisionError as err:
                        tddb.Failed_in_CSV = True
                    all_devices_failed_lst.append(single_device_failed)
            print(all_devices_failed_lst)
            all_devices_failed = all(all_devices_failed_lst)
            t_stress_end = time.time()

            lstTempMeas = [] # init lst
            if t_stress_end - t_stress_begin >= 50:
                for tddb in lstTDDB:
                    if not (tddb.Failed_in_SILC or tddb.Failed_in_pre or tddb.Failed_in_CSV):
                        chnStress = session.channels[tddb.chnStress.resource]
                        chnStress.voltage_level = tddb.chnStress.V_force_SILC

                time.sleep(2)
                measurements = session.measure_multiple()
                print("############SILC#############")
                print(measurements)
                print("############SILC#############")
                for i in range(len(measurements)):
                    for k in range(len(measurements[i])):
                        lstTempMeas.append(measurements[i][k])
                    if i % 3 == 0:
                        tddb = lstTDDB[int(i / 3)]
                        lstTempMeas.append(tddb.dieName)
                        lstTempMeas.append(tddb.Failed_in_pre)
                        lstTempMeas.append(tddb.Failed_in_CSV)
                        lstTempMeas.append(tddb.Failed_in_SILC)
                emit(lstTempMeas, CSV_name)

                for i in range(len(measurements)):
                    if i % 3 == 0:
                        tddb = lstTDDB[int(i / 3)]
                        current_I_SILC = measurements[i].current
                        try:
                            if abs(current_I_SILC) / tddb.I_SILC >= 5:
                                tddb.Failed_in_SILC = True
                                session.channels[tddb.chnStress.resource].output_enabled = False
                                session.channels[tddb.chnStress.resource].output_connected = False
                                print("channel {} has been closed for SILC fail".format(tddb.chnStress.resource))
                            else:
                                tddb.I_SILC = current_I_SILC
                        except ZeroDivisionError as err:
                            tddb.Failed_in_SILC = True
                for tddb in lstTDDB:
                    if not (tddb.Failed_in_SILC or tddb.Failed_in_pre or tddb.Failed_in_CSV):

                        chnStress = session.channels[tddb.chnStress.resource]
                        chnStress.voltage_level = tddb.chnStress.V_force_stress

 
def runTimming(*lstTDDB: TDDB, CSV_name):
    resources: dict[tuple[str,int],TDDB]= {}

    def chnKey(chn):
        key = chn.split('/')
        if len(key)==1:
            key.append(0)
        return tuple(key)
    for tddb in lstTDDB:
        key = chnKey(tddb.chnStress.resource)
        if key in resources:
            raise ValueError(f'SMU {tddb.chnStress.resource} used more than once')
        resources[key] = tddb.chnStress.resource
        for bias in tddb.biases:
            key = chnKey(bias.resource)
            if key in resources:
                raise ValueError(f'SMU {bias.resource} used more than once')
            resources[key] = bias.resource

    resources = [resources[key] for key in resources]  # sorted channel names
    session = nidcpower.Session(resource_name=resources)

    session.power_line_frequency = 50
    session.aperture_time_units = nidcpower.ApertureTimeUnits.SECONDS
    session.samples_to_average = 1
    session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
    session.measure_record_length_is_finite = True
    session.source_mode = nidcpower.SourceMode.SEQUENCE
    session.output_function = nidcpower.OutputFunction.DC_CURRENT
    session.current_autorange = True
    session.current_level = 0.0
    session.output_connected = True
    session.output_enabled = True
    # session.source_delay = hightime.timedelta(seconds=0.5)
    session.measure_complete_event_delay = 0.0
    # session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
    #PreTest Ramp
    for tddb in lstTDDB:
        chnSweep = session.channels[tddb.chnStress.resource]
        chnSweep.aperture_time = tddb.apertureTime
        chnSweep.current_limit_range = tddb.chnStress.I_compl
        chnSweep.current_limit = tddb.chnStress.I_compl

        V_start, V_stop, V_step = tddb.chnStress.V_start, tddb.chnStress.V_stop, tddb.chnStress.V_step
        numStep = round((V_stop - V_start) / V_step) + 1
        tSteps = np.ones(numStep + 1)
        vSteps = np.zeros(numStep + 1)

        vSteps[:-1] = range(numStep)
        vSteps *= V_step
        tSteps *= tddb.sourceDelay
        chnSweep.set_sequence(vSteps, tSteps)

        for bias in tddb.biases:
            chnBias = session.channels[bias.resource]
            chnBias.aperture_time = tddb.apertureTime
            chnBias.current_limit_range = bias.I_compl
            chnBias.current_limit = bias.I_compl
            chnBias.voltage_level = bias.V_force
            vSteps = np.zeros(numStep + 1)
            vSteps[:-1] = bias.V_force
            chnBias.set_sequence(vSteps, tSteps)


    timeout = hightime.timedelta(seconds=50)
    # print('Effective measurement rate: {0} S/s'.format(session.measure_record_delta_time / 1))

    print('Channel           Num  Voltage    Current    In Compliance')
    row_format = '{0:15} {1:3d}    {2:8.6f}   {3:8.6f}   {4}'
    with session.initiate():
        # Pre Test
        pretest_temp_list = []

        session.wait_for_event(nidcpower.Event.SEQUENCE_ENGINE_DONE)
        for TDDBSweep in lstTDDB:

            chnSweep = session.channels[TDDBSweep.chnStress.resource]
            num  = chnSweep.fetch_backlog
            measurements = chnSweep.fetch_multiple(num, timeout=timeout)[:-1]
            df_gate_pre_test = pd.DataFrame(measurements)
            max_current_in_pre_test = df_gate_pre_test['current'].abs().max()
            # print(df_gate_pre_test)
            TDDBSweep.I_SILC = max_current_in_pre_test

            if not df_gate_pre_test['in_compliance'].eq(False).all(): # check compliance
                TDDBSweep.Failed_in_pre = True


            for i in range(len(measurements)):

                # lstSingleMeasurement.append()
                temp_list = [TDDBSweep.chnStress.resource, i, measurements[i].voltage, measurements[i].current,
                                        measurements[i].in_compliance]
                print(row_format.format(TDDBSweep.chnStress.resource, i, measurements[i].voltage, measurements[i].current,
                                        measurements[i].in_compliance))
                pretest_temp_list.append(temp_list)






            for bias in TDDBSweep.biases:
                chnBias = session.channels[bias.resource]
                num = chnBias.fetch_backlog
                measurements = chnBias.fetch_multiple(num, timeout=timeout)[:-1]


                for i in range(len(measurements)):
                    temp_list = [bias.resource, i, measurements[i].voltage, measurements[i].current,
                                 measurements[i].in_compliance]

                    print(row_format.format(bias.resource, i, measurements[i].voltage, measurements[i].current,
                                            measurements[i].in_compliance))
                    pretest_temp_list.append(temp_list)
        pretest_df = pd.DataFrame(pretest_temp_list, columns=["Channel", "Num", "Voltage", "Current", "In Compliance"])
        pretest_df.to_csv(CSV_name)




        #### now we ride!!!!!!!  go to timming samples
    session.source_mode = nidcpower.SourceMode.SINGLE_POINT
    session.measure_when = nidcpower.MeasureWhen.ON_DEMAND

    for tddb in lstTDDB:
        chnStress = session.channels[tddb.chnStress.resource]
        chnStress.aperture_time = tddb.apertureTime
        chnStress.current_limit_range = tddb.chnStress.I_compl
        chnStress.current_limit = tddb.chnStress.I_compl
        chnStress.voltage_level = tddb.chnStress.V_force_stress



        for bias in tddb.biases:
            chnBias = session.channels[bias.resource]
            chnBias.aperture_time = tddb.apertureTime
            chnBias.current_limit_range = bias.I_compl
            chnBias.current_limit = bias.I_compl
            chnBias.voltage_level = bias.V_force

    with session.initiate():
        session.wait_for_event(nidcpower.Event.SOURCE_COMPLETE)

        # print(pretest_df)
        measurements = session.measure_multiple()
        for i in range(len(measurements)):
            if i % 3 == 0:
                tddb = lstTDDB[int(i/3)]
                tddb.I_CVS = measurements[i].current     #record first I_CVS
                if not (tddb.Failed_in_pre or tddb.Failed_in_CSV or tddb.Failed_in_SILC):
                    if abs(tddb.I_CVS) / tddb.chnStress.I_compl >= 0.95:   # if I_CVS is greater than 95% of I_compl we define it as CVS fail
                        tddb.Failed_in_CSV = True

        t_stress_begin = time.time()
        all_devices_failed = False
        while not all_devices_failed:
            # t_a_cycle_begin = time.time()

            all_devices_failed_lst = []
            tic = time.time()
            lstTempMeas = []
            measurements = session.measure_multiple()

            toc = time.time()
            for i in range(len(measurements)):
                for k in range(len(measurements[i])):
                    lstTempMeas.append(measurements[i][k])
                if i % 3 == 0:
                    tddb = lstTDDB[int(i / 3)]
                    lstTempMeas.append(tddb.dieName)
                    lstTempMeas.append(tddb.Failed_in_pre)
                    lstTempMeas.append(tddb.Failed_in_CSV)
                    lstTempMeas.append(tddb.Failed_in_SILC)
            emit(lstTempMeas, CSV_name)
            print("############CVS#############")
            print(measurements)
            print("############CVS#############")
            # fetch multiple channels' measurements

            for i in range(len(measurements)):
                if i % 3 == 0:
                    tddb = lstTDDB[int(i / 3)]
                    single_device_failed = (tddb.Failed_in_CSV or tddb.Failed_in_pre or tddb.Failed_in_SILC)
                    current_I_CVS = measurements[i].current
                    try:
                        if abs(current_I_CVS) / tddb.I_CVS >= 10 or abs(current_I_CVS) / tddb.chnStress.I_compl >= 0.96:
                            tddb.Failed_in_CSV = True
                            session.channels[tddb.chnStress.resource].output_enabled = False
                            session.channels[tddb.chnStress.resource].output_connected = False
                            session.channels[tddb.chnStress.resource].voltage_level = 0
                            print("channel {} has been closed for CVS fail".format(tddb.chnStress.resource))
                        else:
                            tddb.I_CVS = current_I_CVS
                    except ZeroDivisionError as err:
                        tddb.Failed_in_CSV = True
                    all_devices_failed_lst.append(single_device_failed)
            print(all_devices_failed_lst)
            all_devices_failed = all(all_devices_failed_lst)
            t_stress_end = time.time()

            lstTempMeas = [] # init lst
            if t_stress_end - t_stress_begin >= 50:
                for tddb in lstTDDB:
                    if not (tddb.Failed_in_SILC or tddb.Failed_in_pre or tddb.Failed_in_CSV):
                        chnStress = session.channels[tddb.chnStress.resource]
                        chnStress.voltage_level = tddb.chnStress.V_force_SILC

                time.sleep(2)
                measurements = session.measure_multiple()
                print("############SILC#############")
                print(measurements)
                print("############SILC#############")
                for i in range(len(measurements)):
                    for k in range(len(measurements[i])):
                        lstTempMeas.append(measurements[i][k])
                    if i % 3 == 0:
                        tddb = lstTDDB[int(i / 3)]
                        lstTempMeas.append(tddb.dieName)
                        lstTempMeas.append(tddb.Failed_in_pre)
                        lstTempMeas.append(tddb.Failed_in_CSV)
                        lstTempMeas.append(tddb.Failed_in_SILC)
                emit(lstTempMeas, CSV_name)

                for i in range(len(measurements)):
                    if i % 3 == 0:
                        tddb = lstTDDB[int(i / 3)]
                        current_I_SILC = measurements[i].current
                        try:
                            if abs(current_I_SILC) / tddb.I_SILC >= 5:
                                tddb.Failed_in_SILC = True
                                session.channels[tddb.chnStress.resource].output_enabled = False
                                session.channels[tddb.chnStress.resource].output_connected = False
                                print("channel {} has been closed for SILC fail".format(tddb.chnStress.resource))
                            else:
                                tddb.I_SILC = current_I_SILC
                        except ZeroDivisionError as err:
                            tddb.Failed_in_SILC = True
                for tddb in lstTDDB:
                    if not (tddb.Failed_in_SILC or tddb.Failed_in_pre or tddb.Failed_in_CSV):

                        chnStress = session.channels[tddb.chnStress.resource]
                        chnStress.voltage_level = tddb.chnStress.V_force_stress

 
def runTimmingAmp(*lstTDDB: TDDB, CSV_name):
    resources: dict[tuple[str,int],TDDB]= {}

    def chnKey(chn):
        key = chn.split('/')
        if len(key)==1:
            key.append(0)
        return tuple(key)
    for tddb in lstTDDB:
        key = chnKey(tddb.chnStress.resource)
        if key in resources:
            raise ValueError(f'SMU {tddb.chnStress.resource} used more than once')
        resources[key] = tddb.chnStress.resource
        for bias in tddb.biases:
            key = chnKey(bias.resource)
            if key in resources:
                raise ValueError(f'SMU {bias.resource} used more than once')
            resources[key] = bias.resource

    resources = [resources[key] for key in resources]  # sorted channel names
    session = nidcpower.Session(resource_name=resources)

    session.power_line_frequency = 50
    session.aperture_time_units = nidcpower.ApertureTimeUnits.SECONDS
    session.samples_to_average = 1
    session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
    session.measure_record_length_is_finite = True
    session.sense = nidcpower.Sense.REMOTE
    session.source_mode = nidcpower.SourceMode.SEQUENCE
    session.output_function = nidcpower.OutputFunction.DC_CURRENT
    session.current_level_autorange = True
    session.current_level = 0.0
    session.output_connected = True
    session.output_enabled = True
    # session.voltage_limit_autorange = True
    # session.source_delay = hightime.timedelta(seconds=0.5)
    session.measure_complete_event_delay = 0.0
    # session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
    #PreTest Ramp
    for tddb in lstTDDB:
        chnSweep = session.channels[tddb.chnStress.resource]
        chnSweep.aperture_time = tddb.apertureTime
        chnSweep.voltage_limit_range = tddb.chnStress.V_compl
        chnSweep.voltage_limit = tddb.chnStress.V_compl

        I_start, I_stop, I_step = tddb.chnStress.I_start, tddb.chnStress.I_stop, tddb.chnStress.I_step
        numStep = round((I_stop - I_start) / I_step) + 1
        iSteps = np.ones(numStep + 1)
        tSteps = np.zeros(numStep + 1)

        iSteps[:-1] = range(numStep)
        iSteps *= I_step
        tSteps *= tddb.sourceDelay
        chnSweep.set_sequence(iSteps, tSteps)

        for bias in tddb.biases:
            chnBias = session.channels[bias.resource]
            chnBias.aperture_time = tddb.apertureTime
            chnBias.output_function = nidcpower.OutputFunction.DC_VOLTAGE
            chnBias.current_limit_range = bias.I_compl
            chnBias.current_limit = bias.I_compl
            chnBias.voltage_level = bias.V_force
            vSteps = np.zeros(numStep + 1)
            vSteps[:-1] = bias.V_force
            chnBias.set_sequence(vSteps, tSteps)


    timeout = hightime.timedelta(seconds=50)
    # print('Effective measurement rate: {0} S/s'.format(session.measure_record_delta_time / 1))

    print('Channel           Num  Voltage    Current    In Compliance')
    row_format = '{0:15} {1:3d}    {2:8.6f}   {3:8.6f}   {4}'
    with session.initiate():
        # Pre Test
        pretest_temp_list = []

        session.wait_for_event(nidcpower.Event.SEQUENCE_ENGINE_DONE)
        for TDDBSweep in lstTDDB:

            chnSweep = session.channels[TDDBSweep.chnStress.resource]
            num  = chnSweep.fetch_backlog
            measurements = chnSweep.fetch_multiple(num, timeout=timeout)[:-1]
            df_gate_pre_test = pd.DataFrame(measurements)
            # max_current_in_pre_test = df_gate_pre_test['current'].abs().max()
            # print(df_gate_pre_test)
            # TDDBSweep.I_SILC = max_current_in_pre_test

            # if not df_gate_pre_test['in_compliance'].eq(False).all(): # check compliance
            #     TDDBSweep.Failed_in_pre = True


            for i in range(len(measurements)):

                # lstSingleMeasurement.append()
                temp_list = [TDDBSweep.chnStress.resource, i, measurements[i].voltage, measurements[i].current,
                                        measurements[i].in_compliance]
                print(row_format.format(TDDBSweep.chnStress.resource, i, measurements[i].voltage, measurements[i].current,
                                        measurements[i].in_compliance))
                pretest_temp_list.append(temp_list)






            for bias in TDDBSweep.biases:
                chnBias = session.channels[bias.resource]
                num = chnBias.fetch_backlog
                measurements = chnBias.fetch_multiple(num, timeout=timeout)[:-1]


                for i in range(len(measurements)):
                    temp_list = [bias.resource, i, measurements[i].voltage, measurements[i].current,
                                 measurements[i].in_compliance]

                    print(row_format.format(bias.resource, i, measurements[i].voltage, measurements[i].current,
                                            measurements[i].in_compliance))
                    pretest_temp_list.append(temp_list)
        pretest_df = pd.DataFrame(pretest_temp_list, columns=["Channel", "Num", "Voltage", "Current", "In Compliance"])
        pretest_df.to_csv(CSV_name)




        #### now we ride!!!!!!!  go to timming samples
    session.source_mode = nidcpower.SourceMode.SINGLE_POINT
    session.measure_when = nidcpower.MeasureWhen.ON_DEMAND

    for tddb in lstTDDB:
        chnStress = session.channels[tddb.chnStress.resource]
        chnStress.aperture_time = tddb.apertureTime
        chnStress.voltage_limit_range = tddb.chnStress.V_compl
        chnStress.voltage_limit = tddb.chnStress.V_compl
        chnStress.current_level = tddb.chnStress.I_force_stress



        for bias in tddb.biases:
            chnBias = session.channels[bias.resource]
            chnBias.aperture_time = tddb.apertureTime
            chnBias.current_limit_range = bias.I_compl
            chnBias.current_limit = bias.I_compl
            chnBias.voltage_level = bias.V_force

    with session.initiate():
        session.wait_for_event(nidcpower.Event.SOURCE_COMPLETE)

        # print(pretest_df)
        measurements = session.measure_multiple()
        # for i in range(len(measurements)):
        #     if i % 3 == 0:
        #         tddb = lstTDDB[int(i/3)]
        #         tddb.I_CVS = measurements[i].current     #record first I_CVS
        #         if not (tddb.Failed_in_pre or tddb.Failed_in_CSV or tddb.Failed_in_SILC):
        #             if abs(tddb.I_CVS) / tddb.chnStress.I_compl >= 0.95:   # if I_CVS is greater than 95% of I_compl we define it as CVS fail
        #                 tddb.Failed_in_CSV = True

        t_stress_begin = time.time()
        all_devices_failed = False
        while not all_devices_failed:
            # t_a_cycle_begin = time.time()
            time.sleep(1)
            all_devices_failed_lst = []
            tic = time.time()
            lstTempMeas = []
            measurements = session.measure_multiple()

            toc = time.time()
            # for i in range(len(measurements)):
            #     for k in range(len(measurements[i])):
            #         lstTempMeas.append(measurements[i][k])
            #     if i % 3 == 0:
            #         tddb = lstTDDB[int(i / 3)]
            #         lstTempMeas.append(tddb.dieName)
            #         lstTempMeas.append(tddb.Failed_in_pre)
            #         lstTempMeas.append(tddb.Failed_in_CSV)
            #         lstTempMeas.append(tddb.Failed_in_SILC)
            emit(lstTempMeas, CSV_name)
            print("############CVS#############")
            print(measurements)
            print("############CVS#############")
            # fetch multiple channels' measurements

            # for i in range(len(measurements)):
                # if i % 3 == 0:
                #     tddb = lstTDDB[int(i / 3)]
                #     single_device_failed = (tddb.Failed_in_CSV or tddb.Failed_in_pre or tddb.Failed_in_SILC)
                #     current_I_CVS = measurements[i].current
                #     try:
                #         if abs(current_I_CVS) / tddb.I_CVS >= 10 or abs(current_I_CVS) / tddb.chnStress.I_compl >= 0.96:
                #             tddb.Failed_in_CSV = True
                #             session.channels[tddb.chnStress.resource].output_enabled = False
                #             session.channels[tddb.chnStress.resource].output_connected = False
                #             session.channels[tddb.chnStress.resource].voltage_level = 0
                #             print("channel {} has been closed for CVS fail".format(tddb.chnStress.resource))
                #         else:
                #             tddb.I_CVS = current_I_CVS
                #     except ZeroDivisionError as err:
                #         tddb.Failed_in_CSV = True
            #         all_devices_failed_lst.append(single_device_failed)
            # print(all_devices_failed_lst)
            # all_devices_failed = all(all_devices_failed_lst)
            # t_stress_end = time.time()

            # lstTempMeas = [] # init lst
            # if t_stress_end - t_stress_begin >= 50:
            #     for tddb in lstTDDB:
            #         if not (tddb.Failed_in_SILC or tddb.Failed_in_pre or tddb.Failed_in_CSV):
            #             chnStress = session.channels[tddb.chnStress.resource]
            #             chnStress.voltage_level = tddb.chnStress.V_force_SILC

            #     time.sleep(2)
            #     measurements = session.measure_multiple()
            #     print("############SILC#############")
            #     print(measurements)
            #     print("############SILC#############")
            for i in range(len(measurements)):
                for k in range(len(measurements[i])):
                    lstTempMeas.append(measurements[i][k])
            #         if i % 3 == 0:
            #             tddb = lstTDDB[int(i / 3)]
            #             lstTempMeas.append(tddb.dieName)
            #             lstTempMeas.append(tddb.Failed_in_pre)
            #             lstTempMeas.append(tddb.Failed_in_CSV)
            #             lstTempMeas.append(tddb.Failed_in_SILC)
            emit(lstTempMeas, CSV_name)

                # for i in range(len(measurements)):
                #     if i % 3 == 0:
                #         tddb = lstTDDB[int(i / 3)]
                #         current_I_SILC = measurements[i].current
                #         try:
                #             if abs(current_I_SILC) / tddb.I_SILC >= 5:
                #                 tddb.Failed_in_SILC = True
                #                 session.channels[tddb.chnStress.resource].output_enabled = False
                #                 session.channels[tddb.chnStress.resource].output_connected = False
                #                 print("channel {} has been closed for SILC fail".format(tddb.chnStress.resource))
                #             else:
                #                 tddb.I_SILC = current_I_SILC
                #         except ZeroDivisionError as err:
                #             tddb.Failed_in_SILC = True
                # for tddb in lstTDDB:
                #     if not (tddb.Failed_in_SILC or tddb.Failed_in_pre or tddb.Failed_in_CSV):

                #         chnStress = session.channels[tddb.chnStress.resource]
                #         chnStress.voltage_level = tddb.chnStress.V_force_stress

                # t_stress_begin = time.time()

def drawTheCurve():
    pass

#
# class Session(nidcpower.Session):
#
#     @ivi_synchronized
#     def fetch_multiple(self, chn, count, timeout=hightime.timedelta(seconds=1.0)):
#
#         import collections
#         Measurement = collections.namedtuple('Measurement', ['chn', 'voltage', 'current', 'in_compliance'])
#
#         voltage_measurements, current_measurements, in_compliance = self._fetch_multiple(timeout, count)
#         # print("hello***************")
#         return [Measurement(chn=chn, voltage=voltage_measurements[i], current=current_measurements[i],
#                             in_compliance=in_compliance[i]) for i in range(count)]


def fetch_multiple(self, chn, count, timeout=hightime.timedelta(seconds=1.0)):
    import collections
    Measurement = collections.namedtuple('Measurement', ['chn', 'voltage', 'current', 'in_compliance'])
    voltage_measurements, current_measurements, in_compliance = self._fetch_multiple(timeout, count)
    return [Measurement(chn=chn, voltage=voltage_measurements[i], current=current_measurements[i],
                        in_compliance=in_compliance[i]) for i in range(count)]

def runIVSweeps(*lstIVSweep : IVSweep, CSV_name):
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
    # sesseionSlave = nidcpower.Session(resource_name=)
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
    # session.measure_complete_event_delay
    sourceTriggerInputTerminal = None
    measureTriggerInputTerminal = None
    for ivSweep in lstIVSweep:
        

        chnSweep = session.channels[ivSweep.sweep.resource]
        chnSweep.aperture_time = ivSweep.apertureTime
        chnSweep.current_limit_range = ivSweep.sweep.I_compl
        chnSweep.current_limit       = ivSweep.sweep.I_compl
        chnSweep.current_limit_autorange = True
        chnSweep.autorange = True
        # chnSweep.measure_complete_event_delay = 1
        # chnSweep.source_trigger_type =
        V_start, V_stop, V_step = ivSweep.sweep.V_start, ivSweep.sweep.V_stop, ivSweep.sweep.V_step
        # numStep = round(abs((V_stop-V_start)/V_step))+1
        # # print(numStep)
        # tSteps = np.ones(numStep+1)
        #
        # # vSteps[:-1] = range(numStep)
        # vSteps *= V_step
        # tSteps *= tddb.sourceDelay
        # chnSweep.set_sequence(vSteps, tSteps)

        numStep = round((V_stop - V_start) / V_step) + 1
        tSteps = np.ones(numStep + 1)
        vSteps = np.zeros(numStep + 1)

        vSteps[:-1] = range(numStep)
        vSteps *= V_step
        tSteps *= ivSweep.sourceDelay
        chnSweep.set_sequence(vSteps, tSteps)
        print(vSteps)
        # vSteps = np.zeros(numStep+1)
        # vSteps = np.arange(V_start, V_stop, V_step)
        # vSteps = np.insert(vSteps, 0, 0)
        # vSteps = np.insert(vSteps, -1, 1.5)

        # vSteps = np.arange(V_start, V_stop, V_step)
        # vSteps = np.insert(vSteps, 0, 0)
        # vSteps = np.insert(vSteps, -1, 1.5)
        # np.insert(vSteps, -1, 0)
        # vSteps *= V_step
        # tSteps *= ivSweep.sourceDelay
        # chnSweep.set_sequence(vSteps, tSteps)

        if ivSweep.isMaster:
            chnSweep.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
            chnSweep.measure_complete_event_delay = ivSweep.measure_complete_event_delay

            # sourceTriggerInputTerminal = f'/SMU1/Engine{ivSweep.sweep.resource.split("/")[1]}/SourceTrigger'
            # measureTriggerInputTerminal = f'/SMU1/Engine{ivSweep.sweep.resource.split("/")[1]}/SourceCompleteEvent'
            print(measureTriggerInputTerminal)
        for bias in ivSweep.biases:
            if bias.VoltSense:
                chnBias = session.channels[bias.resource]
                chnBias.output_function = nidcpower.OutputFunction.DC_CURRENT
                chnBias.current_level_autorange = True
                chnBias.voltage_limit_range = bias.V_compl
                # chnBias.measure_when = nidcpower.MeasureWhen.ON_MEASURE_TRIGGER
                chnBias.aperture_time = bias.apertureTime
                chnBias.voltage_limit       = bias.V_compl
                chnBias.source_delay = bias.source_delay
                # chnBias.source_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
                chnBias.current_level = bias.I_force
                vSteps = np.zeros(numStep + 1)
                vSteps[:-1] = bias.I_force
                chnBias.set_sequence(vSteps, tSteps)
                # chnBias.measure_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
                # # chnBias.digital_edge_measure_trigger_input_terminal = measureTriggerInputTerminal
                # # chnBias.digital_edge_source_trigger_input_terminal = sourceTriggerInputTerminal
                # chnBias.source_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
            else:
                chnBias = session.channels[bias.resource]
                chnBias.aperture_time = bias.apertureTime
                chnBias.source_delay = bias.source_delay

                chnBias.current_limit_range = bias.I_compl
                # chnBias.measure_when = nidcpower.MeasureWhen.ON_MEASURE_TRIGGER
                # chnBias.source_delay = 0.3e-3
                chnBias.current_limit       = bias.I_compl
                chnBias.voltage_level = bias.V_force
                vSteps = np.zeros(numStep+1)
                vSteps[:-1] = bias.V_force
                chnBias.set_sequence(vSteps, tSteps)
                # print(chnBias.measure_record_delta_time)
                # chnBias.measure_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
                # # chnBias.digital_edge_measure_trigger_input_terminal = measureTriggerInputTerminal
                # # chnBias.digital_edge_source_trigger_input_terminal = sourceTriggerInputTerminal
                # chnBias.source_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE


    timeout = hightime.timedelta(seconds=10)
    # print('Effective measurement rate: {0} S/s'.format(session.measure_record_delta_time / 1))

    # print('Channel           Num  Voltage    Current    In Compliance')
    # row_format = '{0:15} {1:3d}    {2:8.6f}   {3:8.6f}   {4}'
    df_meas_list = []

    #initiate the slaves
    for ivSweep in lstIVSweep:
        if not ivSweep.isMaster:
            chnSweep = session.channels[ivSweep.sweep.resource]
            chnSweep.initiate()
        
        for bias in ivSweep.biases:
            chnBias = session.channels[bias.resource]
            chnBias.initiate()
    #initiate the master
    for ivSweep in lstIVSweep:
        if ivSweep.isMaster:
            chnSweep = session.channels[ivSweep.sweep.resource]
            chnSweep.initiate()

    # with session.initiate():
    session.wait_for_event(nidcpower.Event.SEQUENCE_ENGINE_DONE)
    for ivSweep in lstIVSweep:
        chnSweep = session.channels[ivSweep.sweep.resource]
        num = chnSweep.fetch_backlog
        measurements = fetch_multiple(chnSweep, chn=ivSweep.sweep.remarks, count=num, timeout=timeout)[:-1]
        df = pd.DataFrame(measurements)
        df_meas_list.append(df)


        for bias in ivSweep.biases:
            pretest_temp_list = []
            chnBias = session.channels[bias.resource]
            num = chnBias.fetch_backlog
            measurements = fetch_multiple(chnBias, chn=bias.remarks, count=num, timeout=timeout)[:-1]
            df = pd.DataFrame(measurements)

            df_meas_list.append(df)
    all_meas = pd.concat(df_meas_list, axis=1)
    all_meas.to_csv(CSV_name, mode="a+")
    session.close()
    print(all_meas)
    return all_meas


def doubleSweep():
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
    resources = [resources[key] for key in sorted_resources]  # sorted channel names

    session = nidcpower.Session(resource_name=resources)

    session.power_line_frequency = 50
    session.aperture_time_units = nidcpower.ApertureTimeUnits.SECONDS
    session.samples_to_average = 1
    session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
    session.sense = nidcpower.Sense.REMOTE
    session.source_mode = nidcpower.SourceMode.SEQUENCE
    session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
    session.voltage_level_autorange = True
    session.voltage_level = 0.0
    session.output_connected = True
    session.output_enabled = True
    # session.measure_complete_event_delay

    for ivSweep in lstIVSweep:
        chnSweep = session.channels[ivSweep.sweep.resource]
        chnSweep.aperture_time = ivSweep.apertureTime
        chnSweep.current_limit_range = ivSweep.sweep.I_compl
        chnSweep.current_limit = ivSweep.sweep.I_compl
        # chnSweep.measure_complete_event_delay = 1
        # chnSweep.source_trigger_type =
        V_start, V_stop, V_step = ivSweep.sweep.V_start, ivSweep.sweep.V_stop, ivSweep.sweep.V_step
        numStep = round((V_stop + V_step / 2 - V_start) / V_step) + 1
        tSteps = np.ones(numStep + 1)
        vSteps = np.zeros(numStep + 1)

        vSteps[:-1] = range(numStep)
        vSteps *= V_step
        tSteps *= ivSweep.sourceDelay
        chnSweep.set_sequence(vSteps, tSteps)

        for bias in ivSweep.biases:
            if bias.VoltSense:
                chnBias = session.channels[bias.resource]
                chnBias.output_function = nidcpower.OutputFunction.DC_CURRENT
                chnBias.current_level_autorange = True
                chnBias.voltage_limit_range = bias.V_compl
                # chnBias.measure_when = nidcpower.MeasureWhen.ON_MEASURE_TRIGGER
                chnBias.aperture_time = bias.apertureTime
                chnBias.voltage_limit = bias.V_compl
                # chnBias.source_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
                chnBias.current_level = bias.I_force
                vSteps = np.zeros(numStep + 1)
                vSteps[:-1] = bias.I_force
                chnBias.set_sequence(vSteps, tSteps)

            else:
                chnBias = session.channels[bias.resource]
                chnBias.aperture_time = ivSweep.apertureTime
                chnBias.current_limit_range = bias.I_compl
                # chnBias.measure_when = nidcpower.MeasureWhen.ON_MEASURE_TRIGGER
                # chnBias.source_delay = 0.3e-3
                chnBias.current_limit = bias.I_compl
                chnBias.voltage_level = bias.V_force
                vSteps = np.zeros(numStep + 1)
                vSteps[:-1] = bias.V_force
                chnBias.set_sequence(vSteps, tSteps)
                # print(chnBias.measure_record_delta_time)

    timeout = hightime.timedelta(seconds=10)
    # print('Effective measurement rate: {0} S/s'.format(session.measure_record_delta_time / 1))

    # print('Channel           Num  Voltage    Current    In Compliance')
    # row_format = '{0:15} {1:3d}    {2:8.6f}   {3:8.6f}   {4}'
    df_meas_list = []
    with session.initiate():
        session.wait_for_event(nidcpower.Event.SEQUENCE_ENGINE_DONE)
        for ivSweep in lstIVSweep:
            chnSweep = session.channels[ivSweep.sweep.resource]
            num = chnSweep.fetch_backlog
            measurements = fetch_multiple(chnSweep, chn=ivSweep.sweep.remarks, count=num, timeout=timeout)[:-1]
            df = pd.DataFrame(measurements)
            df_meas_list.append(df)

            for bias in ivSweep.biases:
                pretest_temp_list = []
                chnBias = session.channels[bias.resource]
                num = chnBias.fetch_backlog
                measurements = fetch_multiple(chnBias, chn=bias.remarks, count=num, timeout=timeout)[:-1]
                df = pd.DataFrame(measurements)

                df_meas_list.append(df)
        all_meas = pd.concat(df_meas_list, axis=1)
        all_meas.to_csv(CSV_name)

def runIVSweepsAmp(*lstIVSweep : IVSweep_amp, filename, left, right):
    resources: dict[tuple[str, int], IVSweep] = {}

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
    session.sense = nidcpower.Sense.REMOTE
    session.source_mode = nidcpower.SourceMode.SEQUENCE
    session.output_function = nidcpower.OutputFunction.DC_CURRENT
    session.current_level_autorange = True
    session.voltage_level = 0.0
    session.output_connected = True
    session.output_enabled = True

    for ivSweep in lstIVSweep:
        chnSweep = session.channels[ivSweep.sweep.resource]
        chnSweep.aperture_time = ivSweep.apertureTime
        # chnSweep.sense = nidcpower.Sense.REMOTE
        chnSweep.voltage_limit_range = ivSweep.sweep.V_compl
        chnSweep.voltage_limit       = ivSweep.sweep.V_compl

        I_start, I_stop, I_step = ivSweep.sweep.I_start, ivSweep.sweep.I_stop, ivSweep.sweep.I_step
        print(I_start)
        numStep = round((I_stop+I_step/2 - I_start)/I_step)+1
        tSteps = np.ones(numStep+1)
        iSteps = np.zeros(numStep+1)

        iSteps[:-1] = range(numStep*left, numStep*right)
        # iSteps[:-1] = range(numStep)
        iSteps *= I_step
        tSteps *= ivSweep.sourceDelay
        print(len(iSteps))
        print(len(tSteps))
        chnSweep.set_sequence(iSteps, tSteps)

        for bias in ivSweep.biases:
            chnBias = session.channels[bias.resource]
            chnBias.output_function = nidcpower.OutputFunction.DC_VOLTAGE
            chnBias.source_mode = nidcpower.SourceMode.SEQUENCE
            chnBias.aperture_time = ivSweep.apertureTime
            chnBias.measure_when = nidcpower.MeasureWhen.ON_MEASURE_TRIGGER
            chnBias.current_limit_range = bias.I_compl
            chnBias.current_limit       = bias.I_compl
            chnBias.voltage_level = bias.V_force
            vSteps = np.zeros(numStep+1)
            vSteps[:-1] = bias.V_force
            chnBias.set_sequence(vSteps, tSteps)

    timeout = hightime.timedelta(seconds=20)
    # print('Effective measurement rate: {0} S/s'.format(session.measure_record_delta_time / 1))

    print('Channel           Num  Voltage    Current    In Compliance')
    row_format = '{0:15} {1:3d}    {2:8.6f}   {3:8.12f}   {4}'
    session.commit()

    with session.initiate():
        lstSingleMeasurement = []
        lstAllMeasurements = []
        session.wait_for_event(nidcpower.Event.SEQUENCE_ENGINE_DONE)

        for ivSweep in lstIVSweep:
            chnSweep = session.channels[ivSweep.sweep.resource]
            num  = chnSweep.fetch_backlog
            measurements = chnSweep.fetch_multiple(num, timeout=timeout)[:-1]
            for i in range(len(measurements)):
                lstSingleMeasurement = [ivSweep.sweep.resource, measurements[i].voltage, measurements[i].current, measurements[i].in_compliance]

                lstAllMeasurements.append(lstSingleMeasurement)
                print(row_format.format(ivSweep.sweep.resource, i, measurements[i].voltage, measurements[i].current,
                                        measurements[i].in_compliance))


            for bias in ivSweep.biases:
                chnBias = session.channels[bias.resource]
                num  = chnBias.fetch_backlog
                measurements = chnBias.fetch_multiple(num, timeout=timeout)[:-1]
                for i in range(len(measurements)):
                    lstSingleMeasurement = [bias.resource, measurements[i].voltage, measurements[i].current,
                                            measurements[i].in_compliance]

                    lstAllMeasurements.append(lstSingleMeasurement)
                    print(row_format.format(bias.resource, i, measurements[i].voltage, measurements[i].current,
                                            measurements[i].in_compliance))
        print(lstAllMeasurements)
        df = pd.DataFrame(lstAllMeasurements, columns=['Resource', 'Voltage', 'current', 'in_compliance'], dtype=str)
        df.to_csv(filename, sep="delimiter")


def _test():
    with nidcpower.Session(resource_name="SMU1", reset=True, independent_channels=False) as session:
        # nidcpower.Session(resource_name="Dev2", reset=True, independent_channels=False) as session2:
        print('xxxx', session.instrument_model)
        # print('xxxx', session.channel_count)
        # print('xxxx', session.current_limit_range)
        #session.output_connected = False
        #session.output_enabled = False

    import datetime

   

    HQB1 = IVSweep(ChnVoltSweep('QB', 'SMU1/2', V_start=0.0, V_stop=1.5, V_step=0.05, I_compl=1e-3),
                   [ChnVoltBias('BLB', 'SMU1/3', 1.5, I_compl=1e-3),
                    ChnVoltBias('VSS', 'SMU1/4', 0, I_compl=1e-3),
                    ChnVoltBias('BL', 'SMU1/5', 1.5, I_compl=1e-3),
                    ChnVoltBias('Q', 'SMU1/6', 0, I_compl=1e-3, VoltSense=True, V_compl=3),
                    ChnVoltBias('WL', 'SMU1/7', 0, I_compl=1e-3),
                    ChnVoltBias('VDD', 'SMU1/8', 1.5, I_compl=1e-3),
                    ChnVoltBias('VDD12', 'SMU1/13', 1.5, I_compl=1e-3),
                    ChnVoltBias('VSS12', 'SMU1/14', 0, I_compl=1e-3),
                    ],
                   isMaster=True,
                   apertureTime=10e-3,
                   sourceDelay=5e-3,
                   )

    HQ = IVSweep(ChnVoltSweep('Q', 'SMU1/6', V_start=0.0, V_stop=1.5, V_step=0.05, I_compl=1e-3),
                   [ChnVoltBias('BLB', 'SMU1/3', 1.5, I_compl=1e-3),
                    ChnVoltBias('VSS', 'SMU1/4', 0, I_compl=1e-3),
                    ChnVoltBias('BL', 'SMU1/5', 1.5, I_compl=1e-3),
                    ChnVoltBias('QB', 'SMU1/2', 0, I_compl=1e-3, VoltSense=True, V_compl=3),
                    ChnVoltBias('WL', 'SMU1/7', 0, I_compl=1e-3),
                    ChnVoltBias('VDD', 'SMU1/8', 1.5, I_compl=1e-3),
                    ChnVoltBias('VDD12', 'SMU1/13', 1.5, I_compl=1e-3),
                    ChnVoltBias('VSS12', 'SMU1/14', 0, I_compl=1e-3),
                    ],
                   apertureTime=100e-3,
                   sourceDelay=5e-3,
                   )

    nbti1 = IVSweep(ChnVoltSweep('P33G', 'SMU1/12', V_start=3.3, V_stop=-3.3, V_step=-0.05, I_compl=20e-3),
                 [ChnVoltBias('Drain', 'SMU1/13', 0.1, I_compl=20e-3),
                  ChnVoltBias('Source', 'SMU1/14', 0, I_compl=20e-3),
                  ChnVoltBias('Bulk', 'SMU1/15', 0, I_compl=20e-3),

                  ],
                 apertureTime=1e-3,
                 sourceDelay=1e-3,
                 )
    nbti2 = IVSweep(ChnVoltSweep('P33GatePLR_HCI_2', 'SMU1/12', V_start=-3.3, V_stop=3.3, V_step=0.05, I_compl=20e-3),
                   [ChnVoltBias('Drain', 'SMU1/13', 0.1, I_compl=20e-3),
                    ChnVoltBias('Source', 'SMU1/14', 0, I_compl=20e-3),
                    ChnVoltBias('Bulk', 'SMU1/15', 0, I_compl=20e-3),

                    ],
                   apertureTime=1e-3,
                   sourceDelay=1e-3,
                   )

    RO11 = IVSweep(ChnVoltSweep('P15G', 'SMU1/12', V_start=-1.5, V_stop=1.5, V_step=0.05, I_compl=1e-3),
                  [ChnVoltBias('Drain', 'SMU1/13', 0.1, I_compl=1e-3),
                   ChnVoltBias('Source', 'SMU1/14', 0, I_compl=1e-3),
                   ChnVoltBias('Bulk', 'SMU1/15', 0, I_compl=1e-3),

                   ],
                  apertureTime=1e-3,
                  sourceDelay=1e-3,
                  )

    RO2 = IVSweep(ChnVoltSweep('VDD_SPICE_RO_1_pad17', 'SMU1/17', V_start=0.0, V_stop=1.5, V_step=0.05, I_compl=10e-3),
                  [ChnVoltBias('VSS_SPICE_RO_1_pad19', 'SMU1/18', 0, I_compl=10e-3),
                   ],
                  apertureTime=100e-3,
                  sourceDelay=1e-3,
                  )

    RO3 = IVSweep(ChnVoltSweep('DVDD_SPICE_RO_9_pad5', 'SMU1/4', V_start=0.0, V_stop=1.5, V_step=0.05, I_compl=10e-3),
                  [ChnVoltBias('VSS_SPICE_RO_9_pad4', 'SMU1/3', 0, I_compl=10e-3),
                   ],

                  apertureTime=100e-3,
                  sourceDelay=1e-3,
                  )
    RO4 = IVSweep(ChnVoltSweep('VDD_SPICE_RO_9_pad3', 'SMU2/0', V_start=0.0, V_stop=1.5, V_step=0.05, I_compl=10e-3),
                  [ChnVoltBias('VSS_SPICE_RO_9_pad4', 'SMU3/0', 0, I_compl=10e-3),
                   ],
                  apertureTime=100e-3,
                  sourceDelay=1e-3,
                  )
    HQB_csv = "HQB_A2E049_2_3_SRAM_TK3_2.csv"
    HQ_csv = "HQ_A2E049_2_3_SRAM_TK3.csv"
    # runIVSweeps(HQB1, CSV_name=HQB_csv)
    runIVSweeps(RO4, CSV_name=HQ_csv)
    NBTI = "A2E049_w4_NBTI_PLR_HCI_4_die_0_0_Lg0p3.csv"
    # runIVSweeps(nbti1, CSV_name=NBTI)
    # runIVSweeps(nbti2, CSV_name=NBTI)
    # runIVSweeps(RO2, CSV_name=RO2csv)
    # runIVSweeps(RO3, CSV_name=RO3csv)
    # runIVSweeps(RO4, CSV_name=RO4csv)
    # iv11 = IVSweep_amp(ChnCurrentSweep('Dev1/0', I_start=1000e-12, I_stop=1500e-12, I_step=5e-12, V_compl=5), [ChnVoltBias('Dev2/0', 0, I_compl=5e-6, GND=True)])

    # tddb1_2_3 = TDDB("nmos10000_1_2_3_PLR_TDDB_1", chnGATE('SMU1/0', V_start=0, V_stop=-2.5, V_step=-0.1, V_force_stress=-3.06, V_force_SILC=-2.5),
    #                  [ChnVoltBias('SMU1/1', V_force=0), ChnVoltBias('SMU1/2', V_force=0)])
    # tddb4_5_6 = TDDB('nmos10000_4_5_6_PLR_TDDB_1', chnGATE('SMU1/3', V_start=0, V_stop=-2.5, V_step=-0.1, V_force_stress=-3.06, V_force_SILC=-2.5),
    #                  [ChnVoltBias('SMU1/4', V_force=0), ChnVoltBias('SMU1/5', V_force=0)])
    # tddb7_8_9 = TDDB('pmos400_7_8_9_PLR_TDDB_2',
    #                  chnGATE('SMU1/6', V_start=0, V_stop=2.5, V_step=0.1, V_force_stress=3.3, V_force_SILC=2.5),
    #                  [ChnVoltBias('SMU1/7', V_force=0), ChnVoltBias('SMU1/8', V_force=0)])
    # tddb10_11_12 = TDDB('pmos400_10_11_12_PLR_TDDB_2',
    #                  chnGATE('SMU1/9', V_start=0, V_stop=2.5, V_step=0.1, V_force_stress=3.4, V_force_SILC=2.5),
    #                  [ChnVoltBias('SMU1/10', V_force=0), ChnVoltBias('SMU1/11', V_force=0)])
    # tddb_13_14_15 = TDDB('nmos10000_13_14_15_PLR_TDDB_2',
    #               chnGATE('SMU1/12', V_start=0, V_stop=-4.5, V_step=-0.1, V_force_stress=-8.0, V_force_SILC=-4.5),
    #               [ChnVoltBias('SMU1/13', V_force=0), ChnVoltBias('SMU1/14', V_force=0)])
    # tddb_16_17_18 = TDDB("nmos10000_16_17_18_PLR_TDDB_2",
    #               chnGATE('SMU1/15', V_start=0, V_stop=-4.5, V_step=-0.1, V_force_stress=-7.9, V_force_SILC=-4.5),
    #               [ChnVoltBias('SMU1/16', V_force=0), ChnVoltBias('SMU1/17', V_force=0)])
    # tddb_19_20_21 = TDDB("pmos10000_19_20_21_PLR_TDDB_1",
    #                      chnGATE('SMU1/18', V_start=0, V_stop=2.5, V_step=0.1, V_force_stress=3.1,
    #                              V_force_SILC=2.5),
    #                      [ChnVoltBias('SMU1/19', V_force=0), ChnVoltBias('SMU1/20', V_force=0)])
    # em1 = TDDB("iforce",chnGATE('SMU1/2', I_start=0, I_stop=10e-6, I_step=10e-6, I_force_stress=10e-6,
    #                              V_force_SILC=2.5),
    #                      [ChnVoltBias('monitor','SMU1/8', V_force=0)])
    # #
    # runTimmingAmp(em1, CSV_name="10ua-250.csv")
    t1 = datetime.datetime.now()
    # print(f'elapased time {(t1-t0).total_seconds()*1000}ms.')




_test()
