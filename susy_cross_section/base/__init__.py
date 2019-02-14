"""Table of values with asymmetric uncertainties.

`BaseTable` carries data and the table-level annotation `TableInfo`. The
`TableInfo` class contains the other three classes as sub-information.

========================= =============================================
`base.table.BaseTable`    contains data and `TableInfo`
`base.info.TableInfo`     has table-wide properties and `ColumnInfo`,
                          `ParameterInfo`, and `ValueInfo`
`base.info.ColumnInfo`    has properties of each column
`base.info.ParameterInfo` annotates a column as a parameter
`base.info.ValueInfo`     defines a value from columns
========================= =============================================
"""
