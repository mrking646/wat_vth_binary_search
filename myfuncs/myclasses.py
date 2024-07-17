import attrs
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
                            default=50e-3,
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
                                    default = 50e-3,
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