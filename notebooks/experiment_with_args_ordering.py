"""
Experimentation file to test
having dependencies in constructed
string based on order of arguments.
"""

# %%


def collections_label_func(
    collection: str | None = None,
    date_found: str | None = None,
    species: str | None = None,
):
    provided_args = [
        arg
        for arg in (
            collection,
            date_found,
            species,
        )
        if arg is not None
    ]
    return ", ".join(provided_args)


out1 = collections_label_func(
    collection="Repository TPM",
    date_found="2024-08-08",
    species="Enchodus sp.",
)
print(out1)

out2 = collections_label_func(
    species="Enchodus sp.",
    collection="Repository TPM",
    date_found="2024-08-08",
)
print(out2)
# %%


def collections_label_func_kwargs(**kwargs):
    return ", ".join(kwargs.values())


out1 = collections_label_func_kwargs(
    collection="Repository TPM",
    date_found="2024-08-08",
    species="Enchodus sp.",
)
print(out1)

out2 = collections_label_func_kwargs(
    species="Enchodus sp.",
    collection="Repository TPM",
    date_found="2024-08-08",
)
print(out2)
# %%
