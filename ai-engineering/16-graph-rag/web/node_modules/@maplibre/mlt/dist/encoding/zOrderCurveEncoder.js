export function encodeZOrderCurve(x, y, numBits, coordinateShift) {
    const shiftedX = x + coordinateShift;
    const shiftedY = y + coordinateShift;
    let code = 0;
    for (let i = 0; i < numBits; i++) {
        code |= ((shiftedX & (1 << i)) << i) | ((shiftedY & (1 << i)) << (i + 1));
    }
    return code;
}
//# sourceMappingURL=zOrderCurveEncoder.js.map