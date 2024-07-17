__all__=['TestPlan']

import re

from numpy import sign

class TestPlan:
    busPat = re.compile('(?P<obj>\w+)\.(?P<name>\w+)(\[(?P<idx>[\w+-]+)\])*')

    def __init__(self, fileName, sheetNames=['all']):
        self.fileName  = fileName
        self.tileMap = self.parseAll(sheetNames)

    def iterRows(self, sheetName):
        from openpyxl import Workbook, load_workbook
        from collections import namedtuple

        wb = load_workbook(filename=self.fileName, read_only=True, data_only=True)
        ws = wb[sheetName]

        inTable = False
        header, rows_buf = [], []
        def buildHeader(cols):
            header.clear()
            rows_buf.clear()
            for c in cols:
                if c.value is not None:
                    header.append(c.value.strip())

        def makeRows():
            for i,row in enumerate(rows_buf):
                fullname = None
                dDut, dTile, dTest = {}, {}, {}
                for j,col in enumerate(header):
                    if col=='fullname':
                        fullname = row[j]
                        continue

                    match = self.busPat.match(col).groupdict()
                    obj, name, idx = match['obj'], match['name'], match['idx']
                    if obj=='tile':
                        dTile[name] = row[j]
                    elif obj=='dut':
                        if name=='pads':
                            if not 'ports' in dDut: dDut['ports'] = []
                            if not 'pads'  in dDut: dDut['pads']  = []
                            dDut['ports'].append(idx)
                            dDut['pads'].append(row[j])
                        else:
                            assert idx is None
                            dDut[name] = row[j]
                    elif obj=='test':
                        if name=='ports':
                            if not 'ports' in dTest: dTest['ports'] = []
                            dTest['ports'].append(row[j])
                        else:
                            assert idx is None
                            dTest[name] = row[j]

                testProg = dTest.get('program')
                op = dTest.pop('output_param')
                dTest['output_params'] = (op,)
                dTest['fullnames'] = (fullname,)
                dTest['ports'] = tuple(dTest['ports'])
                dTest['test_num'] = None
                test = namedtuple(testProg, dTest.keys())(**dTest)
                dut  = namedtuple('DUT',    dDut.keys())(**dDut)
                dTile['site_num'] = None
                tile = namedtuple('Tile',   dTile.keys())(**dTile)
                yield (fullname, tile, dut, test)
            rows_buf.clear()

        for row in ws.rows:
            if inTable:
                if row[0].value is None:
                    inTable = False
                    yield from makeRows()
                else:
                    nc = len(header)
                    rows_buf.append([row[j].value for j in range(nc)])
            else:
                if row[0].value is not None:
                    # start new table
                    buildHeader(row)
                    inTable = True

        if len(rows_buf)>0:
            yield from makeRows()

    def parseAll(self, sheetNames=['all']):
        tiles, tileDUTs, tileTests, testProgs = {}, {}, {}, {}

        def updateTestProg(test):
            signature = tuple([(key,getattr(test, key)) for key in sorted(test._fields) if key!='test_num'])
            if not signature in testProgs:
                if test.test_num is None:
                    testProgs[signature] = test._replace(test_num=len(testProgs)+1)
                else:
                    testProgs[signature] = test
            return testProgs[signature]

        def updateTile(tile, duts, tests):
            if not tile.name in tiles:
                tiles     [tile.name] = tile
                tileDUTs  [tile.name] = {}
                tileTests [tile.name] = {}
            for dutName in duts.keys():
                if dutName in tileDUTs[tile.name]:
                    print(f'Warning: duplicate tile/dut name {tile.name}/{dutName}')
                if not dutName in tileTests[tile.name]:
                    tileTests[tile.name][dutName] = []

                tileDUTs [tile.name][dutName] = duts[dutName]
                tileTests[tile.name][dutName].extend([updateTestProg(t) for t in tests[dutName]])

        for sheetName in sheetNames:
            tileLast,dutLast,testLast,sigLast = None,None,None,None
            duts, tests = {}, {}    # saved duts and tests saved for tileLast

            for fullname,tile,dut,test in self.iterRows(sheetName):
                signature = tuple([(key,getattr(test, key)) for key in sorted(test._fields) if not (key=='test_num' or key=='output_params' or key=='fullnames')])
                if tile==tileLast and dut==dutLast and signature==sigLast:
                    # same test program, another parameter
                    testLast = testLast._replace(
                        output_params = testLast.output_params + test.output_params,
                        fullnames     = testLast.fullnames + (fullname,),
                        )
                    tests[dut.name][-1] = testLast
                elif tile==tileLast and dut==dutLast:
                    # new test program
                    tests[dut.name].append(test)
                    testLast = test
                    sigLast = signature
                elif tile==tileLast:
                    # new DUT
                    if not dut.name in duts:
                        duts[dut.name] = dut
                        tests[dut.name] = []
                    tests[dut.name].append(test)
                    dutLast = dut
                    testLast = test
                    sigLast = signature
                else:
                    # new tile found, emit dut/test in the old tile
                    if tileLast is not None:
                        updateTile(tileLast,duts,tests)
                    duts, tests = {}, {}    # reset duts/tests for new tile   
                    if not dut.name in duts:
                        duts[dut.name] = dut
                        tests[dut.name] = []
                    tests[dut.name].append(test)

                    tileLast = tile
                    dutLast = dut
                    testLast = test
                    sigLast = signature
            # last tile
            if tileLast is not None:
                updateTile(tileLast,duts,tests)

        self.tiles     = {}
        self.tileDUTs  = {}
        self.tileTests = {}
        tileCoords = [(tile.x0, tile.y0, tileName) for tileName, tile in tiles.items()]
        for i,(x0,y0,tileName) in enumerate(sorted(tileCoords, key=lambda t: (t[0], t[1]))):
            self.tiles    [tileName] = tiles[tileName]._replace(site_num=i+1)
            self.tileDUTs [tileName] = tileDUTs[tileName]
            self.tileTests[tileName] = tileTests[tileName]
        self.testProgs = testProgs

    def iterTile(self):
        for tileName in self.tiles.keys():
            yield (self.tiles    [tileName],
                    self.tileDUTs [tileName],
                    self.tileTests[tileName],
                    )