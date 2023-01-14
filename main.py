import attrs
import nidcpower
from openpyxl import load_workbook, Workbook
import pandas as pd
from config import wiring
import numpy as np

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
    CurrentLimit: CurrentLimit
    CurrentLimitRange: CurrentLimitRange


@attrs.define
class IbMaxSweep:
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
    CurrentLimit: CurrentLimit
    CurrentLimitRange: CurrentLimitRange



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

  
def dumpExceltoPython(testplan):
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
        GATE = [f'{wiring[(padGATE-1)+24*i][1][0][wiring[(padGATE-1)+24*i][1][1]]}/{wiring[(padGATE-1)+24*i][1][2]}' for i in range(4)]
        DRAIN  = [f'{wiring[(padDRAIN-1)+24*i][1][0][wiring[(padDRAIN-1)+24*i][1][1]]}/{wiring[(padDRAIN-1)+24*i][1][2]}' for i in range(4)]
        SOURCE = [f'{wiring[(padSOURCE-1)+24*i][1][0][wiring[(padSOURCE-1)+24*i][1][1]]}/{wiring[(padSOURCE-1)+24*i][1][2]}' for i in range(4)]
        BULK = [f'{wiring[(padBULK-1)+24*i][1][0][wiring[(padBULK-1)+24*i][1][1]]}/{wiring[(padBULK-1)+24*i][1][2]}' for i in range(4)]
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
            dTest_VtSat[dut] = VtlinSweep(dResource[dut], vForceD, vForceS, vForceB, iComplG, iComplD, iComplS, iComplB, vStepG, vStartG, vStopG)
        elif 'Ibmax' in c:
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
            dTest_IbMAX[dut] = VtlinSweep(dResource[dut], vForceD, vForceS, vForceB, iComplG, iComplD, iComplS, iComplB, vStepG, vStartG, vStopG)
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
    
class HCItest:
    def __init__(self, testplan):
        self.dHCItest = dumpExceltoPython(testplan)
        self.current_limit = CurrentLimit()
        self.current_limit_range = CurrentLimitRange()
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

    def runStress(sess, dHCItest):
        sess.source_mode = nidcpower.SourceMode.SINGLE_POINT
        sess.voltage_level_autorange = True

    # would it be fine if we dump all channels of 4163 into a session and we then open the relays we don't need?
    def common_settings(self):
        sess = nidcpower.Session(resource_name='SMU1, SMU2', reset=False, options={'Simulate': True, 'DriverSetup': {'Model':'4163', 'BoardType':'PXIe'}})
        print(sess.channels['SMU1/0,SMU1/1'])
        sess.voltage_level_autorange = False
        sess.current_limit_autorange = False
        sess.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        sess.voltage_level = 0
        sess.current_limit = 1e-3
        sess.source_mode = nidcpower.SourceMode.SEQUENCE
        sess.output_connected = False # turn off all channels 
        sess.output_enabled = True
        return sess

    def _constructVtlinSweeptest(self):
        sess = self.common_settings()
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
        sess.create_advanced_sequence(sequence_name='VtlinSweep', set_as_active_sequence=True, property_names=properties_used)
        # sess.create_advanced_sequence_step(set_as_active_step=True)

        for dut in self.dHCItest:
            vStart, vStop, vStep = self.dHCItest[dut].Vtlin.V_start_G, self.dHCItest[dut].Vtlin.V_stop_G, self.dHCItest[dut].Vtlin.V_step_G
            numStep = round((vStop+vStep/2 - vStart)/vStep)+1
            container = np.ones(numStep+1)
            vSteps = np.linspace(vStart, vStop, numStep)
            dStepsForALLduts_GATE[dut] = vSteps
            dStepsForALLduts_DRAIN[dut] =  container * self.dHCItest[dut].Vtlin.V_force_D
            dStepsForALLduts_SOURCE[dut] = container * self.dHCItest[dut].Vtlin.V_force_S
            dStepsForALLduts_BULK[dut] = container * self.dHCItest[dut].Vtlin.V_force_B
            # print(dStepsForALLduts_GATE[dut])
        

        
        for i in range(len(dStepsForALLduts_GATE)):
            sess.create_advanced_sequence_step(set_as_active_step=True)
            for dut in self.dHCItest:
                chnGate = sess.channels[','.join(self.dHCItest[dut].Vtlin.resource.GATE)]
                chnDrain = sess.channels[','.join(self.dHCItest[dut].Vtlin.resource.DRAIN)]
                chnSource = sess.channels[','.join(self.dHCItest[dut].Vtlin.resource.SOURCE)]
                chnBulk = sess.channels[','.join(self.dHCItest[dut].Vtlin.resource.BULK)]
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
                chnBulk.current_limit_range = self.current_limit_range.high_level
                chnSource.current_limit_range = self.current_limit_range.high_level
                chnDrain.current_limit_range = self.current_limit_range.high_level
                chnGate.current_limit_range = self.current_limit_range.low_level
        return sess



    def constructVtSatSweeptest(self, sess, **HCI):
        pass

    def constructIbMAXSweeptest(self, sess, **HCI):
        pass


    def write_results(self, sess):
        pass


    def populate(session):
        pass

    def runVtlin(self):
        sess = self._constructVtlinSweeptest()
        sess.initiate()
        for dut in self.dHCItest:
            for drain in self.dHCItest[dut].Vtlin.resource.DRAIN:
                chnDrain = sess.channels[drain]
                num = chnDrain.fetch_backlog
                print(num)
                meas = chnDrain.fetch_multiple(count=num, timeout=10.0)
                print(meas)


        

hci = HCItest('test_plan_HCI_1110_V3.xlsx')
hci.runVtlin()



