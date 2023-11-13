import attrs
import nidcpower
from openpyxl import load_workbook, Workbook
import pandas as pd
from config import wiring
import numpy as np
import hightime
import time
import csv
# -*- coding: utf-8 -*-
# This file was generated
import array  # noqa: F401
# Used by @ivi_synchronized
from functools import wraps

import nidcpower._attributes as _attributes
import nidcpower._converters as _converters
import nidcpower._library_interpreter as _library_interpreter
import nidcpower.enums as enums
import nidcpower.errors as errors

import nidcpower.lcr_load_compensation_spot as lcr_load_compensation_spot  # noqa: F401

import nidcpower.lcr_measurement as lcr_measurement  # noqa: F401

import hightime



def fetch_multiple(self, description, count, timeout=hightime.timedelta(seconds=1.0)):
        '''fetch_multiple

        Returns a list of named tuples (Measurement) that were
        previously taken and are stored in the NI-DCPower buffer. This method
        should not be used when the measure_when property is
        set to MeasureWhen.ON_DEMAND. You must first call
        initiate before calling this method.

        Fields in Measurement:

        - **voltage** (float)
        - **current** (float)
        - **in_compliance** (bool)
        - **channel** (str)

        Note:
        This method is not supported on all devices. For more information about supported devices, search ni.com for Supported Methods by Device.

        Tip:
        This method can be called on specific channels within your :py:class:`nidcpower.Session` instance.
        Use Python index notation on the repeated capabilities container channels to specify a subset,
        and then call this method on the result.

        Example: :py:meth:`my_session.channels[ ... ].fetch_multiple`

        To call the method on all channels, you can call it directly on the :py:class:`nidcpower.Session`.

        Example: :py:meth:`my_session.fetch_multiple`

        Args:
            count (int): Specifies the number of measurements to fetch.

            timeout (hightime.timedelta, datetime.timedelta, or float in seconds): Specifies the maximum time allowed for this method to complete. If the method does not complete within this time interval, NI-DCPower returns an error.
                Default value: 1.0 second

                Note: When setting the timeout interval, ensure you take into account any triggers so that the timeout interval is long enough for your application.


        Returns:
            measurements (list of Measurement): List of named tuples with fields:

                - **voltage** (float)
                - **current** (float)
                - **in_compliance** (bool)
                - **channel** (str)

        '''
        import collections
        Measurement = collections.namedtuple('Measurement', ['Description', 'voltage', 'current', 'in_compliance', 'channel'])

        voltage_measurements, current_measurements, in_compliances = self._fetch_multiple(timeout, count)

        channel_names = _converters.expand_channel_string(
            self._repeated_capability,
            self._all_channels_in_session
        )
        assert len(channel_names) == 1, "fetch_multiple only supports one channel at a time"
        return [
            Measurement(
                description,
                voltage=voltage,
                current=current,
                in_compliance=in_compliance,
                channel=channel_names[0]
            ) for voltage, current, in_compliance in zip(
                
                voltage_measurements, current_measurements, in_compliances
            )
        ]
@attrs.define
class chnVoltBias:
    description     : str
    resource        : str
    V_force         : str
    I_compl         : str = attrs.field(
        default=1e-3,
        kw_only=True,
    )
    VoltSense       : bool = attrs.field(
        default=False,
        kw_only=True,
    )
    V_compl         : float = attrs.field(
        default=3,
        kw_only=True,
    )
    I_force         : float = attrs.field(
        default=0,
        kw_only=True,
    )


class HCIstress:
    resource: str
    dieCoord: str
    tileName: str
    chnStress: str
    biases: list[chnVoltBias] = attrs.field(
        validator=attrs.validators.deep_iterable(member_validator=attrs.validators.instance_of((chnVoltBias)))
    )

    sourceDelay: float = attrs.field(
        default=1e-3,
        kw_only=True,
    )

    apertureTime: float = attrs.field(
        default=1e-3,
        kw_only=True,
    )

@attrs.define
class CurrentLimit:
    low_level = attrs.field(
        default=10e-6,
        kw_only=True,
    )
    high_level = attrs.field(
        default=1e-3,
        kw_only=True,
    )

@attrs.define
class CurrentLimitRange:
    low_level = attrs.field(
        default=100e-9,
        kw_only=True,
    )
    high_level = attrs.field(
        default=30e-3,
        kw_only=True,
    )


@attrs.define
class Resource:
    device: str
    GATE : list
    DRAIN: list
    SOURCE: list
    BULK: list

@attrs.define
class VtlinSweep:
    resource: Resource
    V_force_D: float
    V_force_S: float
    V_force_B: float
    I_compl_G: float
    I_compl_D: float
    I_compl_S: float
    I_compl_B: float
    V_step_G: float
    V_start_G: float
    V_stop_G: float
    # CurrentLimit: CurrentLimit
    # CurrentLimitRange: CurrentLimitRange
    sourceDelay: float = attrs.field(
        default=1e-3,
        kw_only=True,
    )
    apertureTime: float = attrs.field(
        default=1e-3,
        kw_only=True,
    )




