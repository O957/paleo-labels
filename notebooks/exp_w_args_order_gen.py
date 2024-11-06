"""
General experimentation using
attrs and argument ordering.
"""

# %% LIBRARY IMPORTS

import attrs

# %% EXAMPLE CLASS


@attrs.define
class ExampleClassA:
    """
    Test class for a making a message where
    the outcome message depends on which
    order the keywords arguments are given.
    """

    normal_arg: str
    msg_NJLC: str = attrs.field(
        kw_only=True, validator=attrs.validators.instance_of(str)
    )
    msg_NACP: str = attrs.field(
        kw_only=True, validator=attrs.validators.instance_of(str)
    )
    kw_only_args: dict[str, str] = attrs.field(init=False)
    full_message: str = attrs.field(init=False)

    def __attrs_post_init__(self):
        self.kw_only_args = {
            field.name: getattr(self, field.name)
            for field in attrs.fields(type(self))
            if field.kw_only
        }
        self.full_message = "\n".join([key for key in self.kw_only_args])

    def get_message(self):
        print(self.full_message)


# %% FAILURE USING EXAMPLE CLASS A!

cls_inst1 = ExampleClassA("hello", msg_NACP="NACP", msg_NJLC="NJLC")
cls_inst1.get_message()

cls_inst2 = ExampleClassA("hello", msg_NJLC="NJLC", msg_NACP="NACP")
cls_inst2.get_message()


# %% DIFFERENT EXAMPLE CLASS


@attrs.define
class ExampleClassB:
    """
    Test class for a making a message where
    the outcome message depends on which
    order the keywords arguments are given.
    """

    normal_arg: str
    msg_parts: dict[str, str] = attrs.field(
        kw_only=True,
        validator=attrs.validators.instance_of(dict),
        default={"msg_NACP": "NACP", "msg_NJLC": "NJLC"},
    )

    @msg_parts.validator
    def check_keys_safe(self, attribute, value):
        permitted_keys = ["msg_NACP", "msg_NJLC"]
        difference = set(value.keys()).difference(set(permitted_keys))
        if bool(difference):
            raise Exception(f"Foreign keys are present: {difference}")

    full_message: str = attrs.field(init=False)

    def __attrs_post_init__(self):
        self.full_message = "\n".join(
            value for key, value in self.msg_parts.items()
        )

    def get_message(self):
        print(self.full_message)


# %% SUCCESS USING EXAMPLE CLASS!

cls_inst1 = ExampleClassB(
    "hello", msg_parts={"msg_NACP": "NACP", "msg_NJLC": "NJLC"}
)
cls_inst1.get_message()

cls_inst2 = ExampleClassB(
    "hello", msg_parts={"msg_NJLC": "NJLC", "msg_NACP": "NACP"}
)
cls_inst2.get_message()

# %%
