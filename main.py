import attrs
import nidcpower
from openpyxl import load_workbook, Workbook
import pandas as pd
from config import wiring

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
class Resource:
    
    GATE : list
    DRAIN: list
    SOURCE: list
    BULK: list

@attrs.define
class HCIsweep:
    resource: Resource

    dieCoord: str = attrs.field(
        default='A1',
        kw_only=True,
    )
    tileName: str = attrs.field(
        default='A1',
        kw_only=True,

    )

    # biases: list[chnVoltBias] = attrs.field(
    #     validator=attrs.validators.deep_iterable(member_validator=attrs.validators.instance_of((chnVoltBias)))
    # )

    sourceDelay: float = attrs.field(
        default=1e-3,
        kw_only=True,
    )

    apertureTime: float = attrs.field(
        default=1e-3,
        kw_only=True,
    )
    
def populate():
    wb = Workbook()    
    ws = wb.active
    ws['A1'] = 42
    ws.append([1, 2, 3])
    import datetime
    ws['A2'] = datetime.datetime.now()
    wb.save('sample.xlsx')

def runHCI():
    pass

def dumpExceltoPython():
    wb = load_workbook(filename='test_plan_HCI_1110_V3.xlsx')
    ws = wb.active
    dDut, dTile, dTest = {}, {}, {}
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

    count = 0
    for c in df_plan.loc[:, 'fullname']:
        if 'Vtlin' in c:
            padGATE = df_plan.loc[count, ' dut.pads[G]']
            padDRAIN = df_plan.loc[count, ' dut.pads[D]']
            padSOURCE = df_plan.loc[count, ' dut.pads[S]']
            padBULK = df_plan.loc[count, ' dut.pads[B]']
            GATE = [f'{wiring[(padGATE-1)+24*i][1][0][wiring[(padGATE-1)+24*i][1][1]]}/{wiring[(padGATE-1)+24*i][1][2]}' for i in range(4)]
            DRAIN  = [f'{wiring[(padDRAIN-1)+24*i][1][0][wiring[(padDRAIN-1)+24*i][1][1]]}/{wiring[(padDRAIN-1)+24*i][1][2]}' for i in range(4)]
            SOURCE = [f'{wiring[(padSOURCE-1)+24*i][1][0][wiring[(padSOURCE-1)+24*i][1][1]]}/{wiring[(padSOURCE-1)+24*i][1][2]}' for i in range(4)]
            BULK = [f'{wiring[(padBULK-1)+24*i][1][0][wiring[(padBULK-1)+24*i][1][1]]}/{wiring[(padBULK-1)+24*i][1][2]}' for i in range(4)]

            dDut[c] = Resource(GATE, DRAIN, SOURCE, BULK)
            print(dDut[c])
            dTest[c] = HCIsweep(dDut[c])
            print(dTest[c])
        count += 1
def populate(session):
    pass


class HCI:
    
    def __init__(self, fileName, sheetNames=['all']):
        self.dut = None
        
    def prepareVtlin(self):
        pass

    def prepareVtSat(self):
        pass

    def prepareIbmax(self):
        pass


dumpExceltoPython()

