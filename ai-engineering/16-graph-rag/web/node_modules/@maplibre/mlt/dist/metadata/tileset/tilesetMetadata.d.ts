export declare const ColumnScope: {
    readonly FEATURE: 0;
    readonly VERTEX: 1;
};
export declare const ScalarType: {
    readonly BOOLEAN: 0;
    readonly INT_8: 1;
    readonly UINT_8: 2;
    readonly INT_32: 3;
    readonly UINT_32: 4;
    readonly INT_64: 5;
    readonly UINT_64: 6;
    readonly FLOAT: 7;
    readonly DOUBLE: 8;
    readonly STRING: 9;
};
export declare const ComplexType: {
    readonly GEOMETRY: 0;
    readonly STRUCT: 1;
    readonly MAP: 2;
};
export declare const LogicalScalarType: {
    readonly ID: 0;
};
export declare const LogicalComplexType: {
    readonly BINARY: 0;
    readonly RANGE_MAP: 1;
};
export type TileSetMetadata = {
    version?: number;
    featureTables: FeatureTableSchema[];
    name?: string;
    description?: string;
    attribution?: string;
    minZoom?: number;
    maxZoom?: number;
    bounds: number[];
    center: number[];
};
export type FeatureTableSchema = {
    name: string;
    columns: Column[];
};
export type Column = {
    name: string;
    nullable: boolean;
    columnScope: number;
} & ({
    type: "scalarType";
    scalarType: ScalarColumn;
    complexType?: undefined;
} | {
    type: "complexType";
    complexType: ComplexColumn;
    scalarType?: undefined;
});
/** `Omit` that distributes over the union members of {@link Column}, preserving the `type` discriminant. */
export type ColumnWithoutName = Column extends infer C ? (C extends Column ? Omit<C, "name"> : never) : never;
export type ScalarColumn = {
    longID: boolean;
    physicalType?: number;
    logicalType?: number;
    type?: "physicalType" | "logicalType";
};
export type ComplexColumn = {
    physicalType?: number;
    logicalType?: number;
    children: Field[];
    type?: "physicalType" | "logicalType";
};
export type Field = {
    name?: string;
    nullable?: boolean;
} & ({
    type: "scalarField";
    scalarField: ScalarField;
    complexField?: undefined;
} | {
    type: "complexField";
    complexField: ComplexField;
    scalarField?: undefined;
});
export type ScalarField = {
    physicalType?: number;
    logicalType?: number;
    type?: "physicalType" | "logicalType";
};
export type ComplexField = {
    physicalType?: number;
    logicalType?: number;
    children: Field[];
    type?: "physicalType" | "logicalType";
};
