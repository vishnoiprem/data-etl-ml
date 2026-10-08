import { createFlatGeometryVector } from "./flatGeometryVector";
export class GpuVector {
    constructor(_triangleOffsets, _indexBuffer, _vertexBuffer, _topologyVector) {
        this._triangleOffsets = _triangleOffsets;
        this._indexBuffer = _indexBuffer;
        this._vertexBuffer = _vertexBuffer;
        this._topologyVector = _topologyVector;
    }
    get triangleOffsets() {
        return this._triangleOffsets;
    }
    get indexBuffer() {
        return this._indexBuffer;
    }
    get vertexBuffer() {
        return this._vertexBuffer;
    }
    get topologyVector() {
        return this._topologyVector;
    }
    getGeometries() {
        if (!this._topologyVector) {
            throw new Error("Cannot convert GpuVector to coordinates without topology information");
        }
        const types = new Uint32Array(this.numGeometries);
        for (let i = 0; i < this.numGeometries; i++) {
            types[i] = this.geometryType(i);
        }
        return createFlatGeometryVector(types, this._topologyVector, undefined, this._vertexBuffer).getGeometries();
    }
    [Symbol.iterator]() {
        /*for(let i = 1; i < this.triangleOffsets.length; i++) {
           const numTriangles = this.triangleOffsets[i] - this.triangleOffsets[i-1];
           const startIndex = this.triangleOffsets[i-1] * 3;
           const endIndex = this.triangleOffsets[i] * 3;
       }

        while (index < this.numGeometries) {
            yield geometries[index++];
        }*/
        //throw new Error("Iterator on a GpuVector is not implemented yet.");
        return null;
    }
}
//# sourceMappingURL=gpuVector.js.map