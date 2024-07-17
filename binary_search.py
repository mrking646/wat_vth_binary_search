import nidcpower
import hightime
import attrs
import pandas as pd
import contextlib
from myclasses import IVSweep, ChnVoltBias, ChnVoltSweep
import numpy as np

def runIVSweeps_softwareAutoRange(*lstIVSweep : IVSweep, CSV_name="result.csv"):

    # beat(8)

    current_ranges = tuple([10e-9, 1e-6, 100e-6, 1e-3, 10e-3, 50e-3])
    # current_ranges = tuple([1e-3, 10e-3, 50e-3])
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
    session = nidcpower.Session(resource_name=resources, reset=True,  options = {'simulate': True, 'driver_setup': {'Model': '4135', 'BoardType': 'PXIe', }, })

    session.power_line_frequency = 50
    session.aperture_time_units = nidcpower.ApertureTimeUnits.SECONDS
    session.samples_to_average = 1
    session.measure_when = nidcpower.MeasureWhen.ON_DEMAND
    session.source_mode = nidcpower.SourceMode.SINGLE_POINT
    session.autorange = False
    session.sense = nidcpower.Sense.LOCAL
    session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
    session.voltage_level_autorange = True
    # session.voltage_level_range = 6
    session.voltage_level = 0.0
    session.output_connected = True
    session.output_enabled = True
    session.current_limit_autorange = True
    # session.current_limit = current_ranges[0]
    # session.current_limit_range = current_ranges[0]
    
    aperture_time = 20e-3
    vSteps_dict = {}
    numOfSteps = 0
    tolerance = 1e-3
    Ith = 1e-7
    
    timeout = hightime.timedelta(seconds=10)
    with session.initiate():


        for ivSweep in lstIVSweep:
            channels_pair = extract_channel_vs_name_pairs(ivSweep)
            chnSweep = session.channels[ivSweep.sweep.resource]
            chnSweep.current_limit = ivSweep.sweep.I_compl
            chnSweep.current_limit_range = ivSweep.sweep.I_compl
            Vlow = ivSweep.sweep.V_start
            Vhigh = ivSweep.sweep.V_stop
            Vmid = (Vhigh-Vlow)/2.0
            chnSweep.voltage_level = Vmid
            chnSweep.current_limit = ivSweep.sweep.I_compl
            for bias in ivSweep.biases:
                chnBias = session.channels[bias.resource]
                chnBias.voltage_level = bias.V_force
                # chnBias.current_limit_range = bias.I_compl
                chnBias.current_limit = bias.I_compl
                
        count = 0
        while (Vhigh+Vlow)>tolerance:
            Vmid = (Vhigh+Vlow)/2.0
            chnSweep.voltage_level = Vmid
            session.wait_for_event(nidcpower.Event.SOURCE_COMPLETE, timeout=timeout)
            drain_current = session.channels[channels_pair["D"]].measure_multiple()[0].current
            if drain_current > Ith:
                Vhigh = Vmid
            else:
                Vlow = Vmid
            count+=1

        vth = (Vlow+Vhigh)/2
        print(count)
        

        
    # session.reset()
    session.close()
    print(vth)
    return vth


vtlin = IVSweep(ChnVoltSweep('G', 'SMU2/0', V_start=0, V_stop=1.2, V_step=0.02, I_compl=1e-3, remote_sense=False),
                        [ChnVoltBias('D', 'SMU1/0', 0.1, I_compl=1e-3, remote_sense=False),
                        ChnVoltBias('S', 'SMU4/0', 0, I_compl=1e-3, VoltSense=False),
                        ChnVoltBias('B', 'SMU3/0', 0, I_compl=1e-3),

                        
                        
                        ],
                        apertureTime=40e-3,
                        sourceDelay=5e-5,
                        isMaster=1,
                        )

def extract_channel_vs_name_pairs(*lstivSweep:IVSweep):
    channel_vs_name_pair = {}
    for _sweep in lstivSweep:
        channel_vs_name_pair[_sweep.sweep.remarks] = _sweep.sweep.resource
        for bias in _sweep.biases:
            channel_vs_name_pair[bias.remarks] = bias.resource
        return channel_vs_name_pair

# runIVSweeps_softwareAutoRange(vtlin, CSV_name="1.csv")