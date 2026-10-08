import { type Column, type ColumnWithoutName } from "./tilesetMetadata";
/**
 * The single varint32 that introduces every column in the tile metadata, identifying what kind of
 * column follows. Ids occupy a small range of flagged codes, geometry has one code of its own, and
 * scalar properties are laid out from `SCALAR_BASE` upwards, two codes per type.
 */
export declare const ColumnTypeCode: {
    /** Id columns occupy 0..3. */
    readonly ID: 0;
    /** Set on an id column whose values can be null. */
    readonly ID_NULLABLE: 1;
    /** Set on an id column holding 64-bit rather than 32-bit ids. */
    readonly ID_LONG: 2;
    readonly GEOMETRY: 4;
    /** Scalar properties are `SCALAR_BASE + scalarType * 2 + (nullable ? 1 : 0)`. */
    readonly SCALAR_BASE: 10;
    readonly STRUCT: 30;
    readonly MAP: 31;
};
/**
 * The type code is a single varint32 that encodes:
 * - Physical or logical type
 * - Nullable flag
 * - Whether the column has a name (typeCode >= ColumnTypeCode.SCALAR_BASE)
 * - Whether the column has children (typeCode == 30 for STRUCT)
 * - For ID types: whether it uses long (64-bit) IDs
 */
/**
 * Decodes a type code into a Column structure.
 *
 * ID type codes (0..3):
 * - Bit 0: nullable
 * - Bit 1: longID (0/1 -> uint32 IDs, 2/3 -> uint64 IDs)
 *
 * ID columns are kept as logical types so they remain distinguishable
 * from feature properties that may also be named "id".
 */
export declare function decodeColumnType(typeCode: number): ColumnWithoutName | null;
/**
 * Returns true if this type code requires a name to be stored.
 * ID (0-3) and GEOMETRY (4) columns have implicit names.
 * All other types (>= ColumnTypeCode.SCALAR_BASE) require explicit names.
 */
export declare function columnTypeHasName(typeCode: number): boolean;
/**
 * Returns true if this type code has child fields.
 * STRUCT (typeCode 30) and MAP (typeCode 31) have children.
 */
export declare function columnTypeHasChildren(typeCode: number): boolean;
/**
 * Determines if a stream count needs to be read for this column.
 * Mirrors the logic in cpp/include/mlt/metadata/type_map.hpp lines 85-122
 */
export declare function hasStreamCount(column: Column): boolean;
export declare function isLogicalIdColumn(column: Column): boolean;
export declare function isGeometryColumn(column: Column): boolean;
