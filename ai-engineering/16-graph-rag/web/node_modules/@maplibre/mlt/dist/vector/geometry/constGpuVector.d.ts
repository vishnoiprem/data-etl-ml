import { GpuVector } from "./gpuVector";
import type { TopologyVector } from "./topologyVector";
export declare function createConstGpuVector(numGeometries: number, geometryType: number, triangleOffsets: Uint32Array, indexBuffer: Uint32Array, vertexBuffer: Int32Array | Uint32Array, topologyVector?: TopologyVector): GpuVector;
export declare class ConstGpuVector extends GpuVector {
    private readonly _numGeometries;
    private readonly _geometryType;
    constructor(_numGeometries: number, _geometryType: number, triangleOffsets: Uint32Array, indexBuffer: Uint32Array, vertexBuffer: Int32Array | Uint32Array, topologyVector?: TopologyVector);
    geometryType(_index: number): number;
    get numGeometries(): number;
    containsSingleGeometryType(): boolean;
}
