from collections import namedtuple

# Assuming Measurement is a namedtuple or similar class
Measurement = namedtuple('Measurement', ['voltage', 'current', 'in_compliance', 'channel'])

# Example data
data = [
    Measurement(voltage=0.1, current=1.0000000000000001e-07, in_compliance=None, channel='SMU1/0'),
    Measurement(voltage=0.0, current=1.0000000000000001e-07, in_compliance=None, channel='SMU2/0'),
    Measurement(voltage=0.0, current=1.0000000000000001e-07, in_compliance=None, channel='SMU3/0'),
    Measurement(voltage=0.1, current=1.0000000000000001e-07, in_compliance=None, channel='SMU4/0')
]

# Define the channel you want to extract
desired_channel = 'SMU2/0'

# Extract measurements for the desired channel
extracted_measurements = [measurement for measurement in data if measurement.channel == desired_channel]

# Display the extracted measurements
print(extracted_measurements)


class Measurement:
    def __init__(self, voltage, current, in_compliance, channel):
        self.voltage = voltage
        self.current = current
        self.in_compliance = in_compliance
        self.channel = channel

    def __repr__(self):
        return f"Measurement(voltage={self.voltage}, current={self.current}, in_compliance={self.in_compliance}, channel='{self.channel}')"

class InstrumentData:
    def __init__(self):
        self.measurements = []

    def add_measurement(self, measurement):
        self.measurements+=measurement

    def get_measurements_by_channel(self, channel):
        return [m for m in self.measurements if m.channel == channel]
    
    def clear_measurements(self):
        """ Clear all existing measurements. """
        self.measurements = []

    def __repr__(self):
        return f"InstrumentData({self.measurements})"

# Example usage
# instrument_data = InstrumentData()
# instrument_data.add_measurement(Measurement(0.1, 1e-07, None, 'SMU1/0'))
# instrument_data.add_measurement(Measurement(0.0, 1e-07, None, 'SMU2/0'))
# # Add more measurements as needed

# # Get measurements for a specific channel
# channel_measurements = instrument_data.get_measurements_by_channel('SMU1/0')
# print(channel_measurements)
