import { GpuVector } from "./gpuVector";
import type { TopologyVector } from "./topologyVector";
export declare function createFlatGpuVector(geometryTypes: Uint32Array, triangleOffsets: Uint32Array, indexBuffer: Uint32Array, vertexBuffer: Int32Array | Uint32Array, topologyVector?: TopologyVector): GpuVector;
export declare class FlatGpuVector extends GpuVector {
    private readonly _geometryTypes;
    constructor(_geometryTypes: Uint32Array, triangleOffsets: Uint32Array, indexBuffer: Uint32Array, vertexBuffer: Int32Array | Uint32Array, topologyVector?: TopologyVector);
    geometryType(index: number): number;
    get numGeometries(): number;
    containsSingleGeometryType(): boolean;
}
