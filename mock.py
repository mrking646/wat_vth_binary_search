import nidcpower
import hightime
resources = ["PXI1Slot2"]

with nidcpower.Session(resource_name=resources[0], channels="0", reset=True,  options = {'simulate': True, 'driver_setup': {'Model': '4163', 'BoardType': 'PXIe', }, }) as session:
    session.source_mode = nidcpower.SourceMode.SEQUENCE
    session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
    session.voltage_level = 1.0
    session.current_limit = 1
    session.current_limit_range = 1e-3
    properties_used = ['output_enabled', 'output_function', 'voltage_level', 'current_limit']
    session.create_advanced_sequence(sequence_name="test_sequence", set_as_active_sequence=True, property_names=properties_used)

    for i in range(10):
        session.create_advanced_sequence_step(set_as_active_step=True)
        session.voltage_level = 1.0 + i
    session.active_advanced_sequence_step = 11

    session.commit()
    with session.initiate():
        timeout = hightime.timedelta(seconds=10)
        session.wait_for_event(nidcpower.Event.SEQUENCE_ENGINE_DONE, timeout=timeout)
        num = session.fetch_backlog
        print(num)
        measurement = session.fetch_multiple(count=num, timeout=timeout)
        print(measurement)