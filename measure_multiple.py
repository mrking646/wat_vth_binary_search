import nidcpower._converters as _converters

def measure_multiple(self, channel_terminal_pair):
        '''measure_multiple

        Returns a list of named tuples (Measurement) containing the measured voltage
        and current values on the specified output channel(s). Each call to this method
        blocks other method calls until the measurements are returned from the device.
        The order of the measurements returned in the array corresponds to the order
        on the specified output channel(s).

        Fields in Measurement:

        - **voltage** (float)
        - **current** (float)
        - **in_compliance** (bool) - Always None
        - **channel** (str)

        Note:
        This method is not supported on all devices. For more information about supported devices, search ni.com for Supported Methods by Device.

        Tip:
        This method can be called on specific channels within your :py:class:`nidcpower.Session` instance.
        Use Python index notation on the repeated capabilities container channels to specify a subset,
        and then call this method on the result.

        Example: :py:meth:`my_session.channels[ ... ].measure_multiple`

        To call the method on all channels, you can call it directly on the :py:class:`nidcpower.Session`.

        Example: :py:meth:`my_session.measure_multiple`

        Returns:
            measurements (list of Measurement): List of named tuples with fields:

                - **voltage** (float)
                - **current** (float)
                - **in_compliance** (bool) - Always None
                - **channel** (str)

        '''
        import collections
        Measurement = collections.namedtuple('Measurement', ['voltage', 'current', 'in_compliance', 'channel'])

        voltage_measurements, current_measurements = self._measure_multiple()

        channel_names = _converters.expand_channel_string(
            self._repeated_capability,
            self._all_channels_in_session
        )
        assert (
            len(channel_names) == len(voltage_measurements) and len(channel_names) == len(current_measurements)
        ), "measure_multiple should return as many voltage and current measurements as the number of channels specified through the channel string"
        return [
            Measurement(
                
                voltage=voltage,
                current=current,
                in_compliance=None,
                channel=channel_name
            ) for voltage, current, channel_name in zip(
                voltage_measurements, current_measurements, channel_names
            )
        ]