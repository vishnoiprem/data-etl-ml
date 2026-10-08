export var ColumnDataType;
(function (ColumnDataType) {
    ColumnDataType[ColumnDataType["STRING"] = 0] = "STRING";
    ColumnDataType[ColumnDataType["FLOAT"] = 1] = "FLOAT";
    ColumnDataType[ColumnDataType["DOUBLE"] = 2] = "DOUBLE";
    ColumnDataType[ColumnDataType["INT_64"] = 3] = "INT_64";
    ColumnDataType[ColumnDataType["UINT_64"] = 4] = "UINT_64";
    ColumnDataType[ColumnDataType["BOOLEAN"] = 5] = "BOOLEAN";
    ColumnDataType[ColumnDataType["GEOMETRY"] = 6] = "GEOMETRY";
    ColumnDataType[ColumnDataType["GEOMETRY_M"] = 7] = "GEOMETRY_M";
    ColumnDataType[ColumnDataType["GEOMETRY_Z"] = 8] = "GEOMETRY_Z";
    ColumnDataType[ColumnDataType["GEOMETRY_ZM"] = 9] = "GEOMETRY_ZM";
})(ColumnDataType || (ColumnDataType = {}));
export var ColumnEncoding;
(function (ColumnEncoding) {
    /*
     * String -> no dictionary coding
     * Geometry -> standard unsorted encoding
     * */
    ColumnEncoding[ColumnEncoding["PLAIN"] = 0] = "PLAIN";
    ColumnEncoding[ColumnEncoding["VARINT"] = 1] = "VARINT";
    ColumnEncoding[ColumnEncoding["DELTA_VARINT"] = 2] = "DELTA_VARINT";
    ColumnEncoding[ColumnEncoding["RLE"] = 3] = "RLE";
    ColumnEncoding[ColumnEncoding["BOOLEAN_RLE"] = 4] = "BOOLEAN_RLE";
    ColumnEncoding[ColumnEncoding["BYTE_RLE"] = 5] = "BYTE_RLE";
    ColumnEncoding[ColumnEncoding["DICTIONARY"] = 6] = "DICTIONARY";
    ColumnEncoding[ColumnEncoding["LOCALIZED_DICTIONARY"] = 7] = "LOCALIZED_DICTIONARY";
    ColumnEncoding[ColumnEncoding["ORDERED_GEOMETRY_ENCODING"] = 8] = "ORDERED_GEOMETRY_ENCODING";
    ColumnEncoding[ColumnEncoding["INDEXED_COORDINATE_ENCODING"] = 9] = "INDEXED_COORDINATE_ENCODING";
})(ColumnEncoding || (ColumnEncoding = {}));
//# sourceMappingURL=mltMetadata.js.map