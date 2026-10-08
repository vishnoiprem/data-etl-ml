/**
 * Bitmask written ahead of a nested property (MAP) column, marking which optional streams follow
 * the mandatory length stream. Only one of INT32/INT64 and one of UINT32/UINT64 is ever set: the
 * encoder picks the narrower width that fits every value.
 */
export var MapMask;
(function (MapMask) {
    MapMask[MapMask["STRING"] = 1] = "STRING";
    MapMask[MapMask["INT32"] = 2] = "INT32";
    MapMask[MapMask["UINT32"] = 4] = "UINT32";
    MapMask[MapMask["INT64"] = 8] = "INT64";
    MapMask[MapMask["UINT64"] = 16] = "UINT64";
    MapMask[MapMask["FLOAT"] = 32] = "FLOAT";
    MapMask[MapMask["DOUBLE"] = 64] = "DOUBLE";
    MapMask[MapMask["PRESENCE"] = 128] = "PRESENCE";
})(MapMask || (MapMask = {}));
//# sourceMappingURL=mapMask.js.map