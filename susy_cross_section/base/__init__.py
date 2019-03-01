"""Table of values with asymmetric uncertainties.

`BaseFile` carries grid tables as `BaseTable` and annotations as `FileInfo`.
The `FileInfo` class contains the other three classes as sub-information.

========================= =============================================
`base.table.BaseFile`     contains `FileInfo` and multiple `BaseTable`
`base.table.BaseTable`    represents the grid data for cross section.
`base.info.FileInfo`      has file-wide properties and `ColumnInfo`,
                          `ParameterInfo`, and `ValueInfo`
`base.info.ColumnInfo`    has properties of each column
`base.info.ParameterInfo` annotates a column as a parameter
`base.info.ValueInfo`     defines a value from columns
========================= =============================================
"""
