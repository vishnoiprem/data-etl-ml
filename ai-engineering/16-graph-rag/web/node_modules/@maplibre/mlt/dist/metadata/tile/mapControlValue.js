/**
 * Tokens in the data stream of a nested property (MAP) column. Values below `COUNT` describe the
 * structure; anything else is an index into the combined dictionary, offset by `COUNT`. Booleans are
 * encoded directly as tokens rather than being added to a dictionary.
 */
export var MapControlValue;
(function (MapControlValue) {
    MapControlValue[MapControlValue["FALSE"] = 0] = "FALSE";
    MapControlValue[MapControlValue["TRUE"] = 1] = "TRUE";
    /** A nested map follows: this token, the payload length including these two tokens, the payload. */
    MapControlValue[MapControlValue["START_MAP"] = 2] = "START_MAP";
    /** A list follows, laid out the same way as START_MAP. */
    MapControlValue[MapControlValue["START_LIST"] = 3] = "START_LIST";
    /** Number of reserved tokens, i.e. the first dictionary index. */
    MapControlValue[MapControlValue["COUNT"] = 4] = "COUNT";
})(MapControlValue || (MapControlValue = {}));
//# sourceMappingURL=mapControlValue.js.map