@attrs.define
class VtSatSweep:
    resource: Resource
    V_force_D: float
    V_force_S: float
    V_force_B: float
    I_compl_G: float
    I_compl_D: float
    I_compl_S: float
    I_compl_B: float
    V_step_G: float
    V_start_G: float
    V_stop_G: float
    CurrentLimit: CurrentLimit               =  attrs.field(
        default=CurrentLimit(),
        kw_only=True,
    )

    CurrentLimitRange: CurrentLimitRange     = attrs.field(
        default=CurrentLimitRange(),
        kw_only=True,
    )


@attrs.define
class IbMaxSweep:
    resource: Resource
    V_force_D: float
    V_force_S: float
    V_force_B: float
    V_force_G: float
    I_compl_G: float
    I_compl_D: float
    I_compl_S: float
    I_compl_B: float
    V_step_G: float
    V_start_G: float
    V_stop_G: float
    CurrentLimit: CurrentLimit               =  attrs.field(
        default=CurrentLimit(),
        kw_only=True,
    )

    CurrentLimitRange: CurrentLimitRange     = attrs.field(
        default=CurrentLimitRange(),
        kw_only=True,
    )



@attrs.define
class HCIsweep:
    resource: Resource
    description: str
    Vtlin: VtlinSweep
    VtSat: VtSatSweep
    IbMax: IbMaxSweep


    dieCoord: str = attrs.field(
        default='A1',
        kw_only=True,
    )

    tileName: str = attrs.field(
        default='A1',
        kw_only=True,
    )


def dumpExceltoPython(testplan, sitesNum):
    wb = load_workbook(filename=testplan)
    ws = wb.active
    dDut, dHCItest, dTest_Vtlin, dTest_VtSat, dTest_IbMAX, dResource = {}, {}, {}, {}, {}, {}
    header = []
    rows_buf = []
    count = 0
    for row in ws.iter_rows(min_row=None, max_col=None, max_row=None, values_only=True):
        if count == 0:
            header = row
            # print(header)
        else:
            rows_buf.append(row)
        count += 1
    df_plan = pd.DataFrame(rows_buf, columns=header)
    norepeat_df_plan = df_plan.drop_duplicates(subset=[' dut.name']).reset_index()
    # count_1 = 0
    sDuts = set()

    # Get all the DUTs and resources
    count = 0
    for dut in norepeat_df_plan.loc[:, ' dut.name']:
        # print(norepeat_df_plan.loc[:, ' dut.pads[G]'])
        padGATE = norepeat_df_plan.loc[count, ' dut.pads[G]']
        # print(f'Gate is {padGATE}')
        padDRAIN = norepeat_df_plan.loc[count, ' dut.pads[D]']
        padSOURCE = norepeat_df_plan.loc[count, ' dut.pads[S]']
        padBULK = norepeat_df_plan.loc[count, ' dut.pads[B]']
        GATE = [f'{wiring[(padGATE-1)+24*i][1][0][wiring[(padGATE-1)+24*i][1][1]]}/{wiring[(padGATE-1)+24*i][1][2]}' for i in range(sitesNum)]
        DRAIN  = [f'{wiring[(padDRAIN-1)+24*i][1][0][wiring[(padDRAIN-1)+24*i][1][1]]}/{wiring[(padDRAIN-1)+24*i][1][2]}' for i in range(sitesNum)]
        SOURCE = [f'{wiring[(padSOURCE-1)+24*i][1][0][wiring[(padSOURCE-1)+24*i][1][1]]}/{wiring[(padSOURCE-1)+24*i][1][2]}' for i in range(sitesNum)]
        BULK = [f'{wiring[(padBULK-1)+24*i][1][0][wiring[(padBULK-1)+24*i][1][1]]}/{wiring[(padBULK-1)+24*i][1][2]}' for i in range(sitesNum)]
        dResource[dut] = Resource(dut, GATE, DRAIN, SOURCE, BULK)
        sDuts.add(dut)
        count += 1
    # print(dResource)

    count = 0
    for c in df_plan.loc[:, 'fullname']:
        dut = df_plan.loc[count, ' dut.name']
        if 'Vtlin' in c:
            vForceD = df_plan.loc[count,  ' test.V_force_D']
            vForceS = df_plan.loc[count,  ' test.V_force_S']
            vForceB = df_plan.loc[count,  ' test.V_force_B']
            vStartG = df_plan.loc[count,  ' test.V_start_G']
            vStopG = df_plan.loc[count,  ' test.V_stop_G']
            vStepG = df_plan.loc[count,  ' test.V_step_G'] 
            iComplG = df_plan.loc[count,  ' test.I_compl_G']
            iComplD = df_plan.loc[count,  ' test.I_compl_D']
            iComplS = df_plan.loc[count,  ' test.I_compl_S']
            iComplB = df_plan.loc[count,  ' test.I_compl_B']
            dTest_Vtlin[dut] = VtlinSweep(dResource[dut], vForceD, vForceS, vForceB, iComplG, iComplD, iComplS, iComplB, vStepG, vStartG, vStopG)
        elif 'Vtsat' in c:
            vForceD = df_plan.loc[count,  ' test.V_force_D']
            vForceS = df_plan.loc[count,  ' test.V_force_S']
            vForceB = df_plan.loc[count,  ' test.V_force_B']
            vStartG = df_plan.loc[count,  ' test.V_start_G']
            vStopG = df_plan.loc[count,  ' test.V_stop_G']
            vStepG = df_plan.loc[count,  ' test.V_step_G'] 
            iComplG = df_plan.loc[count,  ' test.I_compl_G']
            iComplD = df_plan.loc[count,  ' test.I_compl_D']
            iComplS = df_plan.loc[count,  ' test.I_compl_S']
            iComplB = df_plan.loc[count,  ' test.I_compl_B']
            dTest_VtSat[dut] = VtSatSweep(dResource[dut], vForceD, vForceS, vForceB, iComplG, iComplD, iComplS, iComplB, vStepG, vStartG, vStopG)
        elif 'Ibmax' in c:
            vForceD = df_plan.loc[count,  ' test.V_force_D'] # stress Drain voltage
            vForceS = df_plan.loc[count,  ' test.V_force_S']
            vForceB = df_plan.loc[count,  ' test.V_force_B']
            vStartG = df_plan.loc[count,  ' test.V_start_G']
            vStopG = df_plan.loc[count,  ' test.V_stop_G']
            vStepG = df_plan.loc[count,  ' test.V_step_G']
            vForceG = df_plan.loc[count,  ' test.V_force_G'] # stress Gate voltage
            iComplG = df_plan.loc[count,  ' test.I_compl_G']
            iComplD = df_plan.loc[count,  ' test.I_compl_D']
            iComplS = df_plan.loc[count,  ' test.I_compl_S']
            iComplB = df_plan.loc[count,  ' test.I_compl_B']
            dTest_IbMAX[dut] = IbMaxSweep(dResource[dut], vForceD, vForceS, vForceB, iComplG, iComplD, iComplS, iComplB, iComplG, vStepG, vStartG, vStopG)
        # print(dTest[c])
        count += 1

    # print("hahha")
    for dut in sDuts:
        resource = dResource[dut]
        Vtlin = dTest_Vtlin[dut]
        VtSat = dTest_VtSat[dut]
        Ibmax = dTest_IbMAX[dut]
        dHCItest[dut] = HCIsweep(dResource[dut], dut, dTest_Vtlin[dut], dTest_VtSat[dut], dTest_IbMAX[dut])
    return dHCItest

