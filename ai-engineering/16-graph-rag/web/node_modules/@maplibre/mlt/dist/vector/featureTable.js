import { Int32FlatVector } from "./flat/int32FlatVector";
import { DoubleFlatVector } from "./flat/doubleFlatVector";
import { Int32SequenceVector } from "./sequence/int32SequenceVector";
import { Int32ConstVector } from "./constant/int32ConstVector";
export default class FeatureTable {
    constructor(_name, _geometryVector, _idVector, _propertyVectors, _extent = 4096) {
        this._name = _name;
        this._geometryVector = _geometryVector;
        this._idVector = _idVector;
        this._propertyVectors = _propertyVectors;
        this._extent = _extent;
        if (_name.length === 0) {
            throw new Error("Missing layer name");
        }
    }
    get name() {
        return this._name;
    }
    get idVector() {
        return this._idVector;
    }
    get geometryVector() {
        return this._geometryVector;
    }
    get propertyVectors() {
        return this._propertyVectors ?? [];
    }
    getPropertyVector(name) {
        if (!this.propertyVectorsMap) {
            this.propertyVectorsMap = new Map(this.propertyVectors.map((vector) => [vector.name, vector]));
        }
        return this.propertyVectorsMap.get(name);
    }
    get numFeatures() {
        return this.geometryVector.numGeometries;
    }
    get extent() {
        return this._extent;
    }
    /**
     * Returns all features as an array
     */
    getFeatures() {
        const features = [];
        const geometries = this.geometryVector.getGeometries();
        for (let i = 0; i < this.numFeatures; i++) {
            let id;
            if (this.idVector) {
                const idValue = this.idVector.getValue(i);
                if (idValue !== null) {
                    id = this.containsMaxSafeIntegerValues(this.idVector) ? Number(idValue) : idValue;
                }
            }
            const geometry = {
                coordinates: geometries[i],
                type: this.geometryVector.geometryType(i),
            };
            const properties = {};
            for (const propertyColumn of this.propertyVectors) {
                if (!propertyColumn)
                    continue;
                const columnName = propertyColumn.name;
                const propertyValue = propertyColumn.getValue(i);
                if (propertyValue !== null) {
                    properties[columnName] = propertyValue;
                }
            }
            features.push({ id, geometry, properties });
        }
        return features;
    }
    containsMaxSafeIntegerValues(idVector) {
        return (idVector instanceof Int32FlatVector ||
            idVector instanceof Int32ConstVector ||
            idVector instanceof Int32SequenceVector ||
            idVector instanceof DoubleFlatVector);
    }
}
//# sourceMappingURL=featureTable.js.map