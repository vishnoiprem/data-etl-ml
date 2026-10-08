import { GpuVector } from "./gpuVector";
export function createFlatGpuVector(geometryTypes, triangleOffsets, indexBuffer, vertexBuffer, topologyVector) {
    return new FlatGpuVector(geometryTypes, triangleOffsets, indexBuffer, vertexBuffer, topologyVector);
}
//TODO: extend from GeometryVector -> make topology vector optional
export class FlatGpuVector extends GpuVector {
    constructor(_geometryTypes, triangleOffsets, indexBuffer, vertexBuffer, topologyVector) {
        super(triangleOffsets, indexBuffer, vertexBuffer, topologyVector);
        this._geometryTypes = _geometryTypes;
    }
    geometryType(index) {
        return this._geometryTypes[index];
    }
    get numGeometries() {
        return this._geometryTypes.length;
    }
    containsSingleGeometryType() {
        return false;
    }
}
//# sourceMappingURL=flatGpuVector.js.map