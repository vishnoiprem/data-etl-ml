import type { Geometry, GeometryVector } from "./geometry/geometryVector";
import type Vector from "./vector";
import type { IdVector } from "./idVector";
import type { GpuVector } from "./geometry/gpuVector";
export interface Feature {
    id: number | bigint | undefined;
    geometry: Geometry;
    properties: {
        [key: string]: unknown;
    };
}
export default class FeatureTable {
    private readonly _name;
    private readonly _geometryVector;
    private readonly _idVector?;
    private readonly _propertyVectors?;
    private readonly _extent;
    private propertyVectorsMap?;
    constructor(_name: string, _geometryVector: GeometryVector | GpuVector, _idVector?: IdVector, _propertyVectors?: Vector[], _extent?: number);
    get name(): string;
    get idVector(): IdVector | undefined;
    get geometryVector(): GeometryVector | GpuVector;
    get propertyVectors(): Vector[];
    getPropertyVector(name: string): Vector | undefined;
    get numFeatures(): number;
    get extent(): number;
    /**
     * Returns all features as an array
     */
    getFeatures(): Feature[];
    private containsMaxSafeIntegerValues;
}