from funcs.generateStressTiming import generateInterval
class HCItest:
    

    def __init__(self, testplan, sitesNum):
        self.dHCItest = dumpExceltoPython(testplan, sitesNum=sitesNum)
        self.current_limit = CurrentLimit()
        self.current_limit_range = CurrentLimitRange()
        self.sess = None
        self.stressInterval = generateInterval(10000)
        
    def populate():
        wb = Workbook()    
        ws = wb.active
        ws['A1'] = 42
        ws.append([1, 2, 3])
        import datetime
        ws['A2'] = datetime.datetime.now()
        wb.save('sample.xlsx')

    def runHCI(self):
        pass

    # do voltage stress
    def runStress(self, interval):
        
        self.sess.abort()
        self.sess.active_advanced_sequence = ''
        self.sess.source_mode = nidcpower.SourceMode.SINGLE_POINT
        self.sess.voltage_level_autorange = True
        self.sess.current_limit_autorange = True
        self.sess.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        self.sess.voltage_level = 0
        self.sess.current_limit = 1e-3
        self.sess.output_connected = False
        self.sess.output_enabled = False
        self.sess.measure_when = nidcpower.MeasureWhen.ON_DEMAND
        self.sess.aperture_time = 1e-6
        self.sess.source_delay = 1e-3

        for dut in self.dHCItest:
            chnGate = self.sess.channels[','.join(self.dHCItest[dut].Vtlin.resource.GATE)]
            chnDrain = self.sess.channels[','.join(self.dHCItest[dut].Vtlin.resource.DRAIN)]
            chnSource = self.sess.channels[','.join(self.dHCItest[dut].Vtlin.resource.SOURCE)]
            chnBulk = self.sess.channels[','.join(self.dHCItest[dut].Vtlin.resource.BULK)]

            vStressD = self.dHCItest[dut].IbMax.V_force_D
            vStressS = self.dHCItest[dut].IbMax.V_force_S
            vStressG = self.dHCItest[dut].IbMax.V_force_G
            vStressB = self.dHCItest[dut].IbMax.V_force_B

            iComplD = self.dHCItest[dut].IbMax.I_compl_D
            iComplS = self.dHCItest[dut].IbMax.I_compl_S
            iComplG = self.dHCItest[dut].IbMax.I_compl_G
            iComplB = self.dHCItest[dut].IbMax.I_compl_B

            chnGate.voltage_level = vStressG
            chnDrain.voltage_level = 0 # JEDEC told me that it's a good practice to apply gate voltage first
            chnSource.voltage_level = vStressS
            chnBulk.voltage_level = vStressB
            
            
            for chn in [chnGate, chnDrain, chnSource, chnBulk]:
                # turn on all channels we need
                chn.output_enabled = True
                chn.output_connected = True 
                # measure current on demand
                chn.measure_when = nidcpower.MeasureWhen.ON_DEMAND

            self.sess.commit()
            
        with self.sess.initiate():
            timeout = hightime.timedelta(seconds=(10))
            t_begin = hightime.timedelta(seconds=(time.time()))
            while hightime.timedelta(seconds=(time.time())) - t_begin < interval:
                time.sleep(0.1)
                self.sess.wait_for_event(nidcpower.Event.SOURCE_COMPLETE, timeout=timeout)
                measurements = self.sess.measure_multiple()
                # with 
                # print(measurements)
            else:
                self.sess.abort()
                self.sess.output_enabled = False
                self.sess.output_connected = False



                
                
            







    # would it be fine if we dump all channels of 4163 into a self.session and we then open the relays we don't need?
    def common_settings(self):
        self.sess = nidcpower.Session(resource_name='SMU1', reset=True,  options = {'simulate': True, 'driver_setup': {'Model': '4163', 'BoardType': 'PXIe', }, })
        # print(self.sess.channels['SMU1/0,SMU1/1'])
        self.sess.voltage_level_autorange = True
        self.sess.current_limit_autorange = True
        self.sess.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        self.sess.voltage_level = 0
        self.sess.current_limit = 1e-3
        self.sess.source_mode = nidcpower.SourceMode.SEQUENCE
        self.sess.output_connected = False # turn off all channels 
        self.sess.output_enabled = False
        self.sess.autorange = True
        self.sess.autorange_aperture_time_mode = nidcpower.AutorangeApertureTimeMode.AUTO
        # self.sess.sequence_step_delta_time_enabled = True # not supported in 4163
        
        return self.sess


    def _constructVtlinSweeptest(self):
        self.sess.abort()
        # self.sess = self.common_settings()
        strChnGate = ''
        strChnDrain = ''
        strChnSource = ''
        strChnBulk = ''
        dSteps = {}
        dStepsForALLduts_GATE = {}
        dStepsForALLduts_DRAIN = {}
        dStepsForALLduts_SOURCE = {}
        dStepsForALLduts_BULK = {}
        
        # self.sess.create_advanced_sequence_step(set_as_active_step=True)

        max_length = 0
        for dut in self.dHCItest:
            
            vStart, vStop, vStep = self.dHCItest[dut].Vtlin.V_start_G, self.dHCItest[dut].Vtlin.V_stop_G, self.dHCItest[dut].Vtlin.V_step_G
            numStep = round((vStop+vStep/2 - vStart)/vStep)+1
            container = np.ones(numStep+1)
            vSteps = np.linspace(vStart, vStop, numStep)
            if max_length < len(vSteps):
                max_length = len(vSteps)
            dStepsForALLduts_GATE[dut] = vSteps
            # print(dStepsForALLduts_GATE[dut])
            dStepsForALLduts_DRAIN[dut] =  container * self.dHCItest[dut].Vtlin.V_force_D
            dStepsForALLduts_SOURCE[dut] = container * self.dHCItest[dut].Vtlin.V_force_S
            dStepsForALLduts_BULK[dut] = container * self.dHCItest[dut].Vtlin.V_force_B
            # print(dStepsForALLduts_GATE[dut])
        
        # stuff zero to the end of the shorter ones
        for dut in self.dHCItest:
            if len(dStepsForALLduts_GATE[dut]) < max_length:
                dStepsForALLduts_GATE[dut] = np.append(dStepsForALLduts_GATE[dut], np.zeros(max_length-len(dStepsForALLduts_GATE[dut])))
                dStepsForALLduts_DRAIN[dut] = np.append(dStepsForALLduts_DRAIN[dut], np.zeros(max_length-len(dStepsForALLduts_DRAIN[dut])))
                dStepsForALLduts_SOURCE[dut] = np.append(dStepsForALLduts_SOURCE[dut], np.zeros(max_length-len(dStepsForALLduts_SOURCE[dut])))
                dStepsForALLduts_BULK[dut] = np.append(dStepsForALLduts_BULK[dut], np.zeros(max_length-len(dStepsForALLduts_BULK[dut])))

            # print(dStepsForALLduts_GATE[dut])
            # print(dStepsForALLduts_GATE[dut])


        #step
        # print(max_length)
        properties_used = ['output_enabled', 'output_function', 'voltage_level', 'current_limit']
        self.sess.create_advanced_sequence(sequence_name='VtlinSweep', set_as_active_sequence=True, property_names=properties_used)
        for i in range(max_length):
            self.sess.create_advanced_sequence_step(set_as_active_step=True)
            for dut in self.dHCItest:
                chnGate = self.sess.channels[','.join(self.dHCItest[dut].Vtlin.resource.GATE)]
                chnDrain = self.sess.channels[','.join(self.dHCItest[dut].Vtlin.resource.DRAIN)]
                chnSource = self.sess.channels[','.join(self.dHCItest[dut].Vtlin.resource.SOURCE)]
                chnBulk = self.sess.channels[','.join(self.dHCItest[dut].Vtlin.resource.BULK)]

                chnGate.voltage_level = dStepsForALLduts_GATE[dut][i]
                chnDrain.voltage_level = dStepsForALLduts_DRAIN[dut][i]
                chnSource.voltage_level = dStepsForALLduts_SOURCE[dut][i]
                chnBulk.voltage_level = dStepsForALLduts_BULK[dut][i]
                # print(dStepsForALLduts_GATE[dut][i])
                chnGate.output_enabled = True
                chnDrain.output_enabled = True
                chnSource.output_enabled = True
                chnBulk.output_enabled = True
                # chnGate.output_connected = True
                # chnDrain.output_connected = True
                # chnSource.output_connected = True
                # chnBulk.output_connected = True
                chnGate.output_function = nidcpower.OutputFunction.DC_VOLTAGE
                chnDrain.output_function = nidcpower.OutputFunction.DC_VOLTAGE
                chnSource.output_function = nidcpower.OutputFunction.DC_VOLTAGE
                chnBulk.output_function = nidcpower.OutputFunction.DC_VOLTAGE
                chnBulk.current_limit = self.current_limit.high_level
                chnSource.current_limit = self.current_limit.high_level
                chnDrain.current_limit = self.current_limit.high_level
                chnGate.current_limit = self.current_limit.low_level
                chnBulk.current_limit_range = self.current_limit_range.high_level
                chnSource.current_limit_range = self.current_limit_range.high_level
                chnDrain.current_limit_range = self.current_limit_range.high_level
                chnGate.current_limit_range = self.current_limit_range.low_level
                # chnBulk.current_limit_autorange = True
                # chnSource.current_limit_autorange = True
                # chnDrain.current_limit_autorange = True
                # chnGate.current_limit_autorange = True
        # self.sess.commit()
        



    def _constructVtSatSweeptest(self, **HCI):
        self.sess.abort()
        # self.sess = self.common_settings()
        strChnGate = ''
        strChnDrain = ''
        strChnSource = ''
        strChnBulk = ''
        dSteps = {}
        dStepsForALLduts_GATE = {}
        dStepsForALLduts_DRAIN = {}
        dStepsForALLduts_SOURCE = {}
        dStepsForALLduts_BULK = {}
        properties_used = ['output_enabled', 'output_function', 'voltage_level', 'current_limit']
        self.sess.create_advanced_sequence(sequence_name='VtsatSweep', set_as_active_sequence=True, property_names=properties_used)
        # self.sess.create_advanced_sequence_step(set_as_active_step=True)

        max_length = 0
        for dut in self.dHCItest:
            
            vStart, vStop, vStep = self.dHCItest[dut].VtSat.V_start_G, self.dHCItest[dut].VtSat.V_stop_G, self.dHCItest[dut].VtSat.V_step_G
            numStep = round((vStop+vStep/2 - vStart)/vStep)+1
            container = np.ones(numStep+1)
            vSteps = np.linspace(vStart, vStop, numStep)
            if max_length < len(vSteps):
                max_length = len(vSteps)
            dStepsForALLduts_GATE[dut] = vSteps
            # print(dStepsForALLduts_GATE[dut])
            dStepsForALLduts_DRAIN[dut] =  container * self.dHCItest[dut].VtSat.V_force_D
            dStepsForALLduts_SOURCE[dut] = container * self.dHCItest[dut].VtSat.V_force_S
            dStepsForALLduts_BULK[dut] = container * self.dHCItest[dut].VtSat.V_force_B
            # print(dStepsForALLduts_GATE[dut])
        
        # stuff zero to the end of the shorter ones
        for dut in self.dHCItest:
            if len(dStepsForALLduts_GATE[dut]) < max_length:
                dStepsForALLduts_GATE[dut] = np.append(dStepsForALLduts_GATE[dut], np.zeros(max_length-len(dStepsForALLduts_GATE[dut])))
                dStepsForALLduts_DRAIN[dut] = np.append(dStepsForALLduts_DRAIN[dut], np.zeros(max_length-len(dStepsForALLduts_DRAIN[dut])))
                dStepsForALLduts_SOURCE[dut] = np.append(dStepsForALLduts_SOURCE[dut], np.zeros(max_length-len(dStepsForALLduts_SOURCE[dut])))
                dStepsForALLduts_BULK[dut] = np.append(dStepsForALLduts_BULK[dut], np.zeros(max_length-len(dStepsForALLduts_BULK[dut])))

            # print(dStepsForALLduts_GATE[dut])
            # print(dStepsForALLduts_GATE[dut])


        #step
        # print(max_length)
        for i in range(max_length):
            self.sess.create_advanced_sequence_step(set_as_active_step=True)
            for dut in self.dHCItest:
                chnGate = self.sess.channels[','.join(self.dHCItest[dut].VtSat.resource.GATE)]
                chnDrain = self.sess.channels[','.join(self.dHCItest[dut].VtSat.resource.DRAIN)]
                chnSource = self.sess.channels[','.join(self.dHCItest[dut].VtSat.resource.SOURCE)]
                chnBulk = self.sess.channels[','.join(self.dHCItest[dut].VtSat.resource.BULK)]
                
                chnGate.voltage_level = dStepsForALLduts_GATE[dut][i]
                chnDrain.voltage_level = dStepsForALLduts_DRAIN[dut][i]
                chnSource.voltage_level = dStepsForALLduts_SOURCE[dut][i]
                chnBulk.voltage_level = dStepsForALLduts_BULK[dut][i]
                for chns in [chnGate, chnBulk, chnSource, chnDrain]:
                    chns.output_function = nidcpower.OutputFunction.DC_VOLTAGE
                    chns.current_limit = self.current_limit.high_level
                    chns.current_limit_autorange = True
                    chns.output_enabled = True

        self.sess.commit()


    def _constructIbMAXSweeptest(self, **HCI):
        self.sess.abort()
        strChnGate = ''
        strChnDrain = ''
        strChnSource = ''
        strChnBulk = ''
        dSteps = {}
        dStepsForALLduts_GATE = {}
        dStepsForALLduts_DRAIN = {}
        dStepsForALLduts_SOURCE = {}
        dStepsForALLduts_BULK = {}
        properties_used = ['output_enabled', 'output_function', 'voltage_level']
        
        self.sess.create_advanced_sequence(sequence_name='IbMAXSweep', set_as_active_sequence=True, property_names=properties_used)
        # self.sess.create_advanced_sequence_step(set_as_active_step=True)

        for dut in self.dHCItest:
            vStart, vStop, vStep = self.dHCItest[dut].IbMax.V_start_G, self.dHCItest[dut].IbMax.V_stop_G, self.dHCItest[dut].IbMax.V_step_G
            numStep = round((vStop+vStep/2 - vStart)/vStep)+1
            container = np.ones(numStep+1)
            vSteps = np.linspace(vStart, vStop, numStep)
            dStepsForALLduts_GATE[dut] = vSteps
            dStepsForALLduts_DRAIN[dut] =  container * self.dHCItest[dut].IbMax.V_force_D
            dStepsForALLduts_SOURCE[dut] = container * self.dHCItest[dut].IbMax.V_force_S
            dStepsForALLduts_BULK[dut] = container * self.dHCItest[dut].IbMax.V_force_B
            # print(dStepsForALLduts_GATE[dut])
        

        
        for i in range(len(dStepsForALLduts_GATE)):
            self.sess.create_advanced_sequence_step(set_as_active_step=True)
            for dut in self.dHCItest:
                chnGate = self.sess.channels[','.join(self.dHCItest[dut].IbMax.resource.GATE)]
                chnDrain = self.sess.channels[','.join(self.dHCItest[dut].IbMax.resource.DRAIN)]
                chnSource = self.sess.channels[','.join(self.dHCItest[dut].IbMax.resource.SOURCE)]
                chnBulk = self.sess.channels[','.join(self.dHCItest[dut].IbMax.resource.BULK)]
                chnGate.voltage_level = dStepsForALLduts_GATE[dut][i]
                chnDrain.voltage_level = dStepsForALLduts_DRAIN[dut][i]
                chnSource.voltage_level = dStepsForALLduts_SOURCE[dut][i]
                chnBulk.voltage_level = dStepsForALLduts_BULK[dut][i]
                chnGate.output_enabled = True
                chnDrain.output_enabled = True
                chnSource.output_enabled = True
                chnBulk.output_enabled = True
                chnGate.output_function = nidcpower.OutputFunction.DC_VOLTAGE
                chnDrain.output_function = nidcpower.OutputFunction.DC_VOLTAGE
                chnSource.output_function = nidcpower.OutputFunction.DC_VOLTAGE
                chnBulk.output_function = nidcpower.OutputFunction.DC_VOLTAGE
                chnBulk.current_limit = self.current_limit.high_level
                chnSource.current_limit = self.current_limit.high_level
                chnDrain.current_limit = self.current_limit.high_level
                chnGate.current_limit = self.current_limit.low_level
                chnBulk.current_limit_autorange = True
                chnSource.current_limit_autorange = True
                chnDrain.current_limit_autorange = True
                chnGate.current_limit_autorange = True
        
        self.sess.commit()


    def write_results(self):
        pass

    def prepareForSequenceMode(self):
        self.sess.abort()
        self.sess.source_mode = nidcpower.SourceMode.SEQUENCE
        self.sess.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
        

    def populate(self):
        pass

    def runVtlin(self):
        self.sess.source_mode = nidcpower.SourceMode.SEQUENCE
        self.sess.active_advanced_sequence = 'VtlinSweep'
        
        with self.sess.initiate():
            self.sess.wait_for_event(nidcpower.Event.SEQUENCE_ENGINE_DONE, timeout=100.0)
            for dut in self.dHCItest:
                lst_meas_drain = []
                lst_meas_source = []
                lst_meas_bulk = []
                lst_meas_gate = []
                for drain in self.dHCItest[dut].Vtlin.resource.DRAIN:
                    chnDrain = self.sess.channels[drain]
                    num = chnDrain.fetch_backlog
                    descrip = f"Drain_{dut}"
                    meas_drain = fetch_multiple(chnDrain,descrip, count=num, timeout=100.0) 
                    lst_meas_drain.append(meas_drain) 

                for source in self.dHCItest[dut].Vtlin.resource.SOURCE:
                    chnSource = self.sess.channels[source]
                    num = chnSource.fetch_backlog
                    descrip = f"Source_{dut}"
                    meas_source = fetch_multiple(chnSource,descrip, count=num, timeout=100.0)
                    lst_meas_source.append(meas_source)

                for bulk in self.dHCItest[dut].Vtlin.resource.BULK:
                    chnBulk = self.sess.channels[bulk]
                    num = chnBulk.fetch_backlog
                    descrip = f"Bulk_{dut}"
                    meas_bulk = fetch_multiple(chnBulk,descrip, count=num, timeout=100.0)
                    lst_meas_bulk.append(meas_bulk)

                for gate in self.dHCItest[dut].Vtlin.resource.GATE:
                    chnGate = self.sess.channels[gate]
                    num = chnGate.fetch_backlog
                    descrip = f"Gate_{dut}"
                    meas_gate = fetch_multiple(chnGate,descrip, count=num, timeout=100.0)
                    lst_meas_gate.append(meas_gate)

                csv_file_path = f'{dut}_Vth.csv'
                with open(csv_file_path, mode='a', newline='') as csv_file:
                    fieldnames = ['Description', 'voltage', 'current', 'in_compliance', 'channel']
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    writer.writeheader()

                meas_dict = {
                    'Drain': lst_meas_drain,
                    'Source': lst_meas_source,
                    'Bulk': lst_meas_bulk,
                    'Gate': lst_meas_gate
                }  

                
                    # write header to csv
                    

                for terminal, lst_meas in meas_dict.items():
                    # print(terminal, lst_meas)
                    # with open(f'{terminal}.csv', 'w') as f:
                    for measurements in lst_meas:
                        for measurement in measurements:
                            # print(measurement)
                            with open(csv_file_path, mode='a', newline='') as csv_file:
                                fieldnames = ['Description', 'voltage', 'current', 'in_compliance', 'channel']
                                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                                # Write the header
                                

                                # Write the data
                                writer.writerow({
                                    'Description': measurement.Description,
                                    'voltage': measurement.voltage,
                                    'current': measurement.current,
                                    'in_compliance': measurement.in_compliance,
                                    'channel': measurement.channel
                                })

                            print(f'Data has been written to {csv_file_path}')         

                    




        # return meas_drain, meas_source, meas_bulk, meas_gate        
    def runVtSat(self):
        self.sess.abort()
        self.sess.source_mode = nidcpower.SourceMode.SEQUENCE
        self.sess.active_advanced_sequence = 'VtsatSweep'
        with self.sess.initiate():
            self.sess.wait_for_event(nidcpower.Event.SEQUENCE_ENGINE_DONE, timeout=100.0)
            for dut in self.dHCItest:
                lst_meas_drain = []
                lst_meas_source = []
                lst_meas_bulk = []
                lst_meas_gate = []
                for drain in self.dHCItest[dut].VtSat.resource.DRAIN:
                    chnDrain = self.sess.channels[drain]
                    num = chnDrain.fetch_backlog
                    descrip = f"Drain_{dut}"
                    meas_drain = fetch_multiple(chnDrain,descrip, count=num, timeout=100.0) 
                    lst_meas_drain.append(meas_drain) 

                for source in self.dHCItest[dut].VtSat.resource.SOURCE:
                    chnSource = self.sess.channels[source]
                    num = chnSource.fetch_backlog
                    descrip = f"Source_{dut}"
                    meas_source = fetch_multiple(chnSource,descrip, count=num, timeout=100.0)
                    lst_meas_source.append(meas_source)

                for bulk in self.dHCItest[dut].VtSat.resource.BULK:
                    chnBulk = self.sess.channels[bulk]
                    num = chnBulk.fetch_backlog
                    descrip = f"Bulk_{dut}"
                    meas_bulk = fetch_multiple(chnBulk,descrip, count=num, timeout=100.0)
                    lst_meas_bulk.append(meas_bulk)

                for gate in self.dHCItest[dut].VtSat.resource.GATE:
                    chnGate = self.sess.channels[gate]
                    num = chnGate.fetch_backlog
                    descrip = f"Gate_{dut}"
                    meas_gate = fetch_multiple(chnGate,descrip, count=num, timeout=100.0)
                    lst_meas_gate.append(meas_gate)

                csv_file_path = f'{dut}_VtSat.csv'
                with open(csv_file_path, mode='a', newline='') as csv_file:
                    fieldnames = ['Description', 'voltage', 'current', 'in_compliance', 'channel']
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    writer.writeheader()

                meas_dict = {
                    'Drain': lst_meas_drain,
                    'Source': lst_meas_source,
                    'Bulk': lst_meas_bulk,
                    'Gate': lst_meas_gate
                }  

                
                    # write header to csv
                    

                for terminal, lst_meas in meas_dict.items():
                    # print(terminal, lst_meas)
                    # with open(f'{terminal}.csv', 'w') as f:
                    for measurements in lst_meas:
                        for measurement in measurements:
                            # print(measurement)
                            with open(csv_file_path, mode='a', newline='') as csv_file:
                                fieldnames = ['Description', 'voltage', 'current', 'in_compliance', 'channel']
                                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                                # Write the header
                                

                                # Write the data
                                writer.writerow({
                                    'Description': measurement.Description,
                                    'voltage': measurement.voltage,
                                    'current': measurement.current,
                                    'in_compliance': measurement.in_compliance,
                                    'channel': measurement.channel
                                })

                            print(f'Data has been written to {csv_file_path}')       



    def runIbMAX(self):
        timeout = hightime.timedelta(seconds=10)
        self.sess.abort()
        self.sess.source_mode = nidcpower.SourceMode.SEQUENCE
        self.sess.active_advanced_sequence = 'IbMAXSweep'
        with self.sess.initiate():
            self.sess.wait_for_event(nidcpower.Event.SEQUENCE_ENGINE_DONE, timeout=100.0)
            for dut in self.dHCItest:
                lst_meas_drain = []
                lst_meas_source = []
                lst_meas_bulk = []
                lst_meas_gate = []
                for drain in self.dHCItest[dut].IbMax.resource.DRAIN:
                    chnDrain = self.sess.channels[drain]
                    num = chnDrain.fetch_backlog
                    descrip = f"Drain_{dut}"
                    meas_drain = fetch_multiple(chnDrain,descrip, count=num, timeout=100.0) 
                    lst_meas_drain.append(meas_drain) 

                for source in self.dHCItest[dut].IbMax.resource.SOURCE:
                    chnSource = self.sess.channels[source]
                    num = chnSource.fetch_backlog
                    descrip = f"Source_{dut}"
                    meas_source = fetch_multiple(chnSource,descrip, count=num, timeout=100.0)
                    lst_meas_source.append(meas_source)

                for bulk in self.dHCItest[dut].IbMax.resource.BULK:
                    chnBulk = self.sess.channels[bulk]
                    num = chnBulk.fetch_backlog
                    descrip = f"Bulk_{dut}"
                    meas_bulk = fetch_multiple(chnBulk,descrip, count=num, timeout=100.0)
                    lst_meas_bulk.append(meas_bulk)

                for gate in self.dHCItest[dut].IbMax.resource.GATE:
                    chnGate = self.sess.channels[gate]
                    num = chnGate.fetch_backlog
                    descrip = f"Gate_{dut}"
                    meas_gate = fetch_multiple(chnGate,descrip, count=num, timeout=100.0)
                    lst_meas_gate.append(meas_gate)

                csv_file_path = f'{dut}_IbMax.csv'
                with open(csv_file_path, mode='a', newline='') as csv_file:
                    fieldnames = ['Description', 'voltage', 'current', 'in_compliance', 'channel']
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    writer.writeheader()

                meas_dict = {
                    'Drain': lst_meas_drain,
                    'Source': lst_meas_source,
                    'Bulk': lst_meas_bulk,
                    'Gate': lst_meas_gate
                }  

                
                    # write header to csv
                    

                for terminal, lst_meas in meas_dict.items():
                    # print(terminal, lst_meas)
                    # with open(f'{terminal}.csv', 'w') as f:
                    for measurements in lst_meas:
                        for measurement in measurements:
                            # print(measurement)
                            with open(csv_file_path, mode='a', newline='') as csv_file:
                                fieldnames = ['Description', 'voltage', 'current', 'in_compliance', 'channel']
                                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                                # Write the header
                                

                                # Write the data
                                writer.writerow({
                                    'Description': measurement.Description,
                                    'voltage': measurement.voltage,
                                    'current': measurement.current,
                                    'in_compliance': measurement.in_compliance,
                                    'channel': measurement.channel
                                })

                            print(f'Data has been written to {csv_file_path}')       
    
    def extract_vth_using_const_current(self):
        pass

    def extract_vth_using_maxGM(self):
        pass
    

hci = HCItest('test_plan_HCI_1110_V3.xlsx', sitesNum=1)
hci.common_settings()
hci._constructVtlinSweeptest()
hci._constructVtSatSweeptest()
hci._constructIbMAXSweeptest()


for i in range(len(hci.stressInterval)):
    # print(hci.stressInterval[i])
    # calculate the interval
    if i == 0:
        time_interval = hightime.timedelta(seconds=(hci.stressInterval[i]-0))
    else:
        time_interval = hightime.timedelta(seconds=(hci.stressInterval[i]-hci.stressInterval[i-1]))

    # wait for the interval
    print(time_interval)
    t0 = time.time()
    hci.runStress(time_interval)
    t1 = time.time()
    print("time elapsed: ", t1-t0)
    hci.prepareForSequenceMode()
    hci.runVtlin()
    hci.runVtSat()
    hci.runIbMAX()
    print(i)
    time.sleep(1000)
hci.sess.close()



