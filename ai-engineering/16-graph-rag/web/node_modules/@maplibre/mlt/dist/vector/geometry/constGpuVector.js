import { GpuVector } from "./gpuVector";
export function createConstGpuVector(numGeometries, geometryType, triangleOffsets, indexBuffer, vertexBuffer, topologyVector) {
    return new ConstGpuVector(numGeometries, geometryType, triangleOffsets, indexBuffer, vertexBuffer, topologyVector);
}
//TODO: extend from GeometryVector -> make topology vector optional
export class ConstGpuVector extends GpuVector {
    constructor(_numGeometries, _geometryType, triangleOffsets, indexBuffer, vertexBuffer, topologyVector) {
        super(triangleOffsets, indexBuffer, vertexBuffer, topologyVector);
        this._numGeometries = _numGeometries;
        this._geometryType = _geometryType;
    }
    geometryType(_index) {
        return this._geometryType;
    }
    get numGeometries() {
        return this._numGeometries;
    }
    containsSingleGeometryType() {
        return true;
    }
}
//# sourceMappingURL=constGpuVector.js.map